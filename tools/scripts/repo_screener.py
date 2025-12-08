"""
Repository Screening Tool - Analyzes codebase for missing functions, files, and inconsistencies

This tool screens the entire repository to identify:
1. Missing function implementations (declared but not defined)
2. Orphaned imports (imported but never used)
3. Missing test coverage
4. Inconsistencies between documentation and code
5. Missing files referenced in imports
6. Unused functions and classes
"""

import ast
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    path: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    exports: List[str]
    docstring: str
    line_count: int
    has_tests: bool
    errors: List[str]


@dataclass
class RepositoryReport:
    """Complete repository analysis report."""
    total_files: int
    total_python_files: int
    total_javascript_files: int
    total_functions: int
    total_classes: int
    missing_implementations: List[Dict[str, Any]]
    orphaned_imports: List[Dict[str, Any]]
    missing_tests: List[str]
    missing_files: List[Dict[str, Any]]
    unused_functions: List[Dict[str, Any]]
    documentation_mismatches: List[Dict[str, Any]]
    file_analyses: List[FileAnalysis]


class RepositoryScreener:
    """Comprehensive repository analysis tool."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.python_files: List[Path] = []
        self.javascript_files: List[Path] = []
        self.file_analyses: Dict[str, FileAnalysis] = {}
        self.all_functions: Dict[str, Set[str]] = defaultdict(set)  # file -> functions
        self.all_classes: Dict[str, Set[str]] = defaultdict(set)  # file -> classes
        self.all_imports: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # file -> [(module, name)]
        self.test_files: Set[str] = set()
        
        # Patterns to exclude
        self.exclude_patterns = [
            '*/node_modules/*',
            '*/__pycache__/*',
            '*/venv/*',
            '*/env/*',
            '*/.git/*',
            '*/migrations/*',
            '*/logs/*',
            '*.pyc',
            '*.pyo',
            '*/.pytest_cache/*',
            '*/htmlcov/*',
            '*/.coverage',
            '*/dist/*',
            '*/build/*',
            '*.min.js'
        ]
    
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if Path(path_str).match(pattern):
                return True
        return False
    
    def discover_files(self):
        """Discover all Python and JavaScript files in the repository."""
        print("🔍 Discovering files...")
        
        for path in self.repo_root.rglob('*'):
            if not path.is_file() or self.should_exclude(path):
                continue
            
            if path.suffix == '.py':
                self.python_files.append(path)
                if 'test' in path.name or 'test' in str(path.parent):
                    self.test_files.add(str(path.relative_to(self.repo_root)))
            elif path.suffix == '.js':
                self.javascript_files.append(path)
        
        print(f"   Found {len(self.python_files)} Python files")
        print(f"   Found {len(self.javascript_files)} JavaScript files")
        print(f"   Found {len(self.test_files)} test files")
    
    def analyze_python_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a Python file for functions, classes, and imports."""
        rel_path = str(file_path.relative_to(self.repo_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            functions = []
            classes = []
            imports = []
            exports = []
            docstring = ast.get_docstring(tree) or ""
            errors = []
            
            # Extract module-level definitions
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    self.all_functions[rel_path].add(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    self.all_classes[rel_path].add(node.name)
                    # Also extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            functions.append(f"{node.name}.{item.name}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        self.all_imports[rel_path].append(('', alias.name))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                        self.all_imports[rel_path].append((module, alias.name))
            
            # Look for __all__ exports
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        exports.append(elt.value)
            
            line_count = len(content.split('\n'))
            has_tests = any(test_file for test_file in self.test_files 
                          if file_path.stem in test_file)
            
            return FileAnalysis(
                path=rel_path,
                functions=functions,
                classes=classes,
                imports=imports,
                exports=exports,
                docstring=docstring,
                line_count=line_count,
                has_tests=has_tests,
                errors=errors
            )
        
        except SyntaxError as e:
            return FileAnalysis(
                path=rel_path,
                functions=[],
                classes=[],
                imports=[],
                exports=[],
                docstring="",
                line_count=0,
                has_tests=False,
                errors=[f"Syntax error: {str(e)}"]
            )
        except Exception as e:
            return FileAnalysis(
                path=rel_path,
                functions=[],
                classes=[],
                imports=[],
                exports=[],
                docstring="",
                line_count=0,
                has_tests=False,
                errors=[f"Error: {str(e)}"]
            )
    
    def analyze_javascript_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a JavaScript file for functions and exports."""
        rel_path = str(file_path.relative_to(self.repo_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based analysis (not as robust as AST)
            functions = []
            classes = []
            imports = []
            exports = []
            errors = []
            
            # Find function declarations
            func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))'
            for match in re.finditer(func_pattern, content):
                func_name = match.group(1) or match.group(2)
                if func_name:
                    functions.append(func_name)
            
            # Find class declarations
            class_pattern = r'class\s+(\w+)'
            for match in re.finditer(class_pattern, content):
                classes.append(match.group(1))
            
            # Find imports
            import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(import_pattern, content):
                imports.append(match.group(1))
            
            # Find exports
            export_pattern = r'export\s+(?:default\s+)?(?:function\s+(\w+)|class\s+(\w+)|(?:const|let|var)\s+(\w+))'
            for match in re.finditer(export_pattern, content):
                export_name = match.group(1) or match.group(2) or match.group(3)
                if export_name:
                    exports.append(export_name)
            
            line_count = len(content.split('\n'))
            has_tests = any(test_file for test_file in self.test_files 
                          if file_path.stem in test_file)
            
            return FileAnalysis(
                path=rel_path,
                functions=functions,
                classes=classes,
                imports=imports,
                exports=exports,
                docstring="",
                line_count=line_count,
                has_tests=has_tests,
                errors=errors
            )
        
        except Exception as e:
            return FileAnalysis(
                path=rel_path,
                functions=[],
                classes=[],
                imports=[],
                exports=[],
                docstring="",
                line_count=0,
                has_tests=False,
                errors=[f"Error: {str(e)}"]
            )
    
    def analyze_all_files(self):
        """Analyze all discovered files."""
        print("📊 Analyzing files...")
        
        for py_file in self.python_files:
            analysis = self.analyze_python_file(py_file)
            self.file_analyses[analysis.path] = analysis
        
        for js_file in self.javascript_files:
            analysis = self.analyze_javascript_file(js_file)
            self.file_analyses[analysis.path] = analysis
        
        print(f"   Analyzed {len(self.file_analyses)} files")
    
    def find_missing_implementations(self) -> List[Dict[str, Any]]:
        """Find functions/classes that are imported but not defined."""
        print("🔎 Finding missing implementations...")
        missing = []
        
        for file_path, imports in self.all_imports.items():
            for module, name in imports:
                if not module:
                    continue
                
                # Convert module path to file path
                module_parts = module.split('.')
                
                # Try to find the module file
                possible_paths = [
                    '/'.join(module_parts) + '.py',
                    '/'.join(module_parts) + '/__init__.py',
                ]
                
                found = False
                for possible_path in possible_paths:
                    if possible_path in self.file_analyses:
                        analysis = self.file_analyses[possible_path]
                        # Check if the imported name exists
                        if name in analysis.functions or name in analysis.classes or name in analysis.exports:
                            found = True
                            break
                        elif name == '*':
                            found = True
                            break
                
                if not found and not module.startswith(('os', 'sys', 'json', 're', 'time', 
                                                        'datetime', 'pathlib', 'typing',
                                                        'collections', 'dataclasses', 'ast',
                                                        'logging', 'unittest', 'pytest')):
                    missing.append({
                        'file': file_path,
                        'module': module,
                        'name': name,
                        'import_statement': f"from {module} import {name}" if module else f"import {name}"
                    })
        
        print(f"   Found {len(missing)} potentially missing implementations")
        return missing
    
    def find_orphaned_imports(self) -> List[Dict[str, Any]]:
        """Find imports that are never used in the file."""
        print("🗑️  Finding orphaned imports...")
        orphaned = []
        
        for file_path, analysis in self.file_analyses.items():
            if not file_path.endswith('.py'):
                continue
            
            try:
                file_full_path = self.repo_root / file_path
                with open(file_full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for module, name in self.all_imports[file_path]:
                    # Skip special imports
                    if name in ('*', '__future__'):
                        continue
                    
                    # Simple check: is the name used elsewhere in the file?
                    # This is a heuristic and may have false positives
                    pattern = r'\b' + re.escape(name) + r'\b'
                    matches = list(re.finditer(pattern, content))
                    
                    # If only mentioned in import statement, it might be orphaned
                    if len(matches) <= 1:
                        orphaned.append({
                            'file': file_path,
                            'module': module,
                            'name': name
                        })
            
            except Exception:
                pass
        
        print(f"   Found {len(orphaned)} potentially orphaned imports")
        return orphaned
    
    def find_missing_tests(self) -> List[str]:
        """Find files that don't have corresponding test files."""
        print("🧪 Finding files without tests...")
        missing_tests = []
        
        for file_path, analysis in self.file_analyses.items():
            # Skip test files themselves
            if 'test' in file_path:
                continue
            
            # Skip certain directories
            if any(skip in file_path for skip in ['migrations', 'logs', '__pycache__', 
                                                   'node_modules', 'frontend', 'desktop']):
                continue
            
            # Only check Python files with functions/classes
            if file_path.endswith('.py') and (analysis.functions or analysis.classes):
                if not analysis.has_tests:
                    missing_tests.append(file_path)
        
        print(f"   Found {len(missing_tests)} files without tests")
        return missing_tests
    
    def find_missing_files(self) -> List[Dict[str, Any]]:
        """Find files referenced in imports that don't exist."""
        print("📁 Finding missing files...")
        missing_files = []
        seen = set()
        
        for file_path, imports in self.all_imports.items():
            for module, name in imports:
                if not module or module in seen:
                    continue
                
                seen.add(module)
                
                # Skip standard library and third-party modules
                if module.split('.')[0] in ['os', 'sys', 'json', 're', 'time', 'datetime',
                                             'pathlib', 'typing', 'collections', 'dataclasses',
                                             'ast', 'logging', 'unittest', 'pytest', 'flask',
                                             'torch', 'transformers', 'PIL', 'numpy', 'cv2',
                                             'stripe', 'boto3', 'google', 'dropbox', 'opentelemetry']:
                    continue
                
                # Convert module to file path
                module_parts = module.split('.')
                possible_paths = [
                    self.repo_root / '/'.join(module_parts) / '__init__.py',
                    self.repo_root / f"{'/'.join(module_parts)}.py",
                ]
                
                # Check if any of these paths exist
                if not any(path.exists() for path in possible_paths):
                    missing_files.append({
                        'module': module,
                        'referenced_in': file_path,
                        'expected_paths': [str(p.relative_to(self.repo_root)) for p in possible_paths]
                    })
        
        print(f"   Found {len(missing_files)} potentially missing files")
        return missing_files
    
    def find_unused_functions(self) -> List[Dict[str, Any]]:
        """Find functions that are defined but never called."""
        print("🔧 Finding unused functions...")
        unused = []
        
        # Build a set of all function/class names used across all files
        all_used_names = set()
        
        for file_path, analysis in self.file_analyses.items():
            try:
                file_full_path = self.repo_root / file_path
                with open(file_full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract all identifiers (simplified)
                identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
                all_used_names.update(identifiers)
            except Exception:
                pass
        
        # Check each function
        for file_path, analysis in self.file_analyses.items():
            for func in analysis.functions:
                # Skip private functions, test functions, main, etc.
                func_base = func.split('.')[0]
                if func_base.startswith('_') or func_base.startswith('test_') or func_base in ('main', 'setup', 'teardown'):
                    continue
                
                # Check if function name appears in the used names set
                # This is a heuristic and may have false positives
                if func_base not in all_used_names or func in analysis.exports:
                    # Function name is used or exported, so probably not unused
                    continue
                else:
                    # Count occurrences across all files
                    count = sum(1 for name in all_used_names if name == func_base)
                    if count <= 1:  # Only defined, never called
                        unused.append({
                            'file': file_path,
                            'function': func,
                            'type': 'function'
                        })
        
        print(f"   Found {len(unused)} potentially unused functions")
        return unused
    
    def check_documentation_consistency(self) -> List[Dict[str, Any]]:
        """Check if documentation matches actual code."""
        print("📝 Checking documentation consistency...")
        mismatches = []
        
        # Check if README mentions functions that don't exist
        readme_path = self.repo_root / 'README.md'
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Extract code references from README (simple heuristic)
                # Look for backtick-enclosed names
                code_refs = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_]*)`', readme_content)
                
                all_defined = set()
                for analysis in self.file_analyses.values():
                    all_defined.update(analysis.functions)
                    all_defined.update(analysis.classes)
                
                for ref in set(code_refs):
                    # Skip common words
                    if ref.lower() in ('the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                                       'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is'):
                        continue
                    
                    # Check if this looks like a function/class name
                    if ref[0].isupper() or '_' in ref:
                        if ref not in all_defined:
                            mismatches.append({
                                'type': 'README reference',
                                'name': ref,
                                'issue': 'Referenced in README but not found in code'
                            })
            except Exception as e:
                pass
        
        print(f"   Found {len(mismatches)} documentation mismatches")
        return mismatches
    
    def generate_report(self) -> RepositoryReport:
        """Generate comprehensive repository report."""
        print("\n📋 Generating comprehensive report...\n")
        
        total_functions = sum(len(a.functions) for a in self.file_analyses.values())
        total_classes = sum(len(a.classes) for a in self.file_analyses.values())
        
        missing_implementations = self.find_missing_implementations()
        orphaned_imports = self.find_orphaned_imports()
        missing_tests = self.find_missing_tests()
        missing_files = self.find_missing_files()
        unused_functions = self.find_unused_functions()
        documentation_mismatches = self.check_documentation_consistency()
        
        return RepositoryReport(
            total_files=len(self.file_analyses),
            total_python_files=len(self.python_files),
            total_javascript_files=len(self.javascript_files),
            total_functions=total_functions,
            total_classes=total_classes,
            missing_implementations=missing_implementations,
            orphaned_imports=orphaned_imports,
            missing_tests=missing_tests,
            missing_files=missing_files,
            unused_functions=unused_functions,
            documentation_mismatches=documentation_mismatches,
            file_analyses=list(self.file_analyses.values())
        )
    
    def save_markdown_report(self, report: RepositoryReport, output_path: str):
        """Save report as markdown file."""
        print(f"💾 Saving markdown report to {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Repository Analysis Report\n\n")
            f.write(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Total Files Analyzed:** {report.total_files}\n")
            f.write(f"- **Python Files:** {report.total_python_files}\n")
            f.write(f"- **JavaScript Files:** {report.total_javascript_files}\n")
            f.write(f"- **Total Functions:** {report.total_functions}\n")
            f.write(f"- **Total Classes:** {report.total_classes}\n\n")
            
            # Issues Summary
            f.write("## ⚠️ Issues Found\n\n")
            f.write(f"- **Missing Implementations:** {len(report.missing_implementations)}\n")
            f.write(f"- **Orphaned Imports:** {len(report.orphaned_imports)}\n")
            f.write(f"- **Files Without Tests:** {len(report.missing_tests)}\n")
            f.write(f"- **Missing Files:** {len(report.missing_files)}\n")
            f.write(f"- **Potentially Unused Functions:** {len(report.unused_functions)}\n")
            f.write(f"- **Documentation Mismatches:** {len(report.documentation_mismatches)}\n\n")
            
            # Detailed Sections
            if report.missing_implementations:
                f.write("## 🔴 Missing Implementations\n\n")
                f.write("Functions or classes that are imported but not defined in the expected module.\n\n")
                for item in report.missing_implementations[:50]:  # Limit to first 50
                    f.write(f"- **File:** `{item['file']}`\n")
                    f.write(f"  - **Import:** `{item['import_statement']}`\n")
                    f.write(f"  - **Missing:** `{item['name']}` from module `{item['module']}`\n\n")
                if len(report.missing_implementations) > 50:
                    f.write(f"*...and {len(report.missing_implementations) - 50} more*\n\n")
            
            if report.orphaned_imports:
                f.write("## 🗑️ Orphaned Imports\n\n")
                f.write("Imports that appear to be unused in their files.\n\n")
                for item in report.orphaned_imports[:50]:
                    f.write(f"- **File:** `{item['file']}`\n")
                    f.write(f"  - **Unused:** `{item['name']}` from `{item['module']}`\n\n")
                if len(report.orphaned_imports) > 50:
                    f.write(f"*...and {len(report.orphaned_imports) - 50} more*\n\n")
            
            if report.missing_tests:
                f.write("## 🧪 Files Without Tests\n\n")
                f.write("Python files with functions/classes that lack corresponding test files.\n\n")
                for file_path in report.missing_tests[:50]:
                    analysis = next((a for a in report.file_analyses if a.path == file_path), None)
                    if analysis:
                        f.write(f"- **File:** `{file_path}`\n")
                        f.write(f"  - Functions: {len(analysis.functions)}, Classes: {len(analysis.classes)}\n\n")
                if len(report.missing_tests) > 50:
                    f.write(f"*...and {len(report.missing_tests) - 50} more*\n\n")
            
            if report.missing_files:
                f.write("## 📁 Missing Files\n\n")
                f.write("Files that are imported but don't exist in the repository.\n\n")
                for item in report.missing_files[:50]:
                    f.write(f"- **Module:** `{item['module']}`\n")
                    f.write(f"  - **Referenced in:** `{item['referenced_in']}`\n")
                    f.write(f"  - **Expected at:** {', '.join(f'`{p}`' for p in item['expected_paths'])}\n\n")
                if len(report.missing_files) > 50:
                    f.write(f"*...and {len(report.missing_files) - 50} more*\n\n")
            
            if report.unused_functions:
                f.write("## 🔧 Potentially Unused Functions\n\n")
                f.write("Functions that appear to be defined but never called (heuristic analysis).\n\n")
                for item in report.unused_functions[:50]:
                    f.write(f"- **File:** `{item['file']}`\n")
                    f.write(f"  - **Function:** `{item['function']}`\n\n")
                if len(report.unused_functions) > 50:
                    f.write(f"*...and {len(report.unused_functions) - 50} more*\n\n")
            
            if report.documentation_mismatches:
                f.write("## 📝 Documentation Mismatches\n\n")
                f.write("References in documentation that don't match the actual code.\n\n")
                for item in report.documentation_mismatches:
                    f.write(f"- **Type:** {item['type']}\n")
                    f.write(f"  - **Name:** `{item['name']}`\n")
                    f.write(f"  - **Issue:** {item['issue']}\n\n")
            
            # File Analysis Details
            f.write("## 📄 File Analysis Details\n\n")
            f.write("### Files by Category\n\n")
            
            # Categorize files
            backend_files = [a for a in report.file_analyses if 'backend' in a.path]
            frontend_files = [a for a in report.file_analyses if 'frontend' in a.path or 'desktop' in a.path]
            shared_files = [a for a in report.file_analyses if 'shared' in a.path]
            test_files = [a for a in report.file_analyses if 'test' in a.path]
            
            f.write(f"- **Backend Files:** {len(backend_files)}\n")
            f.write(f"- **Frontend/Desktop Files:** {len(frontend_files)}\n")
            f.write(f"- **Shared Module Files:** {len(shared_files)}\n")
            f.write(f"- **Test Files:** {len(test_files)}\n\n")
            
            # Top files by complexity
            f.write("### Top 20 Files by Line Count\n\n")
            sorted_files = sorted(report.file_analyses, key=lambda x: x.line_count, reverse=True)
            f.write("| File | Lines | Functions | Classes | Has Tests |\n")
            f.write("|------|-------|-----------|---------|----------|\n")
            for analysis in sorted_files[:20]:
                f.write(f"| `{analysis.path}` | {analysis.line_count} | {len(analysis.functions)} | {len(analysis.classes)} | {'✅' if analysis.has_tests else '❌'} |\n")
            f.write("\n")
            
            # Errors encountered
            files_with_errors = [a for a in report.file_analyses if a.errors]
            if files_with_errors:
                f.write("## ❗ Files with Analysis Errors\n\n")
                for analysis in files_with_errors[:20]:
                    f.write(f"- **File:** `{analysis.path}`\n")
                    for error in analysis.errors:
                        f.write(f"  - {error}\n")
                    f.write("\n")
            
            f.write("\n---\n\n")
            f.write("*This report was automatically generated by the Repository Screening Tool.*\n")
        
        print("✅ Report saved successfully!")
    
    def save_json_report(self, report: RepositoryReport, output_path: str):
        """Save report as JSON file."""
        print(f"💾 Saving JSON report to {output_path}...")
        
        # Convert dataclasses to dict
        report_dict = {
            'summary': {
                'total_files': report.total_files,
                'total_python_files': report.total_python_files,
                'total_javascript_files': report.total_javascript_files,
                'total_functions': report.total_functions,
                'total_classes': report.total_classes,
            },
            'issues': {
                'missing_implementations': report.missing_implementations,
                'orphaned_imports': report.orphaned_imports,
                'missing_tests': report.missing_tests,
                'missing_files': report.missing_files,
                'unused_functions': report.unused_functions,
                'documentation_mismatches': report.documentation_mismatches,
            },
            'file_analyses': [asdict(a) for a in report.file_analyses]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2)
        
        print("✅ JSON report saved successfully!")
    
    def run(self, markdown_output: str = None, json_output: str = None):
        """Run the complete repository screening process."""
        print("\n" + "="*80)
        print("🔍 REPOSITORY SCREENING TOOL")
        print("="*80 + "\n")
        
        self.discover_files()
        self.analyze_all_files()
        report = self.generate_report()
        
        if markdown_output:
            self.save_markdown_report(report, markdown_output)
        
        if json_output:
            self.save_json_report(report, json_output)
        
        print("\n" + "="*80)
        print("✅ SCREENING COMPLETE")
        print("="*80 + "\n")
        
        return report


def main():
    """Main entry point."""
    import sys
    
    # Get repository root (current directory or first argument)
    repo_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    # Output paths
    markdown_output = os.path.join(repo_root, 'REPOSITORY_ANALYSIS.md')
    json_output = os.path.join(repo_root, 'repository_analysis.json')
    
    # Run screening
    screener = RepositoryScreener(repo_root)
    report = screener.run(markdown_output=markdown_output, json_output=json_output)
    
    # Print summary
    print("\n📊 SUMMARY:")
    print(f"   Total Files: {report.total_files}")
    print(f"   Total Functions: {report.total_functions}")
    print(f"   Total Classes: {report.total_classes}")
    print(f"\n⚠️  ISSUES:")
    print(f"   Missing Implementations: {len(report.missing_implementations)}")
    print(f"   Orphaned Imports: {len(report.orphaned_imports)}")
    print(f"   Files Without Tests: {len(report.missing_tests)}")
    print(f"   Missing Files: {len(report.missing_files)}")
    print(f"   Unused Functions: {len(report.unused_functions)}")
    print(f"   Documentation Mismatches: {len(report.documentation_mismatches)}")
    print(f"\n📁 Reports saved to:")
    print(f"   - {markdown_output}")
    print(f"   - {json_output}")


if __name__ == '__main__':
    main()
