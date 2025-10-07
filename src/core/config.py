"""所有站点的统一配置加载器。

本模块提供单一类 `UnifiedConfigManager`，从 `config/users.json` 加载
各站点的凭据和配置，并提供带有环境变量回退的轻量访问器以保持向后兼容性。

支持的格式
----------
基于站点的 users 格式（唯一支持格式）:
{
  "config": {
    "task_name": "image",
    "run_duration": 15,
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 30
  },
  "users": [
    {"site": "openi", "username": "u", "password": "p"},
    {"site": "linuxdo", "email": "e", "password": "p"},
    {"site": "anyrouter", "email": "e", "password": "p"}
  ]
}

环境变量回退
------------
- linuxdo:   `LINUXDO_EMAIL`, `LINUXDO_PASSWORD`
- anyrouter: `ANYROUTER_EMAIL`, `ANYROUTER_PASSWORD`，若未设置则回退到
             `LINUXDO_EMAIL`, `LINUXDO_PASSWORD`
- openi:     `OPENI_USERNAME`, `OPENI_PASSWORD`（可选便利项）

设计说明
--------
- 每个进程最多读取一次配置并进行缓存，以满足性能约束。
- 不引入外部依赖；I/O 使用标准库完成。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.core.paths import get_project_paths


class UnifiedConfigManager:
    """用于凭据和各站点设置的统一配置管理器。

    该管理器会读取一次 `config/users.json`，并为支持的站点（"openi"、"linuxdo"、"anyrouter"）
    提供凭据与配置。

    如果文件缺失或某站点没有条目，方法会回退到环境变量以保持向后兼容。

    实例是轻量级的；加载的数据在实例级缓存。创建一个实例并在需要处复用即可。
    """

    def __init__(self, config_file: str = "users.json") -> None:
        self._config_file: str = config_file
        self._config_path: Path = get_project_paths().config / config_file
        self._data: Optional[Dict] = None  # 首次访问时加载

    # ---- 公共 API -----------------------------------------------------
    def get_credentials(self, site: str, index: int = 0, fallback_env: bool = True) -> Dict:
        """返回指定站点的一条凭据记录。

        参数:
            site:         站点标识，例如 "openi"、"linuxdo"、"anyrouter"（不区分大小写）。
            index:        站点凭据列表中的索引（默认: 0）。
            fallback_env: 为 True 时，当文件凭据不可用或索引越界时，返回基于环境变量的凭据。

        返回:
            凭据字典（例如 openi 为 {"username": ..., "password": ...}，
            linuxdo/anyrouter 为 {"email": ..., "password": ...}）。当未找到且无环境回退时返回空字典。
        """
        key = _normalize_site(site)
        creds = self.get_all_users(key)
        if 0 <= index < len(creds):
            return dict(creds[index] or {})
        if fallback_env:
            env = _env_credentials(key)
            return env if env else {}
        return {}

    def get_all_users(self, site: str) -> List[Dict]:
        """从文件返回某站点的全部凭据记录。

        仅支持新格式：users = [{"site": "openi", ...}, ...]
        
        这里不考虑环境变量；若需带环境回退的单条记录，请使用 `get_credentials()`。
        """
        data = self._load_once()
        key = _normalize_site(site)
        if not data:
            return []

        # 从 users 数组按 site 字段过滤
        users = data.get("users")
        if not isinstance(users, list):
            return []

        return [
            u for u in users
            if isinstance(u, dict) and _normalize_site(u.get("site", "")) == key
        ]

    def get_site_config(self, site: str) -> Dict:
        """返回全局配置字典。

        新格式中，config 为全局配置，所有站点共享。

        缺失时返回空字典。
        """
        data = self._load_once()
        if not data:
            return {}

        cfg = data.get("config")
        if isinstance(cfg, dict):
            return dict(cfg)

        return {}

    # ---- 内部实现 ------------------------------------------------------
    def _load_once(self) -> Dict:
        """从磁盘加载并缓存 JSON 配置。

        若文件不存在或无法解析，则返回空字典。
        """
        if self._data is not None:
            return self._data

        path = self._config_path
        if not path.exists():
            self._data = {}
            return self._data

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._data = data if isinstance(data, dict) else {}
        except Exception:
            # 容错处理：当 JSON 不合法时，允许环境变量回退继续工作
            self._data = {}
        return self._data


# ---- 辅助函数 -------------------------------------------------------------
def _normalize_site(site: str) -> str:
    """将站点标识规范化为小写形式。"""
    return (site or "").strip().lower()


def _env_credentials(site: str) -> Dict:
    """根据站点从环境变量获取凭据。

    各站点对应关系：
    - openi:     OPENI_USERNAME, OPENI_PASSWORD -> {"username", "password"}
    - linuxdo:   LINUXDO_EMAIL,  LINUXDO_PASSWORD -> {"email", "password"}
    - anyrouter: ANYROUTER_EMAIL, ANYROUTER_PASSWORD，若未设置则回退到
                 LINUXDO_EMAIL, LINUXDO_PASSWORD -> {"email", "password"}
    """
    key = _normalize_site(site)

    if key == "openi":
        u = os.getenv("OPENI_USERNAME", "").strip()
        p = os.getenv("OPENI_PASSWORD", "").strip()
        return {"username": u, "password": p} if u and p else {}

    if key == "linuxdo":
        e = os.getenv("LINUXDO_EMAIL", "").strip()
        p = os.getenv("LINUXDO_PASSWORD", "").strip()
        return {"email": e, "password": p} if e and p else {}

    if key == "anyrouter":
        e = os.getenv("ANYROUTER_EMAIL", "").strip()
        p = os.getenv("ANYROUTER_PASSWORD", "").strip()
        if e and p:
            return {"email": e, "password": p}
        # 向后兼容：当前 AnyRouter 通过 LinuxDO OAuth 认证
        e = os.getenv("LINUXDO_EMAIL", "").strip()
        p = os.getenv("LINUXDO_PASSWORD", "").strip()
        return {"email": e, "password": p} if e and p else {}

    return {}


__all__ = [
    "UnifiedConfigManager",
]
