# Microglia ND2 Projection Toolkit

Minimal, config-driven utilities to:

1. Read **multipoint (XY) ND2 z-stacks** containing EGFP (and nuclei) channels.
2. Generate per‑XY **maximum intensity projections (MIPs)** and store them on disk.
3. Load previously generated projections into **napari** for manual inspection or downstream interactive analysis (e.g., with external plugins like Microglia-Analyzer run manually by the user).

This repository no longer attempts to automate third‑party plugin execution (widget/button workflows proved unsuitable for robust headless control). Instead it focuses on a clean separation of data preparation (deterministic, reproducible) and interactive analysis (exploratory, user‑driven).

---

## Features

- ✅ Read **ND2 multipoint (XY)** z-stacks with **Z** dimension
- ✅ Channel keyword matching (EGFP + nuclei) with fail‑fast validation
- ✅ Generate per‑XY MIPs
- ✅ Deterministic on-disk layout (flat): `results/egfp/<nd2_stem>_XY###.tif` and `results/nuc/<nd2_stem>_XY###.tif`
- ✅ Simple two‑stage workflow: projection generation → interactive viewing
- ✅ Single YAML config controls inputs and output root

---

## Repository Layout

```
data/                 # place your own .nd2 inputs here (NOT tracked; large files ignored)
docs/
  USAGE.md
results/              # generated projections live here
scripts/
  generate_projections.py   # stage 1: produce MIPs
  view_projections.py       # stage 2: open all MIPs in napari
src/
  microglia_pipeline/
    __init__.py
    config.py        # YAML schema & loader
    io_nd2.py        # ND2 reading + channel detection
    preprocess.py    # max projection + saving helpers
tests/
  test_smoke.py
config.yaml
```

---

## Installation

**Python:** 3.9+ (3.11 recommended).

```bash
# create an environment
conda create -n microglia python=3.11 -y
conda activate microglia

# core dependencies (projection stage)
pip install nd2 tifffile numpy pandas pyyaml

# for viewing/interacting
pip install "napari[all]"
```

**(Optional) Developer install**

If you add a `pyproject.toml`, you can install the package in editable mode:

```bash
pip install -e .
```

---

## Configuration

All runtime settings live in `config.yaml` (kept intentionally minimal):

```yaml
inputs:
  - "data/**/*.nd2"         # files, globs, or directories

output_root: "results"

channels:
  egfp_keywords: ["egfp", "gfp"]
  nuc_keywords:  ["bfp", "sgbfp", "dapi", "nuc"]

preprocessing:
  projection: "max"         # only 'max' currently supported
```

---

## Data Inputs

No sample ND2 file is tracked (large microscopy binaries are excluded to keep the repository lightweight).

Place your own `.nd2` file(s) under `data/` (any subfolder) or elsewhere, then reference them via glob(s) in `config.yaml` (e.g. `data/**/*.nd2`).

Future enhancement: a small synthetic generator script could optionally produce a mock ND2; open an issue if desired.

## Workflow

### 1. Generate Projections

Reads ND2 files, detects EGFP + nuclei channels by keyword, produces per‑XY MIPs.

```bash
python scripts/generate_projections.py
```

Output layout (current flat format):

```
results/
  egfp/
    <nd2_stem>_XY000.tif
    <nd2_stem>_XY001.tif
    ...
  nuc/
    <nd2_stem>_XY000.tif
    <nd2_stem>_XY001.tif
    ...
```

Legacy (previous) layout with nested `XY_###/mip_*.tif` folders is no longer produced; regenerate projections if you still have the old structure.

### 2. View Projections

Loads every `mip_*.tif` into a napari viewer using consistent naming.

```bash
python scripts/view_projections.py
```

You can now manually launch and operate any napari plugin (e.g., Microglia-Analyzer) from the GUI; outputs you create manually are not automatically captured by this toolkit (by design—separation of concerns).

---

## Outputs

Only per‑XY projection TIFFs are produced (separate EGFP and nuclei directories). No automatic segmentation, feature tables, or aggregation are performed in this streamlined version.

---

## How It Works (High Level)

1. Discover ND2 files by glob(s) from the config.
2. For each file and each XY position:
   - Extract channel volumes, verify Z + C axes exist.
   - Identify EGFP & nuclei channels via case-insensitive substring match.
   - Compute max projection along Z.
  - Persist MIPs to flat deterministic folder structure (`results/egfp`, `results/nuc`).
3. (Optional) Load saved MIPs in napari for interactive exploration.

---

## Tips & Troubleshooting

- Channel detection: Provide sufficiently specific substrings in `channels.egfp_keywords` / `channels.nuc_keywords`.
- Missing channels: The reader fails fast if required channel keywords are not found.
- Large files: The `nd2` reader may produce dask arrays; projections are computed after loading each position.

---

## Testing

```bash
pytest -q
```

`tests/test_smoke.py` validates imports and module wiring.

---