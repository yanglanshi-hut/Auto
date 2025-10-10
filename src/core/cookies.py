"""Cookie 管理工具（已清理 legacy 路径）

变更说明：
- 删除 `_legacy_path()` 与 `_existing_path()`，仅保留统一命名 `{site_name}_cookies.json`。
- 调用方可通过自定义 `site_name`（如 `openi_<username>`）来区分不同账号。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from src.core.paths import get_project_paths


class CookieManager:
    """处理浏览器 Cookie 的持久化与恢复。"""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """初始化 Cookie 管理器。

        若未提供 `base_dir`，默认使用 `ProjectPaths.cookies`。
        """
        self.base_dir = Path(base_dir) if base_dir is not None else get_project_paths().cookies

    def _cookie_path(self, site_name: str) -> Path:
        # 统一文件命名
        return (self.base_dir / f"{site_name}_cookies.json").resolve()

    def get_cookie_path(self, site_name: str) -> Path:
        """返回标准化后的 Cookie 文件路径。"""
        return self._cookie_path(site_name)

    def save_cookies(self, context, site_name: str) -> Path:
        """持久化保存来自指定 Playwright 上下文的 cookies。"""
        cookies = context.cookies()
        payload = {
            "cookies": cookies,
            "saved_at": datetime.now().isoformat(),
        }

        cookie_path = self._cookie_path(site_name)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        with cookie_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

        return cookie_path

    def load_cookies(self, context, site_name: str, expire_days: int = 7) -> bool:
        """若仍有效，则将 cookies 恢复到 Playwright 上下文。"""
        cookie_path = self._cookie_path(site_name)
        if not cookie_path.exists():
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
                # 过期即清理，避免误用
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

