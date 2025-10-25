"""
Project Structure Analysis Module

This module provides functionality to analyze project structure and provide
context to AI agents for better decision making.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectStructureAnalyzer:
    """Analyzes project structure and provides context for AI agents."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.structure_cache = None
        self.cache_timestamp = None
        
    async def get_project_structure(self, force_refresh: bool = False) -> Dict:
        """
        Get comprehensive project structure analysis.
        
        Args:
            force_refresh: Force refresh of cached structure
            
        Returns:
            Dictionary containing project structure information
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.info("[ProjectAnalyzer] Using cached structure")
            return self.structure_cache
            
        logger.info("[ProjectAnalyzer] Analyzing project structure...")
        
        structure = {
            "timestamp": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "files": [],
            "directories": [],
            "languages": {},
            "total_files": 0,
            "key_files": [],
            "file_types": {},
            "size_analysis": {},
            "git_info": {}
        }
        
        try:
            # Get tree structure
            tree_structure = await self._get_tree_structure()
            structure["tree"] = tree_structure
            
            # Analyze files and directories
            await self._analyze_files_and_directories(structure)
            
            # Analyze languages and file types
            await self._analyze_languages_and_types(structure)
            
            # Identify key files
            await self._identify_key_files(structure)
            
            # Get git information
            await self._get_git_info(structure)
            
            # Cache the result
            self.structure_cache = structure
            self.cache_timestamp = datetime.now()
            
            logger.info(f"[ProjectAnalyzer] Analysis complete: {structure['total_files']} files, {len(structure['languages'])} languages")
            return structure
            
        except Exception as e:
            logger.error(f"[ProjectAnalyzer] Error analyzing project structure: {e}")
            return structure
    
    async def _get_tree_structure(self) -> str:
        """Get tree structure using tree command."""
        try:
            # Try to use tree command if available
            result = subprocess.run(
                ["tree", "-a", "-I", "node_modules|.git|__pycache__|*.pyc", "--dirsfirst"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback to Python-based tree
                return await self._generate_python_tree()
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to Python-based tree
            return await self._generate_python_tree()
    
    async def _generate_python_tree(self) -> str:
        """Generate tree structure using Python when tree command is not available."""
        tree_lines = []
        
        def build_tree(path: Path, prefix: str = "", is_last: bool = True):
            if path.name.startswith('.') and path.name not in ['.gitignore', '.env.example']:
                return
                
            if path.name in ['node_modules', '__pycache__', '.git']:
                return
                
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")
            
            if path.is_dir():
                children = sorted([p for p in path.iterdir() if not p.name.startswith('.') or p.name in ['.gitignore', '.env.example']])
                for i, child in enumerate(children):
                    extension = "    " if is_last else "│   "
                    build_tree(child, prefix + extension, i == len(children) - 1)
        
        build_tree(self.repo_path)
        return "\n".join(tree_lines)
    
    async def _analyze_files_and_directories(self, structure: Dict):
        """Analyze files and directories in the project."""
        files = []
        directories = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for filename in filenames:
                if filename.startswith('.') and filename not in ['.gitignore', '.env.example']:
                    continue
                    
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(self.repo_path)
                
                try:
                    stat = file_path.stat()
                    files.append({
                        "path": str(relative_path),
                        "name": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": file_path.suffix,
                        "is_binary": self._is_binary_file(file_path)
                    })
                except (OSError, PermissionError):
                    continue
            
            # Add directories
            for dirname in dirs:
                dir_path = Path(root) / dirname
                relative_path = dir_path.relative_to(self.repo_path)
                directories.append({
                    "path": str(relative_path),
                    "name": dirname
                })
        
        structure["files"] = files
        structure["directories"] = directories
        structure["total_files"] = len(files)
    
    async def _analyze_languages_and_types(self, structure: Dict):
        """Analyze programming languages and file types."""
        languages = {}
        file_types = {}
        
        # Language detection based on file extensions
        language_extensions = {
            'Python': ['.py', '.pyx', '.pyi'],
            'JavaScript': ['.js', '.jsx', '.mjs'],
            'TypeScript': ['.ts', '.tsx'],
            'HTML': ['.html', '.htm'],
            'CSS': ['.css', '.scss', '.sass'],
            'JSON': ['.json'],
            'YAML': ['.yml', '.yaml'],
            'Markdown': ['.md'],
            'Shell': ['.sh', '.bash'],
            'Docker': ['.dockerfile', 'Dockerfile'],
            'SQL': ['.sql'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'Java': ['.java'],
            'C++': ['.cpp', '.cc', '.cxx'],
            'C': ['.c'],
            'PHP': ['.php'],
            'Ruby': ['.rb']
        }
        
        for file_info in structure["files"]:
            ext = file_info["extension"].lower()
            
            # Count file types
            file_types[ext] = file_types.get(ext, 0) + 1
            
            # Detect language
            for lang, extensions in language_extensions.items():
                if ext in extensions:
                    languages[lang] = languages.get(lang, 0) + 1
                    break
        
        structure["languages"] = languages
        structure["file_types"] = file_types
    
    async def _identify_key_files(self, structure: Dict):
        """Identify key files in the project."""
        key_files = []
        
        # Common key file patterns
        key_patterns = [
            'README.md', 'readme.md', 'README.rst',
            'package.json', 'requirements.txt', 'Pipfile',
            'Dockerfile', 'docker-compose.yml',
            'main.py', 'app.py', 'server.py', 'index.py',
            'main.js', 'index.js', 'app.js',
            'main.ts', 'index.ts', 'app.ts',
            'config.py', 'settings.py', 'config.json',
            'setup.py', 'pyproject.toml',
            'Makefile', 'makefile',
            '.gitignore', '.env.example',
            'LICENSE', 'CHANGELOG.md'
        ]
        
        for file_info in structure["files"]:
            filename = file_info["name"]
            if filename in key_patterns:
                key_files.append({
                    "path": file_info["path"],
                    "name": filename,
                    "type": "key_file",
                    "reason": "Common project file"
                })
        
        # Look for main application files
        main_files = [f for f in structure["files"] if f["name"] in ["main.py", "app.py", "server.py", "index.py", "main.js", "index.js"]]
        for file_info in main_files:
            key_files.append({
                "path": file_info["path"],
                "name": file_info["name"],
                "type": "main_file",
                "reason": "Main application entry point"
            })
        
        structure["key_files"] = key_files
    
    async def _get_git_info(self, structure: Dict):
        """Get git repository information."""
        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                structure["git_info"]["status"] = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                structure["git_info"]["current_branch"] = result.stdout.strip()
            
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                structure["git_info"]["recent_commits"] = result.stdout.strip()
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("[ProjectAnalyzer] Git information not available")
            structure["git_info"] = {"error": "Git not available"}
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except (OSError, PermissionError):
            return False
    
    def _is_cache_valid(self) -> bool:
        """Check if cached structure is still valid."""
        if not self.structure_cache or not self.cache_timestamp:
            return False
        
        # Cache valid for 5 minutes
        cache_age = datetime.now() - self.cache_timestamp
        return cache_age.total_seconds() < 300
    
    async def get_agent_context(self, agent_type: str) -> Dict:
        """
        Get project context specific to agent type.
        
        Args:
            agent_type: Type of agent (development, spec, coach, etc.)
            
        Returns:
            Agent-specific context information
        """
        structure = await self.get_project_structure()
        
        context = {
            "agent_type": agent_type,
            "project_overview": {
                "total_files": structure["total_files"],
                "languages": structure["languages"],
                "key_files": structure["key_files"]
            },
            "relevant_files": [],
            "suggestions": []
        }
        
        # Agent-specific file selection
        if agent_type == "development":
            context["relevant_files"] = [
                f for f in structure["files"] 
                if f["extension"] in [".py", ".js", ".ts", ".jsx", ".tsx"] 
                and not f["is_binary"]
            ][:20]  # Limit to 20 most relevant files
            
        elif agent_type == "spec":
            context["relevant_files"] = [
                f for f in structure["files"] 
                if f["name"] in ["README.md", "requirements.txt", "package.json", "pyproject.toml"]
            ]
            
        elif agent_type == "coach":
            context["relevant_files"] = [
                f for f in structure["files"] 
                if f["name"] in ["README.md", "CHANGELOG.md", "LICENSE"]
            ]
        
        return context
