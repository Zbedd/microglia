# Usage

```bash
# (optional) env
conda create -n microglia python=3.9 -y
conda activate microglia

pip install nd2 napari[all] tifffile numpy pandas pyyaml

# editable install (add your own pyproject.toml if desired)
pip install -e .

# run
python scripts/run_microglia_pipeline.py
