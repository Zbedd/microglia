# Data (User-Supplied Only)

No example `.nd2` file is stored to avoid bloating repository history.

Instructions:
1. Copy or symlink your ND2 files into this folder (any depth) OR adjust `config.yaml` to point to another location.
2. Ensure `inputs:` in `config.yaml` matches (e.g. `data/**/*.nd2`).
3. Run `python scripts/generate_projections.py` to create per‑XY MIPs under `results/`.

Git Ignore Policy:
- All binary ND2 files (`*.nd2`) are ignored globally.
- This README (and other README files) remain tracked.

If you need a tiny test asset, consider adding a synthetic creator script (not included yet).