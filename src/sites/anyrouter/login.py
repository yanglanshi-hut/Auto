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
            logger.info(f"未找到 Cookie 文件: {cookie_path}")
            return False

        logger.info("尝试 Cookie 登录...")
        success = super().try_cookie_login(page, verify_url=verify_url, expire_days=expire_days)
        if success:
            logger.info("Cookie 登录成功")
        else:
            logger.info("Cookie 已过期；需要重新登录")
        return success

    def verify_login(self, page: Page) -> bool:
        try:
            current_url = page.url
            logger.info(f"验证登录，当前 URL: {current_url}")

            if '/console' in current_url:
                logger.info("已登录（控制台页面）")
                return True

            # 检测用户名按钮（已登录标志）
            user_button_count = page.locator('button:has-text("linuxdo_")').count()
            logger.info(f"用户按钮数量: {user_button_count}")
            if user_button_count > 0:
                logger.info("已登录（检测到用户按钮）")
                return True

            # 检查是否在登录页面
            if '/login' in current_url or current_url == 'https://anyrouter.top/':
                login_button_count = page.locator('button:has-text("使用 LinuxDO 登录"), button:has-text("使用 LinuxDO 继续")').count()
                logger.info(f"登录按钮数量: {login_button_count}")
                if login_button_count > 0:
                    logger.info("未登录（检测到登录按钮）")
                    return False
                else:
                    # 在登录页但没有登录按钮，可能正在跳转
                    logger.info("在登录页但未检测到登录按钮，等待跳转...")
                    page.wait_for_timeout(2000)
                    new_url = page.url
                    logger.info(f"等待后 URL: {new_url}")
                    if '/console' in new_url:
                        logger.info("已登录（跳转到控制台）")
                        return True

            logger.info("登录状态未知")
            return False
        except Exception as exc:
            logger.warning(f"验证登录出错: {exc}")
            return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """LinuxDO OAuth 登录主流程编排。"""
        logger.info("使用 LinuxDO OAuth 登录...")
        try:
            if not self._navigate_to_login_page(page):
                return False

            self._close_announcement_modal(page)

            # 先在 browser context 中加载 LinuxDO cookie
            # 这样新打开的 OAuth 窗口会自动继承登录状态
            linuxdo_pre_logged = self._preload_linuxdo_cookie(page)

            # 点击 OAuth 按钮并获取新打开的授权页面
            auth_page = self._click_oauth_button(page)
            if not auth_page:
                logger.warning("未能打开授权页面")
                return False

            # 检查是否为 LinuxDO 授权页
            if 'linux.do' not in auth_page.url:
                logger.warning(f"授权页面 URL 不是 LinuxDO: {auth_page.url}")
                return False

            logger.info(f"已打开 LinuxDO 授权页，URL: {auth_page.url}")

            # 如果 LinuxDO cookie 无效，需要在授权页面手动登录
            if not linuxdo_pre_logged:
                if not self._fill_linuxdo_credentials_if_needed(auth_page, page):
                    return False
                # 保存 LinuxDO cookie 供下次使用
                self._save_linuxdo_cookie(auth_page)

            # 提交凭据后，优先尝试早期验证是否已经回到 AnyRouter
            try:
                logger.info(f"登录后检查 AnyRouter 页面，URL: {page.url}")
                if 'anyrouter.top' in page.url and self.verify_login(page):
                    logger.info("提交凭据后登录似乎成功")
                    return True
            except Exception as exc:
                logger.info(f"登录后早期检查出错: {exc}")

            self._handle_oauth_consent(auth_page)

            # 等待 OAuth 授权完成
            page.wait_for_timeout(2000)

            # 切换回 AnyRouter 页面并刷新以显示登录状态
            page.bring_to_front()
            logger.info("已将 AnyRouter 页面置于前台")
            page.wait_for_timeout(2000)

            # 刷新页面以更新登录状态
            logger.info("刷新 AnyRouter 页面以更新登录状态...")
            page.reload()
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)

            logger.info("开始最终登录验证")
            ok = self.verify_login(page)
            if not ok:
                logger.info("最终验证失败；捕获 AnyRouter 页面状态")
                self._shot(page, 'final_verification_failed')
            else:
                logger.info("最终验证成功")
            return ok
        except Exception as exc:
            logger.error(f"登录过程出错: {exc}")
            self._save_error_screenshot(page, 'anyrouter_oauth_exception')
            return False

    # 辅助方法拆分（每个保持单一职责与短小）
    def _preload_linuxdo_cookie(self, page: Page) -> bool:
        """在 browser context 中预加载 LinuxDO cookie，新打开的窗口会自动继承"""
        try:
            from src.core.cookies import CookieManager
            linuxdo_cookie_mgr = CookieManager()
            cookie_path = linuxdo_cookie_mgr.get_cookie_path('linuxdo')

            if not cookie_path.exists():
                logger.info("LinuxDO cookie 文件不存在")
                return False

            logger.info(f"预加载 LinuxDO cookie: {cookie_path}")
            # 直接在 context 中加载 cookie，不需要导航
            if linuxdo_cookie_mgr.load_cookies(page.context, 'linuxdo', expire_days=7):
                logger.info("LinuxDO cookie 已加载到 browser context")
                return True
            else:
                logger.info("LinuxDO cookie 加载失败")
                return False
        except Exception as exc:
            logger.info(f"预加载 LinuxDO cookie 出错: {exc}")
            return False

    def _save_linuxdo_cookie(self, auth_page: Page) -> None:
        """保存 LinuxDO cookie 供后续使用"""
        try:
            from src.core.cookies import CookieManager
            linuxdo_cookie_mgr = CookieManager()
            saved_path = linuxdo_cookie_mgr.save_cookies(auth_page.context, 'linuxdo')
            logger.info(f"已保存 LinuxDO cookie: {saved_path}")
        except Exception as exc:
            logger.warning(f"保存 LinuxDO cookie 失败: {exc}")

    def _navigate_to_login_page(self, page: Page) -> bool:
        try:
            logger.info("导航到登录页: https://anyrouter.top/login")
            page.goto('https://anyrouter.top/login', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            logger.info(f"已加载登录页，URL: {page.url}")
            try:
                logger.info(f"登录页标题: {page.title()}")
            except Exception as exc:
                logger.info(f"获取页面标题失败: {exc}")
            self._shot(page, 'after_goto_login')

            # 首次进入登录页后立刻刷新一次，规避首次点击 OAuth 按钮无响应的问题
            try:
                logger.info("刷新登录页以稳定 OAuth 按钮...")
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(300)
                try:
                    title = page.title()
                except Exception:
                    title = "<无标题>"
                logger.info(f"刷新后 URL: {page.url}，标题: {title}")
                self._shot(page, 'after_refresh_login')
            except Exception as exc:
                logger.info(f"刷新失败: {exc}")
            return True
        except Exception as exc:
            logger.error(f"导航到登录页失败: {exc}")
            return False

    def _close_announcement_modal(self, page: Page) -> None:
        try:
            logger.info("检查公告弹窗...")
            closed_announcement = False
            for name in ('今日关闭', '关闭公告', '关闭'):
                try:
                    logger.info(f"尝试关闭公告按钮: {name}")
                    page.get_by_role('button', name=name).click(timeout=1500)
                    page.wait_for_timeout(500)
                    closed_announcement = True
                    logger.info(f'公告已关闭（点击了"{name}"）')
                    break
                except Exception as exc:
                    logger.info(f"未找到公告按钮 '{name}' 或点击失败: {exc}")
                    continue
            if not closed_announcement:
                logger.info("未检测到公告弹窗")
            else:
                # 弹窗关闭后等待页面稳定
                page.wait_for_timeout(1000)
                page.wait_for_load_state('domcontentloaded')
                logger.info("关闭公告后页面已稳定")

                # 检查"使用 LinuxDO 继续"按钮是否可见，如果不可见则刷新页面
                oauth_button_selectors = [
                    "button:has-text('使用 LinuxDO 继续')",
                    "button:has-text('使用 LinuxDO 登录')",
                ]
                oauth_button_visible = False
                for selector in oauth_button_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            oauth_button_visible = True
                            logger.info(f"检测到 OAuth 按钮: {selector}")
                            break
                    except Exception:
                        continue

                if not oauth_button_visible:
                    logger.info("未检测到 OAuth 按钮，刷新页面...")
                    page.reload(wait_until='domcontentloaded')
                    page.wait_for_timeout(1000)
                    logger.info("页面已刷新")
        except Exception as exc:
            logger.info(f"关闭公告处理出错: {exc}")

    def _click_oauth_button(self, page: Page) -> Optional[Page]:
        """点击 OAuth 按钮并返回新打开的授权页面"""
        actions = [
            ("get_by_role('button', name='使用 LinuxDO 继续')", lambda: page.get_by_role('button', name='使用 LinuxDO 继续')),
            ("get_by_role('button', name='使用 LinuxDO 登录')", lambda: page.get_by_role('button', name='使用 LinuxDO 登录')),
            ("get_by_role('link', name='使用 LinuxDO 继续')", lambda: page.get_by_role('link', name='使用 LinuxDO 继续')),
            ("get_by_text('使用 LinuxDO 继续')", lambda: page.get_by_text('使用 LinuxDO 继续')),
            ("get_by_text('使用 LinuxDO 登录')", lambda: page.get_by_text('使用 LinuxDO 登录')),
            ("locator('button:has-text(\"LinuxDO\")')", lambda: page.locator('button:has-text("LinuxDO")').first),
        ]
        try:
            logger.info(f"点击前页面数: {len(page.context.pages)}")
        except Exception:
            pass
        self._shot(page, 'before_oauth_click')

        for desc, locator_func in actions:
            try:
                logger.info(f"尝试 OAuth 按钮选择器: {desc}")
                locator = locator_func()

                # 使用 expect_popup 捕获新打开的窗口
                with page.expect_popup(timeout=10000) as popup_info:
                    locator.click(timeout=5000)
                    logger.info("OAuth 按钮点击成功，等待新窗口...")

                popup_page = popup_info.value
                logger.info(f"新窗口已打开，URL: {popup_page.url}")
                popup_page.wait_for_load_state('domcontentloaded')
                try:
                    logger.info(f"当前打开的标签页数: {len(page.context.pages)}")
                except Exception:
                    pass
                self._shot(page, 'after_oauth_click')
                return popup_page
            except Exception as e:
                logger.info(f"OAuth 点击失败，选择器: {desc}，错误: {e}")
                continue

        try:
            debug_dir = Path('.playwright-debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = debug_dir / f"anyrouter_oauth_click_failed_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"已保存截图: {screenshot_path}")
        except Exception:
            pass
        logger.warning("所有 OAuth 按钮点击失败；终止登录")
        return None

    def _find_linuxdo_auth_page(self, page: Page) -> Optional[Page]:
        auth_page = None
        pages_after = list(page.context.pages)
        try:
            logger.info(f"点击后页面数: {len(pages_after)}")
        except Exception:
            pass
        for idx, candidate in enumerate(pages_after, start=1):
            try:
                url = candidate.url
                logger.info(f"检查页面[{idx}] URL: {url}")
                if 'linux.do' in url:
                    auth_page = candidate
                    logger.info(f"在页面[{idx}]检测到 LinuxDO 授权页")
                    break
            except Exception as exc:
                logger.info(f"检查页面[{idx}]出错: {exc}")
                continue
        if not auth_page:
            logger.warning("未在标签页中找到 LinuxDO 授权页")
            try:
                debug_dir = Path('.playwright-debug')
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = debug_dir / f"anyrouter_oauth_no_auth_tab_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"已保存截图: {screenshot_path}")
            except Exception:
                pass
            return None

        auth_page.bring_to_front()
        logger.info("已将 LinuxDO 授权页置于前台")
        auth_page.wait_for_load_state('domcontentloaded')
        try:
            logger.info(f"授权页已加载，URL: {auth_page.url}")
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
            logger.info("授权页似乎是登录表单；尝试先点击登录按钮")
            auth_page.locator('#login-button').click()
            auth_page.wait_for_timeout(500)
        except Exception as exc:
            logger.info(f"初始登录按钮点击被忽略/失败: {exc}")
        self._shot(auth_page, 'before_fill_credentials')
        auth_page.locator('#login-account-name, input[name="login"]').first.fill(email)
        pwd = auth_page.locator('#login-account-password, input[name="password"]').first
        pwd.fill(password)
        try:
            logger.info("通过提交按钮提交登录表单")
            auth_page.locator('form:has(#login-account-name) button[type="submit"]').first.click()
        except Exception as exc:
            logger.info(f"提交按钮点击失败: {exc}；在密码字段按 Enter")
            pwd.press('Enter')
        auth_page.wait_for_timeout(2000)
        self._shot(auth_page, 'after_submit_credentials')

        return True

    def _handle_oauth_consent(self, auth_page: Page) -> None:
        try:
            # 先检查是否已经跳转回 AnyRouter（可能已经自动授权）
            try:
                current_url = auth_page.url
                if 'anyrouter.top' in current_url or 'linux.do' not in current_url:
                    logger.info(f"页面已跳转，无需点击允许。当前 URL: {current_url}")
                    return
            except Exception:
                pass

            # 检查"允许"按钮是否存在
            has_allow = False
            for selector in (
                'link:has-text("允许")',
                'button:has-text("允许")',
                'text=允许',
                'a:has-text("允许")',
            ):
                try:
                    if auth_page.locator(selector).count() > 0:
                        has_allow = True
                        break
                except Exception:
                    continue

            if not has_allow:
                logger.info('未找到"允许"按钮，可能已自动授权')
                self._shot(auth_page, 'no_allow_button_found')
                return

            try:
                cb = auth_page.get_by_role('checkbox', name='记住这次授权')
                if cb.is_visible(timeout=1000):
                    logger.info('勾选"记住这次授权"复选框')
                    cb.check()
            except Exception as exc:
                logger.info(f'未找到"记住授权"复选框或勾选失败: {exc}')

            for action in (
                lambda: auth_page.get_by_role('link', name='允许').click(timeout=5000),
                lambda: auth_page.get_by_role('button', name='允许').click(timeout=5000),
                lambda: auth_page.get_by_text('允许').click(timeout=5000),
                lambda: auth_page.locator('a:has-text("允许")').click(timeout=5000),
            ):
                try:
                    logger.info('在 OAuth 同意页点击"允许"')
                    action()
                    self._shot(auth_page, 'after_click_allow')
                    logger.info("已点击允许按钮，等待授权完成...")
                    auth_page.wait_for_timeout(3000)
                    logger.info("授权等待完成")
                    break
                except Exception as exc:
                    logger.info(f"同意点击尝试失败: {exc}")
                    continue
        except Exception as exc:
            logger.warning(f"OAuth 同意处理出错: {exc}")

    def _save_error_screenshot(self, page: Page, name: str) -> None:
        """保存错误截图的辅助方法"""
        try:
            debug_dir = Path('.playwright-debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = debug_dir / f"{name}_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"已保存截图: {screenshot_path}")
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
