#!/usr/bin/env python
from __future__ import annotations
from pathlib import Path
import sys
import traceback
from microglia_pipeline.config import load_config
from microglia_pipeline.io_nd2 import read_positions
from microglia_pipeline.preprocess import ensure_dir, save_xy_mips


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
    ensure_dir(Path(cfg.output_root))
    for nd2_path in nd2_paths:
        nd2_stem = nd2_path.stem
        nd2_out = ensure_dir(Path(cfg.output_root) / nd2_stem)
        print(f"[generate] Processing {nd2_path.name} -> {nd2_out}")
        for item in read_positions(
            nd2_path,
            cfg.channels.egfp_keywords,
            cfg.channels.nuc_keywords,
        ):
            xy = int(item['xy_index'])
            xy_dir = ensure_dir(nd2_out / f"XY_{xy:03d}")
            save_xy_mips(xy_dir, item['egfp_mip'], item['nuc_mip'])
    print('[generate] Done.')


if __name__ == '__main__':
    try:
        generate()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
