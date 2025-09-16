from __future__ import annotations
from pathlib import Path
import pandas as pd

def aggregate_per_nd2(output_root: Path, nd2_stem: str) -> Path | None:
    nd2_dir = output_root / nd2_stem
    rows = []
    for xy_dir in sorted(nd2_dir.glob("XY_*")):
        # accept common names produced/saved during plugin run
        for candidate in ("features.csv", "features_global.csv"):
            f = xy_dir / candidate
            if f.exists():
                df = pd.read_csv(f)
                df.insert(0, "nd2", nd2_stem)
                df.insert(1, "xy_dir", xy_dir.name)
                rows.append(df)
                break
    if not rows:
        return None
    out = pd.concat(rows, ignore_index=True)
    out_path = nd2_dir / "summary.csv"
    out.to_csv(out_path, index=False)
    return out_path

def aggregate_all(output_root: Path) -> Path | None:
    rows = []
    for nd2_dir in output_root.iterdir():
        if not nd2_dir.is_dir():
            continue
        summ = nd2_dir / "summary.csv"
        if summ.exists():
            df = pd.read_csv(summ)
            df.insert(0, "nd2_folder", nd2_dir.name)
            rows.append(df)
    if not rows:
        return None
    out = pd.concat(rows, ignore_index=True)
    out_path = output_root / "summary.csv"
    out.to_csv(out_path, index=False)
    return out_path
