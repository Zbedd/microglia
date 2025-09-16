#!/usr/bin/env python
from __future__ import annotations
from pathlib import Path
import sys, traceback
import tifffile as tiff

# Fail-fast for napari only here
try:
    import napari  # type: ignore
except Exception as e:
    raise ImportError("napari is required to view projections. Install it and retry.") from e

from microglia_pipeline.config import load_config


def _iter_projection_dirs(output_root: Path):
    for nd2_dir in sorted(output_root.iterdir()):
        if not nd2_dir.is_dir():
            continue
        xy_dirs = sorted([p for p in nd2_dir.glob('XY_*') if p.is_dir()])
        if not xy_dirs:
            continue
        yield nd2_dir, xy_dirs


def view():
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root / 'config.yaml')
    out_root = Path(cfg.output_root)
    if not out_root.exists():
        raise FileNotFoundError(f"Output root {out_root} does not exist. Run generate_projections first.")

    v = napari.Viewer(title='Microglia Projections')
    for nd2_dir, xy_dirs in _iter_projection_dirs(out_root):
        nd2_stem = nd2_dir.name
        for xy_dir in xy_dirs:
            xy_name = xy_dir.name  # XY_###
            egfp = xy_dir / 'mip_egfp.tif'
            nuc  = xy_dir / 'mip_nuc.tif'
            if egfp.exists():
                try:
                    egfp_arr = tiff.imread(egfp)
                    v.add_image(egfp_arr, name=f"{nd2_stem}_{xy_name}_EGFP_MIP", blending='additive', colormap='green')
                except Exception as e:  # pragma: no cover - defensive
                    print(f"[warn] Failed to load {egfp}: {e}")
            if nuc.exists():
                try:
                    nuc_arr = tiff.imread(nuc)
                    v.add_image(nuc_arr, name=f"{nd2_stem}_{xy_name}_NUC_MIP", blending='additive', colormap='blue')
                except Exception as e:  # pragma: no cover
                    print(f"[warn] Failed to load {nuc}: {e}")
    napari.run()


if __name__ == '__main__':
    try:
        view()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
