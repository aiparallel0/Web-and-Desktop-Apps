"""
Standardized Logging - Syslog, CLF, and Cisco Format Support

Implements three industry-standard log formats:
1. Syslog (RFC 5424) - Standard system logging protocol
2. Common Log Format (CLF) - Apache/NCSA standard
3. Cisco IOS Format - Network device standard

Usage:
    from shared.utils.standard_logging import get_standard_logger, LogFormat
    
    logger = get_standard_logger('myapp', log_format=LogFormat.SYSLOG)
    logger.info('Application started')
"""

import logging
import logging.handlers
import socket
import os
import sys
import json
import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.standard_logging",
            file_path=__file__,
            description="Standardized logging with Syslog, CLF, and Cisco format support",
            dependencies=["shared.circular_exchange"],
            exports=["get_standard_logger", "LogFormat", "SyslogFormatter", "CLFFormatter", "CiscoFormatter"]
        ))
    except Exception:
        pass


class LogFormat(Enum):
    """Supported log format standards."""
    SYSLOG = "syslog"      # RFC 5424
    CLF = "clf"            # Common Log Format
    CISCO = "cisco"        # Cisco IOS format
    JSON = "json"          # Structured JSON


# Syslog severity levels (RFC 5424)
SYSLOG_SEVERITY = {
    'DEBUG': 7,      # Debug
    'INFO': 6,       # Informational
    'WARNING': 4,    # Warning
    'ERROR': 3,      # Error
    'CRITICAL': 2,   # Critical
}

# Syslog facility codes
SYSLOG_FACILITY = {
    'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
    'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
    'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
    'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
    'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
}

# Cisco severity levels
CISCO_SEVERITY = {
    'DEBUG': 7,
    'INFO': 6,
    'WARNING': 4,
    'ERROR': 3,
    'CRITICAL': 2,
}


class SyslogFormatter(logging.Formatter):
    """
    RFC 5424 Syslog Format:
    <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    
    Example:
    <134>1 2024-01-15T10:30:00.000Z server1 myapp 1234 - - Application started
    """
    
    def __init__(self, app_name: str = "app", facility: str = "local0"):
        super().__init__()
        self.app_name = app_name
        self.facility = SYSLOG_FACILITY.get(facility, 16)
        self.hostname = socket.gethostname()
        self.version = "1"
    
    def format(self, record: logging.LogRecord) -> str:
        severity = SYSLOG_SEVERITY.get(record.levelname, 6)
        priority = (self.facility * 8) + severity
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        procid = os.getpid()
        msgid = "-"
        structured_data = "-"
        
        message = record.getMessage()
        if record.exc_info:
            message += f" | Exception: {self.formatException(record.exc_info)}"
        
        return f"<{priority}>{self.version} {timestamp} {self.hostname} {self.app_name} {procid} {msgid} {structured_data} {message}"


class CLFFormatter(logging.Formatter):
    """
    Common Log Format (NCSA/Apache):
    host ident authuser date request status bytes
    
    Extended for application logging:
    host - user [timestamp] "LEVEL module:function" status message
    
    Example:
    192.168.1.1 - admin [15/Jan/2024:10:30:00 +0000] "INFO mymodule:process" 200 "Processing complete"
    """
    
    def __init__(self):
        super().__init__()
        self.hostname = socket.gethostname()
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S %z")
        if not timestamp.endswith("+0000"):
            timestamp = timestamp[:-2] + "+0000"
        
        user = getattr(record, 'user', '-')
        status = "200" if record.levelno < logging.ERROR else "500"
        
        request = f"{record.levelname} {record.module}:{record.funcName}"
        message = record.getMessage().replace('"', '\\"')
        
        if record.exc_info:
            message += f" | {self.formatException(record.exc_info).replace(chr(10), ' ')}"
        
        return f'{self.hostname} - {user} [{timestamp}] "{request}" {status} "{message}"'


class CiscoFormatter(logging.Formatter):
    """
    Cisco IOS Log Format:
    *timestamp: %FACILITY-SEVERITY-MNEMONIC: Message
    
    Example:
    *Jan 15 10:30:00.000: %SYS-6-INFO: Application started successfully
    
    Cisco Severity Levels:
    0-Emergency, 1-Alert, 2-Critical, 3-Error, 4-Warning, 5-Notice, 6-Info, 7-Debug
    """
    
    def __init__(self, facility: str = "SYS"):
        super().__init__()
        self.facility = facility.upper()
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%b %d %H:%M:%S.%f")[:-3]
        severity = CISCO_SEVERITY.get(record.levelname, 6)
        
        mnemonic = record.funcName.upper()[:10] if record.funcName else "LOG"
        message = record.getMessage()
        
        if record.exc_info:
            message += f" - Exception: {self.formatException(record.exc_info).replace(chr(10), ' ')}"
        
        return f"*{timestamp}: %{self.facility}-{severity}-{mnemonic}: {message}"


class StandardJSONFormatter(logging.Formatter):
    """JSON format with Syslog-compatible fields."""
    
    def __init__(self, app_name: str = "app"):
        super().__init__()
        self.app_name = app_name
        self.hostname = socket.gethostname()
    
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": self.hostname,
            "app_name": self.app_name,
            "pid": os.getpid(),
            "level": record.levelname,
            "severity": SYSLOG_SEVERITY.get(record.levelname, 6),
            "facility": "local0",
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(data, default=str)


_loggers: Dict[str, logging.Logger] = {}
_lock = threading.Lock()


def get_standard_logger(
    name: str,
    log_format: LogFormat = LogFormat.SYSLOG,
    level: str = "INFO",
    log_dir: str = "logs",
    console: bool = True,
    file_output: bool = True,
    facility: str = "local0",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Get a standardized logger with specified format.
    
    Args:
        name: Logger name
        log_format: One of SYSLOG, CLF, CISCO, JSON
        level: Log level
        log_dir: Directory for log files
        console: Enable console output
        file_output: Enable file output
        facility: Syslog facility (for SYSLOG format)
        max_bytes: Max file size before rotation
        backup_count: Number of backup files
    
    Returns:
        Configured logger
    """
    with _lock:
        cache_key = f"{name}_{log_format.value}"
        if cache_key in _loggers:
            return _loggers[cache_key]
        
        logger = logging.getLogger(f"std.{name}.{log_format.value}")
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers.clear()
        
        # Select formatter
        if log_format == LogFormat.SYSLOG:
            formatter = SyslogFormatter(app_name=name, facility=facility)
            ext = "log"
        elif log_format == LogFormat.CLF:
            formatter = CLFFormatter()
            ext = "clf.log"
        elif log_format == LogFormat.CISCO:
            formatter = CiscoFormatter(facility=name.upper()[:3] or "SYS")
            ext = "cisco.log"
        else:
            formatter = StandardJSONFormatter(app_name=name)
            ext = "json.log"
        
        # Console handler
        if console:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        
        # File handler
        if file_output:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            fh = logging.handlers.RotatingFileHandler(
                log_path / f"{name.replace('.', '_')}.{ext}",
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        _loggers[cache_key] = logger
        return logger


def get_multi_format_logger(
    name: str,
    formats: list = None,
    **kwargs
) -> Dict[str, logging.Logger]:
    """
    Get loggers in multiple formats simultaneously.
    
    Returns dict mapping format name to logger.
    """
    if formats is None:
        formats = [LogFormat.SYSLOG, LogFormat.CLF, LogFormat.CISCO]
    
    return {
        fmt.value: get_standard_logger(name, log_format=fmt, **kwargs)
        for fmt in formats
    }


# Convenience functions
def syslog(name: str = "app", **kwargs) -> logging.Logger:
    """Get a Syslog-formatted logger."""
    return get_standard_logger(name, LogFormat.SYSLOG, **kwargs)


def clf(name: str = "app", **kwargs) -> logging.Logger:
    """Get a CLF-formatted logger."""
    return get_standard_logger(name, LogFormat.CLF, **kwargs)


def cisco(name: str = "app", **kwargs) -> logging.Logger:
    """Get a Cisco-formatted logger."""
    return get_standard_logger(name, LogFormat.CISCO, **kwargs)
