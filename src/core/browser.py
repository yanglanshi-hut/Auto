"""登录自动化脚本的浏览器管理辅助工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright
from src.core.paths import get_project_paths


class BrowserManager:
    """封装 Playwright 浏览器生命周期管理。"""

    def __init__(self) -> None:
        self._playwright_cm = None
        self._playwright = None

    def launch(self, headless: bool = False, **launch_kwargs):
        """启动 Playwright 并启动一个 Chromium 浏览器。"""
        if self._playwright_cm is not None:
            raise RuntimeError("该管理器已启动浏览器")

        self._playwright_cm = sync_playwright()
        self._playwright = self._playwright_cm.__enter__()
        return self._playwright.chromium.launch(headless=headless, **launch_kwargs)

    def _log_warning(self, message: str) -> None:
        """安全地记录警告日志"""
        try:
            from src.core.logger import setup_logger
            from src.core.paths import get_project_paths
            logger = setup_logger("browser", get_project_paths().logs / "browser.log")
            logger.warning(message)
        except Exception:
            pass

    def close(self, browser) -> None:
        """安全地关闭浏览器并停止 Playwright。"""
        try:
            if browser is not None:
                browser.close()
        except Exception as e:
            self._log_warning(f"关闭浏览器失败: {e}")
        finally:
            if self._playwright_cm is not None:
                try:
                    self._playwright_cm.__exit__(None, None, None)
                except Exception as e:
                    self._log_warning(f"停止 Playwright 失败: {e}")
                self._playwright_cm = None
                self._playwright = None

    def save_error_screenshot(self, page, filename: Optional[str]) -> bool:
        """捕获截图以便排查故障。"""
        if page is None or not filename:
            return False

        try:
            path = Path(filename)
            if not path.is_absolute():
                path = (get_project_paths().screenshots / path).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(path))
            return True
        except Exception:
            return False
