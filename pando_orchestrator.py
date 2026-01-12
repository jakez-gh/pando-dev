"""
Pando Main Orchestrator - Starts and manages persistent Pando system

This is the single entry point that:
1. Starts Flask API server (non-blocking)
2. Starts multiple agent workers (non-blocking)
3. Starts RAG auto-indexing (background)
4. Monitors version health
5. Manages all processes (never stops unless told)
"""

import subprocess
import sys
import time
import threading
import logging
import os
from pathlib import Path
import json
from datetime import datetime
import signal
from pathlib import Path as _Path

import subprocess
import sys
import time
import threading
import logging
import os
from pathlib import Path
import json
from datetime import datetime

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('pando_orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PandoOrchestrator')

# Process management
PROCESSES = {}
PROCESS_LOCK = threading.Lock()


def start_process(name, command, args=None):
    """Start a long-running process (doesn't wait for it to finish)"""
    if args is None:
        args = []
    
    with PROCESS_LOCK:
        if name in PROCESSES and PROCESSES[name].poll() is None:
            logger.info(f"Process {name} already running (PID: {PROCESSES[name].pid})")
            return PROCESSES[name].pid
        
        full_command = [command] + args
        logger.info(f"Starting process {name}: {' '.join(full_command)}")
        
        try:
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            PROCESSES[name] = process
            logger.info(f"[OK] {name} started (PID: {process.pid})")
            
            # Log output in background thread
            def log_output(proc, proc_name):
                """Log process output as it comes"""
                for line in proc.stdout:
                    if line.strip():
                        logger.info(f"[{proc_name}] {line.rstrip()}")
            
            def log_error(proc, proc_name):
                """Log process stderr as errors"""
                for line in proc.stderr:
                    if line.strip():
                        logger.error(f"[{proc_name}][stderr] {line.rstrip()}")
            
            output_thread = threading.Thread(
                target=log_output,
                args=(process, name),
                daemon=True
            )
            output_thread.start()
            err_thread = threading.Thread(
                target=log_error,
                args=(process, name),
                daemon=True
            )
            err_thread.start()
            
            return process.pid
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return None


def monitor_processes():
    """Monitor all processes and restart if they die unexpectedly"""
    logger.info("Starting process monitor...")
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        
        with PROCESS_LOCK:
            for name, process in list(PROCESSES.items()):
                if process.poll() is not None:  # Process exited
                    logger.warning(f"⚠️  Process {name} exited with code {process.returncode}")
                    
                    # Restart based on type
                    if name == 'flask_api':
                        logger.info("Restarting Flask API...")
                        start_process('flask_api', sys.executable, ['pando_gui/backend/app.py'])
                    elif name.startswith('agent_'):
                        logger.info(f"Restarting {name}...")
                        start_process(name, sys.executable, ['agent.py'])


def start_rag_indexer():
    """Start RAG auto-indexing in background thread"""
    logger.info("Starting RAG auto-indexer...")
    
    def index_loop():
        """Continuously monitor for changes and index"""
        from pando_core.direction_api import get_direction_api
        import hashlib
        
        last_hash = None
        
        while True:
            try:
                # Check if code has changed
                git_status = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd()
                )
                current_hash = hashlib.md5(git_status.stdout.encode()).hexdigest()
                
                if current_hash != last_hash and git_status.stdout.strip():
                    logger.info("🔄 Changes detected, updating RAG index...")
                    # Gather metadata for RAG update visibility
                    try:
                        branch_proc = subprocess.run(
                            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                            capture_output=True, text=True, cwd=Path.cwd()
                        )
                        branch = branch_proc.stdout.strip() or 'unknown'

                        # Get changed file list
                        diff_proc = subprocess.run(
                            ['git', 'diff', '--name-only', 'HEAD'],
                            capture_output=True, text=True, cwd=Path.cwd()
                        )
                        changed_files = [f for f in diff_proc.stdout.splitlines() if f.strip()]

                        update_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'repo': Path.cwd().name,
                            'branch': branch,
                            'changed_files': changed_files,
                            'description': git_status.stdout.strip(),
                        }

                        # Persist RAG update metadata
                        with open('pando_rag_updates.jsonl', 'a', encoding='utf-8') as uf:
                            uf.write(json.dumps(update_entry) + "\n")

                        # Notify via message queue for visibility
                        try:
                            from pando_core.message_queue import get_message_queue
                            mq = get_message_queue()
                            mq.send('metric', 'pando', 'copilot', {'event':'rag_update', 'meta': update_entry})
                        except Exception:
                            logger.debug('Could not send RAG update message to queue')

                    except Exception as e:
                        logger.error(f'Error while collecting RAG metadata: {e}')

                    # Trigger indexer.py to update embeddings (non-blocking)
                    try:
                        venv_py_local = _Path('venv') / 'Scripts' / 'python.exe'
                        python_exec_local = str(venv_py_local) if venv_py_local.exists() else sys.executable
                        start_process('indexer', python_exec_local, ['indexer.py'])
                    except Exception as e:
                        logger.error(f'Failed to start indexer.py: {e}')

                    last_hash = current_hash
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"RAG indexer error: {e}")
                time.sleep(30)
    
    indexer_thread = threading.Thread(target=index_loop, daemon=True)
    indexer_thread.start()
    logger.info("✅ RAG auto-indexer started")


def create_system_version():
    """Create system version file if it doesn't exist"""
    # Prefer centralized version manager if available
    try:
        from pando_core.version_manager import get_version_manager
        vm = get_version_manager()
        return vm.current_version
    except Exception:
        # Fallback to a simple version file
        version_file = _Path('pando_version.json')
        if not version_file.exists():
            version_info = {
                "pando_version": "0.1.0",
                "created": datetime.now().isoformat(),
                "components": {
                    "core": "0.1.0",
                    "flask_api": "0.1.0",
                    "agents": "0.1.0",
                    "rag": "0.1.0",
                }
            }
            with open(version_file, 'w') as f:
                json.dump(version_info, f, indent=2)
            logger.info(f"✅ Created version file: {version_info}")
            return version_info

        with open(version_file) as f:
            return json.load(f)


def startup_health_check():
    """Verify all components are available before startup"""
    checks = {
        'config.py': Path('config.py').exists(),
        'pando_core': Path('pando_core').is_dir(),
        'pando_gui': Path('pando_gui').is_dir(),
        'Flask': check_import('flask'),
        'SocketIO': check_import('flask_socketio'),
    }
    
    logger.info("━━ STARTUP HEALTH CHECK ━━")
    all_ok = True
    for check, result in checks.items():
        status = "[OK]" if result else "[ERROR]"
        logger.info(f"  {status} {check}")
        if not result:
            all_ok = False
    
    if not all_ok:
        logger.error("[ERROR] Health check FAILED - cannot start Pando")
        sys.exit(1)
    
    logger.info("[OK] All health checks PASSED\n")
    return True


def check_import(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def print_startup_banner():
    """Print system startup banner"""
    banner = """
========================================================================
                PANDO AUTONOMOUS DEVELOPMENT SYSTEM
                    [STARTING ORCHESTRATOR]
========================================================================
System will run continuously without stopping
Pando will autonomously improve itself
Processes will restart if they fail
RAG database will auto-update
                    Pando is your team now
========================================================================
    """
    print(banner)


def main():
    """Main orchestrator entry point"""
    print_startup_banner()
    
    # Verify system is ready
    logger.info("Checking system health...")
    if not startup_health_check():
        sys.exit(1)
    
    # Create version tracking
    logger.info("Initializing version management...")
    version_info = create_system_version()
    logger.info(f"Pando Version: {version_info['pando_version']}")
    
    # Start RAG auto-indexer
    logger.info("Initializing RAG system...")
    start_rag_indexer()
    
    # Start Flask API (non-blocking)
    logger.info("\nStarting core services...")
    # Prefer the workspace virtualenv python if present
    venv_py = _Path('venv') / 'Scripts' / 'python.exe'
    python_exec = str(venv_py) if venv_py.exists() else sys.executable

    flask_pid = start_process(
        'flask_api',
        python_exec,
        ['pando_gui/backend/app.py']
    )
    
    # Give Flask time to start
    time.sleep(2)
    
    # Start agent workers (multiple instances for parallelism)
    logger.info("Starting agent workers...")
    for i in range(3):  # Start 3 agents initially
        start_process(
            f'agent_{i+1}',
            python_exec,
            ['agent.py']
        )
        time.sleep(1)
    
    # Start monitoring in background thread
    logger.info("Starting process monitor...")
    monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
    monitor_thread.start()
    
    # System ready
    logger.info("\n" + "="*80)
    logger.info("[OK] PANDO ORCHESTRATOR RUNNING")
    logger.info("="*80)
    logger.info(f"Flask API: http://localhost:5000")
    logger.info(f"Agents: {len([p for p in PROCESSES.keys() if p.startswith('agent_')])} active")
    logger.info(f"RAG Auto-Indexing: ENABLED")
    logger.info(f"Process Monitor: ACTIVE")
    logger.info("\nPando is now running autonomously. No stopping unless you kill this process.")


# Graceful shutdown handler that reports reason and notifies Pando message queue
def _shutdown_handler(signum, frame):
    reason = f"signal_{signum}"
    logger.warning(f"Shutting down Pando... reason={reason}")
    try:
        from pando_core.message_queue import get_message_queue
        mq = get_message_queue()
        mq.send('control', 'copilot', 'pando', {'action':'shutdown','reason':reason})
    except Exception:
        logger.debug("Could not notify message queue of shutdown")

    # Attempt to terminate child processes cleanly
    with PROCESS_LOCK:
        for name, proc in list(PROCESSES.items()):
            try:
                logger.info(f"Terminating {name} (PID: {getattr(proc,'pid',None)})")
                proc.terminate()
            except Exception:
                logger.debug(f"Failed to terminate process {name}")

    # Give processes a short time to exit, then force kill if still alive
    time.sleep(5)
    with PROCESS_LOCK:
        for name, proc in list(PROCESSES.items()):
            try:
                if proc.poll() is None:
                    logger.info(f"Killing {name} (PID: {getattr(proc,'pid',None)})")
                    proc.kill()
            except Exception:
                logger.debug(f"Failed to kill process {name}")

    # allow remaining cleanup then exit
    sys.exit(0)


# Register signals
signal.signal(signal.SIGINT, _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)
if __name__ == '__main__':
    # Start orchestrator
    main()

    # Immediately queue self-improvement tasks
    try:
        queue_self_improvement_tasks()
    except Exception:
        logger.debug('Could not queue self-improvement tasks')

    # Main loop - stay alive and report status periodically
    try:
        while True:
            time.sleep(60)
            active = sum(1 for p in PROCESSES.values() if p.poll() is None)
            logger.info(f"Status: {active}/{len(PROCESSES)} processes running")
    except KeyboardInterrupt:
        logger.info("\n\nShutting down Pando (KeyboardInterrupt)...")
        with PROCESS_LOCK:
            for name, process in PROCESSES.items():
                try:
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    logger.debug(f"Error stopping {name}")
        logger.info("✅ Pando shut down cleanly")
        sys.exit(0)


def queue_self_improvement_tasks():
    """Queue initial self-improvement tasks for Pando to work on"""
    try:
        from pando_core.direction_api import get_direction_api
        from pando_core.task_system import get_task_engine
        
        api = get_direction_api()
        
        # Self-improvement tasks
        improvements = [
            {
                "text": "Review and optimize the autonomy engine for better decision quality",
                "priority": "high"
            },
            {
                "text": "Add comprehensive unit tests for all core modules",
                "priority": "high"
            },
            {
                "text": "Implement advanced caching for RAG queries",
                "priority": "medium"
            },
            {
                "text": "Create monitoring dashboard showing system health metrics",
                "priority": "medium"
            },
            {
                "text": "Document all API endpoints with examples",
                "priority": "medium"
            }
        ]
        
        logger.info("[INFO] Queuing self-improvement tasks for Pando...")
        for improvement in improvements:
            direction = api.submit_direction(
                text=improvement['text'],
                priority=improvement['priority'],
                context="Self-improvement task queued by orchestrator"
            )
            logger.info(f"  [OK] Queued: {improvement['text'][:50]}...")
        
        logger.info(f"[INFO] Total tasks queued: {len(improvements)}")
        logger.info("[INFO] Pando will start working on these autonomously\n")
        
    except Exception as e:
        logger.error(f"[ERROR] Error queuing self-improvement tasks: {e}")


def auto_commit_and_push():
    """Background thread that commits and pushes repo changes every 5 minutes"""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            # Check if there are uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            if result.stdout.strip():
                # There are changes, commit and push
                subprocess.run(['git', 'add', '.'], cwd=Path.cwd(), capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'auto: pando work in progress'], cwd=Path.cwd(), capture_output=True)
                subprocess.run(['git', 'push'], cwd=Path.cwd(), capture_output=True)
                logger.info("✅ Auto-commit and push completed")
        except Exception as e:
            logger.error(f"Auto-commit/push error: {e}")


if __name__ == '__main__':
    # Start auto-commit/push background thread
    commit_thread = threading.Thread(target=auto_commit_and_push, daemon=True)
    commit_thread.start()
    logger.info("✅ Auto-commit/push daemon started")

    main()
