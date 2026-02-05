#!/usr/bin/env python3
"""
=============================================================================
LOG MANAGEMENT UTILITY
=============================================================================

Manages log files to prevent disk space issues and improve maintainability.

Features:
- Automatic log rotation
- Compression of old logs
- Cleanup of logs older than retention period
- Log analysis and reporting

Usage:
    # Rotate and clean logs
    python scripts/log_manager.py --rotate --clean
    
    # Analyze current logs
    python scripts/log_manager.py --analyze
    
    # Set up as cron job (daily at 3 AM)
    0 3 * * * /usr/bin/python3 /path/to/log_manager.py --rotate --clean --compress

=============================================================================
"""

import os
import sys
import gzip
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogManager:
    """Manages log files with rotation, compression, and cleanup."""
    
    def __init__(self, base_dir: str = None, retention_days: int = 30):
        """
        Initialize log manager.
        
        Args:
            base_dir: Base directory for logs (default: project root)
            retention_days: Days to keep logs before deletion
        """
        if base_dir is None:
            # Use project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / 'logs'
        self.retention_days = retention_days
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
    
    def find_log_files(self, include_compressed=False):
        """
        Find all log files in base directory and logs/ subdirectory.
        
        Args:
            include_compressed: Include .gz files
            
        Returns:
            List of Path objects for log files
        """
        patterns = ['*.log', '*.csv', '*.json']
        if include_compressed:
            patterns.append('*.gz')
        
        log_files = []
        
        # Check base directory for log files
        for pattern in patterns:
            for log_file in self.base_dir.glob(pattern):
                if 'log' in log_file.name.lower():
                    log_files.append(log_file)
        
        # Check logs subdirectory
        if self.logs_dir.exists():
            for pattern in patterns:
                log_files.extend(self.logs_dir.glob(pattern))
        
        return sorted(log_files, key=lambda p: p.stat().st_mtime)
    
    def rotate_logs(self):
        """
        Rotate log files by moving them to logs/ directory with timestamp.
        
        Returns:
            Number of files rotated
        """
        logger.info("Starting log rotation...")
        rotated = 0
        
        # Find log files in base directory (not in logs/)
        for log_file in self.base_dir.glob('*'):
            if not log_file.is_file():
                continue
            
            # Check if it's a log file
            if 'log' in log_file.name.lower() and log_file.suffix in ('.log', '.csv', '.json'):
                # Don't rotate if already in logs/ directory
                if log_file.parent == self.logs_dir:
                    continue
                
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                timestamp = mtime.strftime('%Y%m%d_%H%M%S')
                
                # Create new filename with timestamp
                new_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
                new_path = self.logs_dir / new_name
                
                # Move file
                try:
                    shutil.move(str(log_file), str(new_path))
                    logger.info(f"Rotated: {log_file.name} -> {new_path.name}")
                    rotated += 1
                except Exception as e:
                    logger.error(f"Failed to rotate {log_file}: {e}")
        
        logger.info(f"Rotated {rotated} log files")
        return rotated
    
    def compress_old_logs(self, days_old: int = 7):
        """
        Compress log files older than specified days.
        
        Args:
            days_old: Compress files older than this many days
            
        Returns:
            Number of files compressed
        """
        logger.info(f"Compressing logs older than {days_old} days...")
        compressed = 0
        cutoff = datetime.now() - timedelta(days=days_old)
        
        for log_file in self.find_log_files(include_compressed=False):
            # Skip if already compressed
            if log_file.suffix == '.gz':
                continue
            
            # Check file age
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                try:
                    # Compress file
                    gz_path = Path(str(log_file) + '.gz')
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(gz_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original
                    log_file.unlink()
                    logger.info(f"Compressed: {log_file.name}")
                    compressed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to compress {log_file}: {e}")
        
        logger.info(f"Compressed {compressed} log files")
        return compressed
    
    def cleanup_old_logs(self):
        """
        Delete logs older than retention period.
        
        Returns:
            Number of files deleted
        """
        logger.info(f"Cleaning up logs older than {self.retention_days} days...")
        deleted = 0
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.find_log_files(include_compressed=True):
            # Check file age
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                try:
                    log_file.unlink()
                    logger.info(f"Deleted: {log_file.name}")
                    deleted += 1
                except Exception as e:
                    logger.error(f"Failed to delete {log_file}: {e}")
        
        logger.info(f"Deleted {deleted} log files")
        return deleted
    
    def analyze_logs(self):
        """
        Analyze log files and generate report.
        
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing log files...")
        
        log_files = self.find_log_files(include_compressed=True)
        
        total_size = sum(f.stat().st_size for f in log_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Count by type
        by_type = {}
        by_age = {'< 1 day': 0, '1-7 days': 0, '7-30 days': 0, '> 30 days': 0}
        
        now = datetime.now()
        
        for log_file in log_files:
            # By extension
            ext = log_file.suffix
            if ext == '.gz':
                # Get original extension
                ext = Path(log_file.stem).suffix
            by_type[ext] = by_type.get(ext, 0) + 1
            
            # By age
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            age_days = (now - mtime).days
            
            if age_days < 1:
                by_age['< 1 day'] += 1
            elif age_days < 7:
                by_age['1-7 days'] += 1
            elif age_days < 30:
                by_age['7-30 days'] += 1
            else:
                by_age['> 30 days'] += 1
        
        analysis = {
            'total_files': len(log_files),
            'total_size_mb': round(total_size_mb, 2),
            'by_type': by_type,
            'by_age': by_age,
            'logs_directory': str(self.logs_dir),
            'retention_days': self.retention_days
        }
        
        return analysis
    
    def print_analysis(self):
        """Print formatted analysis report."""
        analysis = self.analyze_logs()
        
        print("\n" + "="*80)
        print("LOG FILES ANALYSIS")
        print("="*80 + "\n")
        
        print(f"Total Files: {analysis['total_files']}")
        print(f"Total Size: {analysis['total_size_mb']} MB")
        print(f"Logs Directory: {analysis['logs_directory']}")
        print(f"Retention Period: {analysis['retention_days']} days")
        
        print(f"\nBy File Type:")
        for file_type, count in sorted(analysis['by_type'].items()):
            print(f"  {file_type}: {count} files")
        
        print(f"\nBy Age:")
        for age_range, count in analysis['by_age'].items():
            print(f"  {age_range}: {count} files")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage log files with rotation, compression, and cleanup'
    )
    parser.add_argument('--rotate', action='store_true',
                       help='Rotate log files to logs/ directory')
    parser.add_argument('--compress', action='store_true',
                       help='Compress logs older than 7 days')
    parser.add_argument('--clean', action='store_true',
                       help='Delete logs older than retention period')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze and report on log files')
    parser.add_argument('--retention-days', type=int, default=30,
                       help='Retention period in days (default: 30)')
    parser.add_argument('--base-dir', type=str,
                       help='Base directory (default: project root)')
    
    args = parser.parse_args()
    
    # If no action specified, show analysis
    if not any([args.rotate, args.compress, args.clean, args.analyze]):
        args.analyze = True
    
    # Initialize manager
    manager = LogManager(
        base_dir=args.base_dir,
        retention_days=args.retention_days
    )
    
    # Execute actions
    if args.rotate:
        manager.rotate_logs()
    
    if args.compress:
        manager.compress_old_logs()
    
    if args.clean:
        manager.cleanup_old_logs()
    
    if args.analyze:
        manager.print_analysis()


if __name__ == '__main__':
    main()
