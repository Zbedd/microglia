#!/usr/bin/env python3
from __future__ import annotations
"""Visualize max projections exactly as produced by the normal pipeline prior
to plugin execution (no additional preprocessing or modification).

This script:
  1. Loads config.
  2. Reuses the standard ND2 processing logic up to (but NOT including) plugin invocation.
     To achieve this we call `process_nd2_file` but with plugin invocation monkey-patched out.
  3. After images are written (mip_egfp.tif / mip_nuc.tif) we optionally display a simple
     read-only summary via napari (same viewer) and/or print file locations.

We DO NOT alter pixel data; we only display what was saved by `save_xy_mips`.

NOTE: We patch the plugin call inside `process_nd2_file` by temporarily replacing
`try_run_plugin` with a no-op that returns False AFTER adding images, preventing
the function from raising due to mandatory plugin requirement. This lets us reuse
all upstream logic without duplication.
"""
from pathlib import Path
from types import SimpleNamespace
import contextlib

from microglia_pipeline.config import load_config
from microglia_pipeline.orchestrate import _collect_nd2_paths, process_nd2_file
from microglia_pipeline import plugin_runner as _plugin_runner_mod
import microglia_pipeline.orchestrate as _orch
from microglia_pipeline.preprocess import ensure_dir

try:  # Fail fast on napari like main pipeline
    import napari  # type: ignore
except Exception as e:  # pragma: no cover
    raise ImportError("The 'napari' package is required. Install it before running.") from e


@contextlib.contextmanager
def _suppress_plugin_and_assertion():
    """Temporarily disable plugin execution & assertion in process_nd2_file.

    We override try_run_plugin to return True (pretend success) and
    save_plugin_outputs to a no-op, plus patch _assert_xy_outputs to skip the
    post-plugin success check. This keeps behavior identical up to plugin
    invocation point without modifying image data or earlier logic.
    """
    orig_try = _plugin_runner_mod.try_run_plugin
    orig_save = _plugin_runner_mod.save_plugin_outputs
    orig_assert = getattr(_orch, '_assert_xy_outputs')
    # orchestrate references imported symbols directly, so capture originals:
    orig_orch_try = getattr(_orch, 'try_run_plugin')
    orig_orch_save = getattr(_orch, 'save_plugin_outputs')

    def fake_try_run_plugin(*a, **k):  # noqa: D401
        # Return True so downstream logic proceeds quietly.
        return True

    def fake_save_plugin_outputs(*a, **k):
        return None

    def fake_assert(*a, **k):
        return None

    _plugin_runner_mod.try_run_plugin = fake_try_run_plugin  # type: ignore
    _plugin_runner_mod.save_plugin_outputs = fake_save_plugin_outputs  # type: ignore
    _orch._assert_xy_outputs = fake_assert  # type: ignore
    _orch.try_run_plugin = fake_try_run_plugin  # type: ignore
    _orch.save_plugin_outputs = fake_save_plugin_outputs  # type: ignore
    try:
        yield
    finally:  # restore
        _plugin_runner_mod.try_run_plugin = orig_try  # type: ignore
        _plugin_runner_mod.save_plugin_outputs = orig_save  # type: ignore
        _orch._assert_xy_outputs = orig_assert  # type: ignore
        _orch.try_run_plugin = orig_orch_try  # type: ignore
        _orch.save_plugin_outputs = orig_orch_save  # type: ignore


def main():
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root / "config.yaml")

    nd2_paths = _collect_nd2_paths(cfg.inputs)

    # We do not want plugin execution; temporarily neutralize it.
    with _suppress_plugin_and_assertion():
        for nd2_path in nd2_paths:
            process_nd2_file(nd2_path, cfg)

    print("Visualization complete. Inspect napari window for the loaded projections.")
    napari.run()


if __name__ == "__main__":  # pragma: no cover
    main()
