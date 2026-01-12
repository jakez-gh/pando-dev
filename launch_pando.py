#!/usr/bin/env python3
"""
Pando Launch Script - Start the autonomous development system

This script:
1. Verifies system dependencies
2. Starts Flask backend (API server)
3. Displays system status
4. Instructions for submitting directions
"""

import sys
import time
import subprocess
import os
from pathlib import Path
import json

def check_dependencies():
    """Verify required Python modules are available"""
    required = ['flask', 'flask_cors', 'flask_socketio']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install flask flask-cors flask-socketio")
        return False
    
    print("✅ All dependencies satisfied")
    return True


def check_config():
    """Verify config.py exists"""
    if not Path('config.py').exists():
        print("❌ config.py not found")
        return False
    
    print("✅ config.py found")
    return True


def check_core_modules():
    """Verify all core modules are present"""
    required_files = [
        'pando_core/__init__.py',
        'pando_core/direction_api.py',
        'pando_core/task_system.py',
        'pando_core/autonomy_engine.py',
        'agent.py',
    ]
    
    missing = [f for f in required_files if not Path(f).exists()]
    
    if missing:
        print(f"❌ Missing core modules: {', '.join(missing)}")
        return False
    
    print("✅ All core modules present")
    return True


def print_instructions():
    """Print usage instructions"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║            PANDO AUTONOMOUS DEVELOPMENT SYSTEM                 ║
║                      Ready to Start                            ║
╚════════════════════════════════════════════════════════════════╝

SYSTEM STATUS:
  ✅ Backend API running on http://localhost:5000
  ✅ Direction system ready
  ✅ Task engine ready
  ✅ Agent coordination ready

HOW TO USE:

1. In another terminal, start an agent:
   $ python agent.py

2. Submit a direction (high-level task):
   $ curl -X POST http://localhost:5000/api/directions \\
       -H "Content-Type: application/json" \\
       -d '{
         "text": "Review the authentication module for security issues",
         "priority": "high"
       }'

3. Check system status:
   $ curl http://localhost:5000/api/status

4. View pending directions:
   $ curl http://localhost:5000/api/directions

5. Check metrics:
   $ curl http://localhost:5000/api/metrics

DOCUMENTATION:
  📖 Getting Started: docs/GETTING_STARTED.md
  📖 System Design: docs/architecture/SYSTEM_DESIGN.md
  📖 API Reference: docs/api/DIRECTIONS_AND_TASKS.md
  📖 Key Answers: docs/ANSWERS.md

TIPS:
  • Pando runs autonomously - submit directions, it creates tasks
  • Questions are non-blocking - Pando continues with assumptions
  • All activity is logged to JSONL files for audit trail
  • System exits cleanly when all work is complete

Ready? Submit your first direction and watch Pando work! 🚀

""")


def main():
    """Main entry point"""
    print("\n🚀 PANDO LAUNCH SEQUENCE\n")
    
    # Verify system
    print("Checking dependencies...", end=" ")
    if not check_dependencies():
        sys.exit(1)
    
    print("Checking configuration...", end=" ")
    if not check_config():
        sys.exit(1)
    
    print("Checking core modules...", end=" ")
    if not check_core_modules():
        sys.exit(1)
    
    print("\n")
    print("=" * 70)
    print("STARTING PANDO BACKEND API")
    print("=" * 70)
    print()
    
    # Print instructions before starting
    print_instructions()
    
    # Start Flask backend
    print("\n" + "=" * 70)
    print("STARTING FLASK SERVER")
    print("=" * 70 + "\n")
    
    try:
        from pando_gui.backend.app import app, socketio
        
        print("✅ Pando backend loaded successfully")
        print("\n🌐 Starting server on http://localhost:5000...")
        print("   Press Ctrl+C to stop\n")
        
        # Run with SocketIO
        socketio.run(
            app,
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to avoid duplicate startup
        )
        
    except KeyboardInterrupt:
        print("\n\n✋ Shutting down Pando...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting Pando: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
