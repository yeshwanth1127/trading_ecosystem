"""
Comprehensive Error Handling Service
===================================

Provides centralized error handling with:
- Custom exception classes
- Error categorization and logging
- User-friendly error messages
- Error recovery strategies
- Performance monitoring
"""

import asyncio
import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from fastapi import HTTPException
from sqlalchemy.exc import (
    IntegrityError, 
    OperationalError, 
    DisconnectionError,
    TimeoutError as SQLTimeoutError,
    StatementError
)
import redis.exceptions as redis_exceptions

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization"""
    DATABASE = "database"
    REDIS = "redis"
    NETWORK = "network"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    SYSTEM = "system"

@dataclass
class ErrorContext:
    """Context information for error handling"""
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    order_id: Optional[str] = None
    trade_id: Optional[str] = None
    position_id: Optional[str] = None
    instrument_symbol: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: str
    message: str
    user_message: str
    context: ErrorContext
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

class TradingSystemError(Exception):
    """Base exception for trading system errors"""
    
    def __init__(
        self,
        message: str,
        user_message: str = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext = None,
        recovery_suggestions: List[str] = None
    ):
        super().__init__(message)
        self.user_message = user_message or message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.now(timezone.utc)

class DatabaseError(TradingSystemError):
    """Database-related errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "A database error occurred. Please try again.",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context=context,
            recovery_suggestions=[
                "Check database connection",
                "Verify data integrity",
                "Retry the operation"
            ]
        )

class RedisError(TradingSystemError):
    """Redis-related errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "A caching error occurred. Please try again.",
            category=ErrorCategory.REDIS,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            recovery_suggestions=[
                "Check Redis connection",
                "Clear cache if necessary",
                "Retry the operation"
            ]
        )

class ValidationError(TradingSystemError):
    """Data validation errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "Invalid data provided. Please check your input.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            context=context,
            recovery_suggestions=[
                "Check input data format",
                "Verify required fields",
                "Ensure data is within valid ranges"
            ]
        )

class BusinessLogicError(TradingSystemError):
    """Business logic errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "A business rule violation occurred.",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            recovery_suggestions=[
                "Check account balance",
                "Verify position limits",
                "Review order parameters"
            ]
        )

class ExternalAPIError(TradingSystemError):
    """External API errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "External service temporarily unavailable.",
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            recovery_suggestions=[
                "Retry the operation",
                "Check external service status",
                "Use cached data if available"
            ]
        )

class AuthenticationError(TradingSystemError):
    """Authentication errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "Authentication failed. Please log in again.",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            recovery_suggestions=[
                "Check login credentials",
                "Refresh authentication token",
                "Contact support if issue persists"
            ]
        )

class RateLimitError(TradingSystemError):
    """Rate limiting errors"""
    
    def __init__(self, message: str, user_message: str = None, context: ErrorContext = None):
        super().__init__(
            message=message,
            user_message=user_message or "Too many requests. Please wait before trying again.",
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.LOW,
            context=context,
            recovery_suggestions=[
                "Wait before retrying",
                "Reduce request frequency",
                "Check rate limit status"
            ]
        )

class ErrorHandler:
    """
    Centralized error handling service
    
    Features:
    - Error categorization and logging
    - User-friendly error messages
    - Error recovery strategies
    - Performance monitoring
    - Error aggregation and reporting
    """
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[ErrorInfo] = []
        self.max_history_size = 1000
        self.rate_limit_threshold = 100  # errors per minute
        self.error_rate_limits: Dict[str, Dict] = {}  # error_key -> {count, last_reset}
        self.rate_limit_window = 60  # seconds
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext = None,
        user_message: str = None,
        severity: ErrorSeverity = None
    ) -> ErrorInfo:
        """
        Handle and categorize an error
        
        Args:
            error: The exception that occurred
            context: Additional context information
            user_message: User-friendly error message
            severity: Error severity level
            
        Returns:
            ErrorInfo object with structured error information
        """
        error_info = self._categorize_error(error, context, user_message, severity)
        
        # Check rate limiting before processing
        if self._is_rate_limited(error_info):
            return error_info
        
        # Log the error
        self._log_error(error_info)
        
        # Update error counts
        self._update_error_counts(error_info)
        
        # Add to history
        self._add_to_history(error_info)
        
        # Check for error patterns
        self._check_error_patterns(error_info)
        
        return error_info
    
    def _is_rate_limited(self, error_info: ErrorInfo) -> bool:
        """Check if error should be rate limited"""
        # Create a unique key for this error type and context
        error_key = f"{error_info.error_type}_{error_info.category}"
        if error_info.context and error_info.context.instrument_symbol:
            error_key += f"_{error_info.context.instrument_symbol}"
        
        current_time = datetime.now(timezone.utc)
        
        # Initialize or reset rate limit data
        if error_key not in self.error_rate_limits:
            self.error_rate_limits[error_key] = {
                'count': 0,
                'last_reset': current_time
            }
        
        rate_data = self.error_rate_limits[error_key]
        
        # Reset counter if window has passed
        if (current_time - rate_data['last_reset']).total_seconds() > self.rate_limit_window:
            rate_data['count'] = 0
            rate_data['last_reset'] = current_time
        
        # Increment counter
        rate_data['count'] += 1
        
        # Rate limit if too many errors of this type
        max_errors_per_window = 10  # Allow max 10 of same error per minute
        if rate_data['count'] > max_errors_per_window:
            # Only log every 50th occurrence to reduce spam
            if rate_data['count'] % 50 == 0:
                logger.warning(f"Rate limiting error: {error_key} (occurred {rate_data['count']} times in last minute)")
            return True
        
        return False
    
    def _categorize_error(
        self,
        error: Exception,
        context: ErrorContext = None,
        user_message: str = None,
        severity: ErrorSeverity = None
    ) -> ErrorInfo:
        """Categorize and structure error information"""
        
        # Determine error category and severity
        if isinstance(error, TradingSystemError):
            category = error.category
            severity = severity or error.severity
            user_message = user_message or error.user_message
            context = context or error.context
            recovery_suggestions = error.recovery_suggestions
        else:
            category, severity, user_message, recovery_suggestions = self._classify_standard_error(error)
            context = context or ErrorContext()
        
        # Generate error ID
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
        
        # Get stack trace for debugging
        stack_trace = traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        
        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            category=category,
            severity=severity,
            error_type=type(error).__name__,
            message=str(error),
            user_message=user_message,
            context=context,
            stack_trace=stack_trace,
            recovery_suggestions=recovery_suggestions
        )
    
    def _classify_standard_error(self, error: Exception) -> tuple:
        """Classify standard Python exceptions"""
        
        if isinstance(error, (IntegrityError, OperationalError, DisconnectionError, SQLTimeoutError, StatementError)):
            return (
                ErrorCategory.DATABASE,
                ErrorSeverity.HIGH,
                "A database error occurred. Please try again.",
                ["Check database connection", "Retry the operation", "Contact support if issue persists"]
            )
        
        elif isinstance(error, redis_exceptions.RedisError):
            return (
                ErrorCategory.REDIS,
                ErrorSeverity.MEDIUM,
                "A caching error occurred. Please try again.",
                ["Check Redis connection", "Clear cache if necessary", "Retry the operation"]
            )
        
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return (
                ErrorCategory.NETWORK,
                ErrorSeverity.MEDIUM,
                "Network connection error. Please check your connection.",
                ["Check internet connection", "Retry the operation", "Contact support if issue persists"]
            )
        
        elif isinstance(error, ValueError):
            return (
                ErrorCategory.VALIDATION,
                ErrorSeverity.LOW,
                "Invalid data provided. Please check your input.",
                ["Check input data format", "Verify required fields", "Ensure data is within valid ranges"]
            )
        
        elif isinstance(error, HTTPException):
            return (
                ErrorCategory.SYSTEM,
                ErrorSeverity.MEDIUM,
                error.detail,
                ["Retry the operation", "Contact support if issue persists"]
            )
        
        else:
            return (
                ErrorCategory.SYSTEM,
                ErrorSeverity.MEDIUM,
                "An unexpected error occurred. Please try again.",
                ["Retry the operation", "Contact support if issue persists"]
            )
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        
        log_data = {
            "error_id": error_info.error_id,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "error_type": error_info.error_type,
            "message": error_info.message,
            "context": {
                "user_id": error_info.context.user_id,
                "account_id": error_info.context.account_id,
                "operation": error_info.context.operation
            }
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {log_data}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {log_data}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {log_data}")
        else:
            logger.info(f"LOW SEVERITY ERROR: {log_data}")
    
    def _update_error_counts(self, error_info: ErrorInfo):
        """Update error counts for monitoring"""
        key = f"{error_info.category.value}_{error_info.error_type}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _add_to_history(self, error_info: ErrorInfo):
        """Add error to history (with size limit)"""
        self.error_history.append(error_info)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _check_error_patterns(self, error_info: ErrorInfo):
        """Check for error patterns that might indicate system issues"""
        
        # Check for high error rates
        recent_errors = [
            e for e in self.error_history 
            if (datetime.now(timezone.utc) - e.timestamp).total_seconds() < 60
        ]
        
        if len(recent_errors) > self.rate_limit_threshold:
            logger.critical(f"High error rate detected: {len(recent_errors)} errors in the last minute")
        
        # Check for repeated errors
        same_errors = [
            e for e in recent_errors 
            if e.error_type == error_info.error_type and e.category == error_info.category
        ]
        
        if len(same_errors) > 10:
            logger.warning(f"Repeated error pattern detected: {error_info.error_type} occurred {len(same_errors)} times")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "recent_errors": len([
                e for e in self.error_history 
                if (datetime.now(timezone.utc) - e.timestamp).total_seconds() < 300  # Last 5 minutes
            ]),
            "critical_errors": len([
                e for e in self.error_history 
                if e.severity == ErrorSeverity.CRITICAL
            ]),
            "high_severity_errors": len([
                e for e in self.error_history 
                if e.severity == ErrorSeverity.HIGH
            ])
        }
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get errors filtered by category"""
        return [e for e in self.error_history if e.category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """Get errors filtered by severity"""
        return [e for e in self.error_history if e.severity == severity]
    
    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counts.clear()

# Global error handler instance
error_handler = ErrorHandler()

# Decorator for automatic error handling
def handle_errors(
    user_message: str = None,
    severity: ErrorSeverity = None,
    context: ErrorContext = None
):
    """
    Decorator for automatic error handling
    
    Usage:
        @handle_errors(user_message="Failed to process order", severity=ErrorSeverity.HIGH)
        async def process_order(order_data):
            # Function will automatically handle errors
            pass
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = error_handler.handle_error(
                    error=e,
                    context=context,
                    user_message=user_message,
                    severity=severity
                )
                
                # Re-raise as appropriate exception type
                if error_info.severity == ErrorSeverity.CRITICAL:
                    raise TradingSystemError(
                        message=error_info.message,
                        user_message=error_info.user_message,
                        category=error_info.category,
                        severity=error_info.severity,
                        context=error_info.context
                    )
                else:
                    raise HTTPException(
                        status_code=500 if error_info.severity == ErrorSeverity.HIGH else 400,
                        detail=error_info.user_message
                    )
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = error_handler.handle_error(
                    error=e,
                    context=context,
                    user_message=user_message,
                    severity=severity
                )
                
                # Re-raise as appropriate exception type
                if error_info.severity == ErrorSeverity.CRITICAL:
                    raise TradingSystemError(
                        message=error_info.message,
                        user_message=error_info.user_message,
                        category=error_info.category,
                        severity=error_info.severity,
                        context=error_info.context
                    )
                else:
                    raise HTTPException(
                        status_code=500 if error_info.severity == ErrorSeverity.HIGH else 400,
                        detail=error_info.user_message
                    )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
