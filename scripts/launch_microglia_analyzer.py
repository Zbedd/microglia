#!/usr/bin/env python
"""Launch napari and open the Microglia Analyzer plugin widget (if installed).

Purpose:
- Start a clean napari session WITHOUT preloading any images.
- Add the Microglia Analyzer dock widget so the user can immediately choose sources.

What this script deliberately does NOT do:
- It does not attempt to auto-select the 'Sources Folder'. The plugin's UI requires an interactive
    click on the 'Sources Folder' button within the Media Control panel.

If the plugin cannot be located, a plain napari viewer is launched and you can access the plugin via:
Plugins -> Microglia Analyzer -> Microglia Analyzer
"""
from __future__ import annotations
from pathlib import Path
import sys, traceback

try:
    import napari  # type: ignore
    from napari.plugins import plugin_manager  # type: ignore
except Exception as e:  # pragma: no cover
    raise ImportError("napari (and its plugin system) is required. Install napari before running this script.") from e

from microglia_pipeline.config import load_config


def _find_microglia_widget():
    """Return (plugin_name, widget_name, widget_factory) for a widget containing 'microglia'.

    Primary target (menu path): Plugins -> Microglia Analyzer -> Microglia Analyzer
    If the exact pair ('microglia-analyzer', 'Microglia Analyzer') or variations are not found,
    fall back to heuristic substring search.
    """
    registry = getattr(plugin_manager, '_dock_widgets', {})
    # First: attempt canonical names / likely variants
    preferred_pairs = [
        ('microglia-analyzer', 'Microglia Analyzer'),
        ('microglia_analyzer', 'Microglia Analyzer'),
        ('Microglia Analyzer', 'Microglia Analyzer'),  # sometimes plugin name mirrors label
    ]
    for pair in preferred_pairs:
        if pair in registry:
            return pair[0], pair[1], registry[pair]
    # Fallback: substring search
    for (plugin_name, widget_name), factory in registry.items():
        key_combo = f"{plugin_name}.{widget_name}".lower()
        if 'microglia' in key_combo:
            return plugin_name, widget_name, factory
    return None


def _try_add_via_public_api(viewer):
    """Attempt to add the plugin dock widget using napari's public API call first.

    Returns the instantiated widget if successful, else None.
    """
    add_api = getattr(viewer.window, 'add_plugin_dock_widget', None)
    if not callable(add_api):
        return None
    candidate_plugin_names = [
        'microglia-analyzer',
        'microglia_analyzer',
        'Microglia Analyzer',
    ]
    candidate_widget_names = [
        'Microglia Analyzer',
        'microglia analyzer',
    ]
    for plugin_name in candidate_plugin_names:
        for widget_name in candidate_widget_names:
            try:
                result = add_api(plugin_name, widget_name)
                # napari returns (widget, dock_widget)
                if isinstance(result, (tuple, list)) and result:
                    widget = result[0]
                else:
                    widget = result
                if widget is not None:
                    print(f"[launcher] Added via public API: {plugin_name} -> {widget_name}")
                    return widget
            except Exception:
                continue
    return None


## Removed: auto directory heuristics (intentionally simplified per request)


def launch():
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root / 'config.yaml')
    # Only ensure projections likely exist; no strict requirement to start viewer
    egfp_dir = Path(cfg.output_root) / 'egfp'
    if not egfp_dir.exists():
        print(f"[launcher] Warning: EGFP directory not found at {egfp_dir}. You can still open the plugin and set sources later.")

    viewer = napari.Viewer(title='Microglia Analyzer Launcher')
    # First try public API
    widget_instance = _try_add_via_public_api(viewer)

    if widget_instance is None:
        # Fallback to internal registry access
        info = _find_microglia_widget()
        if not info:
            print("[launcher] Could not locate a 'Microglia Analyzer' dock widget. Ensure the plugin is installed.")
            print("           Launching plain viewer; use Plugins -> Microglia Analyzer manually.")
            napari.run()
            return
        plugin_name, widget_name, factory = info
        try:
            widget_instance = factory(viewer)
        except Exception as e:
            print(f"[launcher] Failed to instantiate widget '{plugin_name}:{widget_name}': {e}")
            napari.run()
            return
        try:
            viewer.window.add_dock_widget(widget_instance, name=widget_name, area='right')
            print(f"[launcher] Added dock widget {plugin_name}:{widget_name} (internal registry)")
        except Exception as e:  # pragma: no cover
            print(f"[launcher] Failed adding dock widget: {e}")

    # At this point widget_instance may still be None if everything failed
    if widget_instance is None:
        napari.run()
        return

    # Attempt auto-directory injection
    print("[launcher] Use the 'Sources Folder' button inside the Microglia Analyzer 'Media Control' panel to choose:")
    print(f"           {egfp_dir if egfp_dir.exists() else '<your EGFP projections directory>'}")

    napari.run()


if __name__ == '__main__':
    try:
        launch()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
