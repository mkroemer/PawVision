"""Logging configuration for PawVision."""

import logging
import logging.handlers
import os
import sys


def setup_logging(log_level: int = logging.INFO, 
                  log_file: str = None,
                  dev_mode: bool = False) -> logging.Logger:
    """Set up structured logging for PawVision.
    
    Args:
        log_level: Logging level (e.g., logging.INFO)
        log_file: Path to log file (optional)
        dev_mode: Whether running in development mode
        
    Returns:
        Configured logger instance
    """
    # Create formatter
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    # Set console level based on mode
    if dev_mode:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(log_level)
    
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(log_format)
            file_handler.setLevel(logging.DEBUG)  # File gets all messages
            
            root_logger.addHandler(file_handler)
            
            # Log initial message
            logger = logging.getLogger(__name__)
            logger.info("Logging initialized - file: %s, level: %s", 
                       log_file, logging.getLevelName(log_level))
            
        except OSError as e:
            # Fall back to console only
            console_logger = logging.getLogger(__name__)
            console_logger.error("Could not initialize file logging: %s", e)
            console_logger.info("Using console logging only")
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info("PawVision logging started - dev_mode: %s", dev_mode)
    
    return root_logger


class PawVisionLogger:
    """Custom logger wrapper with additional context."""
    
    def __init__(self, name: str, context: dict = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        """Add context to log message."""
        if self.context:
            context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"{message} | {context_str}"
        return message
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), *args, **kwargs)
    
    def set_context(self, **kwargs):
        """Update logger context."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logger context."""
        self.context.clear()


def get_logger(name: str, context: dict = None) -> PawVisionLogger:
    """Get a PawVision logger with optional context.
    
    Args:
        name: Logger name
        context: Additional context to include in messages
        
    Returns:
        PawVisionLogger instance
    """
    return PawVisionLogger(name, context)


def log_system_info():
    """Log system information for debugging."""
    import platform
    
    logger = logging.getLogger(__name__)
    
    logger.info("=== System Information ===")
    logger.info("Platform: %s", platform.platform())
    logger.info("Python: %s", platform.python_version())
    
    try:
        import psutil
        logger.info("CPU cores: %d", psutil.cpu_count())
        logger.info("Memory: %.1f GB", psutil.virtual_memory().total / (1024**3))
        logger.info("Disk free: %.1f GB", psutil.disk_usage('/').free / (1024**3))
    except ImportError:
        logger.info("psutil not available for detailed system info")
    
    logger.info("=== End System Information ===")


def log_performance_metrics(func):
    """Decorator to log function performance metrics."""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug("Function %s completed in %.3fs", func.__name__, duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Function %s failed after %.3fs: %s", 
                        func.__name__, duration, e)
            raise
    
    return wrapper


class ContextualFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self, context: dict = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        """Add context to the log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_request_logging(app):
    """Set up request logging for Flask app."""
    
    @app.before_request
    def log_request_info():
        """Log incoming request information."""
        from flask import request
        logger = logging.getLogger('pawvision.web')
        
        logger.info("Request: %s %s from %s", 
                   request.method, request.path, request.remote_addr)
        
        if request.form:
            # Log form data (excluding sensitive fields)
            safe_form = {k: v for k, v in request.form.items() 
                        if 'password' not in k.lower() and 'token' not in k.lower()}
            logger.debug("Form data: %s", safe_form)
    
    @app.after_request
    def log_response_info(response):
        """Log response information."""
        logger = logging.getLogger('pawvision.web')
        logger.info("Response: %d %s", response.status_code, response.status)
        return response
