from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict
import importlib
import asyncio

from app.api.deps import get_db
from app.core.security import verify_token
from app.crud import challenge_selection
from app.services.trading_challenge_service import TradingChallengeService
from app.orchestrator import orchestrator

router = APIRouter()
security = HTTPBearer()
_rate_limits: dict[str, list[float]] = {}
_user_locks: dict[str, asyncio.Lock] = {}


def _rate_limiter(user_id: str, max_calls: int = 10, per_seconds: int = 60) -> None:
    import time as _time
    now = _time.time()
    window_start = now - per_seconds
    calls = _rate_limits.get(user_id, [])
    # Drop old calls
    calls = [t for t in calls if t >= window_start]
    if len(calls) >= max_calls:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    calls.append(now)
    _rate_limits[user_id] = calls


async def _get_user_id(credentials: HTTPAuthorizationCredentials) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id


@router.get("/status")
async def status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = await _get_user_id(credentials)
    rec = orchestrator.get_instance(user_id)
    return {"running": rec is not None}


@router.post("/start")
async def start_instance(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(credentials)
    _rate_limiter(user_id, max_calls=5, per_seconds=60)
    lock = _user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        # Determine initial balance from active challenge selection, or fallback to existing config
        active = await challenge_selection.get_active_by_user_id(db, user_id=user_id)
        if active:
            initial_balance = TradingChallengeService.parse_amount(active.amount)
            if initial_balance <= 0:
                initial_balance = orchestrator._read_user_dry_run_wallet(user_id)
        else:
            initial_balance = orchestrator._read_user_dry_run_wallet(user_id)
        orchestrator.start_instance(user_id, dry_run_wallet=initial_balance)
        return {"started": True}


@router.post("/stop")
async def stop_instance(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = await _get_user_id(credentials)
    _rate_limiter(user_id, max_calls=5, per_seconds=60)
    lock = _user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        stopped = orchestrator.stop_instance(user_id)
        return {"stopped": stopped}


@router.get("/balance")
async def balance(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    status_code, data = await orchestrator._request(user_id, "GET", "/balance")
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=data)
    # Sanitize
    return {
        "total": data.get("total", {}),
        "available": data.get("available", {}),
        "currency": data.get("currency"),
    }


@router.get("/overview")
async def overview(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    sc_b, balance = await orchestrator._request(user_id, "GET", "/balance")
    if sc_b >= 400:
        raise HTTPException(status_code=sc_b, detail=balance)
    sc_s, status_data = await orchestrator._request(user_id, "GET", "/status")
    if sc_s >= 400:
        raise HTTPException(status_code=sc_s, detail=status_data)
    # Compute simple unrealized PnL from open trades
    unrealized = 0.0
    try:
        for tr in status_data or []:
            # profit_abs may be None
            pnl = tr.get("profit_abs")
            if pnl is not None:
                unrealized += float(pnl)
    except Exception:
        pass
    # Pick primary currency
    currency = balance.get("currency") or "USDT"
    available_map = balance.get("available", {}) or {}
    total_map = balance.get("total", {}) or {}
    # Extract numeric balances
    def _first_num(dct: Dict[str, Any]) -> float:
        for v in dct.values():
            try:
                return float(v)
            except Exception:
                continue
        return 0.0
    available_balance = _first_num(available_map)
    total_equity = _first_num(total_map)
    if total_equity == 0.0:
        total_equity = available_balance + unrealized
    return {
        "available_balance": available_balance,
        "equity": total_equity,
        "total_equity": total_equity,
        "unrealized_pnl": unrealized,
        "currency": currency,
    }


@router.get("/trades")
async def trades(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    status_code, data = await orchestrator._request(user_id, "GET", "/trades")
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=data)
    # Map to a simplified order/trade model for frontend
    mapped: list[Dict[str, Any]] = []
    for t in data or []:
        side = "buy" if (t.get("profit_abs", 0) is not None) else "buy"
        qty = float(t.get("amount", 0) or 0)
        entry = float(t.get("open_rate", 0) or 0)
        exit_r = float(t.get("close_rate", 0) or 0) if t.get("close_rate") is not None else None
        total_amt = qty * (entry if entry else 0)
        mapped.append({
            "order_id": str(t.get("trade_id")),
            "user_id": user_id,
            "instrument_id": t.get("pair"),
            "order_type": "market",
            "side": side,
            "quantity": qty,
            "filled_quantity": qty if (t.get("is_open") is False) else 0.0,
            "price": entry,
            "stop_price": None,
            "total_amount": total_amt,
            "commission": float(t.get("fee_abs", 0) or 0),
            "notes": (f"exit:{exit_r}" if exit_r is not None else None),
            "created_at": t.get("open_date"),
            "updated_at": t.get("close_date") or t.get("open_date"),
            "filled_at": t.get("close_date"),
            "cancelled_at": None,
        })
    return {"trades": mapped}


@router.get("/positions")
async def positions(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    status_code, data = await orchestrator._request(user_id, "GET", "/status")
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=data)
    # Map Freqtrade open trades to frontend position model
    positions = []
    for t in data or []:
        pos = {
            "position_id": str(t.get("trade_id")),
            "user_id": user_id,
            "instrument_id": t.get("pair"),
            "instrument_symbol": t.get("pair"),
            "side": "long",
            "status": "open",
            "quantity": float(t.get("amount", 0) or 0),
            "average_entry_price": float(t.get("open_rate", 0) or 0),
            "current_price": float(t.get("current_rate", 0) or 0),
            "unrealized_pnl": float(t.get("profit_abs", 0) or 0),
            "realized_pnl": None,
            "margin_used": None,
            "leverage": None,
            "opened_at": t.get("open_date"),
            "closed_at": None,
            "last_updated": t.get("open_date"),
        }
        positions.append(pos)
    return {"positions": positions}


@router.post("/forcebuy")
async def forcebuy(
    payload: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = await _get_user_id(credentials)
    _rate_limiter(user_id)
    lock = _user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
    # Validate payload (symbol, price, amount)
        pair = payload.get("pair")
        if not pair or not isinstance(pair, str):
            raise HTTPException(status_code=400, detail="pair is required")
        # Whitelist enforcement
        try:
            cfg_path = orchestrator._config_path(user_id)
            import json as _json
            cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
            allowed = set((cfg.get("exchange", {}).get("pair_whitelist", [])))
            if allowed and pair not in allowed:
                raise HTTPException(status_code=400, detail="Pair not whitelisted")
        except HTTPException:
            raise
        except Exception:
            pass
        amount = payload.get("amount")
        status_code, data = await orchestrator._request(user_id, "POST", "/forcebuy", json_payload={"pair": pair, "amount": amount})
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=data)
        return data


@router.post("/forcesell")
async def forcesell(
    payload: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = await _get_user_id(credentials)
    _rate_limiter(user_id)
    lock = _user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        trade_id = payload.get("tradeid") or payload.get("trade_id")
        if not trade_id:
            raise HTTPException(status_code=400, detail="tradeid is required")
        status_code, data = await orchestrator._request(user_id, "POST", "/forcesell", json_payload={"tradeid": trade_id})
        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=data)
        return data


@router.get("/profit")
async def profit(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    status_code, data = await orchestrator._request(user_id, "GET", "/profit")
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=data)
    return {"profit": data}


@router.get("/profit_all")
async def profit_all(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    user_id = await _get_user_id(credentials)
    status_code, data = await orchestrator._request(user_id, "GET", "/profit_all")
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=data)
    return {"profit_all": data}

@router.post("/sync-whitelist")
async def sync_whitelist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Fetch all Binance USDT futures pairs and write them to the user's whitelist."""
    user_id = await _get_user_id(credentials)
    _rate_limiter(user_id, max_calls=2, per_seconds=60)
    lock = _user_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        # Ensure ccxt is available
        try:
            ccxt = importlib.import_module("ccxt")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ccxt not available: {e}")
        try:
            ex = ccxt.binance({"options": {"defaultType": "future"}})
            markets = ex.load_markets()
            usdt_pairs: list[str] = []
            for symbol, m in markets.items():
                try:
                    if (
                        isinstance(symbol, str)
                        and symbol.endswith("/USDT")
                        and m.get("contract") is True
                        and (m.get("linear") is True or m.get("settle") == "USDT")
                        and m.get("type") in ("future", "swap")
                        and m.get("active", True)
                    ):
                        usdt_pairs.append(symbol)
                except Exception:
                    continue
            usdt_pairs = sorted(list(set(usdt_pairs)))
            if not usdt_pairs:
                raise HTTPException(status_code=502, detail="No USDT pairs found from Binance")
            orchestrator.update_user_pair_whitelist(user_id, usdt_pairs)
            return {"updated": True, "count": len(usdt_pairs)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Whitelist sync failed: {e}")

