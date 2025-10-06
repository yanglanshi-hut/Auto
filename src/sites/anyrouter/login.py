"""AnyRouter 登录自动化脚本"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

# 统一通过 `python -m src` 启动，无需修改 sys.path

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.core.config import UnifiedConfigManager

logger = setup_logger("anyrouter", get_project_paths().logs / "anyrouter.log")


class AnyrouterLogin(LoginAutomation):
    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('anyrouter', headless=headless)
        # 确保调试目录存在
        self.debug_dir = get_project_paths().screenshots / "anyrouter_debug"
        try:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _shot(self, page: Page, name: str) -> None:
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = self.debug_dir / f"{ts}_{name}.png"
            page.screenshot(path=str(path), full_page=True)
            logger.info(f"Saved screenshot: {path}")
        except Exception as exc:
            logger.warning(f"Screenshot failed ({name}): {exc}")

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
    ) -> bool:
        cookie_path = self.cookie_manager.get_cookie_path(self.site_name)
        if not cookie_path.exists():
            logger.info(f"Cookie file not found: {cookie_path}")
            return False

        logger.info("Try cookie login...")
        success = super().try_cookie_login(page, verify_url=verify_url, expire_days=expire_days)
        if success:
            logger.info("Cookie login success")
        else:
            logger.info("Cookie expired; re-login required")
        return success

    def verify_login(self, page: Page) -> bool:
        try:
            if '/console' in page.url:
                logger.info("Logged in (console)")
                return True

            if page.locator('button:has-text("linuxdo_")').count() > 0:
                logger.info("Logged in (user detected)")
                return True

            if '/login' in page.url or page.url == 'https://anyrouter.top/':
                if page.locator('button:has-text("使用 LinuxDO 登录")').count() > 0:
                    logger.info("Not logged in (login page)")
                    return False

            return False
        except Exception as exc:
            logger.warning(f"Verify login error: {exc}")
            return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """LinuxDO OAuth 登录主流程编排。"""
        logger.info("Login with LinuxDO OAuth...")
        try:
            if not self._navigate_to_login_page(page):
                return False

            self._close_announcement_modal(page)

            if not self._click_oauth_button(page):
                return False

            auth_page = self._find_linuxdo_auth_page(page)
            if not auth_page:
                return False

            if not self._fill_linuxdo_credentials_if_needed(auth_page, page):
                return False

            # 提交凭据后，优先尝试早期验证是否已经回到 AnyRouter
            try:
                logger.info(f"Post-login check on AnyRouter page. URL: {page.url}")
                if 'anyrouter.top' in page.url and self.verify_login(page):
                    logger.info("Login appears successful after credentials submission")
                    return True
            except Exception as exc:
                logger.info(f"Post-login early check error: {exc}")

            self._handle_oauth_consent(auth_page)

            page.bring_to_front()
            logger.info("Brought AnyRouter page to front for final verification")
            ok = self.verify_login(page)
            if not ok:
                logger.info("Final verification failed; capturing AnyRouter page state")
                self._shot(page, 'final_verification_failed')
            else:
                logger.info("Final verification succeeded")
            return ok
        except Exception as exc:
            logger.error(f"登录过程出错: {exc}")
            self._save_error_screenshot(page, 'anyrouter_oauth_exception')
            return False

    # 辅助方法拆分（每个保持单一职责与短小）
    def _navigate_to_login_page(self, page: Page) -> bool:
        try:
            logger.info("Navigating to login page: https://anyrouter.top/login")
            page.goto('https://anyrouter.top/login', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            logger.info(f"Loaded login page. URL: {page.url}")
            try:
                logger.info(f"Login page title: {page.title()}")
            except Exception as exc:
                logger.info(f"Failed to get page title: {exc}")
            self._shot(page, 'after_goto_login')

            # 首次进入登录页后立刻刷新一次，规避首次点击 OAuth 按钮无响应的问题
            try:
                logger.info("Refreshing login page to stabilize OAuth button...")
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(300)
                try:
                    title = page.title()
                except Exception:
                    title = "<no title>"
                logger.info(f"After refresh. URL: {page.url}, Title: {title}")
                self._shot(page, 'after_refresh_login')
            except Exception as exc:
                logger.info(f"Refresh failed: {exc}")
            return True
        except Exception as exc:
            logger.error(f"Navigate to login page failed: {exc}")
            return False

    def _close_announcement_modal(self, page: Page) -> None:
        try:
            logger.info("Checking for announcement modal...")
            closed_announcement = False
            for name in ('关闭公告', '今日关闭', '关闭'):
                try:
                    logger.info(f"Attempt closing announcement with button: {name}")
                    page.get_by_role('button', name=name).click(timeout=1500)
                    page.wait_for_timeout(500)
                    closed_announcement = True
                    logger.info("Announcement closed")
                    break
                except Exception as exc:
                    logger.info(f"No announcement button '{name}' or click failed: {exc}")
                    continue
            if not closed_announcement:
                logger.info("No announcement modal detected.")
        except Exception as exc:
            logger.info(f"Announcement close handling error: {exc}")

    def _click_oauth_button(self, page: Page) -> bool:
        clicked = False
        actions = [
            ("get_by_role('button', name='使用 LinuxDO 继续')", lambda: page.get_by_role('button', name='使用 LinuxDO 继续').click(timeout=5000)),
            ("get_by_role('button', name='使用 LinuxDO 登录')", lambda: page.get_by_role('button', name='使用 LinuxDO 登录').click(timeout=5000)),
            ("get_by_role('link', name='使用 LinuxDO 继续')", lambda: page.get_by_role('link', name='使用 LinuxDO 继续').click(timeout=5000)),
            ("get_by_text('使用 LinuxDO 继续')", lambda: page.get_by_text('使用 LinuxDO 继续').click(timeout=5000)),
            ("get_by_text('使用 LinuxDO 登录')", lambda: page.get_by_text('使用 LinuxDO 登录').click(timeout=5000)),
            ("locator('button:has-text(\"LinuxDO\")').first", lambda: page.locator('button:has-text("LinuxDO")').first.click(timeout=5000)),
        ]
        try:
            logger.info(f"Pages before click: {len(page.context.pages)}")
        except Exception:
            pass
        self._shot(page, 'before_oauth_click')
        for desc, action in actions:
            try:
                logger.info(f"Trying OAuth button selector: {desc}")
                action()
                clicked = True
                logger.info("OAuth button clicked successfully")
                try:
                    logger.info(f"Tabs currently open: {len(page.context.pages)}")
                except Exception:
                    pass
                self._shot(page, 'after_oauth_click')
                break
            except Exception as e:
                logger.info(f"OAuth click attempt failed with selector: {desc}. Error: {e}")
                continue
        if not clicked:
            try:
                debug_dir = Path('.playwright-debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = debug_dir / f"anyrouter_oauth_click_failed_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Saved screenshot: {screenshot_path}")
            except Exception:
                pass
            logger.warning("Failed to click any OAuth button; aborting login")
            return False
        return True

    def _find_linuxdo_auth_page(self, page: Page) -> Optional[Page]:
        auth_page = None
        pages_after = list(page.context.pages)
        try:
            logger.info(f"Pages after click: {len(pages_after)}")
        except Exception:
            pass
        for idx, candidate in enumerate(pages_after, start=1):
            try:
                url = candidate.url
                logger.info(f"Inspecting page[{idx}] URL: {url}")
                if 'linux.do' in url:
                    auth_page = candidate
                    logger.info(f"LinuxDO auth page detected at page[{idx}]")
                    break
            except Exception as exc:
                logger.info(f"Error inspecting page[{idx}]: {exc}")
                continue
        if not auth_page:
            logger.warning("No LinuxDO auth page found in tabs")
            try:
                debug_dir = Path('.playwright-debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = debug_dir / f"anyrouter_oauth_no_auth_tab_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Saved screenshot: {screenshot_path}")
            except Exception:
                pass
            return None

        auth_page.bring_to_front()
        logger.info("Brought LinuxDO auth page to front")
        auth_page.wait_for_load_state('domcontentloaded')
        try:
            logger.info(f"Auth page loaded. URL: {auth_page.url}")
        except Exception:
            pass
        self._shot(auth_page, 'auth_page_loaded')
        return auth_page

    def _fill_linuxdo_credentials_if_needed(self, auth_page: Page, page: Page) -> bool:
        # 仅在出现登录表单时填写凭据
        if auth_page.locator('#login-account-name, input[name="login"]').count() == 0:
            return True

        # 优先从统一配置管理器获取凭据，保持环境变量回退
        email = ''
        password = ''
        try:
            config_mgr = UnifiedConfigManager()
            creds = config_mgr.get_credentials('anyrouter', fallback_env=True)
            email = creds.get('email', '')
            password = creds.get('password', '')
        except Exception:
            # 兜底：直接从环境变量读取（支持 ANYROUTER_* 或 LINUXDO_*）
            import os
            email = os.getenv('ANYROUTER_EMAIL') or os.getenv('LINUXDO_EMAIL', '')
            password = os.getenv('ANYROUTER_PASSWORD') or os.getenv('LINUXDO_PASSWORD', '')

        if not email or not password:
            logger.error("未提供 LinuxDO/AnyRouter 凭据")
            logger.error("请设置 ANYROUTER_EMAIL/ANYROUTER_PASSWORD 或 LINUXDO_EMAIL/LINUXDO_PASSWORD")
            return False

        try:
            logger.info("Auth page appears to be login form; attempting to focus/login button first")
            auth_page.locator('#login-button').click()
            auth_page.wait_for_timeout(500)
        except Exception as exc:
            logger.info(f"Initial login button click ignored/failed: {exc}")
        self._shot(auth_page, 'before_fill_credentials')
        auth_page.locator('#login-account-name, input[name="login"]').first.fill(email)
        pwd = auth_page.locator('#login-account-password, input[name="password"]').first
        pwd.fill(password)
        try:
            logger.info("Submitting login form via submit button")
            auth_page.locator('form:has(#login-account-name) button[type="submit"]').first.click()
        except Exception as exc:
            logger.info(f"Submit button click failed: {exc}; pressing Enter in password field")
            pwd.press('Enter')
        auth_page.wait_for_timeout(2000)
        self._shot(auth_page, 'after_submit_credentials')

        return True

    def _handle_oauth_consent(self, auth_page: Page) -> None:
        try:
            try:
                cb = auth_page.get_by_role('checkbox', name='记住这次授权')
                if cb.is_visible(timeout=2000):
                    logger.info("Checking 'remember this authorization' checkbox")
                    cb.check()
            except Exception as exc:
                logger.info(f"No 'remember authorization' checkbox or check failed: {exc}")
            for action in (
                lambda: auth_page.get_by_role('link', name='允许').click(),
                lambda: auth_page.get_by_role('button', name='允许').click(),
                lambda: auth_page.get_by_text('允许').click(),
            ):
                try:
                    logger.info("Clicking 'Allow' on OAuth consent page")
                    action()
                    self._shot(auth_page, 'after_click_allow')
                    break
                except Exception as exc:
                    logger.warning(f"Consent click attempt failed: {exc}")
                    continue
        except Exception as exc:
            logger.warning(f"OAuth consent handling error: {exc}")

    def _save_error_screenshot(self, page: Page, name: str) -> None:
        """保存错误截图的辅助方法"""
        try:
            debug_dir = Path('.playwright-debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = debug_dir / f"{name}_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Saved screenshot: {screenshot_path}")
        except Exception:
            pass

    def do_login(self, page: Page, **_credentials) -> bool:
        return self.login_with_linuxdo_oauth(page)

    def after_login(self, page: Page, **_credentials) -> None:
        try:
            if '/console/token' not in page.url:
                page.goto('https://anyrouter.top/console/token', timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(2000)
            page.wait_for_load_state('networkidle')
        except Exception as exc:
            logger.error(f"登录后处理异常: {exc}")


def login_to_anyrouter(*, use_cookie: bool = True, headless: bool = False) -> bool:
    automation = AnyrouterLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://anyrouter.top/console/token',
        )
    except Exception as exc:
        logger.error(f"运行异常: {exc}")
        return False


if __name__ == "__main__":
    USE_COOKIE = True
    HEADLESS = False

    login_to_anyrouter(
        use_cookie=USE_COOKIE,
        headless=HEADLESS,
    )
