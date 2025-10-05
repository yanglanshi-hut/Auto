"""AnyRouter Login Automation Script"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# 将项目根目录加入 Python 路径（指向 auto-refactored/）
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from playwright.sync_api import Page

from src.core.base import LoginAutomation


class AnyrouterLogin(LoginAutomation):
    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('anyrouter', headless=headless)
        # Ensure debug directory exists
        self.debug_dir = Path(project_root) / ".playwright-debug"
        try:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _ts(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, msg: str) -> None:
        try:
            print(f"[{self._ts()}] {msg}")
        except Exception:
            print(msg)

    def _shot(self, page: Page, name: str) -> None:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = self.debug_dir / f"{ts}_{name}.png"
            page.screenshot(path=str(path), full_page=True)
            self._log(f"Saved screenshot: {path}")
        except Exception as exc:
            self._log(f"Screenshot failed ({name}): {exc}")

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
    ) -> bool:
        cookie_path = self.cookie_manager.get_cookie_path(self.site_name)
        if not cookie_path.exists():
            self._log(f"Cookie file not found: {cookie_path}")
            return False

        self._log("Try cookie login...")
        success = super().try_cookie_login(page, verify_url=verify_url, expire_days=expire_days)
        if success:
            self._log("Cookie login success")
        else:
            self._log("Cookie expired; re-login required")
        return success

    def verify_login(self, page: Page) -> bool:
        try:
            if '/console' in page.url:
                self._log("Logged in (console)")
                return True

            if page.locator('button:has-text("linuxdo_")').count() > 0:
                self._log("Logged in (user detected)")
                return True

            if '/login' in page.url or page.url == 'https://anyrouter.top/':
                if page.locator('button:has-text("使用 LinuxDO 登录")').count() > 0:
                    self._log("Not logged in (login page)")
                    return False

            return False
        except Exception as exc:
            self._log(f"Verify login error: {exc}")
            return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        self._log("Login with LinuxDO OAuth...")
        try:
            self._log("Navigating to login page: https://anyrouter.top/login")
            page.goto('https://anyrouter.top/login', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            self._log(f"Loaded login page. URL: {page.url}")
            try:
                self._log(f"Login page title: {page.title()}")
            except Exception as exc:
                self._log(f"Failed to get page title: {exc}")
            self._shot(page, 'after_goto_login')

            # 首次进入登录页后立刻刷新一次，规避首次点击 OAuth 按钮无响应的问题
            try:
                self._log("Refreshing login page to stabilize OAuth button...")
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(300)
                try:
                    title = page.title()
                except Exception:
                    title = "<no title>"
                self._log(f"After refresh. URL: {page.url}, Title: {title}")
                self._shot(page, 'after_refresh_login')
            except Exception as exc:
                self._log(f"Refresh failed: {exc}")

            # 关闭系统公告弹窗
            try:
                self._log("Checking for announcement modal...")
                closed_announcement = False
                for name in ('关闭公告', '今日关闭', '关闭'):
                    try:
                        self._log(f"Attempt closing announcement with button: {name}")
                        page.get_by_role('button', name=name).click(timeout=1500)
                        page.wait_for_timeout(500)
                        closed_announcement = True
                        self._log("Announcement closed")
                        break
                    except Exception as exc:
                        self._log(f"No announcement button '{name}' or click failed: {exc}")
                        continue
                if not closed_announcement:
                    self._log("No announcement modal detected.")
            except Exception as exc:
                self._log(f"Announcement close handling error: {exc}")

            # 点击 LinuxDO 登录按钮
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
                self._log(f"Pages before click: {len(page.context.pages)}")
            except Exception:
                pass
            self._shot(page, 'before_oauth_click')
            for desc, action in actions:
                try:
                    self._log(f"Trying OAuth button selector: {desc}")
                    action()
                    clicked = True
                    self._log("OAuth button clicked successfully")
                    try:
                        self._log(f"Tabs currently open: {len(page.context.pages)}")
                    except Exception:
                        pass
                    self._shot(page, 'after_oauth_click')
                    break
                except Exception as e:
                    # keep trying next selector
                    self._log(f"OAuth click attempt failed with selector: {desc}. Error: {e}")
                    continue
            if not clicked:
                # Save a screenshot before returning False
                try:
                    debug_dir = Path('.playwright-debug')
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = debug_dir / f"anyrouter_oauth_click_failed_{int(time.time())}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    self._log(f"Saved screenshot: {screenshot_path}")
                except Exception:
                    pass
                return False

            # 查找 LinuxDO 认证页面
            auth_page = None
            pages_after = list(page.context.pages)
            try:
                self._log(f"Pages after click: {len(pages_after)}")
            except Exception:
                pass
            for idx, candidate in enumerate(pages_after, start=1):
                try:
                    url = candidate.url
                    self._log(f"Inspecting page[{idx}] URL: {url}")
                    if 'linux.do' in url:
                        auth_page = candidate
                        self._log(f"LinuxDO auth page detected at page[{idx}]")
                        break
                except Exception as exc:
                    self._log(f"Error inspecting page[{idx}]: {exc}")
                    continue
            if not auth_page:
                # Debug: no auth page found and save screenshot
                self._log("No LinuxDO page found in tabs")
                try:
                    debug_dir = Path('.playwright-debug')
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    screenshot_path = debug_dir / f"anyrouter_oauth_no_auth_tab_{int(time.time())}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    self._log(f"Saved screenshot: {screenshot_path}")
                except Exception:
                    pass
                return False

            auth_page.bring_to_front()
            self._log("Brought LinuxDO auth page to front")
            auth_page.wait_for_load_state('domcontentloaded')
            try:
                self._log(f"Auth page loaded. URL: {auth_page.url}")
            except Exception:
                pass
            self._shot(auth_page, 'auth_page_loaded')

            # 如果在 LinuxDO 登录页面，填写凭据
            if auth_page.locator('#login-account-name, input[name="login"]').count() > 0:
                email = "yanglanshi@qq.com"
                password = "yls123123."
                try:
                    self._log("Auth page appears to be login form; attempting to focus/login button first")
                    auth_page.locator('#login-button').click()
                    auth_page.wait_for_timeout(500)
                except Exception as exc:
                    self._log(f"Initial login button click ignored/failed: {exc}")
                self._shot(auth_page, 'before_fill_credentials')
                auth_page.locator('#login-account-name, input[name="login"]').first.fill(email)
                pwd = auth_page.locator('#login-account-password, input[name="password"]').first
                pwd.fill(password)
                try:
                    self._log("Submitting login form via submit button")
                    auth_page.locator('form:has(#login-account-name) button[type="submit"]').first.click()
                except Exception as exc:
                    self._log(f"Submit button click failed: {exc}; pressing Enter in password field")
                    pwd.press('Enter')
                auth_page.wait_for_timeout(2000)
                self._shot(auth_page, 'after_submit_credentials')

            # 检查是否已回到 AnyRouter 并登录成功
            try:
                self._log(f"Post-login check on AnyRouter page. URL: {page.url}")
                if 'anyrouter.top' in page.url and self.verify_login(page):
                    self._log("Login appears successful after credentials submission")
                    return True
            except Exception as exc:
                self._log(f"Post-login early check error: {exc}")

            # 处理 OAuth 授权页面
            try:
                try:
                    cb = auth_page.get_by_role('checkbox', name='记住这次授权')
                    if cb.is_visible(timeout=2000):
                        self._log("Checking 'remember this authorization' checkbox")
                        cb.check()
                except Exception as exc:
                    self._log(f"No 'remember authorization' checkbox or check failed: {exc}")
                for action in (
                    lambda: auth_page.get_by_role('link', name='允许').click(),
                    lambda: auth_page.get_by_role('button', name='允许').click(),
                    lambda: auth_page.get_by_text('允许').click(),
                ):
                    try:
                        self._log("Clicking 'Allow' on OAuth consent page")
                        action()
                        self._shot(auth_page, 'after_click_allow')
                        break
                    except Exception as exc:
                        self._log(f"Consent click attempt failed: {exc}")
                        continue
            except Exception as exc:
                self._log(f"OAuth consent handling error: {exc}")

            page.bring_to_front()
            self._log("Brought AnyRouter page to front for final verification")
            ok = self.verify_login(page)
            if not ok:
                self._log("Final verification failed; capturing AnyRouter page state")
                self._shot(page, 'final_verification_failed')
            else:
                self._log("Final verification succeeded")
            return ok
        except Exception as exc:
            self._log(f"登录过程出错: {exc}")
            # Save screenshot before returning False
            try:
                debug_dir = Path('.playwright-debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = debug_dir / f"anyrouter_oauth_exception_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                self._log(f"Saved screenshot: {screenshot_path}")
            except Exception:
                pass
            return False

    def do_login(self, page: Page, **_credentials) -> bool:
        return self.login_with_linuxdo_oauth(page)

    def after_login(self, page: Page, **_credentials) -> None:
        try:
            if '/console/token' not in page.url:
                page.goto('https://anyrouter.top/console/token', timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(2000)
            time.sleep(2)
        except Exception as exc:
            print(f"登录后处理异常: {exc}")


def login_to_anyrouter(*, use_cookie: bool = True, headless: bool = False) -> bool:
    automation = AnyrouterLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://anyrouter.top/console/token',
        )
    except Exception as exc:
        print(f"运行异常: {exc}")
        return False


if __name__ == "__main__":
    USE_COOKIE = True
    HEADLESS = False

    login_to_anyrouter(
        use_cookie=USE_COOKIE,
        headless=HEADLESS,
    )
