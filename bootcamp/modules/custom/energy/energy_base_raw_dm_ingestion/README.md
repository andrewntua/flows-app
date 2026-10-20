# energy_base_raw_dm_ingestion

Recreate **energy_dm** domain instances in a new CDF project from RAW tables and SQL transformations (20 views). Staging data is **`bootcamp/data/energy_dm_base_raw/*.RawRows.csv`** (Data plugin upload), not DMS instance NDJSON.

Does **not** load CDM 3D, SAP PM, or time-series datapoints. **EnergyFile** metadata comes from RAW + workflow; upload binaries separately from `bootcamp/data/energy_files_content/` (see [DEPLOY.md](../../../../docs/DEPLOY.md)).

## New-project sequence

1. Deploy `energy_data_model` (wipe + keep view `v1` if that is your process).
2. Deploy this module, upload RAW rows (`cdf data upload dir bootcamp/data/energy_dm_base_raw`), then run `wf_energy_base_raw_to_dm` in CDF.
3. Upload EnergyFile binaries: `cdf data upload dir bootcamp/data/energy_files_content`.
4. Optional, separate: `cognite_file_category`, datapoints, 3D, `sap_pm`.

## Refresh the snapshot from staging

Toolkit `cdf dump` covers resources, not view instances. Dump nodes with:

```text
uv run python scripts/build_energy_base_raw_from_cdf.py
```

Uses repo root `.env` by default (`--env-path` to override). `--skip-dump` regenerates SQL/workflow from existing `bootcamp/data/energy_dm_base_raw/*.RawRows.csv`.

## Layout

| Path | Role |
| --- | --- |
| `raw/` | RAW database + one table per view (deployed with the module; sole copy of `*.Table.yaml`) |
| `transformations/` | `{View}_nodes` then `{View}_relations` (direct relations only, `ignoreNullFields: true`) |
| `workflows/wf_energy_base_raw_to_dm` | All node tasks in parallel, then relation overlays `dependsOn` source + target node tasks |
| `bootcamp/data/energy_dm_base_raw/` | Data plugin `RawRows.csv` + manifests |
| `bootcamp/data/energy_files_content/` | Data plugin `CogniteFileContent` manifest + `files/` binaries |
