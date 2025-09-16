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

    # In manual mode we register a callback that saves any new plugin output layers
    manual_mode = getattr(cfg.plugin, "manual_mode", False)
    saved_xy_dirs = []  # track which XY dirs have at least one output
    def _on_new_layer(event):  # type: ignore[unused-private-member]
        layer = event.value
        name = str(getattr(layer, "name", ""))
        if f"{nd2_stem}_XY" not in name:
            return
        try:
            part = name.split(f"{nd2_stem}_XY", 1)[1][:3]
            xy_idx = int(part)
        except Exception:
            return
        xy_dir = Path(cfg.output_root) / nd2_stem / f"XY_{xy_idx:03d}"
        if not xy_dir.exists():
            return
        # Persist this single layer if relevant
        try:
            cls = layer.__class__.__name__.lower()
            if cls == "labels":
                from .plugin_runner import save_labels_layer
                save_labels_layer(layer, xy_dir / "segmentation_labels.tif")
            elif cls == "shapes":
                from .plugin_runner import save_shapes_layer
                save_shapes_layer(layer, xy_dir / "shapes.csv")
            feats = getattr(layer, "features", None)
            if feats is not None and len(feats):
                import pandas as _pd
                _pd.DataFrame(feats).to_csv(xy_dir / "features.csv", index=False)
            if xy_dir not in saved_xy_dirs:
                saved_xy_dirs.append(xy_dir)
        except Exception:
            return

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

        if manual_mode:
            # Defer plugin execution; user will trigger via GUI. We attach callback once.
            if not hasattr(viewer, "_microglia_manual_hook"):
                try:
                    viewer.layers.events.inserted.connect(_on_new_layer)  # type: ignore[attr-defined]
                    viewer._microglia_manual_hook = True  # type: ignore[attr-defined]
                except Exception:
                    pass
        else:
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

    if not manual_mode:
        aggregate_per_nd2(Path(cfg.output_root), nd2_stem)

## Note: run_from_config has been intentionally removed. The orchestration
## logic now lives directly inside scripts/run_microglia_pipeline.py:main().
