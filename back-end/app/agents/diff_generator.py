"""
Diff Generator

Utilities for generating diffs and patches.
"""

import difflib
import os
from typing import Optional, Tuple
from pathlib import Path


def generate_unified_diff(
    file_path: str,
    old_content: str,
    new_content: str,
    context_lines: int = 3
) -> str:
    """
    Generate unified diff between old and new content.
    
    Args:
        file_path: Path to file (for diff header)
        old_content: Current file content
        new_content: Proposed file content
        context_lines: Number of context lines
    
    Returns:
        Unified diff string
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=context_lines
    )
    
    return ''.join(diff)


def generate_git_patch(
    file_path: str,
    old_content: str,
    new_content: str
) -> str:
    """
    Generate Git-style patch.
    
    Args:
        file_path: Path to file
        old_content: Current content
        new_content: Proposed content
    
    Returns:
        Git patch string
    """
    diff = generate_unified_diff(file_path, old_content, new_content)
    
    # Add Git patch header
    patch = f"""diff --git a/{file_path} b/{file_path}
index 0000000..1111111 100644
--- a/{file_path}
+++ b/{file_path}
{diff}"""
    
    return patch


def apply_patch(
    file_path: str,
    patch: str,
    workspace_path: str
) -> Tuple[bool, Optional[str]]:
    """
    Apply patch to file.
    
    Args:
        file_path: Path to file (relative to workspace)
        patch: Unified diff or git patch
        workspace_path: Workspace root path
    
    Returns:
        (success, error_message)
    """
    full_path = Path(workspace_path) / file_path
    
    try:
        # Read current content
        if full_path.exists():
            with open(full_path, 'r') as f:
                current_content = f.read()
        else:
            current_content = ""
        
        # Parse patch and apply
        # For now, we'll use a simple approach
        # In production, use `patch` command or library like `unidiff`
        
        # Extract new content from patch
        # This is a simplified version - in production use proper patch library
        lines = patch.split('\n')
        new_lines = []
        in_diff = False
        
        for line in lines:
            if line.startswith('+++'):
                in_diff = True
                continue
            if in_diff:
                if line.startswith('+'):
                    new_lines.append(line[1:])
                elif line.startswith(' '):
                    new_lines.append(line[1:])
                elif line.startswith('-'):
                    continue  # Skip removed lines
        
        new_content = '\n'.join(new_lines)
        
        # Write new content
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(new_content)
        
        return True, None
    
    except Exception as e:
        return False, str(e)


def read_file_safe(file_path: str, workspace_path: str) -> str:
    """
    Safely read file content.
    
    Args:
        file_path: Path to file (relative to workspace)
        workspace_path: Workspace root path
    
    Returns:
        File content or empty string if not exists
    """
    full_path = Path(workspace_path) / file_path
    
    if not full_path.exists():
        return ""
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def generate_diff_summary(diff: str) -> dict:
    """
    Generate summary statistics from diff.
    
    Args:
        diff: Unified diff string
    
    Returns:
        Dict with additions, deletions, changes
    """
    lines = diff.split('\n')
    
    additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
    
    return {
        'additions': additions,
        'deletions': deletions,
        'changes': additions + deletions,
        'files_changed': 1  # For single file diff
    }

