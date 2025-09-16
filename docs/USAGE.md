# Usage

## 1. Environment

```bash
conda create -n microglia python=3.11 -y
conda activate microglia

# projection dependencies
pip install nd2 tifffile numpy pandas pyyaml

# for viewing (napari GUI)
pip install "napari[all]"

# (optional) dev install
pip install -e .


## 2. Configure

Edit `config.yaml` with your ND2 glob(s):

```yaml
inputs:
	- "data/sample_data/*.nd2"
output_root: "results"
channels:
	egfp_keywords: ["egfp", "gfp"]
	nuc_keywords:  ["bfp", "sgbfp", "dapi", "nuc"]
preprocessing:
	projection: "max"
```

## 3. Generate Projections

```bash
python scripts/generate_projections.py
```

Outputs land in `results/<nd2_stem>/XY_###/mip_*.tif`.

## 4. View Projections

```bash
python scripts/view_projections.py
```

All MIPs load into a single napari viewer.

From here you may manually launch external plugins (e.g., Microglia-Analyzer) if installed; this repository does not automate them.

## 5. Testing

```bash
pytest -q
```

Smoke test ensures core modules import.
