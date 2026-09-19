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
| Portfolio engine | IMPLEMENTED_CURRENT | `analysis/portfolio_engine.py` | `tests/test_portfolio_engine.py` | Positions/risk/correlation | RAILWAY / PC_WORKER for stress | 16 | pending CI |
| Correlation matrix | IMPLEMENTED_CURRENT | `analysis/portfolio_engine.py` + `worker/executors.py::correlation_matrix` | `tests/test_portfolio_engine.py`, worker contracts | Multi-symbol history | PC_WORKER | 16 | pending CI |
| Portfolio stress | IMPLEMENTED_CURRENT | `analysis/portfolio_engine.py` + `worker/executors.py::portfolio_stress` | `tests/test_portfolio_engine.py`, worker research tests | Portfolio/correlation | PC_WORKER | 16 | pending CI |
| Real backtesting | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical data | PC_WORKER | 9 | e571a972 |
| Walk-forward | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical data | PC_WORKER | 9 | e571a972 |
| Monte Carlo | VERIFIED_HISTORICAL_PARTIAL | `worker/executors.py` | Existing | Historical returns | PC_WORKER | 9 | e571a972 |
| Stress/sensitivity research | IMPLEMENTED_CURRENT | `worker/executors.py::stress_sensitivity` | `tests/test_worker_advanced_research.py` | Portfolio/shocks | PC_WORKER | 17 | pending CI |\n| Robustness / temporal leakage checks | IMPLEMENTED_CURRENT | `analysis/robustness_engine.py` + `worker/executors.py::robustness_analysis` | `tests/test_robustness_engine.py` | Historical prices/timestamps | PC_WORKER | 17 | pending CI |
| Strategy DNA/adaptation/retirement | IMPLEMENTED_CURRENT | `analysis/strategy_intelligence.py` registry/DNA/adaptation/weakness/retirement/rollback | `tests/test_strategy_intelligence.py` | Research/backtest/journal | PC_WORKER + RAILWAY | 18 | pending CI |
| Champion/challenger | IMPLEMENTED_CURRENT | `analysis/strategy_intelligence.py::compare/promote` + worker evaluation | `tests/test_strategy_intelligence.py`, `tests/test_strategy_worker_executor.py` | Strategy lifecycle | PC_WORKER | 18 | pending CI |
| Scanner universe | VERIFIED_HISTORICAL | `services/telegram/scanner.py` | Existing | Providers | RAILWAY / PC_WORKER for large scans | 9 | e571a972 |
| Opportunity ranking | IMPLEMENTED_CURRENT | `analysis/opportunity_engine.py` + Telegram scanner | `tests/test_opportunity_engine.py` | Scanner/decision/risk | RAILWAY / PC_WORKER | 19 | pending CI |
| Heatmap | IMPLEMENTED_CURRENT | `analysis/opportunity_engine.py` | `tests/test_opportunity_engine.py` | Scanner/statistics | RAILWAY / PC_WORKER | 19 | pending CI |
| Journal | VERIFIED_HISTORICAL | `services/telegram/journal.py` | Existing | Persistence | RAILWAY | 10/12 | e571a972 |
| Paper trading | PARTIAL | Production policy/configuration exists; no full lifecycle ledger | Partial | Decision/risk/persistence | RAILWAY | 20 | — |
| Shadow trading | NOT_IMPLEMENTED | Missing | Missing | Live/paper comparison | RAILWAY | 20 | — |
| Market replay | NOT_IMPLEMENTED | Missing | Missing | Historical candles | PC_WORKER | 20 | — |
| Time Machine | IMPLEMENTED_CURRENT | `analysis/time_machine.py` + `worker/executors.py::time_machine` | `tests/test_time_machine.py` | Replay + counterfactual | PC_WORKER | 20 | pending CI |
| News/macro risk | EXTERNAL_DEPENDENCY | Readiness stage exists; no canonical real provider integration | Contract-only | External data provider | EXTERNAL + RAILWAY | 21 | — |
| Telegram localization | VERIFIED_HISTORICAL | `services/telegram/i18n.py` | Existing | Telegram | RAILWAY | 12 | e571a972 |
| Alerts/reports | PARTIAL | Existing signal/tracker/report surfaces | Existing | Telegram | RAILWAY | 22 | — |
| Persistent engineering state | IMPLEMENTED_CURRENT | State docs + resume contract | Documentation verification | Git history/CI | RAILWAY/GitHub | 0 | pending CI |
| Railway final gate | DEFERRED | Intentionally postponed until code roadmap closes | Not claimed | External deployment | EXTERNAL | Final | — |

## Execution Rule

Large historical, simulation, optimization, multi-symbol, multi-timeframe, correlation, stress, replay, and portfolio workloads belong on the PC Worker. Railway remains the control plane and light-processing boundary. A worker outage must degrade to explicit pending/deferred/no-compute states rather than crashing the core path.


| Paper trading | IMPLEMENTED_CURRENT | `services/paper_trading.py` | `tests/test_paper_trading.py` | Decision/risk/persistence | RAILWAY | 20 | pending CI |
| Shadow trading | IMPLEMENTED_CURRENT | `services/paper_trading.py` comparison contract | `tests/test_paper_trading.py` | Live/paper decision streams | RAILWAY | 20 | pending CI |
| Market replay | IMPLEMENTED_CURRENT | `worker/executors.py::market_replay` | `tests/test_market_replay_executor.py` | Historical candles/full analysis | PC_WORKER | 20 | pending CI |
| Time Machine | IMPLEMENTED_CURRENT | `analysis/time_machine.py` + `worker/executors.py::time_machine` | `tests/test_time_machine.py` | Replay + counterfactual | PC_WORKER | 20 | pending CI |

| News provider integration | IMPLEMENTED_CURRENT | `analysis/macro_risk.py::NewsAPIProvider` | `tests/test_macro_risk.py` | NEWSAPI_API_KEY | RAILWAY | 11 | pending CI |
| Macro/FRED provider integration | IMPLEMENTED_CURRENT | `analysis/macro_risk.py::FREDProvider` | `tests/test_macro_risk.py` | FRED_API_KEY | RAILWAY | 11 | pending CI |
| Macro event risk gating | IMPLEMENTED_CURRENT | `MacroRiskEngine.assess` + FullAnalysisEngine + DecisionEngine | `tests/test_macro_risk.py`, `tests/test_full_engine.py` | Macro context | RAILWAY | 11 | pending CI |

| Out-of-sample validation | IMPLEMENTED_CURRENT | `analysis/research_engine.py::out_of_sample` | `tests/test_research_engine.py` | Historical prices | PC_WORKER | 14/17 | pending CI |
| Rolling walk-forward validation | IMPLEMENTED_CURRENT | `analysis/research_engine.py::walk_forward` + `worker/executors.py::research_validation` | `tests/test_research_engine.py`, worker contract | Historical prices/parameter grid | PC_WORKER | 14/17 | pending CI |
| Overfitting diagnostics | IMPLEMENTED_CURRENT | `analysis/research_engine.py::overfitting_diagnostics` | `tests/test_research_engine.py` | OOS results | PC_WORKER | 17 | pending CI |
| Temporal leakage enforcement/check | IMPLEMENTED_CURRENT | `analysis/research_engine.py::temporal_leakage_check` | `tests/test_research_engine.py` | Feature/target timestamps | PC_WORKER | 17 | pending CI |


| Version-bound strategy validation | IMPLEMENTED_CURRENT | analysis/strategy_intelligence.py::StrategyValidationEvidence | tests/test_strategy_intelligence.py | Strategy DNA/version + research evidence | PC_WORKER + RAILWAY | 18 | pending CI |
| Research-backed strategy evaluation | IMPLEMENTED_CURRENT | worker/executors.py::strategy_evaluation + analysis/research_engine.py | tests/test_strategy_worker_executor.py | Historical prices/OOS/walk-forward | PC_WORKER | 18 | pending CI |

| Validation-aware continuous evaluation history | IMPLEMENTED_CURRENT | analysis/strategy_intelligence.py::StrategyEvaluationSnapshot + continuous_evaluate | tests/test_strategy_intelligence.py | Strategy lifecycle + versioned validation | RAILWAY / PC_WORKER | 18 | pending CI |

| Research-backed robustness gate | IMPLEMENTED_CURRENT | worker/executors.py + analysis/robustness_engine.py | tests/test_strategy_worker_executor.py | Historical prices + robustness matrix | PC_WORKER | 18 | pending CI |

| Validation-gated strategy lifecycle | IMPLEMENTED_CURRENT | analysis/strategy_intelligence.py::evaluate | tests/test_strategy_intelligence.py | Version-bound research validation | RAILWAY / PC_WORKER | 18 | pending CI |
| Research validation diagnostics | IMPLEMENTED_CURRENT | worker/executors.py::strategy_evaluation + StrategyValidationEvidence | tests/test_strategy_worker_executor.py | OOS/walk-forward + robustness | PC_WORKER | 18 | pending CI |
| Automatic strategy retirement guard | IMPLEMENTED_CURRENT | analysis/strategy_intelligence.py::evaluate | tests/test_strategy_intelligence.py | Sample/expectancy/drawdown | RAILWAY / PC_WORKER | 18 | pending CI |


| Paper equity / mark-to-market | IMPLEMENTED_CURRENT | services/paper_trading.py | tests/test_paper_trading.py | Paper ledger | RAILWAY | 20 | pending CI |
| Deterministic alert policy | IMPLEMENTED_CURRENT | services/alert_engine.py | tests/test_alert_engine.py | Reports/signals | RAILWAY | 22 | pending CI |
| Report alert contract | IMPLEMENTED_CURRENT | analysis/report.py::alert_context | tests/test_alert_report_contract.py | Analysis report | RAILWAY | 22 | pending CI |
| Macro collection cache/orchestration | IMPLEMENTED_CURRENT | analysis/macro_risk.py | tests/test_macro_risk.py | External providers | RAILWAY | 21 | pending CI |

| Portfolio pre-trade risk guard | IMPLEMENTED_CURRENT | analysis/portfolio_risk_guard.py + FullAnalysisEngine/DecisionEngine integration | tests/test_portfolio_risk_guard.py, tests/test_full_engine.py | Portfolio/risk/decision | RAILWAY; heavy portfolio analysis remains PC_WORKER | 14/20 | pending CI |
| Equity-aware gross exposure | IMPLEMENTED_CURRENT | PortfolioRiskGuard.assess/can_add | tests/test_portfolio_risk_guard.py | Portfolio equity | RAILWAY | 14/20 | pending CI |
| Shadow comparison history | IMPLEMENTED_CURRENT | services/paper_trading.py::ShadowComparisonLedger | tests/test_paper_trading.py | Paper/shadow lifecycle | RAILWAY | 20 | pending CI |
