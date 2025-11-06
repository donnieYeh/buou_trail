# Repository Guidelines

## Project Structure & Module Organization
Root-level trading scripts (`chua_ok.py`, `chua_bn.py`, `chua_bitget.py`, `chua_ok_all.py`, `chua_ok_bot.py`) load exchange settings from `config.json` (copied from `config.template.json`) and drive the monitoring loop. The `okx/` package wraps OKX REST endpoints (`okx/client.py`, `okx/Trade_api.py`) and is reused by the OKX-facing scripts; shared helpers live in `okx/consts.py` and `okx/exceptions.py`. Logs rotate daily into `log/`, so create that directory before launching.

## Build, Test, and Development Commands
Create an isolated environment before installing dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Run an OKX session with the configured monitor interval (defaults to 4 s):
```bash
python3 chua_ok.py
```
Use the Binance or Bitget variants by invoking the corresponding script.

## Coding Style & Naming Conventions
Follow standard Python 3.9 conventions: 4-space indents, UTF-8 encoded source, and snake_case for variables, functions, and configuration keys (see `config.template.json`). Keep class names in PascalCase (`MultiAssetTradingBot`). Logging should use the module-level `logging` facility with contextual messages; reuse existing loggers and keep exchange-specific logic behind `okx.` imports.

## Testing Guidelines
Automated tests are not yet wired in; rely on staged dry runs. Before pushing, point `config.json` to demo accounts or minimal positions and watch the logs for one full position lifecycle. Verify blacklist handling by adding a test symbol (e.g., `"ETH-USDT-SWAP"`) and ensuring it is skipped. Capture terminal output and log excerpts when filing issues so reviewers can replay steps.

## Commit & Pull Request Guidelines
Recent history favors single-line summary commits (often short Mandarin phrases). Keep messages concise, imperative, and scoped to one behavior (e.g., `修复浮盈加仓`). For pull requests, describe the trading scenario you validated, note any configuration changes, and attach sanitized log snippets or exchange screenshots. Call out required updates to `config.template.json` or environment prerequisites so operators can redeploy confidently.

## Security & Configuration Tips
Never commit real API keys; only store production secrets in `config.json`, which stays untracked. Reset credentials immediately if printed to logs. When sharing diagnostics, redact the `feishu_webhook` and account identifiers, and rotate keys after third-party reviews.
