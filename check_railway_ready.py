#!/usr/bin/env python3
"""
=============================================================================
RAILWAY DEPLOYMENT READINESS CHECKER
=============================================================================

Validates that the application is ready for Railway deployment by checking:
- Dockerfile exists and has correct syntax
- railway.json exists and is valid JSON
- Package structure is correct (__init__.py files)
- Environment variable documentation exists
- Critical files are present

Version:    1.0.0
Author:     Receipt Extractor Team

Usage:
    python check_railway_ready.py

Exit Codes:
    0 - All checks passed, ready for Railway deployment
    1 - One or more checks failed

=============================================================================
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class DeploymentReadinessChecker:
    """Checks if application is ready for Railway deployment."""
    
    def __init__(self):
        """Initialize checker with project root."""
        self.project_root = Path(__file__).parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def print_header(self, text: str) -> None:
        """Print formatted header."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    def print_success(self, text: str) -> None:
        """Print success message."""
        print(f"{Colors.GREEN}✅ {text}{Colors.END}")
    
    def print_error(self, text: str) -> None:
        """Print error message."""
        print(f"{Colors.RED}❌ {text}{Colors.END}")
        self.errors.append(text)
    
    def print_warning(self, text: str) -> None:
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")
        self.warnings.append(text)
    
    def print_info(self, text: str) -> None:
        """Print info message."""
        print(f"ℹ️  {text}")
    
    def check_dockerfile(self) -> bool:
        """
        Check if Dockerfile exists and has correct configuration.
        
        Returns:
            bool: True if Dockerfile is valid, False otherwise
        """
        self.print_info("Checking Dockerfile...")
        self.checks_total += 1
        
        dockerfile_path = self.project_root / 'Dockerfile'
        
        if not dockerfile_path.exists():
            self.print_error("Dockerfile not found")
            return False
        
        try:
            content = dockerfile_path.read_text()
            
            # Check for required directives
            required_directives = [
                ('FROM', 'Base image'),
                ('WORKDIR', 'Working directory'),
                ('COPY', 'File copying'),
                ('RUN', 'Build commands'),
                ('CMD', 'Start command'),
                ('EXPOSE', 'Port exposure')
            ]
            
            missing_directives = []
            for directive, description in required_directives:
                if directive not in content:
                    missing_directives.append(f"{directive} ({description})")
            
            if missing_directives:
                self.print_error(f"Dockerfile missing directives: {', '.join(missing_directives)}")
                return False
            
            # Check for optimized worker configuration (should be 2 workers, not 4)
            if '--workers 4' in content:
                self.print_warning("Dockerfile still uses 4 workers - should be 2 for Railway")
            elif '--workers 2' in content:
                self.print_info("  Workers: 2 (optimized for Railway)")
            
            # Check for exec form CMD (proper signal handling)
            if 'CMD ["sh", "-c"' in content or 'CMD ["/bin/sh", "-c"' in content:
                self.print_info("  CMD: Exec form with shell (correct)")
            elif 'CMD gunicorn' in content and not content.count('CMD [') > 0:
                self.print_warning("CMD uses shell form - should use exec form for signal handling")
            
            # Check for log configuration
            if '--access-logfile -' in content and '--error-logfile -' in content:
                self.print_info("  Logging: Configured for stdout/stderr")
            else:
                self.print_warning("Logging not configured for stdout/stderr (Railway best practice)")
            
            self.print_success("Dockerfile: Valid")
            self.checks_passed += 1
            return True
            
        except Exception as e:
            self.print_error(f"Dockerfile validation error: {e}")
            return False
    
    def check_railway_json(self) -> bool:
        """
        Check if railway.json exists and is valid JSON.
        
        Returns:
            bool: True if railway.json is valid, False otherwise
        """
        self.print_info("Checking railway.json...")
        self.checks_total += 1
        
        railway_json_path = self.project_root / 'railway.json'
        
        if not railway_json_path.exists():
            self.print_error("railway.json not found")
            return False
        
        try:
            with open(railway_json_path) as f:
                config = json.load(f)
            
            # Check required fields
            required_fields = {
                'deploy': {
                    'healthcheckPath': '/api/health',
                    'healthcheckTimeout': 600,  # Should be 600 for Railway
                    'restartPolicyMaxRetries': 3  # Should be 3
                }
            }
            
            # Validate deploy configuration
            if 'deploy' not in config:
                self.print_error("railway.json missing 'deploy' section")
                return False
            
            deploy = config['deploy']
            
            # Check healthcheck configuration
            if deploy.get('healthcheckPath') != '/api/health':
                self.print_warning(f"healthcheckPath should be '/api/health', got: {deploy.get('healthcheckPath')}")
            else:
                self.print_info("  Health check path: /api/health")
            
            timeout = deploy.get('healthcheckTimeout', 0)
            if timeout < 600:
                self.print_warning(f"healthcheckTimeout is {timeout}s - should be 600s for Railway")
            else:
                self.print_info(f"  Health check timeout: {timeout}s")
            
            retries = deploy.get('restartPolicyMaxRetries', 0)
            if retries != 3:
                self.print_warning(f"restartPolicyMaxRetries is {retries} - recommended: 3")
            else:
                self.print_info(f"  Restart max retries: {retries}")
            
            # Check for sleepApplication
            if deploy.get('sleepApplication', True) != False:
                self.print_warning("sleepApplication should be set to false")
            else:
                self.print_info("  Sleep application: false")
            
            self.print_success("railway.json: Valid")
            self.checks_passed += 1
            return True
            
        except json.JSONDecodeError as e:
            self.print_error(f"railway.json is not valid JSON: {e}")
            return False
        except Exception as e:
            self.print_error(f"railway.json validation error: {e}")
            return False
    
    def check_package_structure(self) -> bool:
        """
        Check if Python package structure is correct.
        
        Returns:
            bool: True if package structure is valid, False otherwise
        """
        self.print_info("Checking package structure...")
        self.checks_total += 1
        
        required_init_files = [
            'web/__init__.py',
            'web/backend/__init__.py',
            'shared/__init__.py',
        ]
        
        missing_files = []
        for init_file in required_init_files:
            init_path = self.project_root / init_file
            if not init_path.exists():
                missing_files.append(init_file)
                self.print_error(f"Missing: {init_file}")
            else:
                self.print_info(f"  Found: {init_file}")
        
        if missing_files:
            self.print_error(f"Package structure invalid - missing {len(missing_files)} __init__.py files")
            return False
        
        self.print_success("Package structure: Valid")
        self.checks_passed += 1
        return True
    
    def check_environment_docs(self) -> bool:
        """
        Check if environment variable documentation exists.
        
        Returns:
            bool: True if documentation exists, False otherwise
        """
        self.print_info("Checking environment variable documentation...")
        self.checks_total += 1
        
        env_docs = [
            ('.env.example', 'Environment variables example'),
            ('.env.railway.template', 'Railway-specific template'),
        ]
        
        missing_docs = []
        for doc_file, description in env_docs:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                missing_docs.append(f"{doc_file} ({description})")
                self.print_warning(f"Missing: {doc_file}")
            else:
                self.print_info(f"  Found: {doc_file}")
        
        if missing_docs:
            self.print_warning(f"Missing environment docs: {', '.join(missing_docs)}")
        
        # Check for generate-secrets.py
        secrets_script = self.project_root / 'generate-secrets.py'
        if not secrets_script.exists():
            self.print_warning("generate-secrets.py not found - needed for SECRET_KEY generation")
        else:
            self.print_info("  Found: generate-secrets.py")
        
        self.print_success("Environment docs: Complete")
        self.checks_passed += 1
        return True
    
    def check_critical_files(self) -> bool:
        """
        Check if critical application files exist.
        
        Returns:
            bool: True if all critical files exist, False otherwise
        """
        self.print_info("Checking critical application files...")
        self.checks_total += 1
        
        critical_files = [
            ('web/backend/app.py', 'Main Flask application'),
            ('web/backend/startup_validator.py', 'Startup validation script'),
            ('requirements.txt', 'Python dependencies'),
            ('requirements-prod.txt', 'Production dependencies'),
        ]
        
        missing_files = []
        for file_path, description in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(f"{file_path} ({description})")
                self.print_error(f"Missing: {file_path}")
            else:
                self.print_info(f"  Found: {file_path}")
        
        if missing_files:
            self.print_error(f"Missing critical files: {', '.join(missing_files)}")
            return False
        
        self.print_success("Critical files: Present")
        self.checks_passed += 1
        return True
    
    def check_documentation(self) -> bool:
        """
        Check if deployment documentation exists.
        
        Returns:
            bool: True if documentation exists, False otherwise
        """
        self.print_info("Checking deployment documentation...")
        self.checks_total += 1
        
        docs = [
            ('docs/RAILWAY_DEPLOYMENT.md', 'Railway deployment guide'),
            ('README.md', 'Project documentation'),
        ]
        
        missing_docs = []
        for doc_file, description in docs:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                missing_docs.append(f"{doc_file} ({description})")
                self.print_warning(f"Missing: {doc_file}")
            else:
                self.print_info(f"  Found: {doc_file}")
        
        if missing_docs:
            self.print_warning(f"Missing documentation: {', '.join(missing_docs)}")
        
        self.print_success("Documentation: Available")
        self.checks_passed += 1
        return True
    
    def run_all_checks(self) -> bool:
        """
        Run all deployment readiness checks.
        
        Returns:
            bool: True if all critical checks passed, False otherwise
        """
        self.print_header("RAILWAY DEPLOYMENT READINESS CHECKER")
        
        # Run all checks
        checks = [
            ("Dockerfile", self.check_dockerfile),
            ("railway.json", self.check_railway_json),
            ("Package Structure", self.check_package_structure),
            ("Environment Documentation", self.check_environment_docs),
            ("Critical Files", self.check_critical_files),
            ("Documentation", self.check_documentation),
        ]
        
        print(f"{Colors.BOLD}Running {len(checks)} validation checks...{Colors.END}\n")
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.print_error(f"Unexpected error in {check_name}: {e}")
            print()  # Blank line between checks
        
        # Print summary
        self.print_header("VALIDATION SUMMARY")
        
        print(f"{Colors.BOLD}Checks passed: {self.checks_passed}/{self.checks_total}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRORS ({len(self.errors)}):{Colors.END}")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  WARNINGS ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Determine if ready for deployment
        success = len(self.errors) == 0
        
        print()
        if success:
            self.print_success(f"{Colors.BOLD}READY FOR RAILWAY DEPLOYMENT{Colors.END}")
            print()
            print(f"{Colors.YELLOW}⚠️  {Colors.BOLD}REMEMBER:{Colors.END}")
            print(f"  1. Run: {Colors.BOLD}python generate-secrets.py{Colors.END}")
            print(f"  2. Set {Colors.BOLD}SECRET_KEY{Colors.END} in Railway dashboard")
            print(f"  3. Set {Colors.BOLD}JWT_SECRET{Colors.END} in Railway dashboard")
            print(f"  4. Set {Colors.BOLD}FLASK_ENV=production{Colors.END}")
            print(f"  5. Set {Colors.BOLD}FLASK_DEBUG=False{Colors.END}")
            print(f"  6. Deploy and monitor logs")
            print(f"  7. Test: {Colors.BOLD}curl https://your-app.railway.app/api/health{Colors.END}")
        else:
            self.print_error(f"{Colors.BOLD}NOT READY FOR DEPLOYMENT{Colors.END}")
            print(f"\n{Colors.RED}Fix the errors above before deploying to Railway.{Colors.END}")
        
        print()
        self.print_header("END OF VALIDATION")
        
        return success


def main():
    """Main entry point for deployment readiness checker."""
    checker = DeploymentReadinessChecker()
    success = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
