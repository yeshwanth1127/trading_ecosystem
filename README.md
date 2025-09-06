## Multi-User Freqtrade Orchestration (Simulated)

The backend now orchestrates one isolated Freqtrade dry-run instance per authenticated user.

### Layout

```
freqtrade-platform/
  freqtrade/                 # Freqtrade source (single copy)
  users/{user_id}/user_data/ # Per-user directories copied from template
  user_data_template/        # Template user_data (dry-run)
```

### How it works

- On registration: a per-user `user_data` dir is created from `user_data_template`.
- On challenge selection: we pre-provision a config with `dry_run_wallet` set to the challenge amount.
- On login: we start a Freqtrade process for the user with its unique port and credentials.
- Idle processes auto-stop after 30 minutes. Crashed processes are auto-restarted.

### FastAPI endpoints

- Auth: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout`
- Freqtrade proxy (JWT required):
  - `/api/v1/ft/start`, `/api/v1/ft/stop`, `/api/v1/ft/status`
  - `/api/v1/ft/overview` (balance/equity/unrealized pnl)
  - `/api/v1/ft/balance`, `/api/v1/ft/positions`, `/api/v1/ft/trades`
  - `/api/v1/ft/forcebuy`, `/api/v1/ft/forcesell`

### Security

- Per-user Freqtrade ports and HTTP Basic credentials are NOT exposed to the client.
- The backend proxies requests to the user’s Freqtrade instance.
- Pair whitelist is enforced from the user’s config; per-user rate limits protect endpoints.

### Operations

1. Copy or clone Freqtrade sources into `freqtrade-platform/freqtrade`.
2. Ensure `freqtrade-platform/user_data_template/` exists. Minimal config is generated automatically.
3. Run the FastAPI server; upon user login, instances start automatically.

### Watchdog / Process manager

- The orchestrator includes a lightweight crash-restart loop and idle shutdown timer.
- For production, consider running the API under a service manager (systemd, supervisor) and using external monitoring.

trading_ecosystem
