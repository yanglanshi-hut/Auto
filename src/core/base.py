"""登录自动化脚本共享的基类

变更说明：
- 修复所有裸 `except Exception: pass`，统一记录警告日志以便排查问题。
- 将 `cookie_expire_days` 默认值从 7 改为 30 天。
- 引入项目内置 `logger`，为不同站点创建独立日志文件。
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.sync_api import Page

from src.core.browser import BrowserManager
from src.core.cookies import CookieManager
from src.core.logger import setup_logger
from src.core.paths import get_project_paths


class LoginAutomation(abc.ABC):
    """交互式登录流程的通用编排逻辑。"""

    def __init__(
        self,
        site_name: str,
        *,
        headless: bool = False,
        cookie_dir: Optional[Path] = None,
        browser_kwargs: Optional[Dict[str, Any]] = None,
        context_kwargs: Optional[Dict[str, Any]] = None,
        cookie_expire_days: int = 30,  # 默认改为 30 天
    ) -> None:
        self.site_name = site_name
        self.headless = headless
        self.browser_kwargs = browser_kwargs or {}
        self.context_kwargs = context_kwargs or {}
        self.cookie_expire_days = cookie_expire_days

        self.cookie_manager = CookieManager(cookie_dir)
        self.browser_manager = BrowserManager()

        # 初始化站点级日志器：login.<site_name>
        logs_dir = get_project_paths().logs
        self.logger = setup_logger(
            f"login.{site_name}",
            logs_dir / f"login_{site_name}.log",
        )

        self.browser = None
        self.context = None
        self.page = None
        self.logged_in_with_cookies = False

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
    ) -> bool:
        """尝试使用先前保存的 Cookie 进行认证。"""
        effective_expire_days = self.cookie_expire_days if expire_days is None else expire_days

        if not self.cookie_manager.load_cookies(page.context, self.site_name, effective_expire_days):
            return False

        if verify_url:
            try:
                page.goto(verify_url, timeout=60000)
                page.wait_for_load_state("domcontentloaded")
            except Exception as e:  # 记录失败原因，避免静默
                self.logger.warning(f"跳转验证页失败: {e}")
        else:
            try:
                page.reload()
            except Exception as e:
                self.logger.warning(f"页面刷新失败: {e}")

        try:
            page.wait_for_timeout(2000)
        except Exception as e:
            self.logger.warning(f"等待页面稳定失败: {e}")

        return self.verify_login(page)

    @abc.abstractmethod
    def verify_login(self, page: Page) -> bool:
        """当页面反映出已认证的会话时返回 True。"""

    @abc.abstractmethod
    def do_login(self, page: Page, **credentials) -> bool:
        """执行交互式登录流程并返回是否成功。"""

    def after_login(self, page: Page, **credentials) -> None:
        """供子类在登录后执行自动化步骤的钩子。"""

    def run(
        self,
        *,
        use_cookie: bool = True,
        verify_url: Optional[str] = None,
        cookie_expire_days: Optional[int] = None,
        **credentials,
    ) -> bool:
        """执行完整的登录流程。"""
        login_success = False
        self.logged_in_with_cookies = False

        expire_days = self.cookie_expire_days if cookie_expire_days is None else cookie_expire_days

        try:
            self.browser = self.browser_manager.launch(headless=self.headless, **self.browser_kwargs)
            self.context = self.browser.new_context(**self.context_kwargs)
            self.page = self.context.new_page()

            if use_cookie and self.try_cookie_login(self.page, verify_url=verify_url, expire_days=expire_days):
                login_success = True
                self.logged_in_with_cookies = True
            else:
                login_success = self.do_login(self.page, **credentials)
                self.logged_in_with_cookies = False
                if login_success and use_cookie:
                    self.cookie_manager.save_cookies(self.context, self.site_name)

            if login_success:
                self.after_login(self.page, **credentials)

            return login_success
        except Exception:
            # 保持原有行为：保存错误截图并向上传播异常
            self.browser_manager.save_error_screenshot(self.page, self._error_screenshot_path())
            raise
        finally:
            try:
                if self.context is not None:
                    self.context.close()
            except Exception as e:
                # 关闭上下文失败也需要可见日志
                self.logger.warning(f"关闭浏览器上下文失败: {e}")

            self.browser_manager.close(self.browser)
            self.browser = None
            self.context = None
            self.page = None

    def _error_screenshot_path(self) -> str:
        """为失败情况创建一个文件系统安全的截图路径。"""
        safe_name = self.site_name.replace("/", "_").replace("\\", "_")
        screenshots_dir = get_project_paths().screenshots
        return str((screenshots_dir / f"{safe_name}_error_screenshot.png").resolve())

