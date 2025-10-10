"""配置加载器（简化版本）

变更说明：
- 仅支持一种清晰的配置格式（废弃 `credentials` 与旧版 OpenI 单站点格式）。
- 不再进行环境变量回退，只从 `config/users.json` 读取。
- 站点级配置从 `data["sites"][site]` 读取，全局默认从 `data["defaults"]` 读取。

新格式示例：
{
  "users": [
    {"site": "openi", "username": "xxx", "password": "xxx"},
    {"site": "linuxdo", "email": "xxx", "password": "xxx"},
    {"site": "anyrouter", "email": "xxx", "password": "xxx"}
  ],
  "defaults": {
    "cookie_expire_days": 30,
    "headless": true
  },
  "sites": {
    "openi": {"task_name": "image", "run_duration": 15}
  }
}

说明：为兼容旧调用处，保留 `get_credentials(site, index, fallback_env=True)` 签名，
但 `fallback_env` 将被忽略（不再使用环境变量回退）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.core.paths import get_project_paths


def _normalize_site(site: str) -> str:
    return (site or "").strip().lower()


class UnifiedConfigManager:
    """统一配置管理器（仅支持 users + defaults + sites）。"""

    def __init__(self, config_file: str = "users.json") -> None:
        self._config_file: str = config_file
        self._config_path: Path = get_project_paths().config / config_file
        self._data: Optional[Dict] = None  # 首次访问时加载并缓存

    # 公共 API -----------------------------------------------------------
    def get_credentials(self, site: str, index: int = 0, fallback_env: bool = True) -> Dict:
        """返回指定站点的一条凭据记录（不再回退环境变量）。

        为兼容旧调用，`fallback_env` 参数保留但无效。若未找到则返回空字典。
        """
        key = _normalize_site(site)
        users = self.get_all_users(key)
        if 0 <= index < len(users):
            return dict(users[index] or {})
        return {}

    def get_all_users(self, site: str) -> List[Dict]:
        """返回某站点的全部用户，仅支持 users 数组格式。"""
        data = self._load_once()
        key = _normalize_site(site)
        users = data.get("users") if isinstance(data, dict) else None
        if not isinstance(users, list):
            return []
        return [u for u in users if isinstance(u, dict) and _normalize_site(u.get("site", "")) == key]

    def get_site_config(self, site: str) -> Dict:
        """返回站点级配置，从 data["sites"][site] 读取，不存在返回空字典。"""
        data = self._load_once()
        key = _normalize_site(site)
        sites = data.get("sites") if isinstance(data, dict) else None
        if isinstance(sites, dict) and isinstance(sites.get(key), dict):
            return dict(sites[key])
        return {}

    def get_defaults(self) -> Dict:
        """返回全局默认配置（data["defaults"]）。"""
        data = self._load_once()
        defaults = data.get("defaults") if isinstance(data, dict) else None
        return dict(defaults) if isinstance(defaults, dict) else {}

    # 内部实现 -----------------------------------------------------------
    def _load_once(self) -> Dict:
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
            # JSON 不合法时返回空结构（不再提供环境变量回退）
            self._data = {}
        return self._data


__all__ = ["UnifiedConfigManager"]

