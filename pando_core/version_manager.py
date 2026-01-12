"""
Pando Version Management System

Manages:
- Semantic versioning for all components
- Version history with auto-compaction
- Safe deployment and rollback
- Version monitoring
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages Pando versioning and deployment"""
    
    def __init__(self, version_file: str = "pando_version.json"):
        self.version_file = Path(version_file)
        self.history_file = Path("pando_version_history.jsonl")
        self.load_or_create()
    
    def load_or_create(self):
        """Load version info or create if doesn't exist"""
        if not self.version_file.exists():
            self.current_version = {
                "pando_version": "0.1.0",
                "created": datetime.now().isoformat(),
                "components": {
                    "autonomy_engine": "0.1.0",
                    "task_system": "0.1.0",
                    "direction_api": "0.1.0",
                    "async_comm": "0.1.0",
                    "repo_manager": "0.1.0",
                    "agent_coordinator": "0.1.0",
                    "message_bus": "0.1.0",
                    "flask_api": "0.1.0",
                }
            }
            self.save_version()
            logger.info(f"Created initial version: {self.current_version['pando_version']}")
        else:
            with open(self.version_file) as f:
                self.current_version = json.load(f)
            logger.info(f"Loaded version: {self.current_version['pando_version']}")
    
    def save_version(self):
        """Save current version to file"""
        with open(self.version_file, 'w') as f:
            json.dump(self.current_version, f, indent=2)
        
        # Log to history
        with open(self.history_file, 'a') as f:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "version": self.current_version['pando_version'],
                "components": self.current_version.get('components', {})
            }
            f.write(json.dumps(history_entry) + "\n")
    
    def increment_component(self, component: str, bump_type: str = 'patch'):
        """
        Increment component version
        
        bump_type: 'major', 'minor', or 'patch'
        """
        if component not in self.current_version['components']:
            self.current_version['components'][component] = "0.1.0"
        
        version_str = self.current_version['components'][component]
        parts = version_str.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        self.current_version['components'][component] = new_version
        
        logger.info(f"Version bumped: {component} {version_str} → {new_version}")
        self.save_version()
        
        return new_version
    
    def increment_pando(self, bump_type: str = 'patch'):
        """Increment main Pando version"""
        version_str = self.current_version['pando_version']
        parts = version_str.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        self.current_version['pando_version'] = new_version
        
        logger.info(f"Pando version bumped: {version_str} → {new_version}")
        self.save_version()
        
        return new_version
    
    def get_version(self, component: Optional[str] = None) -> str:
        """Get version of component or main Pando"""
        if component:
            return self.current_version['components'].get(component, "0.0.0")
        return self.current_version['pando_version']
    
    def compact_history(self, max_lines: int = 100):
        """Compact version history to keep file size down"""
        if not self.history_file.exists():
            return
        
        with open(self.history_file) as f:
            lines = f.readlines()
        
        if len(lines) <= max_lines:
            return  # No need to compact
        
        logger.info(f"Compacting version history ({len(lines)} → ~{max_lines} entries)")
        
        # Keep first, last, and sample from middle
        keep_indices = [0]  # First
        
        # Sample middle
        step = max(1, len(lines) // (max_lines - 2))
        keep_indices.extend(range(step, len(lines) - 1, step))
        
        keep_indices.append(len(lines) - 1)  # Last
        keep_indices = sorted(set(keep_indices))
        
        compacted = [lines[i] for i in keep_indices if i < len(lines)]
        
        with open(self.history_file, 'w') as f:
            f.writelines(compacted)
        
        logger.info(f"Version history compacted: {len(lines)} → {len(compacted)} entries")
    
    def get_history(self, limit: int = 10) -> list:
        """Get recent version history"""
        if not self.history_file.exists():
            return []
        
        with open(self.history_file) as f:
            lines = f.readlines()
        
        history = []
        for line in lines[-limit:]:
            if line.strip():
                history.append(json.loads(line))
        
        return history


# Singleton instance
_version_manager_instance = None


def get_version_manager() -> VersionManager:
    """Get or create singleton version manager"""
    global _version_manager_instance
    if _version_manager_instance is None:
        _version_manager_instance = VersionManager()
    return _version_manager_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    vm = get_version_manager()
    
    print(f"Current Pando version: {vm.get_version()}")
    print(f"Components: {json.dumps(vm.current_version['components'], indent=2)}")
    
    # Bump a version
    vm.increment_component('autonomy_engine', 'minor')
    vm.increment_pando('patch')
    
    print(f"\nNew Pando version: {vm.get_version()}")
    
    # Compact history
    vm.compact_history()
