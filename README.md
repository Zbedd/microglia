# Microglia Segmentation Pipeline (Napari + Microglia-Analyzer)

Config-driven, end-to-end pipeline for segmenting **EGFP-labeled microglia** from **multipoint ND2 confocal z-stacks** and quantifying morphology (e.g., branches), driven via a napari plugin (e.g., Microglia-Analyzer). No new training data required.

---

## Features

- ✅ Read **ND2 multipoint (XY)** with **Z** stacks
- ✅ Build **maximum-intensity projections (MIP)** per XY
- ✅ Drive a napari plugin (e.g., Microglia-Analyzer) programmatically
- ✅ Save per-XY outputs: `mip_egfp.tif`, `mip_nuc.tif` (if present), `segmentation_labels.tif`, `features.csv`
- ✅ Write per-ND2 summaries and a **global** `results/summary.csv`
- ✅ All behavior controlled by a single **YAML config**

---

## Repository Layout

```
|-- data/                      # (optional) place .nd2 inputs here
|-- docs/
|   `-- USAGE.md               # optional notes
|-- results/                   # default output root
|-- scripts/
|   `-- run_microglia_pipeline.py
|-- src/
|   `-- microglia_pipeline/
|       |-- __init__.py
|       |-- aggregate.py
|       |-- config.py          # YAML loader & schema
|       |-- io_nd2.py
|       |-- orchestrate.py     # orchestrates per config
|       |-- plugin_runner.py
|       `-- preprocess.py
`-- tests/
  `-- test_smoke.py
```

---

## Installation

**Python:** 3.9+ (3.11 recommended).

```bash
# create an environment
conda create -n microglia python=3.11 -y
conda activate microglia

# core dependencies
pip install nd2 tifffile numpy pandas pyyaml

# napari GUI + plugin (plugin must be installed and discoverable via npe2)
pip install "napari[all]" microglia-analyzer
```

**(Optional) Developer install**

If you add a `pyproject.toml`, you can install the package in editable mode:

```bash
pip install -e .
```

---

## Configuration

All runtime settings are in a single YAML file.

```yaml
inputs:
  - "data/**/*.nd2"         # files, globs, or directories

output_root: "results"

channels:
  egfp_keywords: ["egfp", "gfp"]
  nuc_keywords:  ["bfp", "sgbfp", "dapi", "nuc"]

preprocessing:
  projection: "max"         # only 'max' is supported

plugin:
  enabled: true
  plugin_name: "microglia-analyzer"
  launch_gui: true          # napari viewer is shown

aggregation:
  write_global_summary: true
```

---

## Running the Pipeline

```bash
python scripts/run_microglia_pipeline.py
```

- The script loads `config.yaml` from the repository root (no CLI args parsed).
- Per-ND2 outputs → `results/<nd2_stem>/XY_###/…`
- Per-ND2 summary → `results/<nd2_stem>/summary.csv`
- Global summary (if enabled) → `results/summary.csv`

The napari GUI opens and the plugin is driven programmatically with minimal user interaction.

---

## Outputs

For each ND2 and XY:

```
results/
  <nd2_basename>/
    XY_000/
      mip_egfp.tif
      mip_nuc.tif            # present if nuclear channel exists
      segmentation_labels.tif
      features.csv           # per-XY summary
    XY_001/
      ...
  summary.csv                # per-ND2 summary
summary.csv                  # global, across all ND2s (if enabled)
```

---

## How It Works (High Level)

1. **IO & Preprocessing**
  - Load ND2 multipoint z-stacks
  - Detect EGFP and optional nuclei channels via **keyword matching**
  - Build **MIP** per XY (represents 3D morphology in 2D)

2. **Segmentation**
  - Auto-run a napari plugin (e.g., Microglia-Analyzer) programmatically (plugin must be installed)

3. **Quantification**
  - Save plugin-produced masks and features (if any)
  - Aggregate per-XY → per-ND2 → global CSV

---

## Tips & Troubleshooting

- **Channel detection**  
  Channels are matched by substring keywords in ND2 metadata. The reader currently requires both EGFP and nuclei channels to be present.
- **3D fidelity**  
  This pipeline uses **MIP** per XY to keep the output representative of 3D morphology without requiring 3D model training.

---

## Testing

```bash
pytest -q
```

`tests/test_smoke.py` validates imports and module wiring.

---