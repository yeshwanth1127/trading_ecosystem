import asyncio
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiohttp


@dataclass
class InstanceRecord:
    user_id: str
    port: int
    username: str
    password: str
    jwt_secret_key: str
    started_at: float
    last_active_at: float
    pid: Optional[int] = None


class FreqtradeOrchestrator:
    """Manages per-user Freqtrade processes, configs, and proxying.

    Rules:
    - One process per active user
    - Start on login (or explicit start)
    - Stop on logout or inactivity timeout
    - Persist instance metadata for crash recovery
    """

    def __init__(self) -> None:
        self._root_dir: Path = Path(__file__).resolve().parents[1]
        self._platform_dir: Path = self._root_dir / "freqtrade-platform"
        self._freqtrade_pkg_dir: Path = self._platform_dir / "freqtrade" / "build" / "lib"
        self._users_dir: Path = self._platform_dir / "users"
        self._template_dir: Path = self._platform_dir / "user_data_template"
        self._registry_path: Path = self._platform_dir / "instances_registry.json"
        self._processes: Dict[str, Tuple[InstanceRecord, subprocess.Popen]] = {}
        self._idle_timeout: timedelta = timedelta(minutes=30)
        self._monitor_task: Optional[asyncio.Task] = None
        self._port_base: int = 18880
        self._port_max: int = 19999

        # Ensure base directories exist
        self._platform_dir.mkdir(parents=True, exist_ok=True)
        self._users_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------
    def _load_registry(self) -> Dict[str, InstanceRecord]:
        if not self._registry_path.exists():
            return {}
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            records: Dict[str, InstanceRecord] = {}
            for user_id, rec in data.items():
                records[user_id] = InstanceRecord(**rec)
            return records
        except Exception:
            return {}

    def _save_registry(self) -> None:
        try:
            serializable: Dict[str, Any] = {
                user_id: asdict(record)
                for user_id, (record, _proc) in self._processes.items()
            }
            self._registry_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        except Exception:
            # Avoid raising on save errors in hot paths
            pass

    # ---------------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------------
    def _user_dir(self, user_id: str) -> Path:
        return self._users_dir / user_id / "user_data"

    def _config_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "config.json"

    def _is_port_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    def _allocate_port(self) -> int:
        for port in range(self._port_base, self._port_max + 1):
            if self._is_port_free(port):
                return port
        raise RuntimeError("No free ports available in configured range")

    def _ensure_template(self) -> None:
        """Ensure template dir exists with a minimal dry-run config and no strategy files."""
        self._template_dir.mkdir(parents=True, exist_ok=True)
        config = {
            "max_open_trades": 3,
            "stake_currency": "USDT",
            "stake_amount": "unlimited",
            "dry_run": True,
            "dry_run_wallet": 1000,
            "force_entry_enable": True,
            "timeframe": "5m",
            "api_server": {
                "enabled": True,
                "listen_ip": "127.0.0.1",
                "port": 0,
                "username": "",
                "password": "",
                "jwt_secret_key": "",
                "enable_openapi": False,
            },
            "exchange": {
                "name": "binance",
                "key": "",
                "secret": "",
                "ccxt_config": {},
                "ccxt_async_config": {},
                "pair_whitelist": ["BTC/USDT", "ETH/USDT"],
                "pair_blacklist": [],
            },
            "pairlists": [{"method": "StaticPairList"}],
        }
        cfg_path = self._template_dir / "config.json"
        if not cfg_path.exists():
            cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def ensure_user_userdir(self, user_id: str) -> Path:
        """Create `/users/{user_id}/user_data/` by copying the template if missing."""
        self._ensure_template()
        target = self._user_dir(user_id)
        if target.exists():
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self._template_dir, target)
        return target

    def _write_user_config(
        self,
        user_id: str,
        port: int,
        username: str,
        password: str,
        jwt_secret_key: str,
        dry_run_wallet: float,
        pair_whitelist: Optional[list[str]] = None,
    ) -> None:
        cfg_path = self._config_path(user_id)
        config: Dict[str, Any]
        if cfg_path.exists():
            try:
                config = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}
        else:
            config = {}

        # Minimal required fields
        config.setdefault("max_open_trades", 3)
        config.setdefault("stake_currency", "USDT")
        config.setdefault("stake_amount", "unlimited")
        config["dry_run"] = True
        config["dry_run_wallet"] = float(dry_run_wallet)
        config.setdefault("force_entry_enable", True)
        config.setdefault("timeframe", "5m")
        # Ensure strategy path exists in user_data
        strategies_dir = self._user_dir(user_id) if user_id else self._template_dir
        (strategies_dir / "strategies").mkdir(parents=True, exist_ok=True)

        api_server = config.get("api_server", {})
        api_server.update(
            {
                "enabled": True,
                "listen_ip": "127.0.0.1",
                "port": port,
                "username": username,
                "password": password,
                "jwt_secret_key": jwt_secret_key,
                "enable_openapi": False,
            }
        )
        config["api_server"] = api_server

        exchange = config.get("exchange", {})
        exchange.setdefault("name", "binance")
        exchange.setdefault("key", "")
        exchange.setdefault("secret", "")
        exchange.setdefault("ccxt_config", {})
        exchange.setdefault("ccxt_async_config", {})
        if pair_whitelist:
            exchange["pair_whitelist"] = pair_whitelist
        else:
            exchange.setdefault("pair_whitelist", ["BTC/USDT", "ETH/USDT"])  # default whitelist
        exchange.setdefault("pair_blacklist", [])
        config["exchange"] = exchange

        cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def provision_user_config(self, user_id: str, dry_run_wallet: float) -> None:
        """Generate a unique config with assigned port and credentials for the user without launching."""
        self.ensure_user_userdir(user_id)
        cfg_path = self._config_path(user_id)
        existing = {}
        if cfg_path.exists():
            try:
                existing = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        api_cfg = existing.get("api_server", {})
        port = api_cfg.get("port") or self._allocate_port()
        username = api_cfg.get("username") or user_id
        password = api_cfg.get("password") or base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
        jwt_secret = api_cfg.get("jwt_secret_key") or base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")
        self._write_user_config(
            user_id=user_id,
            port=port,
            username=username,
            password=password,
            jwt_secret_key=jwt_secret,
            dry_run_wallet=dry_run_wallet,
        )

    # ---------------------------------------------------------------------
    # Process control
    # ---------------------------------------------------------------------
    def _python_env_with_freqtrade(self) -> Dict[str, str]:
        env = os.environ.copy()
        # Ensure Freqtrade package is importable
        libdir = str(self._freqtrade_pkg_dir)
        if os.path.isdir(libdir):
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = libdir + (os.pathsep + existing if existing else "")
        return env

    def start_instance(self, user_id: str, dry_run_wallet: float) -> InstanceRecord:
        """Start Freqtrade for given user if not already running."""
        # If already running, update last_active and return
        if user_id in self._processes:
            record, proc = self._processes[user_id]
            record.last_active_at = time.time()
            self._save_registry()
            return record

        # Prepare directories and config
        self.ensure_user_userdir(user_id)
        # Reuse pre-provisioned config if present
        port = None
        username = user_id
        password = None
        jwt_secret = None
        cfg_path = self._config_path(user_id)
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                api_cfg = cfg.get("api_server", {})
                port = api_cfg.get("port")
                username = api_cfg.get("username") or user_id
                password = api_cfg.get("password")
                jwt_secret = api_cfg.get("jwt_secret_key")
            except Exception:
                pass
        if port is None or not self._is_port_free(int(port)):
            port = self._allocate_port()
        if not password:
            password = base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
        if not jwt_secret:
            jwt_secret = base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")
        self._write_user_config(
            user_id=user_id,
            port=int(port),
            username=username,
            password=password,
            jwt_secret_key=jwt_secret,
            dry_run_wallet=dry_run_wallet,
        )

        config_path = str(self._config_path(user_id))

        # Launch Freqtrade
        cmd = [
            sys.executable,
            "-m",
            "freqtrade",
            "trade",
            "--config",
            config_path,
            "--strategy",
            "SampleStrategy",
            "--dry-run",
            "--api-server",
            "--api-server-port",
            str(port),
            "--api-server-username",
            username,
            "--api-server-password",
            password,
        ]

        env = self._python_env_with_freqtrade()
        proc = subprocess.Popen(
            cmd,
            cwd=str(self._root_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        record = InstanceRecord(
            user_id=user_id,
            port=port,
            username=username,
            password=password,
            jwt_secret_key=jwt_secret,
            started_at=time.time(),
            last_active_at=time.time(),
            pid=proc.pid,
        )
        self._processes[user_id] = (record, proc)
        self._save_registry()
        return record

    def stop_instance(self, user_id: str) -> bool:
        if user_id not in self._processes:
            return False
        record, proc = self._processes.pop(user_id)
        try:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        finally:
            self._save_registry()
        return True

    def get_instance(self, user_id: str) -> Optional[InstanceRecord]:
        if user_id in self._processes:
            return self._processes[user_id][0]
        # Attempt to reattach to existing PID from registry (if running)
        saved = self._load_registry()
        if user_id in saved:
            rec = saved[user_id]
            if rec.pid and self._pid_is_running(rec.pid):
                # Create a pseudo Popen handle (cannot reattach cleanly) -> restart instead
                # Safer path: restart the instance to rehydrate process handle
                return self.start_instance(user_id, dry_run_wallet=self._read_user_dry_run_wallet(user_id))
        return None

    def _pid_is_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _read_user_dry_run_wallet(self, user_id: str) -> float:
        try:
            cfg = json.loads(self._config_path(user_id).read_text(encoding="utf-8"))
            return float(cfg.get("dry_run_wallet", 1000))
        except Exception:
            return 1000.0

    # ---------------------------------------------------------------------
    # Idle monitor
    # ---------------------------------------------------------------------
    async def _idle_monitor(self) -> None:
        while True:
            now = time.time()
            for user_id in list(self._processes.keys()):
                record, proc = self._processes.get(user_id, (None, None))  # type: ignore
                if not record:
                    continue
                # Restart crashed instances
                if proc.poll() is not None:  # type: ignore[attr-defined]
                    try:
                        self.start_instance(user_id, dry_run_wallet=self._read_user_dry_run_wallet(user_id))
                        continue
                    except Exception:
                        # If restart fails, drop from registry
                        try:
                            self._processes.pop(user_id, None)
                        except Exception:
                            pass
                        continue
                idle_secs = now - record.last_active_at
                if idle_secs > self._idle_timeout.total_seconds():
                    try:
                        self.stop_instance(user_id)
                    except Exception:
                        pass
            await asyncio.sleep(60)

    def start_idle_monitor(self) -> None:
        if self._monitor_task is None or self._monitor_task.done():
            loop = asyncio.get_event_loop()
            self._monitor_task = loop.create_task(self._idle_monitor())

    # ---------------------------------------------------------------------
    # Proxy helpers
    # ---------------------------------------------------------------------
    async def _request(
        self,
        user_id: str,
        method: str,
        path: str,
        json_payload: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
    ) -> Tuple[int, Dict[str, Any]]:
        record = self.get_instance(user_id)
        if not record:
            raise RuntimeError("Freqtrade instance is not running for this user")

        auth = aiohttp.BasicAuth(login=record.username, password=record.password)
        url = f"http://127.0.0.1:{record.port}/api/v1{path}"
        record.last_active_at = time.time()
        self._save_registry()
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.request(method.upper(), url, json=json_payload, timeout=timeout) as resp:
                status = resp.status
                try:
                    data = await resp.json()
                except Exception:
                    text = await resp.text()
                    data = {"detail": text}
                return status, data


# Global orchestrator singleton
orchestrator = FreqtradeOrchestrator()


