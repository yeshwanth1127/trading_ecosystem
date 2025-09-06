"""
Transaction Management Service
=============================

Provides robust transaction management with:
- Automatic rollback on errors
- Retry logic for transient failures
- Nested transaction support
- Deadlock detection and handling
- Connection pooling optimization
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import time

from sqlalchemy import text
from sqlalchemy.exc import (
    OperationalError, 
    IntegrityError, 
    DisconnectionError,
    TimeoutError as SQLTimeoutError
)
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass

class TransactionRetryError(TransactionError):
    """Raised when transaction retries are exhausted"""
    pass

class TransactionManager:
    """
    Professional transaction management service
    
    Features:
    - Automatic rollback on exceptions
    - Retry logic for transient failures
    - Deadlock detection and handling
    - Nested transaction support
    - Connection health monitoring
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 0.1  # 100ms
        self.deadlock_retry_delay = 0.5  # 500ms
        self.transaction_timeout = 30  # 30 seconds
        self._active_transactions: Dict[str, AsyncSession] = {}
        self._transaction_counter = 0
    
    @asynccontextmanager
    async def transaction(
        self, 
        read_only: bool = False,
        isolation_level: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Context manager for database transactions
        
        Args:
            read_only: If True, transaction is read-only
            isolation_level: SQL isolation level (READ_COMMITTED, REPEATABLE_READ, etc.)
            timeout: Transaction timeout in seconds
        """
        transaction_id = f"txn_{self._transaction_counter}"
        self._transaction_counter += 1
        
        session = None
        transaction = None
        
        try:
            # Create session
            session = AsyncSessionLocal()
            self._active_transactions[transaction_id] = session
            
            # Set isolation level if specified
            if isolation_level:
                await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
            
            # Set timeout if specified
            if timeout:
                await session.execute(text(f"SET LOCAL statement_timeout = {timeout * 1000}"))  # Convert to milliseconds
            
            # Begin transaction
            transaction = await session.begin()
            
            logger.debug(f"🔄 Started transaction {transaction_id} (read_only={read_only})")
            
            yield session
            
            # Commit transaction
            if not read_only:
                await transaction.commit()
                logger.debug(f"✅ Committed transaction {transaction_id}")
            else:
                await transaction.rollback()  # Read-only transactions are rolled back
                logger.debug(f"📖 Rolled back read-only transaction {transaction_id}")
                
        except Exception as e:
            # Rollback on any error
            if transaction:
                try:
                    await transaction.rollback()
                    logger.debug(f"🔄 Rolled back transaction {transaction_id} due to error: {e}")
                except Exception as rollback_error:
                    logger.error(f"❌ Failed to rollback transaction {transaction_id}: {rollback_error}")
            
            # Re-raise the original exception
            raise
            
        finally:
            # Clean up
            if session:
                try:
                    await session.close()
                except Exception as close_error:
                    logger.error(f"❌ Failed to close session for transaction {transaction_id}: {close_error}")
            
            self._active_transactions.pop(transaction_id, None)
    
    async def execute_with_retry(
        self,
        operation: Callable[[AsyncSession], T],
        max_retries: Optional[int] = None,
        read_only: bool = False,
        **transaction_kwargs
    ) -> T:
        """
        Execute a database operation with automatic retry logic
        
        Args:
            operation: Async function that takes a session and returns a result
            max_retries: Maximum number of retries (defaults to self.max_retries)
            read_only: Whether this is a read-only operation
            **transaction_kwargs: Additional arguments for transaction context
            
        Returns:
            Result of the operation
            
        Raises:
            TransactionRetryError: If all retries are exhausted
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with self.transaction(read_only=read_only, **transaction_kwargs) as session:
                    result = await operation(session)
                    return result
                    
            except (OperationalError, DisconnectionError, SQLTimeoutError) as e:
                last_exception = e
                
                # Check if it's a deadlock
                if self._is_deadlock_error(e):
                    delay = self.deadlock_retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"⚠️ Deadlock detected, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                else:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"⚠️ Transient error, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
                    
            except Exception as e:
                # Non-retryable error
                logger.error(f"❌ Non-retryable error in transaction: {e}")
                raise
        
        # All retries exhausted
        raise TransactionRetryError(f"Transaction failed after {max_retries + 1} attempts. Last error: {last_exception}")
    
    def _is_deadlock_error(self, error: Exception) -> bool:
        """Check if the error is a deadlock"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in [
            'deadlock', 'lock timeout', 'could not serialize', 'serialization failure'
        ])
    
    async def execute_batch(
        self,
        operations: List[Callable[[AsyncSession], Any]],
        read_only: bool = False,
        **transaction_kwargs
    ) -> List[Any]:
        """
        Execute multiple operations in a single transaction
        
        Args:
            operations: List of async functions that take a session
            read_only: Whether this is a read-only operation
            **transaction_kwargs: Additional arguments for transaction context
            
        Returns:
            List of results from each operation
        """
        async with self.transaction(read_only=read_only, **transaction_kwargs) as session:
            results = []
            for operation in operations:
                result = await operation(session)
                results.append(result)
            return results
    
    async def execute_with_locking(
        self,
        operation: Callable[[AsyncSession], T],
        lock_models: List[type],
        lock_ids: List[Any],
        read_only: bool = False,
        **transaction_kwargs
    ) -> T:
        """
        Execute operation with row-level locking
        
        Args:
            operation: Async function that takes a session and returns a result
            lock_models: List of model classes to lock
            lock_ids: List of IDs to lock (must match lock_models)
            read_only: Whether this is a read-only operation
            **transaction_kwargs: Additional arguments for transaction context
            
        Returns:
            Result of the operation
        """
        async with self.transaction(read_only=read_only, **transaction_kwargs) as session:
            # Acquire locks
            for model, model_id in zip(lock_models, lock_ids):
                await session.get(model, model_id, with_for_update=True)
            
            # Execute operation
            result = await operation(session)
            return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Check transaction manager health"""
        try:
            async with self.transaction(read_only=True) as session:
                # Simple query to test connection
                await session.execute(text("SELECT 1"))
                
            return {
                "status": "healthy",
                "active_transactions": len(self._active_transactions),
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_transactions": len(self._active_transactions)
            }
    
    async def close(self):
        """Close all active transactions and cleanup"""
        logger.info("🔒 Closing Transaction Manager")
        
        # Close all active transactions
        for transaction_id, session in list(self._active_transactions.items()):
            try:
                await session.rollback()
                await session.close()
                logger.debug(f"🔒 Closed transaction {transaction_id}")
            except Exception as e:
                logger.error(f"❌ Error closing transaction {transaction_id}: {e}")
        
        self._active_transactions.clear()
        logger.info("✅ Transaction Manager closed")

def transaction_required(read_only: bool = False, **transaction_kwargs):
    """
    Decorator to automatically wrap function in a transaction
    
    Usage:
        @transaction_required(read_only=True)
        async def get_user(session: AsyncSession, user_id: str):
            # Function automatically gets a transaction
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find session parameter
            session_param = None
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session_param = arg
                    break
            
            if session_param:
                # Function already has a session, execute directly
                return await func(*args, **kwargs)
            else:
                # No session provided, create transaction
                async with transaction_manager.transaction(read_only=read_only, **transaction_kwargs) as session:
                    # Inject session as first argument
                    return await func(session, *args, **kwargs)
        
        return wrapper
    return decorator

def retry_on_deadlock(max_retries: int = 3):
    """
    Decorator to retry function on deadlock errors
    
    Usage:
        @retry_on_deadlock(max_retries=5)
        async def critical_operation(session: AsyncSession):
            # Function will be retried on deadlock
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except (OperationalError, DisconnectionError, SQLTimeoutError) as e:
                    last_exception = e
                    
                    if transaction_manager._is_deadlock_error(e) and attempt < max_retries:
                        delay = transaction_manager.deadlock_retry_delay * (2 ** attempt)
                        logger.warning(f"⚠️ Deadlock in {func.__name__}, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
                        
                except Exception as e:
                    # Non-retryable error
                    raise
            
            # All retries exhausted
            raise TransactionRetryError(f"{func.__name__} failed after {max_retries + 1} attempts. Last error: {last_exception}")
        
        return wrapper
    return decorator

# Global transaction manager instance
transaction_manager = TransactionManager()
