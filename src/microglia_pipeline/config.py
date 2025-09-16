from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import yaml

@dataclass
class ChannelsConfig:
    egfp_keywords: List[str] = field(default_factory=lambda: ["egfp", "gfp"])
    nuc_keywords:  List[str] = field(default_factory=lambda: ["bfp", "sgbfp", "dapi", "nuc"])

@dataclass
class PreprocConfig:
    projection: str = "max"  # only 'max' supported

@dataclass
class Config:
    inputs: List[str]
    output_root: str = "results"
    channels: ChannelsConfig = field(default_factory=ChannelsConfig)
    preprocessing: PreprocConfig = field(default_factory=PreprocConfig)

def load_config(path: str | Path) -> Config:
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    cfg = Config(
        inputs=data.get("inputs", []),
        output_root=data.get("output_root", "results"),
        channels=ChannelsConfig(**data.get("channels", {})),
        preprocessing=PreprocConfig(**data.get("preprocessing", {})),
    )
    # Fail-fast validation
    if not cfg.inputs:
        raise ValueError("config.inputs is required and cannot be empty.")
    if cfg.preprocessing.projection.lower() != "max":
        raise ValueError("Only 'max' projection is supported.")
    if not cfg.channels.egfp_keywords:
        raise ValueError("channels.egfp_keywords must be a non-empty list.")
    if not cfg.channels.nuc_keywords:
        raise ValueError("channels.nuc_keywords must be a non-empty list.")
    return cfg
