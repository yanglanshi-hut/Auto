"""登录自动化脚本的 Cookie 管理工具。"""

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

        若未提供 `base_dir`，则默认使用 `ProjectPaths.cookies`。
        """
        if base_dir is None:
            self.base_dir = get_project_paths().cookies
        else:
            self.base_dir = Path(base_dir)

        # 首次初始化时自动迁移旧格式 Cookie 文件
        self._migrate_legacy_cookies_once()

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
        """返回首选路径，若存在旧版路径则回退使用。"""
        existing = self._existing_path(site_name)
        if existing:
            return existing
        return self._cookie_path(site_name)

    def save_cookies(self, context, site_name: str) -> Path:
        """持久化保存来自指定 Playwright 上下文的 cookies。"""
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

        # 若两个路径同时存在，则保持旧版文件同步
        if target_path is cookie_path and legacy_path.exists():
            with legacy_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

        return target_path

    def load_cookies(self, context, site_name: str, expire_days: int = 7) -> bool:
        """若仍然有效，则将 cookies 恢复到 Playwright 上下文。"""
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

    def _migrate_legacy_cookies_once(self) -> None:
        """自动迁移旧格式 Cookie 文件（*.json → *_cookies.json）

        只在首次初始化时执行一次，使用标记文件避免重复扫描。
        """
        try:
            # 使用标记文件避免每次都扫描目录
            marker = self.base_dir / ".cookies_migrated"
            if marker.exists():
                return

            if not self.base_dir.exists():
                return

            # 扫描旧格式 Cookie 文件
            migrated_count = 0
            for old_path in self.base_dir.glob("*.json"):
                # 跳过已经是新格式的文件
                if old_path.stem.endswith("_cookies"):
                    continue

                # 跳过标记文件
                if old_path.name.startswith("."):
                    continue

                # 构建新路径
                site_name = old_path.stem
                new_path = self.base_dir / f"{site_name}_cookies.json"

                # 如果新路径已存在，跳过（避免覆盖）
                if new_path.exists():
                    continue

                # 重命名文件
                try:
                    old_path.rename(new_path)
                    migrated_count += 1
                except Exception:
                    # 迁移失败不影响程序运行
                    pass

            # 创建标记文件
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()

            if migrated_count > 0:
                # 可选：记录迁移日志
                try:
                    from src.core.logger import setup_logger
                    logger = setup_logger("cookies", get_project_paths().logs / "cookies.log")
                    logger.info(f"已自动迁移 {migrated_count} 个 Cookie 文件到新格式")
                except Exception:
                    pass
        except Exception:
            # 静默失败，不影响 CookieManager 正常工作
            pass
