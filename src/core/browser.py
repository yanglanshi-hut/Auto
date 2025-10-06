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
            raise RuntimeError("Browser already launched for this manager")

        self._playwright_cm = sync_playwright()
        self._playwright = self._playwright_cm.__enter__()
        return self._playwright.chromium.launch(headless=headless, **launch_kwargs)

    def close(self, browser) -> None:
        """安全地关闭浏览器并停止 Playwright。"""
        try:
            if browser is not None:
                browser.close()
        except Exception as e:
            # 记录日志但不抛出异常——清理应尽力而为
            try:
                from src.core.logger import setup_logger
                from src.core.paths import get_project_paths
                logger = setup_logger("browser", get_project_paths().logs / "browser.log")
                logger.warning(f"Failed to close browser: {e}")
            except Exception:
                pass
        finally:
            if self._playwright_cm is not None:
                try:
                    self._playwright_cm.__exit__(None, None, None)
                except Exception as e:
                    try:
                        from src.core.logger import setup_logger
                        from src.core.paths import get_project_paths
                        logger = setup_logger("browser", get_project_paths().logs / "browser.log")
                        logger.warning(f"Failed to stop Playwright: {e}")
                    except Exception:
                        pass
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
