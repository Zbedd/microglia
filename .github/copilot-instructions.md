# Copilot Instructions for microglia

## Big picture
- Goal: Run a config-driven napari pipeline to segment EGFP-labeled microglia from ND2 multipoint Z-stacks and write per-XY and per-file summaries.
- Hard requirements enforced in code: `napari`, `npe2` (plugin system), and `nd2` (modern Nikon reader). If any are missing, the code fails fast on import.
- Entrypoint: `scripts/run_microglia_pipeline.py` which loads `config.yaml` from repo root and calls `microglia_pipeline.orchestrate.run_from_config`.

## Architecture and data flow
- `config.yaml` → parsed by `src/microglia_pipeline/config.py` into dataclasses; validation fails-fast (plugin is mandatory; only `max` projection supported).
- `orchestrate.py`:
  - Collects `.nd2` files via `inputs` glob/paths; creates a napari `Viewer` per ND2; adds MIP images as layers.
  - Invokes plugin commands via `plugin_runner.try_run_plugin` and saves any new layers via `save_plugin_outputs`.
  - Aggregates per-ND2 summaries and optional global summary; keeps napari open via `napari.run()`.
- `io_nd2.py`:
  - Uses `nd2.ND2File`; requires axes `Z` and `C`; extracts channel names from metadata; selects EGFP/nuclei channels via keyword matching; computes MIP per XY.
- `preprocess.py`: `max_proj`, `save_xy_mips` helpers (writes `mip_egfp.tif`, `mip_nuc.tif`).
- `plugin_runner.py`:
  - Discovers `npe2` commands for `plugin_name` or uses explicit `command_ids`.
  - Executes commands with kwargs filtered to the callable signature: supports `viewer`, `image` (EGFP layer), `nuclei` (optional layer), `output_dir`.
  - Persists new napari layers created by the plugin:
    - Labels → `segmentation_labels.tif`
    - Shapes → `shapes.csv`
    - Any layer with `.features` → `features.csv`
- `aggregate.py`: collects `features.csv` from each `XY_###` folder into `summary.csv` per ND2 and optionally `results/summary.csv`.

## How to run and test
- Run (loads `config.yaml` from repo root; no CLI args are parsed):
  - Windows PowerShell: `python scripts/run_microglia_pipeline.py`
- Tests: `pytest -q` (only smoke-test imports in `tests/test_smoke.py`).
- Packaging: minimal `setup.py` with `src/` layout; editable install optional but not required to run the script.

## Configuration contract (actual)
- `inputs`: list of files/dirs/globs; ND2 files are discovered recursively; error if none found.
- `output_root`: default `results/`.
- `channels.egfp_keywords` and `channels.nuc_keywords`: lists used to locate channels by substring in metadata; error if not found.
- `preprocessing.projection`: must be `max`.
- `plugin.enabled`: must be `true`; `plugin_name` identifies the target plugin manifest.
- `plugin.command_ids`: optional preferred command IDs to try first (e.g., `"skan.skeletonize"`).
- `aggregation.write_global_summary`: if true, writes top-level `results/summary.csv`.

## Conventions and invariants
- Napari layer names added for inputs follow: `{nd2_stem}_XY{idx:03d}_EGFP_MIP` and `_NUC_MIP`.
- Plugin execution success is defined as creating at least one of: `segmentation_labels.tif` or `features.csv` in the XY folder.
- Output layout:
  - `results/<nd2_stem>/XY_000/` with `mip_egfp.tif`, `mip_nuc.tif`, `segmentation_labels.tif?`, `shapes.csv?`, `features.csv?`.
  - `results/<nd2_stem>/summary.csv` and optional `results/summary.csv`.

## Extending safely (patterns to follow)
- Adding support for new plugin outputs: extend `save_plugin_outputs` to persist additional layer types or metadata. Keep the “only new layers since baseline” behavior.
- When modifying ND2 IO, preserve fail-fast checks for `Z` and `C` axes and the channel keyword matching contract.
- Broadly, avoid side effects; prefer pure functions where possible; validate inputs and fail fast with clear error messages. Don't rely on backups or silent failures.

Key files: `scripts/run_microglia_pipeline.py`, `src/microglia_pipeline/{orchestrate.py, io_nd2.py, plugin_runner.py, aggregate.py, preprocess.py, config.py}`, `config.yaml`.
