# Capability Matrix

| Capability | Status | Implementation | Tests | Dependency | Execution Location | Phase | Last Verified Commit |
|---|---|---|---|---|---|---|---|
| Multi-asset market registry | VERIFIED_HISTORICAL | `config/symbols.py` | Existing | Providers/conversion | RAILWAY | 3-8 | e571a972 |
| Provider capability/failover | VERIFIED_HISTORICAL | `data/provider_manager.py` + providers | Existing | Market data | RAILWAY | 1-4 | e571a972 |
| Technical/price-action/structure analysis | VERIFIED_HISTORICAL | `analysis/` | Existing | Market data | RAILWAY | 5 | e571a972 |
| Statistical analysis | IMPLEMENTED_CURRENT | `analysis/statistical_engine.py` | `tests/test_advanced_intelligence_contracts.py` | Real prices | RAILWAY / PC_WORKER for batches | 14 | pending CI |
| Scenario engine | IMPLEMENTED_CURRENT | `analysis/scenario_engine.py` + FullAnalysisEngine | Focused | Statistical/market data | RAILWAY / PC_WORKER for large scenarios | 14 | pending CI |
| Counterfactual analysis | IMPLEMENTED_CURRENT | `analysis/counterfactual_engine.py` | Focused | Decision state | RAILWAY / PC_WORKER for batches | 14 | pending CI |
| Signal decay | IMPLEMENTED_CURRENT | `analysis/signal_state.py` + analysis report | Focused | Timestamp | RAILWAY | 15 | pending CI |
| Crisis mode | IMPLEMENTED_CURRENT | `analysis/signal_state.py` + decision gates | Focused | Volatility/timestamps | RAILWAY | 15 | pending CI |
| Decision conflict gates | IMPLEMENTED_CURRENT | `analysis/decision_engine.py` | Existing + focused | Scenario/signal state | RAILWAY | 15 | pending CI |
| Risk/position sizing | VERIFIED_HISTORICAL | `analysis/risk_engine.py`, `position_sizing.py` | Existing | Market metadata/conversion | RAILWAY | 6/8 | e571a972 |
| Portfolio engine | NOT_IMPLEMENTED | Missing canonical portfolio module | Missing | Positions/risk/correlation | RAILWAY / PC_WORKER for stress | 16 | — |
| Correlation matrix | NOT_IMPLEMENTED | Missing canonical portfolio/statistics integration | Missing | Multi-symbol history | PC_WORKER for large matrices | 16 | — |
| Portfolio stress | NOT_IMPLEMENTED | Missing | Missing | Portfolio/correlation | PC_WORKER | 16 | — |
| Real backtesting | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical data | PC_WORKER | 9 | e571a972 |
| Walk-forward | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical data | PC_WORKER | 9 | e571a972 |
| Monte Carlo | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical returns | PC_WORKER | 9 | e571a972 |
| Stress/sensitivity research | NOT_IMPLEMENTED | Missing dedicated contracts | Missing | Worker | PC_WORKER | 17 | — |
| Strategy DNA/adaptation/retirement | NOT_IMPLEMENTED | No canonical lifecycle engine found | Missing | Research/backtest/journal | PC_WORKER + RAILWAY | 18 | — |
| Champion/challenger | NOT_IMPLEMENTED | Missing | Missing | Strategy lifecycle | PC_WORKER | 18 | — |
| Scanner universe | VERIFIED_HISTORICAL | `services/telegram/scanner.py` | Existing | Providers | RAILWAY / PC_WORKER for large scans | 9 | e571a972 |
| Opportunity ranking | NOT_IMPLEMENTED | Missing | Missing | Scanner/statistics/risk | RAILWAY / PC_WORKER | 19 | — |
| Heatmap | NOT_IMPLEMENTED | Missing | Missing | Scanner/statistics | RAILWAY / PC_WORKER | 19 | — |
| Journal | VERIFIED_HISTORICAL | `services/telegram/journal.py` | Existing | Persistence | RAILWAY | 10/12 | e571a972 |
| Paper trading | PARTIAL | Production policy/configuration exists; no full lifecycle ledger | Partial | Decision/risk/persistence | RAILWAY | 20 | — |
| Shadow trading | NOT_IMPLEMENTED | Missing | Missing | Live/paper comparison | RAILWAY | 20 | — |
| Market replay | NOT_IMPLEMENTED | Missing | Missing | Historical candles | PC_WORKER | 20 | — |
| Time Machine | NOT_IMPLEMENTED | Missing | Missing | Replay/counterfactual | PC_WORKER | 20 | — |
| News/macro risk | EXTERNAL_DEPENDENCY | Readiness stage exists; no canonical real provider integration | Contract-only | External data provider | EXTERNAL + RAILWAY | 21 | — |
| Telegram localization | VERIFIED_HISTORICAL | `services/telegram/i18n.py` | Existing | Telegram | RAILWAY | 12 | e571a972 |
| Alerts/reports | PARTIAL | Existing signal/tracker/report surfaces | Existing | Telegram | RAILWAY | 22 | — |
| Persistent engineering state | IMPLEMENTED_CURRENT | State docs + resume contract | Documentation verification | Git history/CI | RAILWAY/GitHub | 0 | pending CI |
| Railway final gate | DEFERRED | Intentionally postponed until code roadmap closes | Not claimed | External deployment | EXTERNAL | Final | — |

## Execution Rule

Large historical, simulation, optimization, multi-symbol, multi-timeframe, correlation, stress, replay, and portfolio workloads belong on the PC Worker. Railway remains the control plane and light-processing boundary. A worker outage must degrade to explicit pending/deferred/no-compute states rather than crashing the core path.
