from __future__ import annotations
from pathlib import Path
import numpy as np
import tifffile as tiff

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def max_proj(stack: np.ndarray, axis: int) -> np.ndarray:
    return np.max(stack, axis=axis)

def save_xy_mips(out_xy_dir: Path, egfp_mip: np.ndarray, nuc_mip: np.ndarray) -> None:
    ensure_dir(out_xy_dir)
    tiff.imwrite(str(out_xy_dir / "mip_egfp.tif"), np.asarray(egfp_mip), photometric="minisblack")
    tiff.imwrite(str(out_xy_dir / "mip_nuc.tif"),  np.asarray(nuc_mip),  photometric="minisblack")
