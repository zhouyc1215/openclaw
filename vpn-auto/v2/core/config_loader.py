#!/usr/bin/env python3
"""
配置加载器
"""

import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'config.yaml'


def load_config(config_path=None):
    """加载配置文件"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config
