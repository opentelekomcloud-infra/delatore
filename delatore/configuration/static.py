"""Configurations fixed for library"""
from dataclasses import dataclass
from typing import Dict, List, Type

import yaml
from ocomone import Resources


@dataclass(frozen=True)
class Configuration:
    """Base configuration class"""
    name: str
    params: dict

    @classmethod
    def from_yaml(cls, src):
        return cls(**src)


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

    @classmethod
    def from_yaml(cls, src: dict):
        src['timings'] = Timings(**src['timings'])
        return super().from_yaml(src)


_CONFIGS = Resources(__file__)
_SOURCES_CFG_FILE = _CONFIGS['sources.yaml']
_OUTPUTS_CFG_FILE = _CONFIGS['outputs.yaml']


def _load_configuration(cfg_file: str, cfg_class: Type[Configuration]) -> Dict[str, Configuration]:
    with open(cfg_file, 'r') as src_cfg:
        configs = yaml.safe_load(src_cfg)
    result = {cfg['name']: cfg_class.from_yaml(cfg) for cfg in configs}
    return result


SOURCES_CFG = _load_configuration(_SOURCES_CFG_FILE, SourceConfiguration)
OUTPUTS_CFG = _load_configuration(_OUTPUTS_CFG_FILE, OutputConfiguration)
