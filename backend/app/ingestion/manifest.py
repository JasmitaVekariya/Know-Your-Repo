"""Manifest generation for repository metadata and structure."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

# Tech stack detection patterns
TECH_STACK_PATTERNS = {
    'python': ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock'],
    'javascript': ['.js', 'package.json', 'yarn.lock', 'package-lock.json'],
    'typescript': ['.ts', '.tsx', 'tsconfig.json'],
    'nodejs': ['package.json', 'node_modules'],
    'react': ['react', 'react-dom', 'jsx', '.jsx'],
    'vue': ['.vue', 'vue.config.js'],
    'angular': ['angular.json', '.angular'],
    'java': ['.java', 'pom.xml', 'build.gradle', 'gradle.properties'],
    'cpp': ['.cpp', '.hpp', '.h', 'CMakeLists.txt', 'Makefile'],
    'c': ['.c', '.h', 'Makefile'],
    'go': ['.go', 'go.mod', 'go.sum'],
    'rust': ['.rs', 'Cargo.toml', 'Cargo.lock'],
    'ruby': ['.rb', 'Gemfile', 'Rakefile'],
    'php': ['.php', 'composer.json'],
    'swift': ['.swift', 'Package.swift'],
    'kotlin': ['.kt', 'build.gradle.kts'],
    'scala': ['.scala', 'build.sbt'],
    'docker': ['Dockerfile', 'docker-compose.yml'],
    'kubernetes': ['.yaml', '.yml'],  # K8s manifests
    'terraform': ['.tf', '.tfvars'],
    'html': ['.html', '.htm'],
    'css': ['.css', '.scss', '.sass', '.less'],
}

# Entry point heuristics
ENTRY_POINT_PATTERNS = [
    # Python
    'main.py', 'app.py', 'index.py', '__main__.py', 'run.py', 'server.py',
    'manage.py', 'wsgi.py', 'asgi.py',
    # JavaScript/TypeScript
    'index.js', 'app.js', 'server.js', 'main.js', 'index.ts', 'app.ts', 'server.ts',
    # Java
    'Main.java', 'Application.java',
    # Go
    'main.go',
    # Rust
    'main.rs', 'lib.rs',
    # C/C++
    'main.cpp', 'main.c',
    # HTML
    'index.html',
]

# Config file patterns
CONFIG_FILE_PATTERNS = [
    'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
    'tsconfig.json', 'webpack.config.js', 'jest.config.js',
    'docker-compose.yml', 'Dockerfile', '.env', '.env.example',
    'config.py', 'settings.py', 'config.js', 'config.ts',
    'go.mod', 'Cargo.toml', 'Gemfile', 'composer.json',
    'CMakeLists.txt', 'Makefile', 'pyproject.toml',
]


def generate_repo_manifest(repo_path: str, file_list: List[str]) -> Dict[str, Any]:
    """
    Generate a manifest of repository structure and metadata.
    
    This function creates a summary document containing:
    - Repository structure (file tree)
    - Key files and their purposes
    - Dependencies and configuration files
    - README and documentation references
    
    Args:
        repo_path: Local path to cloned repository
        file_list: List of file paths in the repository (relative to repo root)
        
    Returns:
        Dictionary containing manifest data:
        {
            "repo_name": str,
            "tech_stack": List[str],
            "entry_points": List[str],
            "core_modules": List[str],
            "config_files": List[str],
            "test_presence": bool,
            "architecture_summary": str
        }
    """
    repo_path_obj = Path(repo_path)
    repo_name = repo_path_obj.name
    
    # Detect tech stack
    tech_stack = detect_tech_stack(file_list)
    
    # Detect entry points
    entry_points = detect_entry_points(repo_path_obj, file_list)
    
    # Identify core modules
    core_modules = identify_core_modules(file_list)
    
    # Find config files
    config_files = find_config_files(file_list)
    
    # Check for test presence
    test_presence = has_tests(file_list)
    
    # Generate architecture summary
    architecture_summary = generate_architecture_summary(
        tech_stack, entry_points, core_modules, config_files, test_presence
    )
    
    manifest = {
        "repo_name": repo_name,
        "tech_stack": tech_stack,
        "entry_points": entry_points,
        "core_modules": core_modules,
        "config_files": config_files,
        "test_presence": test_presence,
        "architecture_summary": architecture_summary
    }
    
    logger.info(f"Generated manifest for {repo_name}: {len(tech_stack)} tech stack items, {len(entry_points)} entry points")
    
    return manifest


def detect_tech_stack(file_list: List[str]) -> List[str]:
    """
    Detect technology stack from file extensions and config files.
    
    Args:
        file_list: List of file paths
        
    Returns:
        List of detected technologies
    """
    detected_techs: Set[str] = set()
    file_names_lower = [f.lower() for f in file_list]
    
    # Check for tech stack patterns
    for tech, patterns in TECH_STACK_PATTERNS.items():
        for pattern in patterns:
            # Check file extensions
            if pattern.startswith('.'):
                if any(f.endswith(pattern) for f in file_list):
                    detected_techs.add(tech)
            # Check file names
            elif any(pattern in f for f in file_names_lower):
                detected_techs.add(tech)
    
    # Special handling for frameworks
    if 'javascript' in detected_techs or 'typescript' in detected_techs:
        # Check for frameworks
        all_files_str = ' '.join(file_names_lower)
        if 'react' in all_files_str or 'jsx' in all_files_str:
            detected_techs.add('react')
        if 'vue' in all_files_str:
            detected_techs.add('vue')
        if 'angular' in all_files_str:
            detected_techs.add('angular')
    
    return sorted(list(detected_techs))


def detect_entry_points(repo_path: Path, file_list: List[str]) -> List[str]:
    """
    Detect entry points using heuristics.
    
    Args:
        repo_path: Path to repository root
        file_list: List of file paths
        
    Returns:
        List of entry point file paths
    """
    entry_points = []
    
    # 1. Check for specific entry point patterns (Exact and Suffix)
    for file_path in file_list:
        file_name = Path(file_path).name.lower() # Case insensitive
        
        # Exact match check
        if file_name in ENTRY_POINT_PATTERNS:
            entry_points.append(file_path)
            continue
            
        # Suffix match for patterns like *Application.java
        # We check specific suffixes known to be entry points
        entry_suffixes = [
            'application.java', 'app.java',
            'main.kt', 'app.kt',
            'application.kt'
        ]
        
        if any(file_name.endswith(suffix) for suffix in entry_suffixes):
             entry_points.append(file_path)
             continue

    # 2. Check for entry point patterns in root directory (Highest priority)
    root_files = [f for f in file_list if '/' not in f or f.count('/') == 0]
    for root_file in root_files:
        file_name = Path(root_file).name.lower()
        # Fallback for generic 'app' or 'main' in root
        if file_name.startswith('main.') or file_name.startswith('app.') or \
           file_name.startswith('index.') or file_name.startswith('server.'):
            if root_file not in entry_points:
                entry_points.append(root_file)
    
    # 3. Check src/main directories
    src_main_files = [f for f in file_list if 'src/main' in f.lower() or 'src/index' in f.lower()]
    for src_file in src_main_files:
        file_name = Path(src_file).name.lower()
        # More aggressive check in src/main
        if 'main' in file_name or 'app' in file_name or 'index' in file_name:
             if any(file_name.endswith(ext) for ext in ['.java', '.py', '.js', '.ts', '.cpp', '.c', '.go']):
                 if src_file not in entry_points:
                     entry_points.append(src_file)
    
    # 4. Fallback: Scan root files again for loose code files if nothing found
    if not entry_points:
        for file_path in file_list:
            # Only check root or first level
            if file_path.count('/') <= 1:
                file_name = Path(file_path).name.lower()
                if ('main' in file_name or 'app' in file_name) and \
                   any(file_name.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go']):
                    entry_points.append(file_path)
                    break
    
    return sorted(list(set(entry_points)))


def identify_core_modules(file_list: List[str]) -> List[str]:
    """
    Identify core modules (non-test, non-config, non-doc files).
    
    Args:
        file_list: List of file paths
        
    Returns:
        List of core module file paths
    """
    core_modules = []
    
    for file_path in file_list:
        path_lower = file_path.lower()
        name_lower = Path(file_path).name.lower()
        
        # Skip tests
        if 'test' in path_lower or 'spec' in path_lower:
            continue
        
        # Skip config files
        if name_lower in [f.lower() for f in CONFIG_FILE_PATTERNS]:
            continue
        
        # Skip documentation
        if name_lower.endswith('.md') or 'doc' in path_lower:
            continue
        
        # Include code files
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
        if any(file_path.endswith(ext) for ext in code_extensions):
            core_modules.append(file_path)
    
    # Limit to top 20 core modules to avoid overwhelming
    return sorted(core_modules)[:20]


def find_config_files(file_list: List[str]) -> List[str]:
    """
    Find configuration files.
    
    Args:
        file_list: List of file paths
        
    Returns:
        List of config file paths
    """
    config_files = []
    file_names_lower = [Path(f).name.lower() for f in file_list]
    
    for file_path in file_list:
        file_name = Path(file_path).name.lower()
        if file_name in [f.lower() for f in CONFIG_FILE_PATTERNS]:
            config_files.append(file_path)
    
    return sorted(config_files)


def has_tests(file_list: List[str]) -> bool:
    """
    Check if repository has test files.
    
    Args:
        file_list: List of file paths
        
    Returns:
        True if tests are present
    """
    test_indicators = ['test', 'spec', '__test__', '__tests__']
    
    for file_path in file_list:
        path_lower = file_path.lower()
        if any(indicator in path_lower for indicator in test_indicators):
            return True
    
    return False


def generate_architecture_summary(
    tech_stack: List[str],
    entry_points: List[str],
    core_modules: List[str],
    config_files: List[str],
    test_presence: bool
) -> str:
    """
    Generate a text summary of the repository architecture.
    
    Args:
        tech_stack: List of detected technologies
        entry_points: List of entry point files
        core_modules: List of core module files
        config_files: List of config files
        test_presence: Whether tests are present
        
    Returns:
        Architecture summary text
    """
    summary_parts = []
    
    # Tech stack
    if tech_stack:
        summary_parts.append(f"Technology Stack: {', '.join(tech_stack)}")
    else:
        summary_parts.append("Technology Stack: Unknown")
    
    # Entry points
    if entry_points:
        summary_parts.append(f"Entry Points: {', '.join(entry_points[:5])}")  # Limit to 5
    else:
        summary_parts.append("Entry Points: Not detected")
    
    # Core modules
    if core_modules:
        summary_parts.append(f"Core Modules: {len(core_modules)} identified")
    else:
        summary_parts.append("Core Modules: None identified")
    
    # Config files
    if config_files:
        summary_parts.append(f"Configuration Files: {len(config_files)} found")
    
    # Tests
    summary_parts.append(f"Tests: {'Present' if test_presence else 'Not found'}")
    
    return "\n".join(summary_parts)


def extract_key_files(file_list: List[str]) -> Dict[str, List[str]]:
    """
    Extract key files from repository (README, config files, etc.).
    
    Args:
        file_list: List of file paths in the repository
        
    Returns:
        Dictionary mapping file categories to file paths
    """
    key_files = {
        'readme': [],
        'license': [],
        'config': [],
        'docker': [],
        'ci_cd': [],
    }
    
    for file_path in file_list:
        name_lower = Path(file_path).name.lower()
        
        if 'readme' in name_lower:
            key_files['readme'].append(file_path)
        elif 'license' in name_lower:
            key_files['license'].append(file_path)
        elif name_lower in ['dockerfile', 'docker-compose.yml']:
            key_files['docker'].append(file_path)
        elif name_lower in ['.github', '.gitlab-ci.yml', 'jenkinsfile']:
            key_files['ci_cd'].append(file_path)
        elif name_lower in [f.lower() for f in CONFIG_FILE_PATTERNS]:
            key_files['config'].append(file_path)
    
    return key_files


def build_file_tree(file_list: List[str]) -> Dict[str, Any]:
    """
    Build a tree structure representation of repository files.
    
    Args:
        file_list: List of file paths in the repository
        
    Returns:
        Nested dictionary representing file tree
    """
    tree = {}
    
    for file_path in file_list:
        parts = file_path.split('/')
        current = tree
        
        for part in parts[:-1]:  # All but last part (directory path)
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add file
        filename = parts[-1]
        if 'files' not in current:
            current['files'] = []
        current['files'].append(filename)
    
    return tree
