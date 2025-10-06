"""OpenI 自动化的配置辅助工具。"""

from __future__ import annotations

import json
from typing import Dict

from src.core.paths import get_project_paths


def load_config(config_file: str = "users.json") -> Dict:
    """从 `config/` 目录加载 OpenI 的用户/配置文件。

    返回包含键 `users` 与可选键 `config` 的字典。
    """
    config_path = get_project_paths().config / config_file
    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件 {config_path} 不存在！\n"
            f"请复制 config/users.json.example 为 config/users.json 并填写您的账号信息"
        )
    with config_path.open('r', encoding='utf-8') as handle:
        config = json.load(handle)
    if 'users' not in config or not config['users']:
        raise ValueError("配置文件中没有用户信息！")
    return config


__all__ = ["load_config"]

