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
import re


def _discover_flat(output_root: Path):
    egfp_dir = output_root / 'egfp'
    nuc_dir = output_root / 'nuc'
    if not egfp_dir.exists() and not nuc_dir.exists():
        raise FileNotFoundError(
            f"Expected flat layout under {output_root}/egfp and {output_root}/nuc. Run generate_projections first." )
    pattern = re.compile(r'^(?P<stem>.+)_XY(?P<xy>\d{3})\.tif$', re.IGNORECASE)
    entries = {}
    if egfp_dir.exists():
        for f in sorted(egfp_dir.glob('*.tif')):
            m = pattern.match(f.name)
            if m:
                key = (m.group('stem'), m.group('xy'))
                entries.setdefault(key, {})['egfp'] = f
    if nuc_dir.exists():
        for f in sorted(nuc_dir.glob('*.tif')):
            m = pattern.match(f.name)
            if m:
                key = (m.group('stem'), m.group('xy'))
                entries.setdefault(key, {})['nuc'] = f
    for (stem, xy), files in sorted(entries.items(), key=lambda x: (x[0][0], x[0][1])):
        yield stem, xy, files.get('egfp'), files.get('nuc')


def view():
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root / 'config.yaml')
    out_root = Path(cfg.output_root)
    if not out_root.exists():
        raise FileNotFoundError(f"Output root {out_root} does not exist. Run generate_projections first.")

    v = napari.Viewer(title='Microglia Projections')
    for stem, xy, egfp_path, nuc_path in _discover_flat(out_root):
        xy_tag = f"XY_{xy}"
        if egfp_path and egfp_path.exists():
            try:
                egfp_arr = tiff.imread(egfp_path)
                v.add_image(egfp_arr, name=f"{stem}_{xy_tag}_EGFP_MIP", blending='additive', colormap='green')
            except Exception as e:  # pragma: no cover
                print(f"[warn] Failed to load {egfp_path}: {e}")
        if nuc_path and nuc_path.exists():
            try:
                nuc_arr = tiff.imread(nuc_path)
                v.add_image(nuc_arr, name=f"{stem}_{xy_tag}_NUC_MIP", blending='additive', colormap='blue')
            except Exception as e:  # pragma: no cover
                print(f"[warn] Failed to load {nuc_path}: {e}")
    napari.run()


if __name__ == '__main__':
    try:
        view()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
