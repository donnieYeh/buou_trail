# Repository Guidelines

## Project Structure & Module Organization
Root-level automation now centers on `chua_ok_all.py`, which loads OKX settings from `config.json` (copied from `config.template.json`) and orchestrates the full-position monitor. Shared risk helpers live in `risk_utils.py`, while the `okx/` package wraps REST endpoints (`okx/client.py`, `okx/Trade_api.py`) reused across the strategy. Logs rotate daily into `log/`, so create that directory before launching.

## Build, Test, and Development Commands
Create an isolated environment before installing dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Run the full-position OKX monitor (defaults to a 4 s loop):
```bash
python3 chua_ok_all.py
```
ATR-based stops refresh automatically on 15-minute boundaries; inspect `log/okx_all.log` to confirm distance-to-stop messages.

## Coding Style & Naming Conventions
Follow standard Python 3.9 conventions: 4-space indents, UTF-8 encoded source, and snake_case for variables, functions, and configuration keys (see `config.template.json`). Keep class names in PascalCase (`MultiAssetTradingBot`). Logging should use the module-level `logging` facility with contextual messages; reuse existing loggers and keep ATR/stop computations funneled through `StopLossEvaluator`.

## Testing Guidelines
Automated tests are not yet wired in; rely on staged dry runs. Before pushing, point `config.json` to demo accounts or minimal positions and watch the logs for at least one full position lifecycle. Confirm that the 15-minute ATR refresh logs appear and that each loop prints a stop-distance line for active symbols. Capture terminal output and log excerpts when filing issues so reviewers can replay steps.

## Commit & Pull Request Guidelines
Recent history favors single-line summary commits (often short Mandarin phrases). Keep messages concise, imperative, and scoped to one behavior (e.g., `修复浮盈加仓`). For pull requests, describe the trading scenario you validated, note any configuration changes, and attach sanitized log snippets or exchange screenshots. Call out required updates to `config.template.json` or environment prerequisites so operators can redeploy confidently.

## Security & Configuration Tips
Never commit real API keys; only store production secrets in `config.json`, which stays untracked. Reset credentials immediately if printed to logs. When sharing diagnostics, redact the `feishu_webhook` and account identifiers, and rotate keys after third-party reviews.
