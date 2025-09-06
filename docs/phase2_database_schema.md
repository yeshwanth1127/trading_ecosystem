# Phase 2 Database Schema Documentation

## Overview

Phase 2 introduces a comprehensive database schema for real-time trading functionality, building upon the existing Phase 1 foundation. The schema is designed to handle high-frequency trading operations, margin trading, and complete audit trails.

## 🗄️ Database Tables

### 1. Account Ledger (NEW)
**Purpose**: Immutable journal for all financial transactions - audit trail

```sql
CREATE TABLE account_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    order_id UUID REFERENCES orders(order_id),
    trade_id UUID REFERENCES trades(trade_id),
    position_id UUID REFERENCES positions(position_id),
    entry_type VARCHAR(20) NOT NULL, -- DEPOSIT, WITHDRAWAL, PNL, FEE, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    amount NUMERIC(20,8) NOT NULL,
    balance_before NUMERIC(20,8) NOT NULL,
    balance_after NUMERIC(20,8) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    exchange_rate NUMERIC(15,8),
    description TEXT,
    reference_id VARCHAR(100),
    extra_data TEXT, -- JSON metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

**Key Features**:
- ✅ **Immutable**: Never updated, only new entries added
- ✅ **Complete Audit Trail**: Every financial transaction tracked
- ✅ **Multi-currency Support**: Exchange rates for conversions
- ✅ **Flexible Metadata**: JSON extra_data for additional context

### 2. Orders (ENHANCED)
**Purpose**: Order management with margin and leverage support

```sql
-- New columns added to existing orders table:
ALTER TABLE orders ADD COLUMN account_id UUID NOT NULL REFERENCES accounts(account_id);
ALTER TABLE orders ADD COLUMN time_in_force VARCHAR(10) NOT NULL DEFAULT 'gtc';
ALTER TABLE orders ADD COLUMN remaining_quantity NUMERIC(20,8) NOT NULL;
ALTER TABLE orders ADD COLUMN average_fill_price NUMERIC(20,8);
ALTER TABLE orders ADD COLUMN filled_amount NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN remaining_amount NUMERIC(20,8) NOT NULL;
ALTER TABLE orders ADD COLUMN commission_rate NUMERIC(8,6) NOT NULL DEFAULT 0.001;
ALTER TABLE orders ADD COLUMN leverage NUMERIC(8,2) NOT NULL DEFAULT 1.0;
ALTER TABLE orders ADD COLUMN margin_required NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN margin_used NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN is_margin_order BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN reduce_only BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN post_only BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN client_order_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN rejection_reason TEXT;
ALTER TABLE orders ADD COLUMN expired_at TIMESTAMP WITH TIME ZONE;
```

**Key Features**:
- ✅ **Margin Trading**: Full leverage and margin support
- ✅ **Order Types**: Market, Limit, Stop, Stop-Limit
- ✅ **Time in Force**: GTC, IOC, FOK, DAY
- ✅ **Partial Fills**: Track filled vs remaining quantities
- ✅ **Risk Management**: Reduce-only, post-only flags

### 3. Trades (ENHANCED)
**Purpose**: Individual trade executions (fills) - every fill = new row

```sql
-- Enhanced trades table with new columns:
ALTER TABLE trades ADD COLUMN order_id UUID REFERENCES orders(order_id);
ALTER TABLE trades ADD COLUMN trade_type VARCHAR(20) NOT NULL DEFAULT 'fill';
ALTER TABLE trades ADD COLUMN quantity NUMERIC(20,8) NOT NULL;
ALTER TABLE trades ADD COLUMN price NUMERIC(20,8) NOT NULL;
ALTER TABLE trades ADD COLUMN amount NUMERIC(20,8) NOT NULL;
ALTER TABLE trades ADD COLUMN commission NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE trades ADD COLUMN commission_rate NUMERIC(8,6) NOT NULL DEFAULT 0.001;
ALTER TABLE trades ADD COLUMN funding_fee NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE trades ADD COLUMN leverage NUMERIC(8,2) NOT NULL DEFAULT 1.0;
ALTER TABLE trades ADD COLUMN margin_used NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE trades ADD COLUMN realized_pnl NUMERIC(20,8);
ALTER TABLE trades ADD COLUMN unrealized_pnl NUMERIC(20,8);
ALTER TABLE trades ADD COLUMN is_maker BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE trades ADD COLUMN execution_id VARCHAR(100);
ALTER TABLE trades ADD COLUMN liquidity VARCHAR(20);
ALTER TABLE trades ADD COLUMN executed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE trades ADD COLUMN extra_data TEXT;
```

**Key Features**:
- ✅ **Fill Tracking**: Every execution creates a new row
- ✅ **PnL Calculation**: Realized and unrealized PnL tracking
- ✅ **Maker/Taker**: Liquidity provider identification
- ✅ **Funding Fees**: Support for perpetual contracts
- ✅ **Execution Details**: Exchange execution IDs

### 4. Positions (ENHANCED)
**Purpose**: Position management with proper status tracking

```sql
-- Enhanced positions table:
ALTER TABLE positions ADD COLUMN account_id UUID NOT NULL REFERENCES accounts(account_id);
ALTER TABLE positions ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open';
ALTER TABLE positions ADD COLUMN side VARCHAR(10) NOT NULL; -- 'long' or 'short'
ALTER TABLE positions ADD COLUMN quantity NUMERIC(20,8) NOT NULL;
ALTER TABLE positions ADD COLUMN average_entry_price NUMERIC(20,8) NOT NULL;
ALTER TABLE positions ADD COLUMN current_price NUMERIC(20,8) NOT NULL;
ALTER TABLE positions ADD COLUMN mark_price NUMERIC(20,8);
ALTER TABLE positions ADD COLUMN unrealized_pnl NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN realized_pnl NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN total_pnl NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN leverage NUMERIC(8,2) NOT NULL DEFAULT 1.0;
ALTER TABLE positions ADD COLUMN margin_used NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN margin_required NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN margin_ratio NUMERIC(8,4) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN liquidation_price NUMERIC(20,8);
ALTER TABLE positions ADD COLUMN stop_loss NUMERIC(20,8);
ALTER TABLE positions ADD COLUMN take_profit NUMERIC(20,8);
ALTER TABLE positions ADD COLUMN total_trades NUMERIC(10,0) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN total_volume NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN total_fees NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE positions ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
ALTER TABLE positions ADD COLUMN extra_data TEXT;
```

**Key Features**:
- ✅ **Status Management**: OPEN, CLOSED, LIQUIDATED
- ✅ **Risk Management**: Stop loss, take profit, liquidation price
- ✅ **Margin Tracking**: Real-time margin calculations
- ✅ **Statistics**: Trade count, volume, fees
- ✅ **Never Deleted**: Marked as CLOSED, not deleted

### 5. Accounts (ENHANCED)
**Purpose**: Comprehensive account management with risk controls

```sql
-- Enhanced accounts table:
ALTER TABLE accounts ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE accounts ADD COLUMN balance NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN equity NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN margin_used NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN margin_available NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN unrealized_pnl NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN realized_pnl NUMERIC(20,8) NOT NULL DEFAULT 0;
ALTER TABLE accounts ADD COLUMN max_leverage NUMERIC(8,2) NOT NULL DEFAULT 1.0;
ALTER TABLE accounts ADD COLUMN margin_call_threshold NUMERIC(8,4) NOT NULL DEFAULT 0.8;
ALTER TABLE accounts ADD COLUMN liquidation_threshold NUMERIC(8,4) NOT NULL DEFAULT 0.5;
ALTER TABLE accounts ADD COLUMN is_margin_enabled BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE accounts ADD COLUMN auto_liquidation BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE accounts ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
```

**Key Features**:
- ✅ **Real-time Balances**: Balance, equity, margin tracking
- ✅ **Risk Management**: Margin call and liquidation thresholds
- ✅ **Leverage Control**: Maximum leverage limits
- ✅ **Account Status**: Active, suspended, closed states

## 🔗 Relationships

### Entity Relationship Diagram
```
Users (1) ──→ (N) Accounts
Users (1) ──→ (N) Orders
Users (1) ──→ (N) Trades
Users (1) ──→ (N) Positions
Users (1) ──→ (N) AccountLedger

Accounts (1) ──→ (N) Orders
Accounts (1) ──→ (N) Trades
Accounts (1) ──→ (N) Positions
Accounts (1) ──→ (N) AccountLedger

Instruments (1) ──→ (N) Orders
Instruments (1) ──→ (N) Trades
Instruments (1) ──→ (N) Positions

Orders (1) ──→ (N) Trades
Orders (1) ──→ (N) AccountLedger

Trades (1) ──→ (N) AccountLedger
Positions (1) ──→ (N) AccountLedger
```

## 📊 Key Features

### 1. **Immutable Audit Trail**
- Every financial transaction recorded in `account_ledger`
- Complete balance history with before/after amounts
- Never updated, only new entries added

### 2. **Real-time Trading Support**
- High-precision decimal fields (NUMERIC(20,8))
- Comprehensive order management
- Fill-by-fill trade tracking

### 3. **Margin & Leverage Trading**
- Full margin calculation support
- Leverage up to 100x
- Risk management with liquidation prices

### 4. **Performance Optimized**
- Strategic indexes on frequently queried columns
- Composite indexes for complex queries
- Foreign key relationships for data integrity

### 5. **Multi-currency Support**
- Currency field in ledger entries
- Exchange rate tracking
- Flexible for international trading

## 🚀 Migration Status

✅ **Phase 2 Migration Completed Successfully**
- All new tables created
- Existing tables enhanced
- Relationships established
- Indexes optimized
- FastAPI server running

## 🔧 Usage Examples

### Creating a New Order
```python
order = Order(
    user_id=user_id,
    account_id=account_id,
    instrument_id=instrument_id,
    order_type=OrderType.LIMIT,
    side=OrderSide.BUY,
    quantity=Decimal('1.5'),
    price=Decimal('50000.00'),
    leverage=Decimal('10.0'),
    is_margin_order=True
)
```

### Recording a Trade Fill
```python
trade = Trade(
    order_id=order.order_id,
    user_id=user_id,
    account_id=account_id,
    instrument_id=instrument_id,
    side=TradeSide.BUY,
    quantity=Decimal('1.5'),
    price=Decimal('50000.00'),
    amount=Decimal('75000.00'),
    commission=Decimal('75.00'),
    leverage=Decimal('10.0')
)
```

### Updating Account Ledger
```python
ledger_entry = AccountLedger(
    user_id=user_id,
    account_id=account_id,
    order_id=order.order_id,
    entry_type=LedgerEntryType.FEE,
    amount=Decimal('-75.00'),
    balance_before=Decimal('10000.00'),
    balance_after=Decimal('9925.00'),
    description="Trading commission for BTC order"
)
```

## 🎯 Next Steps

The database schema is now ready for:
1. **Order Execution Engine** - Process orders in real-time
2. **Position Management** - Track and update positions
3. **Risk Management** - Monitor margin and liquidation
4. **Portfolio Analytics** - Calculate PnL and performance
5. **Audit & Compliance** - Complete transaction history

---

**Phase 2 Database Schema - Complete ✅**
