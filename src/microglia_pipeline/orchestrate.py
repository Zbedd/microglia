from __future__ import annotations
from pathlib import Path
from typing import List
import glob

# Fail-fast: require napari
try:
    import napari  # type: ignore
except Exception as e:
    raise ImportError("The 'napari' package is required. Install it before running.") from e

from .config import Config
from .io_nd2 import read_positions
from .preprocess import save_xy_mips, ensure_dir
from .aggregate import aggregate_per_nd2, aggregate_all
from .plugin_runner import try_run_plugin, save_plugin_outputs

def _collect_nd2_paths(inputs: List[str]) -> List[Path]:
    out: List[Path] = []
    for patt in inputs:
        p = Path(patt)
        if p.is_dir():
            out.extend(sorted(p.glob("*.nd2")))
        else:
            matches = [Path(m) for m in glob.glob(patt, recursive=True)]
            for m in matches:
                if m.is_dir():
                    out.extend(sorted(m.glob("*.nd2")))
                elif m.suffix.lower() == ".nd2":
                    out.append(m)
    # de-dupe preserve order
    seen = set(); uniq = []
    for p in out:
        if p not in seen:
            uniq.append(p); seen.add(p)
    if not uniq:
        raise FileNotFoundError("No ND2 files found from config.inputs.")
    return uniq

def _assert_xy_outputs(xy_dir: Path) -> None:
    # Define minimal success criterion after plugin run
    has_any = (xy_dir / "segmentation_labels.tif").exists() or (xy_dir / "features.csv").exists()
    if not has_any:
        raise RuntimeError(
            f"Plugin did not produce expected outputs in {xy_dir}. "
            "Ensure the plugin exposes npe2 commands that create new napari layers (labels/shapes/features)."
        )

def process_nd2_file(nd2_path: Path, cfg: Config) -> None:
    nd2_stem = nd2_path.stem
    nd2_outdir = ensure_dir(Path(cfg.output_root) / nd2_stem)

    # viewer always required/shown
    viewer = napari.Viewer(title=f"Microglia pipeline: {nd2_stem}")

    for item in read_positions(
        nd2_path,
        cfg.channels.egfp_keywords,
        cfg.channels.nuc_keywords,
    ):
        xy_idx = int(item["xy_index"])
        egfp_mip = item["egfp_mip"]
        nuc_mip = item["nuc_mip"]

        xy_dir = ensure_dir(nd2_outdir / f"XY_{xy_idx:03d}")
        save_xy_mips(xy_dir, egfp_mip, nuc_mip)

        egfp_name = f"{nd2_stem}_XY{xy_idx:03d}_EGFP_MIP"
        nuc_name = f"{nd2_stem}_XY{xy_idx:03d}_NUC_MIP"
        viewer.add_image(egfp_mip, name=egfp_name, blending="additive", colormap="green")
        viewer.add_image(nuc_mip,  name=nuc_name,  blending="additive", colormap="blue")

        if not cfg.plugin.enabled:
            raise RuntimeError("Plugin is mandatory. Set plugin.enabled: true in config.")

        before_names = [str(l.name) for l in viewer.layers]
        ran = try_run_plugin(
            viewer,
            egfp_name,
            nuc_name,
            xy_dir,
            plugin_name=cfg.plugin.plugin_name,
            preferred_command_ids=cfg.plugin.command_ids,
        )
        if not ran:
            raise RuntimeError(
                f"Failed to invoke plugin '{cfg.plugin.plugin_name}'. "
                "Provide explicit plugin.command_ids in config or verify the plugin installation."
            )

        save_plugin_outputs(viewer, xy_dir, only_new_from=before_names)
        _assert_xy_outputs(xy_dir)

    aggregate_per_nd2(Path(cfg.output_root), nd2_stem)

def run_from_config(cfg: Config) -> None:
    nd2_paths = _collect_nd2_paths(cfg.inputs)
    ensure_dir(Path(cfg.output_root))
    for nd2_path in nd2_paths:
        process_nd2_file(nd2_path, cfg)

    if cfg.aggregation.write_global_summary:
        aggregate_all(Path(cfg.output_root))

    # keep napari alive for inspection
    napari.run()
