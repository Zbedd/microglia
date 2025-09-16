from __future__ import annotations
from pathlib import Path
from typing import Iterator, Dict, Any, List
import numpy as np

# Fail-fast: require the modern 'nd2' library only
try:
    import nd2  # type: ignore
except Exception as e:
    raise ImportError("The 'nd2' package is required (tlambert03/nd2). Install it before running.") from e

from .preprocess import max_proj

class ND2ReadError(RuntimeError):
    ...

def _find_channel_index(ch_names: List[str], keywords: List[str]) -> int:
    low = [c.lower() for c in ch_names]
    for kw in keywords:
        for i, name in enumerate(low):
            if kw.lower() in name:
                return i
    raise ND2ReadError(f"Required channel with keywords {keywords} not found in channels {ch_names}.")

def read_positions(
    nd2_path: Path,
    egfp_keywords: List[str],
    nuc_keywords: List[str],
) -> Iterator[Dict[str, Any]]:
    """
    Yields per-XY dicts: xy_index, egfp_mip, nuc_mip, meta
    Fail-fast conditions:
      - Z axis must exist
      - EGFP and nuclei channels must be found
    """
    with nd2.ND2File(str(nd2_path)) as f:
        sizes = dict(f.sizes)  # e.g., {'P':12, 'Z':15, 'C':2, 'Y':1024, 'X':1024}
        # Determine axis order from sizes and array shape
        # nd2 0.10.x returns arr shape ordered as tuple(sizes.values())
        axes = tuple(sizes.keys())
        if "Z" not in sizes or sizes.get("Z", 0) < 1:
            raise ND2ReadError(f"File {nd2_path.name}: no Z axis present; Z is required.")
        if "C" not in sizes or sizes.get("C", 0) < 2:
            raise ND2ReadError(f"File {nd2_path.name}: requires a C axis with EGFP and nuclei channels.")

        # Extract channel names; nd2 0.10.x exposes Channel objects with a `.channel` field (ChannelMeta) containing `.name`
        ch_names: List[str] = []
        chans = list(getattr(f.metadata, "channels", []) or [])
        if not chans:
            raise ND2ReadError(f"File {nd2_path.name}: metadata.channels is missing or empty.")
        for idx, ch in enumerate(chans):
            name = None
            # Preferred: Channel.channel.name
            meta = getattr(ch, "channel", None)
            if meta is not None:
                name = getattr(meta, "name", None)
            # Fallbacks: attempt common attributes
            if not name:
                for cand in ("label", "Label", "description", "text"):
                    name = getattr(ch, cand, None) or (getattr(meta, cand, None) if meta is not None else None)
                    if name:
                        break
            ch_names.append(str(name) if name else f"C{idx}")

        egfp_idx = _find_channel_index(ch_names, egfp_keywords)
        nuc_idx  = _find_channel_index(ch_names, nuc_keywords)

        # Prefer dask for large files; fall back to numpy
        if hasattr(f, "to_dask"):
            arr = f.to_dask()
            compute = True
        else:
            arr = f.asarray()
            compute = False

        ax_index = {ax: i for i, ax in enumerate(axes)}
        pos_axis = ax_index.get("P", None)
        n_pos = sizes.get("P", 1)

        for p in range(n_pos):
            sub = arr
            if pos_axis is not None:
                sl = [slice(None)] * sub.ndim
                sl[pos_axis] = p
                sub = sub[tuple(sl)]
            # materialize if dask
            if compute:
                sub = sub.compute()

            # After slicing P, recompute axis map without P
            old_axes = [ax for ax in axes if ax != "P"]
            aidx = {ax: i for i, ax in enumerate(old_axes)}
            try:
                cdim = aidx["C"]; zdim = aidx["Z"]
            except KeyError:
                raise ND2ReadError(f"File {nd2_path.name}: unexpected axis order {old_axes} (need C and Z).")

            egfp_vol = np.take(sub, indices=egfp_idx, axis=cdim)
            nuc_vol  = np.take(sub, indices=nuc_idx,  axis=cdim)

            egfp_mip = max_proj(egfp_vol, axis=zdim)
            nuc_mip  = max_proj(nuc_vol,  axis=zdim)

            yield dict(
                xy_index=p,
                egfp_mip=np.asarray(egfp_mip),
                nuc_mip=np.asarray(nuc_mip),
                meta=dict(ch_names=ch_names, sizes=sizes, axes="".join(axes), reader="nd2"),
            )
