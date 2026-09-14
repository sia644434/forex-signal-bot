# Engineering Changelog

## 2026-09-14 — Audit synchronization through TASK-083
- TASK-083: identified a concrete RiskEngine policy gap where `_dynamic_risk_percent()` could select up to `2.0%` without respecting a more restrictive configured `risk_percent`.
- TASK-083: changed dynamic sizing so configured `risk_percent` is the account-level ceiling; the dynamic heuristic may reduce risk but cannot silently exceed policy.
- TASK-083: added focused regression coverage for restrictive/non-restrictive ceilings and symmetric directional scoring.
- TASK-083: implementation commit `d9c427b7f44a56db2c4f6c98b37e249a6df8af82`.
- TASK-083: regression commit `cbc09a3fefa6b5d97d77119cb8196f1d21da7604`.
- ProviderManager lifecycle regression expectation was synchronized with the intentional `set_providers()` replacement contract after the CI suite exposed the stale test assumption.
- TASK-082: reconfiguration now replaces the injected provider registry and prunes removed instances/cooldowns while preserving active factory cache state.
- TASK-081: DataQuality now delegates symbol normalization to the canonical symbol layer.
- TASK-080: RiskEngine derives contract size from centralized asset metadata when no explicit override is supplied.
- TASK-079: PositionSizing, Settings, and RiskEngine now share the explicit USDT/USDC currency policy already supported by CurrencyConversion.
- Current verification remains tied to the exact resulting `main` HEAD; no green or live-production claim is made until the required GitHub Actions gates complete successfully.

## 2026-09-14 — TASK-079 through TASK-082
- TASK-082: identified a ProviderManager reconfiguration lifecycle gap where removed injected providers and stale cached state could remain reachable after `set_providers()`.
- TASK-082: replaced the injected-provider registry on reconfiguration and pruned inactive provider instances/cooldowns while preserving active factory cache state.
- TASK-082: added regression coverage for removal, stale cooldown cleanup, re-addition, and same-name instance rebinding.
- TASK-082 implementation commit `46ba02295ddbc2629cca371ebbdafaba47a6a715`.
- TASK-082 regression commits `03cace1b483d1980c3db074bae1be240f487f53c` and `54dfaa6591b90ebf9e99906cf14a10c73a30ea37`.
- TASK-081: aligned DataQuality symbol normalization with `config.symbols.normalize_symbol()` and added slash/underscore regression coverage.
- TASK-081 implementation commit `a3c6f43bf76e0ab10b0cb721fdd0e18a20e04ddd`.
- TASK-081 regression commit `0cbe8b40c62fb6a0b561d0d94d72de10436dbaa5`.
- TASK-080: removed the Forex contract-size default from direct non-Forex RiskEngine calls by deriving asset metadata when no explicit override exists.
- TASK-080 implementation commit `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`.
- TASK-080 regression commit `761e7666b846a69d3e1b5cc07604a4747e738f3f`.
- TASK-079: made the stablecoin currency boundary consistent across PositionSizing, Settings, RiskEngine, and CurrencyConversion.
- TASK-079 implementation commits `75b08aa971f5074db72bfff3850cfb9d9739f46c`, `ffbe2c4d8448e555481cf0a50ce6eeaafa358b3e`, `6f4e28a36338810a4ecb97bbe6b0bb08e9df0e92`.
- TASK-079 regression commits `3ea3828a5ff065944f901cd7fcfcff0d45952d01`, `4441b4b14e4f35db36f42f4cef25f06290d5346f`, `761e7666b846a69d3e1b5cc07604a4747e738f3f`.

## 2026-09-13 — TASK-065
- Identified a concrete RiskEngine configuration gap: `risk_reward_target` was accepted as a constructor parameter but TP2 and reported risk/reward remained hardcoded at `2.0`.
- Wired `risk_reward_target` into BUY/SELL TP2 and `RiskResult.risk_reward`.
- Added validation rejecting non-positive risk/reward targets and regression coverage.
- Implementation commit `377b08e05f47c8eeb5b1fd4d74f5aaa100181f77`.
- Test/verification commit `5b90cb34a43076ef5fda326e761159e3fc4fe69d`.
- Test run `34779486453` / job `103783750712` completed successfully, including lifecycle/persistence tests, full test suite, application health, Telegram imports, signal lifecycle imports, and syntax checks.
- Production E2E Contract Gate run `34779486425` / job `103783750727` completed successfully, including compile, production E2E contract tests, and full test suite.
- TASK-065 is VERIFIED. No local execution is claimed.

## 2026-09-13 — TASK-064
- Fixed a concrete DecisionEngine contract gap: the Supply/Demand decision component was reading `trend_score` instead of explicit `supply_demand_score`.
- Added regression coverage proving explicit Supply/Demand score changes affect the final decision independently of trend score.
- Verification commit `6b21d82f04a4a7deab2865ffe1bc86a066c8fca5` passed Test run `34778972992` and Production Activation Gate run `34778972997`.
- TASK-064 is VERIFIED.

## 2026-09-13 — TASK-063 / TASK-062 / TASK-061 / TASK-060 / TASK-059 / TASK-058
- TASK-063 wired the actual SupplyDemandEngine score into the AnalysisResult confidence contract.
- TASK-062 fixed ConfidenceEngine Supply/Demand score aliasing.
- TASK-061 aligned ConfidenceEngine with the signed analysis-component score contract and preserved neutral semantics.
- TASK-060 fixed FullAnalysisEngine trade-quality score asymmetry by using `abs((score - 50) * 2)`.
- TASK-059 fixed RiskEngine score-contract asymmetry using the same neutral-centered mapping.
- TASK-058 verified explicit-zero FreshnessPolicy threshold handling.
- The historical required CI/Railway verification evidence for these completed checkpoints remains preserved in repository history.

## Historical 2026-09-12 and earlier engineering checkpoints
- Established persistent engineering-memory state under `docs/engineering/`.
- Corrected the PC Worker boundary and removed the accidental local coding-agent/Ollama runtime from the active architecture.
- Removed the residual `multi_agent_analysis` worker workload.
- Added durable SQLite-backed worker queue, crash recovery, persistence configuration, application service composition, authenticated worker heartbeat/readiness, least-privilege health, authenticated jobs, readiness-gated dispatch, and worker observability.
- Consolidated Telegram ownership under `services/telegram/`.
- Consolidated Decision/Risk ownership under canonical `analysis/` engines and removed the unused alternate analysis architecture.
- Audited `ai/` as dormant/unwired future Phase 6 capability.
- Consolidated production Telegram market-data retrieval behind `MarketDataService` while preserving MarketDataEngine quality/freshness gates and ProviderManager routing.
- Removed the dormant direct OANDA price surface and unused lower-level provider compatibility architecture.
- Verified ProviderManager lifecycle and application-scoped market-data service lifetime.
- Hardened Telegram journal ordering, atomic mutations, corruption fail-closed behavior, structure validation, and entry-schema validation.
- Hardened service startup/shutdown cleanup and worker queue resource lifecycle.
