"""
=============================================================================
RAILWAY DEPLOYMENT - STARTUP VALIDATOR
=============================================================================

Validates critical environment variables and system dependencies at startup
to provide clear error messages in Railway logs.

Version:    1.0.0
Author:     Receipt Extractor Team

Usage:
    python web/backend/startup_validator.py
    
Exit Codes:
    0 - All checks passed
    1 - Critical validation failed

=============================================================================
"""

import os
import sys
import time
import logging
import subprocess
from typing import Dict, List, Tuple, Optional

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - STARTUP_VALIDATOR - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates application startup requirements for Railway deployment."""
    
    def __init__(self):
        """Initialize validator with tracking for errors and warnings."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def check_environment_variables(self) -> bool:
        """
        Validate required environment variables are set.
        
        Returns:
            bool: True if all required vars are set, False otherwise
        """
        logger.info("Checking environment variables...")
        self.checks_total += 1
        
        # Required variables that must be present
        required_vars = {
            'SECRET_KEY': 'Flask secret key for session security',
            'JWT_SECRET': 'JWT token signing secret'
        }
        
        # Optional but recommended variables
        optional_vars = {
            'DATABASE_URL': 'PostgreSQL connection string',
            'STRIPE_SECRET_KEY': 'Stripe payment processing',
            'SENDGRID_API_KEY': 'Email service'
        }
        
        all_valid = True
        
        # Check required variables
        for var_name, description in required_vars.items():
            value = os.environ.get(var_name)
            if not value:
                error_msg = f"Missing required environment variable: {var_name} ({description})"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                all_valid = False
            elif len(value) < 32:
                warning_msg = f"{var_name} is too short (< 32 chars) - should use stronger secret"
                self.warnings.append(warning_msg)
                logger.warning(f"⚠️  {warning_msg}")
            else:
                logger.info(f"✅ {var_name}: Set ({len(value)} chars)")
        
        # Check optional variables
        for var_name, description in optional_vars.items():
            value = os.environ.get(var_name)
            if not value:
                logger.info(f"ℹ️  {var_name}: Not set ({description}) - Optional")
            else:
                logger.info(f"✅ {var_name}: Set")
        
        if all_valid:
            self.checks_passed += 1
            logger.info("✅ Environment variables validation PASSED")
        else:
            logger.error("❌ Environment variables validation FAILED")
        
        return all_valid
    
    def check_port_configuration(self) -> bool:
        """
        Validate PORT environment variable.
        
        Returns:
            bool: True if PORT is valid, False otherwise
        """
        logger.info("Checking PORT configuration...")
        self.checks_total += 1
        
        port = os.environ.get('PORT', '5000')
        
        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                error_msg = f"PORT {port} is outside valid range (1-65535)"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return False
            
            logger.info(f"✅ PORT: {port_int} (valid)")
            self.checks_passed += 1
            return True
            
        except ValueError:
            error_msg = f"PORT must be a number, got: {port}"
            self.errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def check_database_connection(self, max_retries: int = 3, retry_delay: int = 2) -> bool:
        """
        Check database connection with retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay in seconds between retries
            
        Returns:
            bool: True if database is accessible or not required, False on failure
        """
        logger.info("Checking database connection...")
        self.checks_total += 1
        
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.info("ℹ️  DATABASE_URL not set - using SQLite (development mode)")
            self.checks_passed += 1
            return True
        
        # Check if psycopg2 is available for PostgreSQL
        try:
            import psycopg2
        except ImportError:
            warning_msg = "psycopg2 not installed - cannot validate PostgreSQL connection"
            self.warnings.append(warning_msg)
            logger.warning(f"⚠️  {warning_msg}")
            self.checks_passed += 1
            return True
        
        # Attempt to connect to database with retries
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting database connection (attempt {attempt}/{max_retries})...")
                
                # Try to establish connection
                import psycopg2
                conn = psycopg2.connect(database_url, connect_timeout=5)
                conn.close()
                
                logger.info(f"✅ Database connection successful")
                self.checks_passed += 1
                return True
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️  Database connection attempt {attempt} failed: {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    error_msg = f"Database connection failed after {max_retries} attempts: {e}"
                    self.errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    return False
        
        return False
    
    def check_system_dependencies(self) -> bool:
        """
        Check required system dependencies (tesseract).
        
        Returns:
            bool: True if dependencies are available, False otherwise
        """
        logger.info("Checking system dependencies...")
        self.checks_total += 1
        
        dependencies = {
            'tesseract': 'tesseract --version'
        }
        
        all_valid = True
        
        for dep_name, check_cmd in dependencies.items():
            try:
                result = subprocess.run(
                    check_cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    logger.info(f"✅ {dep_name}: {version}")
                else:
                    warning_msg = f"{dep_name} check returned non-zero exit code"
                    self.warnings.append(warning_msg)
                    logger.warning(f"⚠️  {warning_msg}")
                    
            except FileNotFoundError:
                error_msg = f"{dep_name} not found in PATH"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                all_valid = False
            except subprocess.TimeoutExpired:
                warning_msg = f"{dep_name} check timed out"
                self.warnings.append(warning_msg)
                logger.warning(f"⚠️  {warning_msg}")
            except Exception as e:
                warning_msg = f"{dep_name} check error: {e}"
                self.warnings.append(warning_msg)
                logger.warning(f"⚠️  {warning_msg}")
        
        if all_valid:
            self.checks_passed += 1
            logger.info("✅ System dependencies check PASSED")
        else:
            logger.error("❌ System dependencies check FAILED")
        
        return all_valid
    
    def check_disk_space(self, min_free_gb: float = 1.0) -> bool:
        """
        Check available disk space.
        
        Args:
            min_free_gb: Minimum required free space in GB
            
        Returns:
            bool: True if enough space available, False otherwise
        """
        logger.info("Checking disk space...")
        self.checks_total += 1
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            
            if free_gb < min_free_gb:
                error_msg = f"Low disk space: {free_gb:.2f} GB free (required: {min_free_gb} GB)"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return False
            
            logger.info(f"✅ Disk space: {free_gb:.2f} GB free / {total_gb:.2f} GB total")
            self.checks_passed += 1
            return True
            
        except Exception as e:
            warning_msg = f"Could not check disk space: {e}"
            self.warnings.append(warning_msg)
            logger.warning(f"⚠️  {warning_msg}")
            self.checks_passed += 1
            return True
    
    def check_memory_availability(self, min_free_mb: float = 256.0) -> bool:
        """
        Check available memory.
        
        Args:
            min_free_mb: Minimum required free memory in MB
            
        Returns:
            bool: True if enough memory available, False otherwise
        """
        logger.info("Checking memory availability...")
        self.checks_total += 1
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            free_mb = memory.available / (1024**2)
            total_mb = memory.total / (1024**2)
            
            if free_mb < min_free_mb:
                warning_msg = f"Low memory: {free_mb:.2f} MB free (recommended: {min_free_mb} MB)"
                self.warnings.append(warning_msg)
                logger.warning(f"⚠️  {warning_msg}")
            
            logger.info(f"✅ Memory: {free_mb:.2f} MB free / {total_mb:.2f} MB total ({memory.percent}% used)")
            self.checks_passed += 1
            return True
            
        except ImportError:
            logger.info("ℹ️  psutil not installed - skipping memory check")
            self.checks_passed += 1
            return True
        except Exception as e:
            warning_msg = f"Could not check memory: {e}"
            self.warnings.append(warning_msg)
            logger.warning(f"⚠️  {warning_msg}")
            self.checks_passed += 1
            return True
    
    def run_all_checks(self) -> bool:
        """
        Run all startup validation checks.
        
        Returns:
            bool: True if all critical checks passed, False otherwise
        """
        logger.info("="*70)
        logger.info("RAILWAY DEPLOYMENT - STARTUP VALIDATION")
        logger.info("="*70)
        
        start_time = time.time()
        
        # Run all validation checks
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("PORT Configuration", self.check_port_configuration),
            ("Database Connection", self.check_database_connection),
            ("System Dependencies", self.check_system_dependencies),
            ("Disk Space", self.check_disk_space),
            ("Memory Availability", self.check_memory_availability),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                error_msg = f"Unexpected error in {check_name}: {e}"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        logger.info("="*70)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*70)
        logger.info(f"Checks passed: {self.checks_passed}/{self.checks_total}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Elapsed time: {elapsed_time:.2f}s")
        
        if self.errors:
            logger.error("\n❌ CRITICAL ERRORS:")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        if self.warnings:
            logger.warning("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")
        
        logger.info("="*70)
        
        # Return True if no critical errors
        success = len(self.errors) == 0
        
        if success:
            logger.info("✅ STARTUP VALIDATION PASSED - Ready for Railway deployment")
        else:
            logger.error("❌ STARTUP VALIDATION FAILED - Fix errors before deploying")
        
        logger.info("="*70)
        
        return success


def main():
    """Main entry point for startup validation."""
    validator = StartupValidator()
    success = validator.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
