#!/usr/bin/env python3
"""
CEFR Dependency Analysis Tool

Analyzes Python imports to detect:
- Circular dependencies
- Import depth
- Module coupling
- Dead imports

Usage:
    python tools/cefr/dependency_analyzer.py
    
Output:
    - Console report
    - docs/DEPENDENCY_ANALYSIS.md (saved report)
    
Exit codes:
    0 - No circular dependencies found
    1 - Circular dependencies detected
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class DependencyAnalyzer:
    """Analyze actual Python imports (not CEFR registry)"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.files: Dict[str, Path] = {}
        
    def scan_project(self):
        """Scan all Python files and extract imports"""
        for py_file in self.project_root.rglob('*.py'):
            # Skip virtual environments and git directories
            if any(skip in str(py_file) for skip in ['venv', '.git', '__pycache__', 'node_modules']):
                continue
            
            module_name = self._path_to_module(py_file)
            self.files[module_name] = py_file
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                    imports = self._extract_imports(tree)
                    self.imports[module_name] = imports
            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}", file=sys.stderr)
    
    def _path_to_module(self, path: Path) -> str:
        """Convert file path to module name"""
        try:
            rel_path = path.relative_to(self.project_root)
        except ValueError:
            # Path is not relative to project root
            return str(path)
        
        module = str(rel_path).replace(os.sep, '.').replace('.py', '')
        # Remove __init__ from module names
        if module.endswith('.__init__'):
            module = module[:-9]
        return module
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST"""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])  # Get root module
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get root module (first part before dot)
                    root = node.module.split('.')[0]
                    imports.add(root)
        
        return imports
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Detect circular import chains"""
        cycles = []
        visited_global = set()
        
        def dfs(module: str, path: List[str], visited_path: Set[str]) -> None:
            if module in path:
                # Found cycle
                idx = path.index(module)
                cycle = path[idx:] + [module]
                # Normalize cycle (start with alphabetically smallest)
                min_idx = cycle.index(min(cycle[:-1]))
                normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                
                if normalized not in cycles:
                    cycles.append(normalized)
                return
            
            if module in visited_global:
                return
            
            if module not in self.imports:
                return
            
            visited_path.add(module)
            path.append(module)
            
            for imported in self.imports.get(module, []):
                if imported in self.imports:  # Only check local modules
                    dfs(imported, path[:], visited_path.copy())
            
            visited_global.add(module)
        
        for module in sorted(self.imports.keys()):
            if module not in visited_global:
                dfs(module, [], set())
        
        return cycles
    
    def calculate_import_depth(self, module: str, visited: Set[str] = None) -> int:
        """Calculate max import depth for a module"""
        if visited is None:
            visited = set()
        
        if module in visited:
            return 0
        
        visited.add(module)
        imports = self.imports.get(module, set())
        
        if not imports:
            return 1
        
        max_depth = 0
        for imp in imports:
            if imp in self.imports:  # Only local modules
                depth = self.calculate_import_depth(imp, visited.copy())
                max_depth = max(max_depth, depth)
        
        return max_depth + 1
    
    def find_bottlenecks(self, threshold: int = 10) -> List[Tuple[str, int]]:
        """Find modules imported by many others"""
        import_counts = defaultdict(int)
        
        for module, imports in self.imports.items():
            for imp in imports:
                import_counts[imp] += 1
        
        bottlenecks = [(mod, count) for mod, count in import_counts.items() 
                      if count >= threshold]
        return sorted(bottlenecks, key=lambda x: x[1], reverse=True)
    
    def find_isolated_modules(self) -> List[str]:
        """Find modules that don't import anything and aren't imported"""
        imported_modules = set()
        for imports in self.imports.values():
            imported_modules.update(imports)
        
        isolated = []
        for module in self.imports.keys():
            if not self.imports[module] and module not in imported_modules:
                isolated.append(module)
        
        return sorted(isolated)
    
    def generate_report(self) -> str:
        """Generate comprehensive dependency report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DEPENDENCY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append(f"Total Python modules: {len(self.imports)}")
        total_imports = sum(len(v) for v in self.imports.values())
        lines.append(f"Total import relationships: {total_imports}")
        lines.append("")
        
        # Circular dependencies
        cycles = self.find_circular_dependencies()
        if cycles:
            lines.append(f"⚠️  CIRCULAR DEPENDENCIES DETECTED: {len(cycles)}")
            lines.append("")
            for i, cycle in enumerate(cycles, 1):
                lines.append(f"{i}. {' → '.join(cycle)}")
            lines.append("")
            lines.append("Action Required: Refactor to break circular dependencies")
            lines.append("")
        else:
            lines.append("✅ No circular dependencies detected")
            lines.append("")
        
        # Import depth
        depths = {mod: self.calculate_import_depth(mod) for mod in list(self.imports.keys())[:50]}
        if depths:
            max_depth = max(depths.values())
            avg_depth = sum(depths.values()) / len(depths)
            
            lines.append(f"Import Depth Analysis:")
            lines.append(f"  Max depth: {max_depth}")
            lines.append(f"  Avg depth: {avg_depth:.1f}")
            
            # Show modules with deepest imports
            deepest = sorted(depths.items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"  Deepest modules:")
            for mod, depth in deepest:
                lines.append(f"    {mod}: depth {depth}")
            lines.append("")
        
        # Bottlenecks
        bottlenecks = self.find_bottlenecks(threshold=10)
        if bottlenecks:
            lines.append(f"Import Bottlenecks (imported by 10+ modules):")
            for module, count in bottlenecks[:10]:
                lines.append(f"  {module}: {count} imports")
            lines.append("")
            lines.append("Consider: These modules are heavily coupled")
            lines.append("")
        
        # Isolated modules
        isolated = self.find_isolated_modules()
        if isolated and len(isolated) < 20:
            lines.append(f"Isolated Modules ({len(isolated)}):")
            for module in isolated[:10]:
                lines.append(f"  {module}")
            if len(isolated) > 10:
                lines.append(f"  ... and {len(isolated) - 10} more")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    analyzer = DependencyAnalyzer(project_root)
    
    print("Scanning project...")
    analyzer.scan_project()
    
    print(analyzer.generate_report())
    
    # Save to file
    docs_dir = project_root / 'docs'
    docs_dir.mkdir(exist_ok=True)
    report_path = docs_dir / 'DEPENDENCY_ANALYSIS.md'
    
    with open(report_path, 'w') as f:
        f.write(analyzer.generate_report())
    
    print(f"\n✅ Report saved to {report_path}")
    
    # Exit with error if circular dependencies found
    cycles = analyzer.find_circular_dependencies()
    if cycles:
        print(f"\n⚠️  Found {len(cycles)} circular dependencies")
        sys.exit(1)
    else:
        print("\n✅ No circular dependencies found")
        sys.exit(0)


if __name__ == '__main__':
    main()
