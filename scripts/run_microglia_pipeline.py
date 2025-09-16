#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import traceback
from microglia_pipeline.config import load_config
from microglia_pipeline.orchestrate import run_from_config

def main():
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config.yaml"
    cfg = load_config(config_path)
    
    run_from_config(cfg)


if __name__ == "__main__":
    main()
