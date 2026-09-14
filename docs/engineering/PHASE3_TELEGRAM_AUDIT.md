# Phase 3 — Telegram Surface Audit

## Audit status

Phase 3 is **IN PROGRESS**.

The audit is intentionally broader than individual handlers: Telegram authorization, commands, callbacks, user settings, market-status gating, scanner rendering, live signal generation, tracker rendering, and journal rendering are treated as one user-facing contract.

## TASK-090 — Telegram Surface Contract Hardening

### Repository-backed gaps found

1. **Callback trust boundary**
   - Settings callbacks were parsed by string prefixes and arbitrary payloads could reach `_apply_setting()`.
   - This allowed callback data that was not emitted by the canonical keyboards to mutate user state.

2. **Settings truthfulness**
   - `/settings` returned hard-coded values rather than the authenticated user's actual state.
   - This made the Telegram UI disagree with the state consumed by `/signal` and callbacks.

3. **Live-signal market-state gate**
   - `/signal` fetched candles and proceeded directly to market-aware analysis.
   - The canonical `OPEN/CLOSED/STALE/NO_DATA` contract was enforced by the scanner but not by the direct Telegram signal path.
   - A direct signal request therefore lacked the same fail-closed market gate as the scanner.

4. **Executable signal coverage**
   - The tracker already recognizes BUY, SELL, STRONG_BUY, and STRONG_SELL, while the live signal handler only registered BUY/SELL.
   - The Telegram surface was therefore narrower than the tracker contract.

5. **Dynamic HTML output**
   - Scanner output and tracked-signal output contained dynamic values without a uniform escaping boundary.
   - Journal rendering also interpolated persisted symbol/side/result values directly into HTML.

6. **Status readiness accuracy**
   - `/status` always reported the application as fully running without exposing whether any market-data provider was actually configured.

### Implemented corrections

- Added a canonical callback allowlist and fail-closed handling for unknown callback payloads.
- Restricted setting mutation to the exact supported market, timeframe, language, analysis-mode, risk, and notification values.
- Changed `/settings` to display the user's actual state.
- Added canonical market-status evaluation to `/signal`; `CLOSED`, `STALE`, and `NO_DATA` return `NO TRADE` before executable analysis or tracking.
- Expanded live-signal tracking eligibility to BUY, SELL, STRONG_BUY, and STRONG_SELL.
- HTML-escaped dynamic scanner fields.
- HTML-escaped dynamic tracked-signal fields.
- HTML-escaped dynamic journal fields.
- Changed `/status` to expose provider readiness.

## Regression coverage

`tests/test_telegram_surface_contract.py` covers:

- callback allowlisting;
- rejection of untrusted setting callback values;
- supported market/timeframe settings;
- invalid state fallback;
- complete executable signal set;
- scanner HTML escaping;
- journal HTML escaping.

## Implementation evidence

Implementation commits:

- `abea95fdd36e8fde1de9108d4659481f0bca2e60` — callback trust boundary
- `f744c8d44c1e6262d7acf0531910e39d97b9745f` — direct signal market-status gate
- `03918668250a2bbea716f302c4382894a1bf5ac3` — status readiness
- `5936b2aa42441bd8f181a836fe5d7043d88f933c` — tracked output escaping
- `cf5ab1e0cbadb4e59897002590d498558226e80e` — scanner output escaping
- `3b3f2610bec1d3348599df9361eae612311551ed` — journal output escaping

Regression commits:

- `4a9481ffa43cc98d387c0425e222486f6a955281` — initial Phase-3 surface tests
- `6ef061809cc8086238cdea0094cf1c07f0d2b8ed` — journal escaping regression

## Verification state

The latest code/documentation changes are now on `main`. GitHub Actions for the current head are running; Phase 3 must not be marked COMPLETE until the required exact-head checks finish successfully.

No agent/model/Ollama architecture was introduced by this phase. The work remains strictly within the Telegram/trading application surface.
