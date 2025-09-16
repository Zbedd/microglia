#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import traceback
from microglia_pipeline.config import load_config
from microglia_pipeline.orchestrate import (
    _collect_nd2_paths,
    process_nd2_file,
)
from microglia_pipeline.aggregate import aggregate_all
from microglia_pipeline.preprocess import ensure_dir

# Fail-fast import napari here (mirrors orchestrate module behavior if imported directly)
try:
    import napari  # type: ignore
except Exception as e:  # pragma: no cover - import guard
    raise ImportError("The 'napari' package is required. Install it before running.") from e

def main():
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config.yaml"
    cfg = load_config(config_path)

    # Inline former run_from_config behavior
    nd2_paths = _collect_nd2_paths(cfg.inputs)
    ensure_dir(Path(cfg.output_root))
    for nd2_path in nd2_paths:
        process_nd2_file(nd2_path, cfg)

    if cfg.aggregation.write_global_summary:
        aggregate_all(Path(cfg.output_root))

    # keep napari event loop alive for inspection of results
    napari.run()


if __name__ == "__main__":
    main()
