#!/usr/bin/env python
from __future__ import annotations
from pathlib import Path
import sys
import traceback
from microglia_pipeline.config import load_config
from microglia_pipeline.io_nd2 import read_positions
from microglia_pipeline.preprocess import ensure_dir
import tifffile as tiff
import numpy as np


def _collect_nd2_paths(inputs):
    from pathlib import Path
    import glob
    out = []
    for patt in inputs:
        p = Path(patt)
        if p.is_dir():
            out.extend(sorted(p.glob('*.nd2')))
        else:
            matches = [Path(m) for m in glob.glob(patt, recursive=True)]
            for m in matches:
                if m.is_dir():
                    out.extend(sorted(m.glob('*.nd2')))
                elif m.suffix.lower() == '.nd2':
                    out.append(m)
    # de-duplicate
    seen = set(); uniq = []
    for p in out:
        if p not in seen:
            uniq.append(p); seen.add(p)
    if not uniq:
        raise FileNotFoundError('No ND2 files found from config.inputs.')
    return uniq


def generate():
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root / 'config.yaml')
    nd2_paths = _collect_nd2_paths(cfg.inputs)
    out_root = ensure_dir(Path(cfg.output_root))
    egfp_root = ensure_dir(out_root / 'egfp')
    nuc_root = ensure_dir(out_root / 'nuc')

    for nd2_path in nd2_paths:
        nd2_stem = nd2_path.stem
        print(f"[generate] Processing {nd2_path.name} -> {egfp_root} / {nuc_root}")
        for item in read_positions(
            nd2_path,
            cfg.channels.egfp_keywords,
            cfg.channels.nuc_keywords,
        ):
            xy = int(item['xy_index'])
            egfp_fname = egfp_root / f"{nd2_stem}_XY{xy:03d}.tif"
            nuc_fname  = nuc_root  / f"{nd2_stem}_XY{xy:03d}.tif"
            # ensure arrays are numpy
            egfp_arr = np.asarray(item['egfp_mip'])
            nuc_arr = np.asarray(item['nuc_mip'])
            tiff.imwrite(str(egfp_fname), egfp_arr, photometric="minisblack")
            tiff.imwrite(str(nuc_fname),  nuc_arr,  photometric="minisblack")
    print('[generate] Done. Wrote flat layout under results/egfp and results/nuc')


if __name__ == '__main__':
    try:
        generate()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
