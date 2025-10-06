"""Unified configuration loader for all sites.

This module provides a single class, `UnifiedConfigManager`, that loads
credentials and per-site configuration from `config/users.json` and offers
lightweight accessors with environment-variable fallbacks for backward
compatibility.

Supported formats
-----------------
1) New unified format (recommended):
   {
     "credentials": {
       "openi":    [{"username": "u", "password": "p"}],
       "linuxdo":  [{"email": "e", "password": "p"}],
       "anyrouter": [{"email": "e", "password": "p"}]
     },
     "config": {
       "openi": {"task_name": "image", "run_duration": 15, ...},
       "linuxdo": {"cookie_expire_days": 7},
       "anyrouter": {"cookie_expire_days": 7}
     }
   }

2) Legacy OpenI format (backward compatible):
   {
     "users":  [{"username": "u", "password": "p"}],
     "config": {"task_name": "image", "run_duration": 15, ...}
   }

Environment fallbacks
---------------------
- linuxdo:   `LINUXDO_EMAIL`, `LINUXDO_PASSWORD`
- anyrouter: `ANYROUTER_EMAIL`, `ANYROUTER_PASSWORD` then fall back to
             `LINUXDO_EMAIL`, `LINUXDO_PASSWORD` if not set
- openi:     `OPENI_USERNAME`, `OPENI_PASSWORD` (optional convenience)

Design notes
------------
- Configuration is read at most once per process and cached for subsequent
  lookups to satisfy the performance constraint.
- No external dependencies are introduced; I/O uses the standard library.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.core.paths import get_project_paths


class UnifiedConfigManager:
    """Unified configuration manager for credentials and per-site settings.

    The manager reads `config/users.json` once and serves credentials and
    configuration for supported sites ("openi", "linuxdo", "anyrouter").

    If the file is missing or a specific site has no entries, methods can fall
    back to environment variables for backward compatibility.

    Instances are lightweight; loaded data is cached per-instance. Create one
    and reuse it where needed.
    """

    def __init__(self, config_file: str = "users.json") -> None:
        self._config_file: str = config_file
        self._config_path: Path = get_project_paths().config / config_file
        self._data: Optional[Dict] = None  # loaded on first access

    # ---- public API -----------------------------------------------------
    def get_credentials(self, site: str, index: int = 0, fallback_env: bool = True) -> Dict:
        """Return a single credential record for a site.

        Parameters:
            site:         Site key, e.g. "openi", "linuxdo", "anyrouter" (case-insensitive).
            index:        Index within the site's credentials list (default: 0).
            fallback_env: When True, return environment-based credentials if file-based
                          credentials are unavailable or out-of-range.

        Returns:
            A credential dict (e.g., {"username": ..., "password": ...} for openi
            or {"email": ..., "password": ...} for linuxdo/anyrouter). Returns an
            empty dict when nothing is found and no environment fallback applies.
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
        """Return all credential records for a site from file only.

        For legacy OpenI configs, the `users` array is returned when `site == "openi"`.
        For the unified format, `credentials[site]` is returned if present.

        Environment variables are NOT considered here; use `get_credentials()`
        for an env-aware single-record fetch.
        """
        data = self._load_once()
        key = _normalize_site(site)
        if not data:
            return []

        # Unified format
        creds = data.get("credentials")
        if isinstance(creds, dict):
            items = creds.get(key)
            return list(items) if isinstance(items, list) else []

        # Legacy OpenI format
        if key == "openi":
            users = data.get("users")
            return list(users) if isinstance(users, list) else []

        return []

    def get_site_config(self, site: str) -> Dict:
        """Return per-site configuration dict.

        In the unified format, this returns `config[site]` if present; in the
        legacy OpenI format, it returns the top-level `config` when `site == 'openi'`.

        Missing entries yield an empty dict.
        """
        data = self._load_once()
        key = _normalize_site(site)
        if not data:
            return {}

        # Unified format: config is a mapping of site -> options
        cfg = data.get("config")
        if isinstance(cfg, dict):
            # If the unified structure exists, prefer specific site config
            if key in cfg and isinstance(cfg[key], dict):
                return dict(cfg[key])
            # Legacy OpenI: top-level config without site-scoping
            if key == "openi" and "credentials" not in data and "users" in data:
                return dict(cfg) if isinstance(cfg, dict) else {}

        return {}

    # ---- internals ------------------------------------------------------
    def _load_once(self) -> Dict:
        """Load and cache the JSON config from disk.

        Returns an empty dict if the file does not exist or cannot be parsed.
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
            # Be tolerant: allow env fallbacks to work when JSON is bad
            self._data = {}
        return self._data


# ---- helpers -------------------------------------------------------------
def _normalize_site(site: str) -> str:
    """Normalize a site identifier to its canonical lowercase form."""
    return (site or "").strip().lower()


def _env_credentials(site: str) -> Dict:
    """Return credentials from environment variables for a specific site.

    Site-specific mapping:
    - openi:     OPENI_USERNAME, OPENI_PASSWORD -> {"username", "password"}
    - linuxdo:   LINUXDO_EMAIL,  LINUXDO_PASSWORD -> {"email", "password"}
    - anyrouter: ANYROUTER_EMAIL, ANYROUTER_PASSWORD, falling back to
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
        # Backward compatible with current AnyRouter implementation which
        # authenticates via LinuxDO OAuth.
        e = os.getenv("LINUXDO_EMAIL", "").strip()
        p = os.getenv("LINUXDO_PASSWORD", "").strip()
        return {"email": e, "password": p} if e and p else {}

    return {}


__all__ = [
    "UnifiedConfigManager",
]

