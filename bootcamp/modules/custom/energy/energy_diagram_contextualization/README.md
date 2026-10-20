# Energy diagram contextualization

CDF Functions and workflow for P&ID diagram annotation: delete existing annotations, detect **asset tags**, then detect **file references** on PDF `EnergyFile` instances.

## Prerequisites

1. Deploy **`modules/custom/groups`** (functions principal needs `diagramParsingAcl`).
2. Deploy **`energy_data_model`** and **`energy_base_raw_dm_ingestion`**.
3. Load instances: RAW upload → workflow **`wf_energy_base_raw_to_dm`**.
4. Upload PDF **binaries**: `cdf data upload dir bootcamp/data/energy_files_content` (diagram parsing requires file content, not metadata only).

Demo data uses `energy_instances` assets with **`WMT:`** external IDs and **15** PDFs under `bootcamp/data/energy_files_content/files/` (filenames match `EnergyFile` instance external IDs).

## Resources

| Resource | External ID |
|----------|-------------|
| Delete function | `fn_diagram_delete_annotations` |
| Tag detect function | `fn_diagram_detect_tag_annotations` |
| File detect function | `fn_diagram_detect_file_annotations` |
| Workflow | `wf_energy_diagram_contextualization` (version `1`) |

Workflow order: **delete**, then **tag detect** and **file detect** in parallel.

## Deploy

From repository root:

```bash
uv run cdf build -c bootcamp/config.dev.yaml
uv run cdf deploy --include functions --include workflows
```

Or deploy the full selected module set from `bootcamp/config.dev.yaml`.

## Run workflow

In CDF **Workflows**, run **`wf_energy_diagram_contextualization`**.

Tag/file detection can take hours (one `diagrams.detect` call per PDF). Detect task timeouts are capped at **43200s (12h)** (CDF maximum).

## Configuration

Set in `bootcamp/config.dev.yaml` under `variables.modules`:

- `energyInstanceSpace` — instance space (`energy_instances`)
- `energyDataModelSpace` — DM space (`energy_dm`)
- `energyAssetPrefix` — asset tag prefix (`WMT:`)
- `viewVersion` — view version (`v1`)
- `diagramWorkflowVersion` — workflow version (`"1"`)

## Smoke test

Invoke a detect function with a limited payload, e.g. `{"limit_pdfs": 1}`.

## Shared code

Canonical logic lives in `_shared/`. Each function folder contains copies of `config.py` and `diagram_annotations.py` for CDF packaging. After editing `_shared/`, copy into the three `functions/fn_*` directories.

See [DEPLOY.md](../../../../docs/DEPLOY.md) for the full bootcamp deploy sequence.
