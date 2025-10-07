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

    def get_cookie_path(self, site_name: str) -> Path:
        """返回 Cookie 文件路径（优先新格式，向后兼容旧格式）。"""
        # 新格式路径
        cookie_path = (self.base_dir / f"{site_name}_cookies.json").resolve()
        if cookie_path.exists():
            return cookie_path
        
        # 向后兼容：检查旧格式路径
        legacy_path = (self.base_dir / f"{site_name}.json").resolve()
        if legacy_path.exists():
            return legacy_path
        
        # 默认返回新格式路径
        return cookie_path

    def save_cookies(self, context, site_name: str, metadata: Optional[dict] = None) -> Path:
        """持久化保存来自指定 Playwright 上下文的 cookies。
        
        Args:
            context: Playwright 浏览器上下文
            site_name: 站点名称
            metadata: 可选的元数据，如 {"login_type": "credentials", "email": "user@example.com"}
        """
        cookies = context.cookies()
        payload = {
            "cookies": cookies,
            "saved_at": datetime.now().isoformat(),
        }
        
        # 添加元数据
        if metadata:
            payload.update(metadata)

        # 始终使用新格式保存
        cookie_path = (self.base_dir / f"{site_name}_cookies.json").resolve()
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        with cookie_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

        return cookie_path

    def load_cookies(
        self, 
        context, 
        site_name: str, 
        expire_days: int = 7,
        required_metadata: Optional[dict] = None
    ) -> bool:
        """若仍然有效，则将 cookies 恢复到 Playwright 上下文。
        
        Args:
            context: Playwright 浏览器上下文
            site_name: 站点名称
            expire_days: Cookie 有效天数
            required_metadata: 必需的元数据匹配，如 {"login_type": "credentials", "email": "user@example.com"}
        
        Returns:
            True 表示成功加载，False 表示失败或不匹配
        """
        cookie_path = self.get_cookie_path(site_name)
        if not cookie_path.exists():
            return False

        try:
            with cookie_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return False

        # 检查元数据是否匹配
        if required_metadata:
            if not self._check_metadata_match(data, required_metadata):
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
    
    def _check_metadata_match(self, data: dict, required_metadata: dict) -> bool:
        """检查 Cookie 元数据是否匹配要求。"""
        for key, required_value in required_metadata.items():
            stored_value = data.get(key)
            if stored_value != required_value:
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
