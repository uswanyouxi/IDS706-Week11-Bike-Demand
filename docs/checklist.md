# Assignment requirement coverage

See the [supplied requirements](../assignment/requirements.md), [TA clarifications](../assignment/ta_clarifications.md), [root project guide](../README.md) and [evidence index](submission.md).

| Requirement | Status / evidence |
| --- | --- |
| Original scheduled Airflow pipeline | Complete: daily 06:00 America/New_York, catchup=False, nine tasks |
| Two distinct datasets | Complete: UCI bike counts and Open-Meteo ERA5 weather |
| Parallel independent cleaning branches | Complete: real ingestion/cleaning overlap verified |
| Validated date merge and database load | Complete: 731 one-to-one matches, no unmatched dates, transactional idempotent PostgreSQL upserts |
| Read database back for analysis | Complete: three genuine database-fed EDA charts |
| Original executable agent loop | Complete: explicit LangGraph state, candidate/evaluation nodes and bounded conditional retry |
| Appropriate held-out metrics | Complete: chronological split, Dummy/Ridge MAE/RMSE/R2, one final test stage |
| Container setup and running instructions | Complete: pinned Docker environments and project commands |
| Required application screenshots | Complete: successful DAG, DAG graph, agent graph and evaluation captures |
| Optional distinct adaptive specialists | Verified: coordinator, diagnostics/refinement, model selection, recovery and reporting |
| Optional evaluation suite/dashboard | Verified for 27 declared executions, with scenario-specific criteria and saved-artifact audit |
| Optional strict two-classroom-baseline comparison | Native DAG and completed LangGraph reproduced on the same fraud sample; Bike Demand ports remain explicitly qualified adaptations |

The latest recorded combined test run passed 102 tests. Thirteen genuine screenshots document both required parts and the optional extension. Course deadline/timezone and any AI-use disclosure requirements are governed by Canvas.
