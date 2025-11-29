"""
Style and consistency checker for the Circular Exchange framework.

This module ensures all code in the repository follows consistent patterns,
reducing the "AI-generated" feel that comes from disconnected prompts.

Run this to check and fix style issues:
    python -m shared.circular_exchange.style_checker --fix
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class StyleIssue:
    """A detected style issue."""
    file_path: str
    line_number: int
    issue_type: str
    message: str
    suggestion: str
    auto_fix: Optional[str] = None


class StyleChecker:
    """
    Checks code for consistency and reduces AI-generated feel.
    
    Rules:
    1. No generic phrases like "This module provides..."
    2. Docstrings must be specific, not boilerplate
    3. Comments should explain WHY, not WHAT
    4. Consistent import ordering
    5. Connected references between files
    """
    
    # Phrases that indicate generic AI text
    GENERIC_PHRASES = [
        r"This module provides",
        r"This class implements",
        r"This function handles",
        r"enterprise-grade",
        r"production-ready",
        r"best practices",
        r"industry standard",
        r"state-of-the-art",
        r"cutting-edge",
        r"robust and scalable",
        r"highly optimized",
        r"seamlessly integrates",
    ]
    
    # Required connections between modules
    MODULE_CONNECTIONS = {
        "shared/models/__init__.py": ["shared/circular_exchange"],
        "shared/utils/__init__.py": ["shared/circular_exchange"],
        "shared/__init__.py": ["shared/circular_exchange/project_config"],
        "web-app/backend/app.py": ["shared"],
    }
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[StyleIssue] = []
    
    def check_file(self, file_path: Path) -> List[StyleIssue]:
        """Check a single file for style issues."""
        issues = []
        
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Check for generic phrases
            for i, line in enumerate(lines, 1):
                for phrase in self.GENERIC_PHRASES:
                    if re.search(phrase, line, re.IGNORECASE):
                        issues.append(StyleIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="generic_phrase",
                            message=f"Generic phrase detected: '{phrase}'",
                            suggestion="Replace with specific, contextual description"
                        ))
            
            # Check for missing circular exchange integration
            rel_path = str(file_path.relative_to(self.project_root))
            if rel_path in self.MODULE_CONNECTIONS:
                for required in self.MODULE_CONNECTIONS[rel_path]:
                    if required not in content:
                        issues.append(StyleIssue(
                            file_path=str(file_path),
                            line_number=1,
                            issue_type="missing_connection",
                            message=f"Missing connection to {required}",
                            suggestion=f"Add import from {required}"
                        ))
            
            # Check for boilerplate docstrings
            if '"""' in content:
                docstring_pattern = r'"""[^"]*"""'
                for match in re.finditer(docstring_pattern, content, re.DOTALL):
                    docstring = match.group()
                    if len(docstring) < 20:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(StyleIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type="short_docstring",
                            message="Docstring too short to be meaningful",
                            suggestion="Expand with specific details"
                        ))
            
        except Exception as e:
            issues.append(StyleIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="parse_error",
                message=str(e),
                suggestion="Fix syntax error"
            ))
        
        return issues
    
    def check_all(self) -> List[StyleIssue]:
        """Check all Python files in the project."""
        self.issues = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if ".git" in str(py_file):
                continue
            
            self.issues.extend(self.check_file(py_file))
        
        return self.issues
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of issues by type."""
        summary = {}
        for issue in self.issues:
            summary[issue.issue_type] = summary.get(issue.issue_type, 0) + 1
        return summary


def make_specific(generic_text: str, context: str) -> str:
    """
    Convert generic text to specific text based on context.
    
    Example:
        generic: "This module provides functionality for..."
        context: "OCR processing"
        result: "Handles OCR text extraction from receipt images"
    """
    replacements = {
        "This module provides": f"Handles {context}",
        "This class implements": f"Manages {context}",
        "This function handles": f"Processes {context}",
    }
    
    result = generic_text
    for generic, specific in replacements.items():
        result = result.replace(generic, specific)
    
    return result


if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent.parent
    checker = StyleChecker(str(project_root))
    
    issues = checker.check_all()
    
    if issues:
        print(f"Found {len(issues)} style issues:\n")
        for issue in issues[:20]:  # Show first 20
            print(f"  {issue.file_path}:{issue.line_number}")
            print(f"    {issue.issue_type}: {issue.message}")
            print(f"    Suggestion: {issue.suggestion}\n")
        
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more issues")
        
        print("\nSummary:")
        for issue_type, count in checker.get_summary().items():
            print(f"  {issue_type}: {count}")
    else:
        print("No style issues found!")
