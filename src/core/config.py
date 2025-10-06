"""所有站点的统一配置加载器。

本模块提供单一类 `UnifiedConfigManager`，从 `config/users.json` 加载
各站点的凭据和配置，并提供带有环境变量回退的轻量访问器以保持向后兼容性。

支持的格式
----------
1) 基于站点的 users 格式（推荐 - 最简洁）:
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

2) 统一凭据格式（向后兼容）:
   {
     "credentials": {
       "openi":    [{"username": "u", "password": "p"}],
       "linuxdo":  [{"email": "e", "password": "p"}],
       "anyrouter": [{"email": "e", "password": "p"}]
     },
     "config": {
       "openi": {"task_name": "image", "run_duration": 15, ...},
       "linuxdo": {"cookie_expire_days": 30},
       "anyrouter": {"cookie_expire_days": 30}
     }
   }

3) 旧版 OpenI 格式（向后兼容）:
   {
     "users":  [{"username": "u", "password": "p"}],
     "config": {"task_name": "image", "run_duration": 15, ...}
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

    def _get_from_credentials_format(self, data: Dict, site: str) -> List[Dict]:
        """格式 1：从 credentials[site] 获取凭据"""
        creds = data.get("credentials")
        if not isinstance(creds, dict):
            return []
        items = creds.get(site)
        return list(items) if isinstance(items, list) else []

    def _get_from_users_format(self, users: List, site: str) -> List[Dict]:
        """格式 2：从 users 数组按 site 字段过滤"""
        return [
            u for u in users
            if isinstance(u, dict) and _normalize_site(u.get("site", "")) == site
        ]

    def _get_from_legacy_openi_format(self, users: List, site: str) -> List[Dict]:
        """格式 3：旧版 OpenI 格式（无 site 字段）"""
        if site != "openi":
            return []
        has_site_field = any(isinstance(u, dict) and "site" in u for u in users)
        return [] if has_site_field else list(users)

    def get_all_users(self, site: str) -> List[Dict]:
        """仅从文件返回某站点的全部凭据记录。

        支持三种格式：
        1. 统一格式：credentials[site] = [...]
        2. 按站点划分的 users 格式：users = [{"site": "openi", ...}, ...]
        3. 旧版 OpenI 格式：users = [{"username": ..., "password": ...}]（无 site 字段）

        这里不考虑环境变量；若需带环境回退的单条记录，请使用 `get_credentials()`。
        """
        data = self._load_once()
        key = _normalize_site(site)
        if not data:
            return []

        # 格式 1：统一凭据格式
        result = self._get_from_credentials_format(data, key)
        if result:
            return result

        # 格式 2 与 3：users 数组
        users = data.get("users")
        if not isinstance(users, list):
            return []

        # 格式 2：按站点划分
        result = self._get_from_users_format(users, key)
        if result:
            return result

        # 格式 3：旧版 OpenI
        return self._get_from_legacy_openi_format(users, key)

    def get_site_config(self, site: str) -> Dict:
        """返回站点级的配置字典。

        在统一格式中，若存在则返回 `config[site]`；在旧版 OpenI 格式中，
        当 `site == 'openi'` 时返回顶层 `config`。

        缺失时返回空字典。
        """
        data = self._load_once()
        key = _normalize_site(site)
        if not data:
            return {}

        # 统一格式：config 是 site -> options 的映射
        cfg = data.get("config")
        if isinstance(cfg, dict):
            # 若存在统一结构，优先返回站点专属配置
            if key in cfg and isinstance(cfg[key], dict):
                return dict(cfg[key])
            # 旧版 OpenI：顶层 config，无站点作用域
            if key == "openi" and "credentials" not in data and "users" in data:
                return dict(cfg) if isinstance(cfg, dict) else {}

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
