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
class PluginConfig:
    enabled: bool = True                 # must be True; plugin is mandatory
    plugin_name: str = "microglia-analyzer"
    launch_gui: bool = True              # viewer is required and will be shown
    command_ids: List[str] = field(default_factory=list)

@dataclass
class AggregationConfig:
    write_global_summary: bool = True

@dataclass
class VisualizeConfig:
    enabled: bool = False                 # Off by default; script can ignore if absent
    number_of_examples: int = 4            # How many XY positions to visualize
    random_sample: bool = True             # If more positions than requested, sample randomly
    save_grid: bool = True                 # Save a montage/grid image
    save_individual: bool = True           # Save individual EGFP + nuclei MIPs

@dataclass
class Config:
    inputs: List[str]
    output_root: str = "results"
    channels: ChannelsConfig = field(default_factory=ChannelsConfig)
    preprocessing: PreprocConfig = field(default_factory=PreprocConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    visualize: VisualizeConfig = field(default_factory=VisualizeConfig)

def load_config(path: str | Path) -> Config:
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    cfg = Config(
        inputs=data.get("inputs", []),
        output_root=data.get("output_root", "results"),
        channels=ChannelsConfig(**data.get("channels", {})),
        preprocessing=PreprocConfig(**data.get("preprocessing", {})),
        plugin=PluginConfig(**data.get("plugin", {})),
        aggregation=AggregationConfig(**data.get("aggregation", {})),
        visualize=VisualizeConfig(**data.get("visualize", {})),
    )
    # Fail-fast validation
    if not cfg.inputs:
        raise ValueError("config.inputs is required and cannot be empty.")
    if cfg.preprocessing.projection.lower() != "max":
        raise ValueError("Only 'max' projection is supported.")
    if not cfg.plugin.enabled:
        raise ValueError("plugin.enabled must be true (plugin is mandatory).")
    if not cfg.channels.egfp_keywords:
        raise ValueError("channels.egfp_keywords must be a non-empty list.")
    if not cfg.channels.nuc_keywords:
        raise ValueError("channels.nuc_keywords must be a non-empty list.")
    return cfg
