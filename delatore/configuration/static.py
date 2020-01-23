"""Configurations fixed for library"""
from dataclasses import dataclass
from typing import Dict, List, Type, TypeVar

import yaml
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
class SourceConfiguration(Configuration):
    """Single source service configuration"""
    publishes: str


_CONFIGS = Resources(__file__)
_SOURCES_CFG_FILE = _CONFIGS['sources.yaml']
_OUTPUTS_CFG_FILE = _CONFIGS['outputs.yaml']

T = TypeVar('T', SourceConfiguration, OutputConfiguration)


def _load_configuration(cfg_file: str, cfg_class: Type[T]) -> Dict[str, T]:
    with open(cfg_file, 'r') as src_cfg:
        configs = yaml.safe_load(src_cfg)
    result = {cfg['name']: cfg_class(**cfg) for cfg in configs}
    return result


SOURCES_CFG = _load_configuration(_SOURCES_CFG_FILE, SourceConfiguration)
OUTPUTS_CFG = _load_configuration(_OUTPUTS_CFG_FILE, OutputConfiguration)
