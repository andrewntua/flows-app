# Energy OID datapoint replication

CDF Function **`fn_oid_replicate_data_points`** copies time series datapoints from the Open Industrial Data **`publicdata`** project into **`energy_time_series`** instances (same external IDs, timestamps shifted forward one week).

## Prerequisites

1. Deploy **`energy_data_model`** and **`energy_base_raw_dm_ingestion`**, then load instances so time series exist in `energy_time_series`.
2. Add the OID app client secret to **`.env`** (deploy injects it into the function; never commit):

   ```bash
   OID_PUBLICDATA_CLIENT_SECRET=<your-oid-client-secret>
   ```

3. Schedule auth uses the same credentials as Toolkit deploy: **`IDP_CLIENT_ID`** and **`IDP_CLIENT_SECRET`** in `.env`.

## Deploy

From the repository root:

```bash
uv run cdf build -c bootcamp/config.dev.yaml
uv run cdf deploy --include functions
```

## Run

After deploy, the schedule runs every **5 minutes** (UTC). You can also invoke **`fn_oid_replicate_data_points`** manually from CDF Functions.

## Configuration

`bootcamp/config.dev.yaml` → `variables.modules`:

- `energyTimeSeriesSpace` — destination instance space (`energy_time_series`)
- `oidRootAssetExternalId` — OID asset subtree root (`WMT:Aker BP`)
- Function secret **`oid-secret`** — from **`.env`** → `OID_PUBLICDATA_CLIENT_SECRET` (see `fn_oid_replicate_data_points.Function.yaml`)
- `oidScheduleClientId` / `oidScheduleClientSecret` — `${IDP_CLIENT_ID}` / `${IDP_CLIENT_SECRET}`
