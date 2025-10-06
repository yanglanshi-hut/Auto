"""AnyRouter 登录自动化脚本（经简化与可维护性优化）"""

from __future__ import annotations

from typing import Optional, Tuple

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.core.config import UnifiedConfigManager

logger = setup_logger("anyrouter", get_project_paths().logs / "anyrouter.log")


class AnyrouterLogin(LoginAutomation):
    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('anyrouter', headless=headless)

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
    ) -> bool:
        cookie_path = self.cookie_manager.get_cookie_path(self.site_name)
        if not cookie_path.exists():
            logger.info(f"未找到 Cookie 文件: {cookie_path}")
            return False
        success = super().try_cookie_login(page, verify_url=verify_url, expire_days=expire_days)
        logger.info("Cookie 登录成功" if success else "Cookie 已过期；需要重新登录")
        return success

    def verify_login(self, page: Page) -> bool:
        try:
            current_url = page.url
            if '/console' in current_url:
                return True
            if page.locator('button:has-text("linuxdo_")').count() > 0:
                return True
            if '/login' in current_url or current_url == 'https://anyrouter.top/':
                has_login_button = page.locator(
                    'button:has-text("使用 LinuxDO 登录"), button:has-text("使用 LinuxDO 继续")'
                ).count() > 0
                if has_login_button:
                    return False
                page.wait_for_timeout(2000)
                return '/console' in page.url
            return False
        except Exception:
            try:
                return '/console' in page.url
            except Exception:
                return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """LinuxDO OAuth 主流程：导航、预加载、授权页、登录/同意、验证

        注意：此方法不负责清除 LinuxDO Cookie，由 do_login() 统一处理
        """
        logger.info("=" * 60)
        logger.info("开始 AnyRouter OAuth 登录流程")
        logger.info("=" * 60)

        try:
            logger.info("[1/6] 导航到登录页...")
            if not self._navigate_to_login_page(page):
                logger.error("[1/6] 失败：导航到登录页失败")
                return False
            logger.info("[1/6] 成功：已到达登录页")

            self._close_announcement_modal(page)

            logger.info("[2/6] 打开 OAuth 授权窗口...")
            auth_page = self._open_oauth_window(page)
            if auth_page is None:
                logger.error("[2/6] 失败：未能打开 OAuth 授权窗口")
                return False
            logger.info("[2/6] 成功：OAuth 窗口已打开")

            if not self._validate_auth_page(auth_page):
                logger.error("[3/6] 失败：授权页验证失败")
                return False
            logger.info("[3/6] 成功：授权页验证通过")

            logger.info("[4/6] 处理 LinuxDO 登录...")
            if not self._fill_linuxdo_credentials_if_needed(auth_page):
                logger.error("[4/6] 失败：填写凭据失败")
                return False
            logger.info("[4/6] 成功：LinuxDO 凭据已提交")

            self._save_linuxdo_cookie(auth_page)

            logger.info("[5/6] 检查是否提前完成授权...")
            if self._early_verify_anyrouter(page):
                logger.info("[5/6] 成功：提前验证通过，无需显式授权")
                logger.info("=" * 60)
                logger.info("OAuth 登录完成")
                logger.info("=" * 60)
                return True
            logger.info("[5/6] 继续：需要处理授权同意")

            logger.info("[6/6] 处理授权同意...")
            self._handle_oauth_consent(auth_page)

            logger.info("[6/6] 最终验证登录状态...")
            result = self._finalize_and_verify(page)

            if result:
                logger.info("=" * 60)
                logger.info("OAuth 登录成功")
                logger.info("=" * 60)
            else:
                logger.error("=" * 60)
                logger.error("OAuth 登录失败")
                logger.error("=" * 60)
            return result
        except Exception as exc:
            logger.error("=" * 60)
            logger.error(f"OAuth 登录异常: {exc}")
            logger.error("=" * 60)
            self.browser_manager.save_error_screenshot(page, 'anyrouter_oauth_exception.png')
            return False

    def _validate_auth_page(self, auth_page: Page) -> bool:
        try:
            if 'linux.do' in auth_page.url:
                return True
            logger.warning(f"授权页面 URL 非 LinuxDO: {auth_page.url}")
            return False
        except Exception:
            return False

    def _clear_linuxdo_cookies(self, context) -> int:
        """清除 context 中所有 linuxdo 域的 Cookie，避免域混杂

        返回:
            清除的 Cookie 数量
        """
        try:
            cookies = context.cookies()
            linuxdo_cookies = [c for c in cookies if 'linux.do' in c.get('domain', '')]
            if linuxdo_cookies:
                for cookie in linuxdo_cookies:
                    context.clear_cookies(name=cookie['name'], domain=cookie['domain'])
                logger.info(f"已清除 {len(linuxdo_cookies)} 个 LinuxDO Cookie")
                return len(linuxdo_cookies)
            return 0
        except Exception as exc:
            logger.warning(f"清除 LinuxDO Cookie 失败: {exc}")
            return 0

    def _verify_context_clean(self, context) -> bool:
        """验证 context 中是否还有 LinuxDO Cookie

        返回:
            True 表示干净（没有 LinuxDO Cookie），False 表示仍有残留
        """
        try:
            cookies = context.cookies()
            linuxdo_cookies = [c for c in cookies if 'linux.do' in c.get('domain', '')]
            if linuxdo_cookies:
                logger.warning(f"检测到 {len(linuxdo_cookies)} 个残留的 LinuxDO Cookie")
                return False
            return True
        except Exception:
            return True  # 检测失败时假定干净，避免阻塞流程

    def _finalize_and_verify(self, page: Page) -> bool:
        """最终验证登录状态

        注意：不再在此处清除 LinuxDO Cookie，由 do_login() 统一处理
        """
        try:
            page.bring_to_front()
            # 等待 OAuth 回调完成
            page.wait_for_timeout(3000)

            # 检查是否已经跳转到 /console
            if '/console' in page.url:
                logger.info("OAuth 回调成功，已自动跳转")
                return True

            # 如果还在 /login，尝试刷新
            if '/login' in page.url:
                page.reload()
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(2000)

            # 多次尝试验证
            for i in range(5):
                if self.verify_login(page):
                    return True
                logger.info(f"第 {i+1} 次验证失败，当前 URL: {page.url}")
                page.wait_for_timeout(1500)

            logger.warning(f"验证失败，当前 URL: {page.url}")
            return False
        except Exception as exc:
            logger.error(f"最终验证异常: {exc}")
            return False

    def _navigate_to_login_page(self, page: Page) -> bool:
        try:
            page.goto('https://anyrouter.top/login', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            try:
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(300)
            except Exception:
                pass
            return True
        except Exception as exc:
            logger.error(f"导航到登录页失败: {exc}")
            return False

    def _close_announcement_modal(self, page: Page) -> None:
        try:
            for name in ('今日关闭', '关闭公告', '关闭'):
                try:
                    page.get_by_role('button', name=name).click(timeout=1200)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(500)
            if page.locator("button:has-text('使用 LinuxDO 继续'), button:has-text('使用 LinuxDO 登录')").count() == 0:
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(500)
        except Exception:
            pass

    def _preload_linuxdo_cookie(self, page: Page) -> bool:
        """将 LinuxDO Cookie 预加载到 context 以便新窗口复用"""
        try:
            from src.core.cookies import CookieManager
            mgr = CookieManager()
            if not mgr.get_cookie_path('linuxdo').exists():
                return False
            return bool(mgr.load_cookies(page.context, 'linuxdo', expire_days=7))
        except Exception:
            return False

    def _save_linuxdo_cookie(self, auth_page: Page) -> None:
        """保存 LinuxDO cookie 供后续使用"""
        try:
            from src.core.cookies import CookieManager
            mgr = CookieManager()
            saved_path = mgr.save_cookies(auth_page.context, 'linuxdo')
            logger.info(f"已保存 LinuxDO cookie: {saved_path}")
        except Exception as exc:
            logger.warning(f"保存 LinuxDO cookie 失败: {exc}")

    def _open_oauth_window(self, page: Page) -> Optional[Page]:
        """点击 OAuth 按钮并返回新打开的授权页"""
        for locator in self._oauth_button_candidates(page):
            try:
                with page.expect_popup(timeout=10000) as popup_info:
                    locator.click(timeout=5000)
                popup = popup_info.value
                popup.wait_for_load_state('domcontentloaded')
                return popup
            except Exception:
                continue
        logger.warning("未能点击任何 OAuth 按钮")
        return None

    def _oauth_button_candidates(self, page: Page):
        return [
            page.get_by_role('button', name='使用 LinuxDO 继续'),
            page.get_by_role('button', name='使用 LinuxDO 登录'),
            page.get_by_role('link', name='使用 LinuxDO 继续'),
            page.get_by_text('使用 LinuxDO 继续'),
            page.get_by_text('使用 LinuxDO 登录'),
            page.locator('button:has-text("LinuxDO")').first,
        ]

    def _fill_linuxdo_credentials_if_needed(self, auth_page: Page) -> bool:
        """在 LinuxDO 授权页上填写并提交凭据（如需要）"""
        if auth_page.locator('#login-account-name, input[name="login"]').count() == 0:
            return True

        email, password = self._get_linuxdo_credentials()
        if not email or not password:
            logger.error("未提供 LinuxDO/AnyRouter 凭据；请设置 ANYROUTER_* 或 LINUXDO_* 环境变量或配置")
            return False

        try:
            auth_page.locator('#login-button').click()
            auth_page.wait_for_timeout(300)
        except Exception:
            pass

        self._fill_and_submit(auth_page, email, password)
        auth_page.wait_for_timeout(1500)
        return True

    def _get_linuxdo_credentials(self) -> Tuple[str, str]:
        try:
            cfg = UnifiedConfigManager()
            c = cfg.get_credentials('anyrouter', fallback_env=True)
            return c.get('email', ''), c.get('password', '')
        except Exception:
            import os
            return (
                os.getenv('ANYROUTER_EMAIL') or os.getenv('LINUXDO_EMAIL', ''),
                os.getenv('ANYROUTER_PASSWORD') or os.getenv('LINUXDO_PASSWORD', ''),
            )

    def _fill_and_submit(self, auth_page: Page, email: str, password: str) -> None:
        auth_page.locator('#login-account-name, input[name="login"]').first.fill(email)
        pwd = auth_page.locator('#login-account-password, input[name="password"]').first
        pwd.fill(password)
        try:
            auth_page.locator('form:has(#login-account-name) button[type="submit"]').first.click()
        except Exception:
            try:
                pwd.press('Enter')
            except Exception:
                pass

    def _handle_oauth_consent(self, auth_page: Page) -> None:
        try:
            try:
                url = auth_page.url
                if 'anyrouter.top' in url or 'linux.do' not in url:
                    return
            except Exception:
                return

            try:
                cb = auth_page.get_by_role('checkbox', name='记住这次授权')
                if cb.is_visible(timeout=800):
                    cb.check()
            except Exception:
                pass

            for selector in (
                'role=link[name="允许"]',
                'role=button[name="允许"]',
                'text=允许',
                'a:has-text("允许")',
            ):
                try:
                    auth_page.locator(selector).first.click(timeout=5000)
                    # 等待 OAuth 回调完成（popup 应该跳转到 anyrouter.top）
                    auth_page.wait_for_timeout(3000)

                    # 检查是否已经跳转到 anyrouter
                    try:
                        if 'anyrouter.top' in auth_page.url:
                            logger.info(f"OAuth popup 已跳转到: {auth_page.url}")
                    except Exception:
                        pass

                    break
                except Exception:
                    continue
        except Exception:
            pass

    def _early_verify_anyrouter(self, page: Page) -> bool:
        try:
            return 'anyrouter.top' in page.url and self.verify_login(page)
        except Exception:
            return False

    def do_login(self, page: Page, **_credentials) -> bool:
        """执行登录流程，确保返回前清除 LinuxDO Cookie"""
        try:
            success = self.login_with_linuxdo_oauth(page)
            return success
        finally:
            # 无论成功失败，都确保清除 LinuxDO Cookie
            logger.info("清理 Context 中的 LinuxDO Cookie...")
            cleared_count = self._clear_linuxdo_cookies(page.context)
            if cleared_count > 0:
                logger.info(f"已清除 {cleared_count} 个 LinuxDO Cookie")
            else:
                logger.info("Context 中没有 LinuxDO Cookie，无需清除")

            if not self._verify_context_clean(page.context):
                logger.error("⚠️ 清除后仍检测到 LinuxDO Cookie 残留，可能影响 Cookie 保存")

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
