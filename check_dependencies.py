#!/usr/bin/env python3
"""
check_dependencies.py

- Reads requirements.txt (PEP 440 simple "pkg==version" / "pkg>=version" lines).
- Compares against installed packages.
- Reports missing or version-mismatched packages.
- With --install will attempt to install missing or mismatched packages using pip.

Usage:
  python check_dependencies.py          # report-only
  python check_dependencies.py --install  # attempt to install missing/mismatched packages
  python check_dependencies.py --file dev-requirements.txt
"""

from __future__ import annotations
import sys
import subprocess
import argparse
import re
from pathlib import Path
from typing import Dict, Tuple, List

try:
    # Python 3.8+: importlib.metadata in stdlib
    from importlib.metadata import distributions, PackageNotFoundError, version as pkg_version
except Exception:
    # Fallback for older Pythons (unlikely)
    try:
        from importlib_metadata import distributions, PackageNotFoundError, version as pkg_version  # type: ignore
    except Exception:
        distributions = None
        PackageNotFoundError = Exception
        def pkg_version(name: str) -> str:
            raise PackageNotFoundError

REQ_LINE_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*(?:([<>=!~]{1,2})\s*([^\s;#]+))?')

def parse_requirements(path: Path) -> Dict[str, Tuple[str, str]]:
    """
    Parse a simple requirements file into a mapping:
      package_name -> (comparator, version)
    Lines that cannot be parsed are ignored.
    Package names are normalized to lowercase with underscores.
    """
    reqs: Dict[str, Tuple[str, str]] = {}
    if not path.exists():
        return reqs
    for raw in path.read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        m = REQ_LINE_RE.match(line)
        if not m:
            continue
        name, op, ver = m.group(1), m.group(2) or "", m.group(3) or ""
        # Normalize: lowercase and replace hyphens with underscores
        normalized_name = name.lower().replace('-', '_')
        reqs[normalized_name] = (op, ver)
    return reqs

def get_installed_versions() -> Dict[str, str]:
    """
    Get a dictionary of installed package names to versions.
    Package names are normalized to lowercase with underscores.
    """
    installed: Dict[str, str] = {}
    # importlib.metadata distributions returns normalized names
    try:
        for dist in distributions():
            # Normalize: lowercase and replace hyphens with underscores
            normalized_name = dist.metadata['Name'].lower().replace('-', '_')
            installed[normalized_name] = dist.version
    except Exception:
        # fallback: try pkg_version for common packages if distributions unavailable
        pass
    return installed

def compare(reqs: Dict[str, Tuple[str, str]], installed: Dict[str, str]) -> Tuple[List[str], List[str]]:
    missing: List[str] = []
    mismatched: List[str] = []
    for name, (op, reqver) in reqs.items():
        instver = installed.get(name)
        if instver is None:
            missing.append(name)
        elif op and reqver:
            try:
                # Use simple string compare for mismatches when operator is present.
                # For more robust version comparison, pkg_resources.parse_version or packaging.version can be used.
                from packaging.version import Version, InvalidVersion  # type: ignore
                ok = True
                rv = Version(reqver)
                iv = Version(instver)
                if op in ("==", "==="):
                    ok = iv == rv
                elif op == ">=":
                    ok = iv >= rv
                elif op == "<=":
                    ok = iv <= rv
                elif op == ">":
                    ok = iv > rv
                elif op == "<":
                    ok = iv < rv
                elif op == "!=":
                    ok = iv != rv
                else:
                    ok = True
                if not ok:
                    mismatched.append(f"{name} (installed: {instver}, required: {op}{reqver})")
            except Exception:
                # If packaging not available or parse error, fallback to simple string inequality check
                if instver != reqver:
                    mismatched.append(f"{name} (installed: {instver}, required: {op}{reqver})")
    return missing, mismatched

def pip_install(packages: List[str]) -> int:
    if not packages:
        return 0
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)

def main() -> int:
    parser = argparse.ArgumentParser(description="Check and optionally install Python dependencies from a requirements file.")
    parser.add_argument("--file", "-f", default="requirements.txt", help="Path to requirements file (default: requirements.txt)")
    parser.add_argument("--install", action="store_true", help="Attempt to install missing or mismatched packages with pip")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    req_path = Path(args.file)
    if not req_path.exists():
        print(f"Requirements file not found at {req_path}. Exiting with status 0.")
        return 0

    reqs = parse_requirements(req_path)
    if not reqs:
        if not args.quiet:
            print(f"No parseable requirements found in {req_path}.")
        return 0

    installed = get_installed_versions()
    missing, mismatched = compare(reqs, installed)

    if not args.quiet:
        print(f"Checked {len(reqs)} requirements from {req_path}.")
        if missing:
            print(f"Missing packages ({len(missing)}):")
            for m in missing:
                print("  -", m)
        if mismatched:
            print(f"Version mismatches ({len(mismatched)}):")
            for mm in mismatched:
                print("  -", mm)
        if not missing and not mismatched:
            print("All requirements satisfied.")

    if args.install and (missing or mismatched):
        to_install = []
        # Build a pip spec list using requirements lines where present
        for name in missing:
            # try to get original requirement line
            # default to just name (let pip pick latest or satisfy constraints)
            to_install.append(name)
        for mm in mismatched:
            # mm looks like "pkg (installed: x, required: >=y)"
            m = re.match(r'^([A-Za-z0-9_.\-]+).*\brequired:\s*(.+)\)$', mm)
            if m:
                name = m.group(1)
                req = mm.split('required:')[-1].strip().rstrip(')')
                # Try using name+specifier if clean
                to_install.append(f"{name}{req}")
            else:
                # fallback
                to_install.append(mm.split()[0])
        rc = pip_install(to_install)
        if rc != 0:
            print("pip install returned non-zero exit code:", rc)
            return rc
        else:
            if not args.quiet:
                print("Install attempt finished. You may want to re-run this script to verify.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
