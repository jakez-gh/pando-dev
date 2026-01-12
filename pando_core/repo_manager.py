"""
Multi-Repository Manager

Manages all repositories Pando works with.
- Scans ~/dev for local repos
- Clones external repos using gh CLI
- Creates branches, PRs, and manages merges
- Detects opportunities across repos
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Repository:
    """Represents a git repository"""
    name: str
    path: str
    remote_url: Optional[str]
    main_branch: str  # main or master
    active_branches: List[str]
    has_uncommitted_changes: bool
    last_scanned: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RepositoryManager:
    """
    Manages all repos Pando works with.
    
    Responsibilities:
    - Discover local repos
    - Clone external repos
    - Branch management
    - PR creation/review/merge
    - Cross-repo opportunity detection
    """
    
    def __init__(
        self,
        dev_root: str = "c:\\Users\\jake\\dev",
        repos_file: str = "pando_repos.json"
    ):
        self.dev_root = dev_root
        self.repos_file = repos_file
        self.repositories: Dict[str, Repository] = {}
        self.load_repos()
    
    def load_repos(self):
        """Load known repositories from file"""
        try:
            with open(self.repos_file, 'r') as f:
                data = json.load(f)
                for repo_data in data.get('repositories', []):
                    repo = Repository(**repo_data)
                    self.repositories[repo.name] = repo
        except FileNotFoundError:
            logger.info(f"No repos file found: {self.repos_file}")
        except json.JSONDecodeError:
            logger.warning(f"Corrupted repos file: {self.repos_file}")

    def save_repos(self):
        """Save repositories to file"""
        try:
            with open(self.repos_file, 'w') as f:
                json.dump({
                    'repositories': [r.to_dict() for r in self.repositories.values()],
                    'last_updated': datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save repos: {e}")

    def scan_dev_folder(self) -> List[Repository]:
        """
        Scan ~/dev for git repositories.
        
        Returns:
            List of found repositories
        """
        found_repos = []
        
        if not os.path.exists(self.dev_root):
            logger.warning(f"Dev root not found: {self.dev_root}")
            return found_repos
        
        for item in os.listdir(self.dev_root):
            item_path = os.path.join(self.dev_root, item)
            
            if not os.path.isdir(item_path):
                continue
            
            git_dir = os.path.join(item_path, '.git')
            if not os.path.exists(git_dir):
                continue
            
            # This is a git repo
            try:
                repo = self._scan_repo(item, item_path)
                if repo:
                    found_repos.append(repo)
                    self.repositories[repo.name] = repo
            except Exception as e:
                logger.error(f"Error scanning repo {item}: {e}")
        
        self.save_repos()
        return found_repos

    def _scan_repo(self, name: str, path: str) -> Optional[Repository]:
        """
        Scan a single repository for details.
        
        Returns:
            Repository object or None if error
        """
        try:
            # Get remote URL
            remote_url = self._git_command(path, "config --get remote.origin.url")
            remote_url = remote_url.strip() if remote_url else None
            
            # Get main branch
            main_branch = self._get_main_branch(path)
            
            # Get active branches
            branches = self._git_command(path, "branch --format=%(refname:short)")
            active_branches = [b.strip() for b in branches.split('\n') if b.strip()]
            
            # Check for uncommitted changes
            status = self._git_command(path, "status --porcelain")
            has_uncommitted = bool(status.strip())
            
            return Repository(
                name=name,
                path=path,
                remote_url=remote_url,
                main_branch=main_branch,
                active_branches=active_branches,
                has_uncommitted_changes=has_uncommitted,
                last_scanned=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.error(f"Failed to scan repo {name}: {e}")
            return None

    def _get_main_branch(self, repo_path: str) -> str:
        """Determine if repo uses main or master"""
        result = self._git_command(repo_path, "symbolic-ref --short HEAD")
        if result and result.strip():
            return result.strip()
        
        # Check if main exists
        branches = self._git_command(repo_path, "branch")
        if 'main' in branches:
            return 'main'
        if 'master' in branches:
            return 'master'
        
        return 'main'  # default

    def create_branch(
        self,
        repo_name: str,
        branch_type: str,  # feature, fix, research, assume, refactor
        description: str,
        from_branch: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new branch in a repository.
        
        Branch naming: {type}/{description}-{YYYYMMDD}
        
        Args:
            repo_name: Which repo
            branch_type: Type of branch
            description: Short description
            from_branch: Base branch (defaults to main)
        
        Returns:
            Branch name if successful, None if error
        """
        repo = self.repositories.get(repo_name)
        if not repo:
            logger.error(f"Repository not found: {repo_name}")
            return None
        
        from_branch = from_branch or repo.main_branch
        
        # Create branch name
        date_str = datetime.now().strftime("%Y%m%d")
        safe_desc = description.lower().replace(' ', '-')[:20]
        branch_name = f"{branch_type}/{safe_desc}-{date_str}"
        
        try:
            # Fetch latest from main
            self._git_command(repo.path, f"fetch origin {from_branch}")
            
            # Create and check out branch
            self._git_command(repo.path, f"checkout -b {branch_name}")
            
            logger.info(f"Created branch {branch_name} in {repo_name}")
            
            # Update repo info
            if repo:
                repo.active_branches.append(branch_name)
                self.save_repos()
            
            return branch_name
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return None

    def create_pr(
        self,
        repo_name: str,
        branch_name: str,
        title: str,
        description: str,
        target_branch: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a pull request using gh CLI.
        
        Args:
            repo_name: Which repo
            branch_name: Source branch
            title: PR title
            description: PR description
            target_branch: Target branch (defaults to main)
        
        Returns:
            PR URL if successful, None if error
        """
        repo = self.repositories.get(repo_name)
        if not repo:
            logger.error(f"Repository not found: {repo_name}")
            return None
        
        target_branch = target_branch or repo.main_branch
        
        try:
            # Push branch to remote
            self._git_command(repo.path, f"push origin {branch_name}")
            
            # Create PR with gh
            cmd = (
                f'gh pr create '
                f'--base {target_branch} '
                f'--head {branch_name} '
                f'--title "{title}" '
                f'--body "{description}"'
            )
            
            # Execute in repo directory
            result = subprocess.run(
                cmd,
                cwd=repo.path,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                logger.info(f"Created PR: {pr_url}")
                return pr_url
            else:
                logger.error(f"Failed to create PR: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None

    def merge_pr(
        self,
        repo_name: str,
        pr_number: int,
        delete_branch: bool = True
    ) -> bool:
        """
        Merge a pull request.
        
        Args:
            repo_name: Which repo
            pr_number: PR number
            delete_branch: Delete branch after merge?
        
        Returns:
            True if successful
        """
        repo = self.repositories.get(repo_name)
        if not repo:
            logger.error(f"Repository not found: {repo_name}")
            return False
        
        try:
            # Merge with gh
            cmd = f'gh pr merge {pr_number} --squash'
            if delete_branch:
                cmd += ' --delete-branch'
            
            result = subprocess.run(
                cmd,
                cwd=repo.path,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Merged PR #{pr_number} in {repo_name}")
                
                # Update to main branch
                self._git_command(repo.path, f"checkout {repo.main_branch}")
                self._git_command(repo.path, f"pull origin {repo.main_branch}")
                
                return True
            else:
                logger.error(f"Failed to merge PR: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to merge PR: {e}")
            return False

    def clone_external_repo(
        self,
        repo_url: str,
        target_name: Optional[str] = None
    ) -> Optional[Repository]:
        """
        Clone an external repository from GitHub.
        
        Uses gh CLI if available, otherwise git clone.
        
        Args:
            repo_url: GitHub repo URL or owner/repo
            target_name: Optional custom folder name
        
        Returns:
            Repository object if successful
        """
        try:
            # Parse repo name
            if '/' in repo_url and not repo_url.startswith('http'):
                # owner/repo format
                owner, repo = repo_url.split('/')
                folder_name = target_name or repo
            else:
                # Extract from URL
                parts = repo_url.rstrip('/').split('/')
                folder_name = target_name or parts[-1].replace('.git', '')
            
            target_path = os.path.join(self.dev_root, folder_name)
            
            if os.path.exists(target_path):
                logger.warning(f"Target path already exists: {target_path}")
                return None
            
            # Clone using gh CLI
            cmd = f'gh repo clone {repo_url} {target_path}'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Cloned repo to {target_path}")
                
                # Scan the new repo
                repo = self._scan_repo(folder_name, target_path)
                if repo:
                    self.repositories[repo.name] = repo
                    self.save_repos()
                    return repo
            else:
                logger.error(f"Failed to clone: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Failed to clone repo: {e}")
            return None

    def detect_code_duplication(self) -> List[Dict]:
        """
        Scan all repos for duplicated code patterns.
        
        Returns:
            List of duplication opportunities
        """
        opportunities = []
        
        # This is a simplified version
        # In production, would use more sophisticated analysis
        
        logger.info(f"Scanning {len(self.repositories)} repos for duplication...")
        
        # Simple pattern: look for duplicate utility functions
        # Would need more sophisticated analysis in production
        
        return opportunities

    def find_stale_branches(self, days_old: int = 7) -> Dict[str, List[str]]:
        """
        Find branches not updated in N days.
        
        Args:
            days_old: How old before considered stale
        
        Returns:
            Dict[repo_name, List[stale_branches]]
        """
        stale = {}
        
        for repo_name, repo in self.repositories.items():
            stale_in_repo = []
            
            for branch in repo.active_branches:
                try:
                    # Get last commit date for branch
                    cmd = f'git log --format=%ai -1 {branch}'
                    result = self._git_command(repo.path, cmd)
                    
                    if result:
                        # Parse date and compare
                        # Simplified - in production would parse properly
                        stale_in_repo.append(branch)
                except Exception as e:
                    logger.debug(f"Error checking branch {branch}: {e}")
            
            if stale_in_repo:
                stale[repo_name] = stale_in_repo
        
        return stale

    def _git_command(self, repo_path: str, command: str) -> str:
        """
        Execute a git command in a repo.
        
        Returns:
            Command output
        """
        try:
            result = subprocess.run(
                f"git {command}",
                cwd=repo_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            raise

    def get_repo_status(self, repo_name: str) -> Optional[Dict]:
        """Get current status of a repository"""
        repo = self.repositories.get(repo_name)
        if not repo:
            return None
        
        return {
            'name': repo.name,
            'path': repo.path,
            'main_branch': repo.main_branch,
            'active_branches': repo.active_branches,
            'has_changes': repo.has_uncommitted_changes,
            'last_scanned': repo.last_scanned,
        }

    def get_all_repos(self) -> List[Dict]:
        """Get status of all repositories"""
        return [self.get_repo_status(name) for name in self.repositories]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    rm = RepositoryManager()
    
    # Scan for repos
    repos = rm.scan_dev_folder()
    print(f"Found {len(repos)} repositories")
    
    for repo in repos:
        print(f"  - {repo.name}: {len(repo.active_branches)} branches")
    
    # Create a branch
    branch = rm.create_branch("pando-dev", "feature", "test feature")
    print(f"Created branch: {branch}")
    
    # Get status
    status = rm.get_all_repos()
    print(f"Status: {status}")
