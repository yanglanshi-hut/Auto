"""Cookie management utilities for login automation scripts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from src.core.paths import get_project_paths


class CookieManager:
    """Handle persistence and restoration of browser cookies."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """Initialize the cookie manager.

        If `base_dir` is not provided, defaults to `ProjectPaths.cookies`.
        """
        if base_dir is None:
            self.base_dir = get_project_paths().cookies
        else:
            self.base_dir = Path(base_dir)

    def _cookie_path(self, site_name: str) -> Path:
        return (self.base_dir / f"{site_name}_cookies.json").resolve()

    def _legacy_path(self, site_name: str) -> Path:
        return (self.base_dir / f"{site_name}.json").resolve()

    def _existing_path(self, site_name: str) -> Optional[Path]:
        cookie_path = self._cookie_path(site_name)
        if cookie_path.exists():
            return cookie_path
        legacy_path = self._legacy_path(site_name)
        if legacy_path.exists():
            return legacy_path
        return None

    def get_cookie_path(self, site_name: str) -> Path:
        """Return preferred path, falling back to legacy if it exists."""
        existing = self._existing_path(site_name)
        if existing:
            return existing
        return self._cookie_path(site_name)

    def save_cookies(self, context, site_name: str) -> Path:
        """Persist cookies from the given Playwright context."""
        cookies = context.cookies()
        payload = {
            "cookies": cookies,
            "saved_at": datetime.now().isoformat(),
        }

        cookie_path = self._cookie_path(site_name)
        legacy_path = self._legacy_path(site_name)

        target_path = cookie_path
        if legacy_path.exists() and not cookie_path.exists():
            target_path = legacy_path

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

        # Keep legacy file in sync if both paths are present
        if target_path is cookie_path and legacy_path.exists():
            with legacy_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

        return target_path

    def load_cookies(self, context, site_name: str, expire_days: int = 7) -> bool:
        """Restore cookies into the Playwright context if still valid."""
        cookie_path = self._existing_path(site_name)
        if not cookie_path:
            return False

        try:
            with cookie_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return False

        cookies, saved_at = self._parse_cookie_payload(data, cookie_path)
        if not cookies:
            return False

        if expire_days is not None and saved_at is not None:
            if datetime.now() - saved_at > timedelta(days=expire_days):
                try:
                    cookie_path.unlink()
                except OSError:
                    pass
                return False

        try:
            context.add_cookies(cookies)
        except Exception:
            return False

        return True

    def _parse_cookie_payload(self, data, cookie_path: Path) -> Tuple[list, Optional[datetime]]:
        saved_at: Optional[datetime] = None
        cookies: Optional[list] = None

        if isinstance(data, list):
            cookies = data
        elif isinstance(data, dict):
            cookies = data.get("cookies")
            saved_at_str = data.get("saved_at")
            if isinstance(saved_at_str, str):
                try:
                    saved_at = datetime.fromisoformat(saved_at_str)
                except ValueError:
                    saved_at = None

        if saved_at is None:
            try:
                saved_at = datetime.fromtimestamp(cookie_path.stat().st_mtime)
            except (OSError, ValueError):
                saved_at = None

        return cookies or [], saved_at
