# Copilot Instructions for microglia (Projection-Only Version)

## Big picture
- Goal: Provide a minimal, reproducible path to convert multipoint ND2 z-stacks (EGFP + nuclei channels) into per‑XY maximum intensity projection TIFFs, and a lightweight viewer script to load them into napari.
- The repository deliberately avoids automating interactive napari plugins (e.g., Microglia-Analyzer). Users perform any downstream segmentation manually within the GUI.

## Architecture and data flow
1. `config.yaml` defines: `inputs`, `output_root`, `channels.egfp_keywords`, `channels.nuc_keywords`, and `preprocessing.projection` (must be `max`).
2. `scripts/generate_projections.py`:
   - Discovers ND2 files from config inputs (dirs, globs, or explicit paths).
   - Uses `io_nd2.read_positions` to iterate XY positions and produce MIPs.
   - Writes `mip_egfp.tif` and `mip_nuc.tif` into `results/<nd2_stem>/XY_###/`.
3. `scripts/view_projections.py`:
   - Scans the `results/` tree.
   - Loads all `mip_*.tif` into a single napari viewer (naming pattern: `<nd2_stem>_XY###_EGFP_MIP` / `_NUC_MIP`).
4. Users may manually run external napari plugins; outputs are not auto-saved by this toolkit.

## Core modules
- `config.py`: Dataclasses + loader with fail-fast validation (projection must be `max`).
- `io_nd2.py`: ND2 reading, channel detection, per-XY iteration, MIP computation helper call.
- `preprocess.py`: `max_proj` and `save_xy_mips` utilities.

## Removed / intentionally absent
- No `orchestrate.py`, `plugin_runner.py`, or aggregation/summary logic.
- No automated segmentation or feature extraction.

## Configuration contract
- `inputs`: list[str] (files, directories, or glob patterns). Must yield at least one `.nd2` file.
- `output_root`: path for results (default `results`).
- `channels.egfp_keywords`: ordered list of substrings to locate EGFP channel.
- `channels.nuc_keywords`: ordered list to locate nuclei channel.
- `preprocessing.projection`: only `max` accepted; fail fast otherwise.

## Output layout
```
results/
  <nd2_stem>/
    XY_000/mip_egfp.tif
           mip_nuc.tif
    XY_001/...
```

## Naming invariants
- Viewer layer names follow: `<nd2_stem>_XY###_EGFP_MIP` and `<nd2_stem>_XY###_NUC_MIP` (set in viewer script).
- Each XY directory stands alone; no cross‑XY dependencies.

## Extension guidelines
- To store additional derived images (e.g., intensity-normalized projections), add new save functions in `preprocess.py` and modify `generate_projections.py` accordingly.
- Preserve fail-fast validation for channel discovery and projection type.
- Avoid embedding GUI logic inside generation step (keep stage 1 headless).

## Testing
- `pytest -q` runs smoke test ensuring imports succeed.

Key files: `scripts/generate_projections.py`, `scripts/view_projections.py`, `src/microglia_pipeline/{config.py, io_nd2.py, preprocess.py}`, `config.yaml`.
