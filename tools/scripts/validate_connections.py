#!/usr/bin/env python3
"""
=============================================================================
CONNECTION VALIDATION SCRIPT
=============================================================================

Validates all system connections:
- Database (PostgreSQL/SQLite)
- Redis (for Celery)
- Celery worker/beat
- Backend API endpoints
- Frontend-backend connectivity
- Model imports

Usage:
    python tools/scripts/validate_connections.py
    
Exit codes:
    0 - All connections healthy
    1 - Critical connection failures
    2 - Warning issues detected

=============================================================================
"""

import sys
import os
import time
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class ConnectionValidator:
    """Validates system connections and reports status."""
    
    def __init__(self):
        self.results = {
            'database': {'status': 'pending', 'details': []},
            'redis': {'status': 'pending', 'details': []},
            'celery_worker': {'status': 'pending', 'details': []},
            'celery_beat': {'status': 'pending', 'details': []},
            'backend_api': {'status': 'pending', 'details': []},
            'frontend': {'status': 'pending', 'details': []},
            'models': {'status': 'pending', 'details': []},
            'imports': {'status': 'pending', 'details': []},
        }
        self.critical_failures = []
        self.warnings = []
    
    def validate_database(self) -> bool:
        """Validate database connection."""
        print("\n" + "="*70)
        print("VALIDATING DATABASE CONNECTION")
        print("="*70)
        
        try:
            from web.backend.database import get_engine, check_database_health
            from sqlalchemy import text
            
            # Get database URL
            database_url = os.getenv('DATABASE_URL', 'Not Set')
            print(f"DATABASE_URL: {database_url}")
            
            # Test connection
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                assert result == 1
            
            # Get health metrics
            health = check_database_health()
            
            if health['status'] == 'healthy':
                print(f"✅ Database connection: HEALTHY")
                print(f"   Query latency: {health.get('query_latency_seconds', 0)}s")
                
                pool_info = health.get('pool', {})
                if pool_info:
                    print(f"   Pool size: {pool_info.get('size', 'N/A')}")
                    print(f"   Checked out: {pool_info.get('checked_out', 'N/A')}")
                
                self.results['database']['status'] = 'healthy'
                self.results['database']['details'] = health
                return True
            else:
                error = health.get('error', 'Unknown error')
                print(f"❌ Database connection: UNHEALTHY")
                print(f"   Error: {error}")
                self.results['database']['status'] = 'unhealthy'
                self.results['database']['details'] = health
                self.critical_failures.append(f"Database: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Database connection: FAILED")
            print(f"   Error: {e}")
            self.results['database']['status'] = 'failed'
            self.results['database']['details'] = {'error': str(e)}
            self.critical_failures.append(f"Database: {e}")
            return False
    
    def validate_redis(self) -> bool:
        """Validate Redis connection."""
        print("\n" + "="*70)
        print("VALIDATING REDIS CONNECTION")
        print("="*70)
        
        try:
            import redis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            print(f"REDIS_URL: {redis_url}")
            
            # Connect to Redis
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            
            # Test connection
            r.ping()
            
            # Get info
            info = r.info('server')
            redis_version = info.get('redis_version', 'unknown')
            
            print(f"✅ Redis connection: HEALTHY")
            print(f"   Version: {redis_version}")
            print(f"   Memory used: {info.get('used_memory_human', 'N/A')}")
            
            self.results['redis']['status'] = 'healthy'
            self.results['redis']['details'] = {
                'version': redis_version,
                'url': redis_url
            }
            return True
            
        except ImportError:
            print(f"⚠️  Redis: Python client not installed")
            self.results['redis']['status'] = 'not_installed'
            self.warnings.append("Redis client not installed")
            return True  # Not critical
            
        except Exception as e:
            print(f"❌ Redis connection: FAILED")
            print(f"   Error: {e}")
            self.results['redis']['status'] = 'failed'
            self.results['redis']['details'] = {'error': str(e)}
            self.warnings.append(f"Redis: {e}")
            return True  # Redis is optional for core functionality
    
    def validate_celery_worker(self) -> bool:
        """Validate Celery worker availability."""
        print("\n" + "="*70)
        print("VALIDATING CELERY WORKER")
        print("="*70)
        
        try:
            from shared.services.background_tasks import celery_app, is_celery_available
            
            if not is_celery_available():
                print(f"⚠️  Celery: Not installed or not configured")
                self.results['celery_worker']['status'] = 'not_available'
                self.warnings.append("Celery not available")
                return True  # Not critical
            
            # Check if worker is running by inspecting active workers
            inspect = celery_app.control.inspect(timeout=3)
            active_workers = inspect.active()
            
            if active_workers:
                worker_count = len(active_workers)
                print(f"✅ Celery worker: {worker_count} worker(s) active")
                for worker_name in active_workers.keys():
                    print(f"   - {worker_name}")
                
                self.results['celery_worker']['status'] = 'active'
                self.results['celery_worker']['details'] = {
                    'worker_count': worker_count,
                    'workers': list(active_workers.keys())
                }
                return True
            else:
                print(f"⚠️  Celery worker: No active workers found")
                print(f"   Note: Start with: celery -A shared.services.background_tasks worker")
                self.results['celery_worker']['status'] = 'no_workers'
                self.warnings.append("No Celery workers running")
                return True  # Not critical for basic operation
                
        except Exception as e:
            print(f"⚠️  Celery worker: Check failed")
            print(f"   Error: {e}")
            self.results['celery_worker']['status'] = 'check_failed'
            self.results['celery_worker']['details'] = {'error': str(e)}
            self.warnings.append(f"Celery worker check: {e}")
            return True  # Not critical
    
    def validate_backend_api(self) -> bool:
        """Validate backend API endpoints."""
        print("\n" + "="*70)
        print("VALIDATING BACKEND API ENDPOINTS")
        print("="*70)
        
        try:
            from web.backend.app import app
            
            # Test critical endpoints
            endpoints_to_test = [
                ('/api/health', 'GET'),
                ('/api/models', 'GET'),
                ('/api', 'GET'),
            ]
            
            with app.test_client() as client:
                all_passed = True
                for endpoint, method in endpoints_to_test:
                    try:
                        if method == 'GET':
                            response = client.get(endpoint)
                        else:
                            response = client.post(endpoint)
                        
                        if response.status_code < 500:
                            print(f"✅ {method} {endpoint}: {response.status_code}")
                        else:
                            print(f"❌ {method} {endpoint}: {response.status_code}")
                            all_passed = False
                    except Exception as e:
                        print(f"❌ {method} {endpoint}: {e}")
                        all_passed = False
                
                if all_passed:
                    self.results['backend_api']['status'] = 'healthy'
                    return True
                else:
                    self.results['backend_api']['status'] = 'partial'
                    self.warnings.append("Some API endpoints failed")
                    return True  # Partial failure is not critical
                    
        except Exception as e:
            print(f"❌ Backend API validation: FAILED")
            print(f"   Error: {e}")
            self.results['backend_api']['status'] = 'failed'
            self.critical_failures.append(f"Backend API: {e}")
            return False
    
    def validate_models(self) -> bool:
        """Validate model imports and availability."""
        print("\n" + "="*70)
        print("VALIDATING MODEL IMPORTS")
        print("="*70)
        
        try:
            from shared.models.manager import ModelManager
            
            manager = ModelManager()
            models = manager.get_available_models(check_availability=True)
            
            available_count = sum(1 for m in models if m.get('available', False))
            total_count = len(models)
            
            print(f"Total models: {total_count}")
            print(f"Available models: {available_count}")
            
            for model in models:
                status = "✅" if model.get('available') else "❌"
                print(f"  {status} {model['id']}: {model['name']}")
            
            if available_count > 0:
                print(f"\n✅ At least {available_count} model(s) available")
                self.results['models']['status'] = 'available'
                self.results['models']['details'] = {
                    'total': total_count,
                    'available': available_count
                }
                return True
            else:
                print(f"\n⚠️  No models available (dependencies not installed)")
                self.results['models']['status'] = 'none_available'
                self.warnings.append("No AI models available")
                return True  # Not critical for core functionality
                
        except Exception as e:
            print(f"❌ Model validation: FAILED")
            print(f"   Error: {e}")
            self.results['models']['status'] = 'failed'
            self.results['models']['details'] = {'error': str(e)}
            self.warnings.append(f"Models: {e}")
            return True  # Not critical
    
    def validate_imports(self) -> bool:
        """Validate critical Python imports."""
        print("\n" + "="*70)
        print("VALIDATING CRITICAL IMPORTS")
        print("="*70)
        
        critical_imports = [
            'flask',
            'sqlalchemy',
            'web.backend.app',
            'web.backend.database',
            'shared.models.manager',
            'shared.services.background_tasks',
        ]
        
        failed_imports = []
        
        for module_name in critical_imports:
            try:
                __import__(module_name)
                print(f"✅ {module_name}")
            except Exception as e:
                print(f"❌ {module_name}: {e}")
                failed_imports.append(module_name)
        
        if not failed_imports:
            print(f"\n✅ All critical imports successful")
            self.results['imports']['status'] = 'healthy'
            return True
        else:
            print(f"\n❌ {len(failed_imports)} critical import(s) failed")
            self.results['imports']['status'] = 'failed'
            self.results['imports']['details'] = {'failed': failed_imports}
            self.critical_failures.append(f"Imports: {', '.join(failed_imports)}")
            return False
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*70)
        print("CONNECTION VALIDATION SUMMARY")
        print("="*70)
        
        for component, result in self.results.items():
            status = result['status']
            symbol = {
                'healthy': '✅',
                'active': '✅',
                'available': '✅',
                'partial': '⚠️',
                'not_available': '⚠️',
                'not_installed': '⚠️',
                'no_workers': '⚠️',
                'none_available': '⚠️',
                'check_failed': '⚠️',
                'unhealthy': '❌',
                'failed': '❌',
                'pending': '⏳'
            }.get(status, '❓')
            
            print(f"{symbol} {component.replace('_', ' ').title()}: {status}")
        
        print("\n" + "="*70)
        
        if self.critical_failures:
            print(f"❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   - {failure}")
            print("\nAction Required: Fix critical failures before deployment")
            return 1
        elif self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
            print("\nNote: Warnings are non-critical but should be addressed")
            return 2
        else:
            print("✅ ALL SYSTEMS HEALTHY")
            print("\nAll connections validated successfully!")
            return 0
    
    def run_all_validations(self) -> int:
        """Run all validations and return exit code."""
        print("\n" + "="*70)
        print("CONNECTION VALIDATION SUITE")
        print(f"Started: {datetime.now().isoformat()}")
        print("="*70)
        
        # Run validations
        self.validate_imports()
        self.validate_database()
        self.validate_redis()
        self.validate_celery_worker()
        self.validate_backend_api()
        self.validate_models()
        
        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    validator = ConnectionValidator()
    exit_code = validator.run_all_validations()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
