"""
Account Balance API Endpoints
============================

Real-time account balance and P&L endpoints for the trading system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
import logging
from uuid import UUID

from app.api.deps import get_current_user
from app.models.user import User
from app.services.account_balance_service import account_balance_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/balance", response_model=Dict[str, Any])
async def get_account_balance(
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time account balance and P&L for the current user
    
    Returns:
    - balance: Available balance
    - equity: Total equity (balance + realized_pnl + unrealized_pnl)
    - realized_pnl: Realized profit/loss from closed positions
    - unrealized_pnl: Unrealized profit/loss from open positions
    - margin_used: Total margin used by open positions
    - free_margin: Available margin for new positions
    - margin_ratio: Margin usage ratio
    """
    try:
        balance_data = await account_balance_service.get_user_balance(str(current_user.user_id))
        
        if not balance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account balance not found"
            )
        
        return {
            "success": True,
            "data": balance_data,
            "message": "Account balance retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get account balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account balance"
        )

@router.get("/balance/{account_id}", response_model=Dict[str, Any])
async def get_specific_account_balance(
    account_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time account balance for a specific account
    
    Args:
        account_id: The account ID to get balance for
    """
    try:
        balance_data = await account_balance_service.get_account_balance(str(account_id))
        
        if not balance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account balance not found"
            )
        
        # Verify the account belongs to the current user
        if balance_data['user_id'] != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account"
            )
        
        return {
            "success": True,
            "data": balance_data,
            "message": "Account balance retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get account balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account balance"
        )

@router.get("/balance/summary", response_model=Dict[str, Any])
async def get_balance_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of account balance with key metrics
    
    Returns a simplified view of account balance for UI display
    """
    try:
        balance_data = await account_balance_service.get_user_balance(str(current_user.user_id))
        
        if not balance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account balance not found"
            )
        
        # Calculate additional metrics
        total_pnl = balance_data['realized_pnl'] + balance_data['unrealized_pnl']
        pnl_percentage = (total_pnl / balance_data['balance'] * 100) if balance_data['balance'] > 0 else 0
        
        summary = {
            "account_id": balance_data['account_id'],
            "balance": balance_data['balance'],
            "equity": balance_data['equity'],
            "total_pnl": total_pnl,
            "pnl_percentage": round(pnl_percentage, 2),
            "unrealized_pnl": balance_data['unrealized_pnl'],
            "realized_pnl": balance_data['realized_pnl'],
            "margin_used": balance_data['margin_used'],
            "free_margin": balance_data['free_margin'],
            "margin_ratio": balance_data['margin_ratio'],
            "last_updated": balance_data['last_updated']
        }
        
        return {
            "success": True,
            "data": summary,
            "message": "Balance summary retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get balance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance summary"
        )

@router.get("/balance/status", response_model=Dict[str, Any])
async def get_balance_service_status():
    """
    Get the status of the account balance service
    
    Returns whether the service is running and connected to Redis
    """
    try:
        status_data = {
            "service_running": account_balance_service.is_running,
            "redis_connected": account_balance_service.redis_client is not None,
            "update_task_running": account_balance_service.update_task is not None and not account_balance_service.update_task.done()
        }
        
        return {
            "success": True,
            "data": status_data,
            "message": "Balance service status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get balance service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service status"
        )
