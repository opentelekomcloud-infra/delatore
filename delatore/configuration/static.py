"""Configurations fixed for library"""
from dataclasses import dataclass
from typing import Dict, List

import tyaml
from ocomone import Resources


@dataclass(frozen=True)
class Configuration:
    """Base configuration class"""
    name: str
    params: dict


@dataclass(frozen=True)
class OutputConfiguration(Configuration):
    """Single output service configuration"""
    subscriptions: List[str]


@dataclass(frozen=True)
class Timings:
    polling_interval: float
    request_timeout: float


@dataclass(frozen=True)
class SourceConfiguration(Configuration):
    """Single source service configuration"""
    publishes: str
    timings: Timings


_CONFIGS = Resources(__file__)


def _cfg_load(cfg_file: str, cfg_class):
    with open(cfg_file, 'r') as src_cfg:
        configs = tyaml.load(src_cfg, cfg_class)  # type: List[Configuration]
    result = {cfg.name: cfg for cfg in configs}
    return result


SOURCES_CFG: Dict[str, SourceConfiguration] = _cfg_load(_CONFIGS['sources.yaml'], List[SourceConfiguration])
OUTPUTS_CFG: Dict[str, OutputConfiguration] = _cfg_load(_CONFIGS['outputs.yaml'], List[OutputConfiguration])
