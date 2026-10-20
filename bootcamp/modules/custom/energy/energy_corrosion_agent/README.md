# Energy corrosion loop agent

Atlas AI agent for corrosion-loop, **EnergyPiping**, CUI/RBI, CML/wall-thickness, and related **energy_dm** questions. Migrated from `tech-sales-quickstart` `agents_core` corrosion piping agent.

## Prerequisites

1. **`energy_data_model`** and **`energy_base_raw_dm_ingestion`** deployed with instances loaded (`wf_energy_base_raw_to_dm`).
2. Instance spaces **`energy_instances`** and **`energy_time_series`** populated (matches `bootcamp/config.dev.yaml`).
3. **`modules/custom/groups`** (or equivalent) with `agentsAcl` for deploy/run.

## Deploy

```bash
uv run cdf build -c bootcamp/config.dev.yaml
uv run cdf deploy --include agents
```

Agent external ID: `f3a9c2e1-8d4b-4f67-a1c0-9e7b5d3a2f81`  
Model is set in `agents/energy_corrosion_piping.Agent.yaml` (`model` field).

## Data model compatibility (bootcamp `energy_dm` v1)

| Agent expectation | Bootcamp |
| --- | --- |
| Data model `energy_dm` / `energy_dm` / `v1` | Yes (`energy_dm.DataModel.yaml`) |
| Instance space `energy_instances` | Yes |
| Time series space `energy_time_series` | Yes |
| **CorrosionLoop**, **EnergyPiping**, **Material**, **InspectionRecommendation** | Yes |
| **ConditionMonitoringLocation** + **WallThicknessMeasuringPoint** (UT path) | Yes (`nominalThicknessMm`, `tminMm`, `measuredThicknessMm`) |
| **EnergyAsset**, **Equipment**, **File**, maintenance, notifications, failure RCA views | Yes |
| **EquipmentType** (was `VEquipmentType` in quickstart) | Yes — agent YAML updated |
| **PipingCorrosionInference** | Yes — included in `query_energy_dm` view list |

## Built-in tools (in agent YAML)

- `query_energy_dm` — DMS queries on `energy_instances`
- `find_time_series` / `query_time_series_datapoints` — `energy_time_series`
- `ask_documents` / `summarize_documents` — after resolving **EnergyFile**

## AIM Risk Flows client tools (not in this module)

Instructions reference **filter_rbi_analysis_lines**, **list_asset_time_series**, **modify_chart_time_series**, and **modify_3d_highlights**. Those are registered by the **AIM Risk** Flows app (`apps/aim-risk` in quickstart), not by Toolkit deploy. Without that app, the agent still works for data/document/time-series Q&A; table/chart/3D actions need the Flows app on this branch (planned).

## Related docs

- [DEPLOY.md](../../../../docs/DEPLOY.md) — full bootcamp deploy
