from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import importlib
import inspect
import pandas as pd

# Fail-fast: require napari and npe2 (modern plugin system)
try:
    import napari  # type: ignore
    from npe2 import PluginManager  # type: ignore
except Exception as e:
    raise ImportError(
        "This pipeline requires napari and npe2 for plugin execution. Install them and restart."
    ) from e

def _get_layer_by_name(viewer, name: str):
    try:
        return viewer.layers[name]
    except Exception:
        for layer in viewer.layers:
            if str(layer.name) == name:
                return layer
    return None

def _new_layers_since(viewer, baseline_names: List[str]):
    existing = set(baseline_names)
    return [l for l in viewer.layers if str(l.name) not in existing]

def save_labels_layer(layer, out_path: Path) -> None:
    import numpy as np, tifffile as tiff
    arr = getattr(layer, "data", None)
    if arr is None:
        return
    tiff.imwrite(str(out_path), (arr.astype("uint32")))

def save_shapes_layer(layer, out_csv: Path) -> None:
    rows = []
    feats = getattr(layer, "features", None)
    for i, shape in enumerate(getattr(layer, "data", [])):
        for j, (y, x) in enumerate(shape):
            rows.append({"shape_index": i, "vertex_index": j, "y": float(y), "x": float(x)})
    df = pd.DataFrame(rows)
    if feats is not None and len(feats) == len(getattr(layer, "data", [])):
        feats = feats.copy()
        feats["shape_index"] = range(len(feats))
        df = df.merge(feats, on="shape_index", how="left")
    df.to_csv(out_csv, index=False)

def try_run_plugin(
    viewer,
    egfp_layer_name: str,
    nuc_layer_name: Optional[str],
    out_dir: Path,
    plugin_name: str,
    preferred_command_ids: Optional[List[str]] = None,
) -> bool:
    """
    Strict npe2-only execution. Discover and execute commands matching the
    given plugin. Fail fast on missing commands or no outputs.
    """
    baseline = [str(l.name) for l in viewer.layers]

    pm = PluginManager.instance()
    pm.discover()

    # Build candidate command IDs: explicit preferred first, then those from manifests filtered by plugin name
    candidates: List[str] = list(preferred_command_ids or [])
    for mani in pm.iter_manifests():
        if plugin_name.lower() in mani.name.lower():
            for cmd in (mani.contributions.commands or []):
                if cmd.id:  # type: ignore[attr-defined]
                    candidates.append(cmd.id)

    # De-dupe, preserve order
    seen = set(); ordered: List[str] = []
    for c in candidates:
        if c and c not in seen:
            ordered.append(c); seen.add(c)

    if not ordered:
        # Prepare helpful diagnostics: list available manifests and commands
        manifests = [m.name for m in pm.iter_manifests()]
        available_cmds = []
        for m in pm.iter_manifests():
            for c in (m.contributions.commands or []):
                available_cmds.append(f"{m.name}:{c.id}")
        raise RuntimeError(
            (
                f"No npe2 commands found for plugin '{plugin_name}'.\n"
                f"Installed manifests: {manifests}\n"
                f"Available commands (name:id): {available_cmds[:50]}{' ...' if len(available_cmds)>50 else ''}\n"
                f"Ensure your plugin is installed and contributes commands, or set explicit command IDs in config.plugin.command_ids."
            )
        )

    # Prepare common argument mappings
    base_kwargs = {
        "viewer": viewer,
        "image": _get_layer_by_name(viewer, egfp_layer_name),
        "nuclei": _get_layer_by_name(viewer, nuc_layer_name) if nuc_layer_name else None,
        "output_dir": str(out_dir),
    }

    errors: List[str] = []
    for cid in ordered:
        try:
            cmd = pm.get_command(cid)
        except KeyError as e:
            errors.append(f"{cid}: not found")
            continue
        if not cmd:
            errors.append(f"{cid}: not found")
            continue

        # Resolve underlying callable from python_name to filter parameters accurately
        func = None
        try:
            pyname = getattr(cmd, "python_name", None)
            if not pyname or ":" not in pyname:
                raise ValueError("Command has no valid python_name")
            mod_name, func_name = pyname.split(":", 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            sig = inspect.signature(func)
            allowed = set(sig.parameters.keys())
        except Exception as e:
            errors.append(f"{cid}: failed to resolve callable - {e}")
            continue

        # Support common alias names (some plugins expect napari_viewer instead of viewer)
        call_kwargs = {k: v for k, v in base_kwargs.items() if k in allowed}
        if "viewer" in call_kwargs and "napari_viewer" in allowed and "napari_viewer" not in call_kwargs:
            call_kwargs["napari_viewer"] = call_kwargs["viewer"]
        # Some commands may use 'image_layer' or 'nuclei_layer'
        if "image" in call_kwargs and "image_layer" in allowed and "image_layer" not in call_kwargs:
            call_kwargs["image_layer"] = call_kwargs["image"]
        if "nuclei" in call_kwargs and "nuclei_layer" in allowed and "nuclei_layer" not in call_kwargs:
            call_kwargs["nuclei_layer"] = call_kwargs["nuclei"]

        try:
            cmd.exec(call_kwargs)
        except Exception as e:
            errors.append(f"{cid}: execution error - {e}")
            continue

        new_layers = _new_layers_since(viewer, baseline)
        if new_layers:
            return True
        else:
            errors.append(f"{cid}: executed but produced no new layers")

    raise RuntimeError(
        "Failed to execute any npe2 command for plugin '"
        + plugin_name
        + "'. Tried: "
        + ", ".join(ordered)
        + ". Errors: "
        + "; ".join(errors)
    )

def save_plugin_outputs(viewer, out_dir: Path, only_new_from: list[str]) -> None:
    before = set(only_new_from)
    for layer in list(viewer.layers):
        if str(layer.name) in before:
            continue
        try:
            if layer.__class__.__name__.lower() == "labels":
                save_labels_layer(layer, out_dir / "segmentation_labels.tif")
            elif layer.__class__.__name__.lower() == "shapes":
                save_shapes_layer(layer, out_dir / "shapes.csv")
            feats = getattr(layer, "features", None)
            if feats is not None and len(feats):
                pd.DataFrame(feats).to_csv(out_dir / "features.csv", index=False)
        except Exception:
            continue
