"""
Error Monitoring API
===================

Provides endpoints for monitoring and managing system errors.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from app.services.error_handler import (
    error_handler, 
    ErrorCategory, 
    ErrorSeverity, 
    ErrorContext,
    TradingSystemError
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/error-monitoring", tags=["error-monitoring"])

@router.get("/summary")
async def get_error_summary():
    """Get error summary for monitoring dashboard"""
    try:
        summary = error_handler.get_error_summary()
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error summary: {str(e)}")

@router.get("/errors")
async def get_errors(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    limit: int = 100
):
    """Get filtered list of errors"""
    try:
        errors = error_handler.error_history
        
        # Apply filters
        if category:
            errors = [e for e in errors if e.category == category]
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        # Limit results
        errors = errors[-limit:] if limit > 0 else errors
        
        # Convert to dict format
        error_data = []
        for error in errors:
            error_data.append({
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "category": error.category.value,
                "severity": error.severity.value,
                "error_type": error.error_type,
                "message": error.message,
                "user_message": error.user_message,
                "context": {
                    "user_id": error.context.user_id,
                    "account_id": error.context.account_id,
                    "order_id": error.context.order_id,
                    "trade_id": error.context.trade_id,
                    "position_id": error.context.position_id,
                    "instrument_symbol": error.context.instrument_symbol,
                    "operation": error.context.operation,
                    "additional_data": error.context.additional_data
                },
                "recovery_suggestions": error.recovery_suggestions,
                "retry_count": error.retry_count,
                "max_retries": error.max_retries
            })
        
        return {
            "status": "success",
            "data": error_data,
            "count": len(error_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors: {str(e)}")

@router.get("/errors/{error_id}")
async def get_error_details(error_id: str):
    """Get detailed information about a specific error"""
    try:
        error = next(
            (e for e in error_handler.error_history if e.error_id == error_id), 
            None
        )
        
        if not error:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {
            "status": "success",
            "data": {
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "category": error.category.value,
                "severity": error.severity.value,
                "error_type": error.error_type,
                "message": error.message,
                "user_message": error.user_message,
                "context": {
                    "user_id": error.context.user_id,
                    "account_id": error.context.account_id,
                    "order_id": error.context.order_id,
                    "trade_id": error.context.trade_id,
                    "position_id": error.context.position_id,
                    "instrument_symbol": error.context.instrument_symbol,
                    "operation": error.context.operation,
                    "additional_data": error.context.additional_data
                },
                "stack_trace": error.stack_trace,
                "recovery_suggestions": error.recovery_suggestions,
                "retry_count": error.retry_count,
                "max_retries": error.max_retries
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error details: {str(e)}")

@router.get("/errors/category/{category}")
async def get_errors_by_category(category: ErrorCategory, limit: int = 100):
    """Get errors filtered by category"""
    try:
        errors = error_handler.get_errors_by_category(category)
        errors = errors[-limit:] if limit > 0 else errors
        
        error_data = []
        for error in errors:
            error_data.append({
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "severity": error.severity.value,
                "error_type": error.error_type,
                "message": error.message,
                "user_message": error.user_message,
                "context": {
                    "user_id": error.context.user_id,
                    "account_id": error.context.account_id,
                    "operation": error.context.operation
                }
            })
        
        return {
            "status": "success",
            "data": error_data,
            "count": len(error_data),
            "category": category.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors by category: {str(e)}")

@router.get("/errors/severity/{severity}")
async def get_errors_by_severity(severity: ErrorSeverity, limit: int = 100):
    """Get errors filtered by severity"""
    try:
        errors = error_handler.get_errors_by_severity(severity)
        errors = errors[-limit:] if limit > 0 else errors
        
        error_data = []
        for error in errors:
            error_data.append({
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "category": error.category.value,
                "error_type": error.error_type,
                "message": error.message,
                "user_message": error.user_message,
                "context": {
                    "user_id": error.context.user_id,
                    "account_id": error.context.account_id,
                    "operation": error.context.operation
                }
            })
        
        return {
            "status": "success",
            "data": error_data,
            "count": len(error_data),
            "severity": severity.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors by severity: {str(e)}")

@router.delete("/errors/history")
async def clear_error_history():
    """Clear error history (admin only)"""
    try:
        error_handler.clear_history()
        return {
            "status": "success",
            "message": "Error history cleared successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear error history: {str(e)}")

@router.get("/health")
async def get_error_monitoring_health():
    """Get error monitoring system health"""
    try:
        summary = error_handler.get_error_summary()
        
        # Determine health status based on error patterns
        health_status = "healthy"
        if summary["critical_errors"] > 0:
            health_status = "critical"
        elif summary["high_severity_errors"] > 10:
            health_status = "warning"
        elif summary["recent_errors"] > 50:
            health_status = "degraded"
        
        return {
            "status": "success",
            "data": {
                "health_status": health_status,
                "error_summary": summary,
                "monitoring_active": True
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "data": {
                "health_status": "unhealthy",
                "error": str(e),
                "monitoring_active": False
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/test-error")
async def test_error_handling(
    error_type: str = "test",
    severity: ErrorSeverity = ErrorSeverity.LOW,
    message: str = "Test error message"
):
    """Test error handling system (for development/testing)"""
    try:
        # Create a test error
        test_error = TradingSystemError(
            message=message,
            user_message=f"Test error: {message}",
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=ErrorContext(
                operation="test_error_handling",
                additional_data={"test": True, "error_type": error_type}
            )
        )
        
        # Handle the error
        error_info = error_handler.handle_error(test_error)
        
        return {
            "status": "success",
            "message": "Test error created and handled successfully",
            "error_id": error_info.error_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test error: {str(e)}")
