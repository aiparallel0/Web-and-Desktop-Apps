#!/usr/bin/env python3
"""
Log Analysis Script
Analyzes log files (CSV and JSON) to identify problems and potential issues
"""

import json
import csv
import re
from collections import Counter, defaultdict
from datetime import datetime
import os

def analyze_csv_logs(filepath):
    """Analyze CSV log file"""
    print(f"\n{'='*80}")
    print(f"Analyzing CSV Log: {filepath}")
    print(f"{'='*80}\n")
    
    errors = []
    error_types = Counter()
    error_patterns = Counter()
    timestamps = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                message = row.get('message', '')
                timestamp = row.get('timestamp', '')
                
                if timestamp:
                    timestamps.append(timestamp)
                
                # Detect error patterns
                if 'error' in message.lower() or 'exception' in message.lower() or 'traceback' in message.lower():
                    errors.append({'message': message, 'timestamp': timestamp})
                    
                    # Extract error types
                    if 'Error:' in message and message.split('Error:'):
                        parts = message.split('Error:')[0].split()
                        if parts:
                            error_type = parts[-1] + 'Error'
                            error_types[error_type] += 1
                    elif 'Exception:' in message and message.split('Exception:'):
                        parts = message.split('Exception:')[0].split()
                        if parts:
                            error_type = parts[-1] + 'Exception'
                            error_types[error_type] += 1
                    
                    # Common error patterns
                    if 'TypeError' in message:
                        error_patterns['TypeError'] += 1
                    if 'AttributeError' in message:
                        error_patterns['AttributeError'] += 1
                    if 'ImportError' in message or 'ModuleNotFoundError' in message:
                        error_patterns['Import/Module Error'] += 1
                    if 'ConnectionError' in message or 'connection refused' in message.lower():
                        error_patterns['Connection Error'] += 1
                    if 'timeout' in message.lower():
                        error_patterns['Timeout'] += 1
                    if 'celery' in message.lower():
                        error_patterns['Celery Issue'] += 1
                    if 'database' in message.lower() or 'sql' in message.lower():
                        error_patterns['Database Issue'] += 1
                    if 'memory' in message.lower():
                        error_patterns['Memory Issue'] += 1
                    if 'string indices must be integers' in message.lower():
                        error_patterns['Type Mismatch (string indices)'] += 1
    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return {
        'total_errors': len(errors),
        'error_types': error_types,
        'error_patterns': error_patterns,
        'sample_errors': errors[:10],
        'timestamps': timestamps
    }

def analyze_json_logs(filepath):
    """Analyze JSON log file"""
    print(f"\n{'='*80}")
    print(f"Analyzing JSON Log: {filepath}")
    print(f"{'='*80}\n")
    
    errors = []
    error_types = Counter()
    error_patterns = Counter()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Try to read as JSON array
            try:
                logs = json.load(f)
            except:
                # If not an array, try line-by-line JSON
                f.seek(0)
                logs = []
                for line in f:
                    if line.strip():
                        try:
                            logs.append(json.loads(line))
                        except:
                            pass
        
        for log in logs:
            message = log.get('message', '')
            
            # Detect error patterns
            if 'error' in message.lower() or 'exception' in message.lower() or 'traceback' in message.lower():
                errors.append(log)
                
                # Extract error types
                if 'Error:' in message and message.split('Error:'):
                    parts = message.split('Error:')[0].split()
                    if parts:
                        error_type = parts[-1] + 'Error'
                        error_types[error_type] += 1
                elif 'Exception:' in message and message.split('Exception:'):
                    parts = message.split('Exception:')[0].split()
                    if parts:
                        error_type = parts[-1] + 'Exception'
                        error_types[error_type] += 1
                
                # Common error patterns
                if 'TypeError' in message:
                    error_patterns['TypeError'] += 1
                if 'AttributeError' in message:
                    error_patterns['AttributeError'] += 1
                if 'ImportError' in message or 'ModuleNotFoundError' in message:
                    error_patterns['Import/Module Error'] += 1
                if 'ConnectionError' in message or 'connection refused' in message.lower():
                    error_patterns['Connection Error'] += 1
                if 'timeout' in message.lower():
                    error_patterns['Timeout'] += 1
                if 'celery' in message.lower():
                    error_patterns['Celery Issue'] += 1
                if 'database' in message.lower() or 'sql' in message.lower():
                    error_patterns['Database Issue'] += 1
    
    except Exception as e:
        print(f"Error reading JSON: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return {
        'total_errors': len(errors),
        'error_types': error_types,
        'error_patterns': error_patterns,
        'sample_errors': errors[:10]
    }

def print_analysis_report(analysis, filename):
    """Print formatted analysis report"""
    if not analysis:
        print(f"⚠️  Could not analyze {filename}")
        return
    
    print(f"\n📊 Analysis Report for: {filename}")
    print(f"{'─'*80}")
    print(f"Total Error Entries: {analysis['total_errors']}")
    
    if analysis['error_patterns']:
        print(f"\n🔍 Error Patterns (Top Issues):")
        for pattern, count in analysis['error_patterns'].most_common(10):
            print(f"  • {pattern}: {count} occurrences")
    
    if analysis['error_types']:
        print(f"\n⚠️  Error Types:")
        for error_type, count in analysis['error_types'].most_common(10):
            print(f"  • {error_type}: {count} occurrences")
    
    if analysis.get('sample_errors'):
        print(f"\n📝 Sample Error Messages (first 5):")
        for i, error in enumerate(analysis['sample_errors'][:5], 1):
            msg = error.get('message', str(error))[:150]
            print(f"  {i}. {msg}...")

def identify_problems(analyses):
    """Identify main problems and future issues"""
    print(f"\n{'='*80}")
    print("🚨 IDENTIFIED PROBLEMS AND FUTURE CONCERNS")
    print(f"{'='*80}\n")
    
    all_patterns = Counter()
    for analysis in analyses.values():
        if analysis:
            all_patterns.update(analysis['error_patterns'])
    
    problems = []
    
    # Analyze patterns
    if all_patterns.get('Type Mismatch (string indices)', 0) > 0:
        problems.append({
            'severity': 'HIGH',
            'category': 'Type Error',
            'description': 'String indices type mismatch - likely configuration issue',
            'count': all_patterns['Type Mismatch (string indices)'],
            'recommendation': 'Fix Celery beat_schedule configuration - likely passing string instead of dict'
        })
    
    if all_patterns.get('Celery Issue', 0) > 50:
        problems.append({
            'severity': 'HIGH',
            'category': 'Celery Configuration',
            'description': 'Multiple Celery-related errors',
            'count': all_patterns['Celery Issue'],
            'recommendation': 'Review Celery configuration, especially beat schedule setup'
        })
    
    if all_patterns.get('Connection Error', 0) > 0:
        problems.append({
            'severity': 'MEDIUM',
            'category': 'Network/Connection',
            'description': 'Connection failures detected',
            'count': all_patterns['Connection Error'],
            'recommendation': 'Check service availability and network configuration'
        })
    
    if all_patterns.get('Database Issue', 0) > 0:
        problems.append({
            'severity': 'MEDIUM',
            'category': 'Database',
            'description': 'Database-related errors',
            'count': all_patterns['Database Issue'],
            'recommendation': 'Check database connection and schema'
        })
    
    if all_patterns.get('Memory Issue', 0) > 0:
        problems.append({
            'severity': 'HIGH',
            'category': 'Performance',
            'description': 'Memory-related issues',
            'count': all_patterns['Memory Issue'],
            'recommendation': 'Monitor memory usage and optimize resource allocation'
        })
    
    # Print problems
    for i, problem in enumerate(sorted(problems, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['severity']]), 1):
        print(f"{i}. [{problem['severity']}] {problem['category']}")
        print(f"   Description: {problem['description']}")
        print(f"   Occurrences: {problem['count']}")
        print(f"   ✅ Recommendation: {problem['recommendation']}")
        print()
    
    return problems

def main():
    """Main analysis function"""
    base_dir = '/home/runner/work/Web-and-Desktop-Apps/Web-and-Desktop-Apps'
    
    # Find log files
    log_files = []
    for filename in os.listdir(base_dir):
        if (filename.endswith('.csv') or filename.endswith('.json')) and 'log' in filename.lower():
            log_files.append(os.path.join(base_dir, filename))
    
    print(f"\n🔍 Found {len(log_files)} log files to analyze")
    print(f"{'='*80}")
    
    analyses = {}
    
    # Analyze each file
    for log_file in log_files:
        filename = os.path.basename(log_file)
        if filename.endswith('.csv'):
            analyses[filename] = analyze_csv_logs(log_file)
            print_analysis_report(analyses[filename], filename)
        elif filename.endswith('.json'):
            analyses[filename] = analyze_json_logs(log_file)
            print_analysis_report(analyses[filename], filename)
    
    # Identify overall problems
    problems = identify_problems(analyses)
    
    # Future concerns
    print(f"\n{'='*80}")
    print("🔮 FUTURE CONCERNS")
    print(f"{'='*80}\n")
    
    print("1. Celery Configuration Management")
    print("   - Current: Configuration errors in beat schedule")
    print("   - Risk: Service instability, failed scheduled tasks")
    print("   - Action: Implement configuration validation before deployment")
    
    print("\n2. Error Monitoring & Alerting")
    print("   - Current: Errors accumulating in logs without active monitoring")
    print("   - Risk: Issues may go unnoticed until critical failure")
    print("   - Action: Set up monitoring and alerting system")
    
    print("\n3. Log Management")
    print("   - Current: Large log files (378KB+) in root directory")
    print("   - Risk: Disk space issues, difficult log analysis")
    print("   - Action: Implement log rotation and centralized logging")
    
    print("\n4. Configuration Validation")
    print("   - Current: Type mismatches in configuration")
    print("   - Risk: Runtime failures due to incorrect config types")
    print("   - Action: Add schema validation for configurations")
    
    print(f"\n{'='*80}")
    print("✅ Analysis Complete")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
