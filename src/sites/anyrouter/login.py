"""AnyRouter 登录自动化脚本"""

from __future__ import annotations

import os
from typing import Optional

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.config import UnifiedConfigManager
from src.core.logger import setup_logger
from src.core.paths import get_project_paths

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
        """验证是否已登录 AnyRouter"""
        current_url = page.url
        
        # 已进入控制台
        if '/console' in current_url:
            return True
        
        # 检测到用户名按钮
        if page.locator('button:has-text("linuxdo_")').count() > 0:
            return True
        
        # 在登录页或首页，检查是否有登录按钮
        if '/login' in current_url or current_url == 'https://anyrouter.top/':
            has_login_button = page.locator(
                'button:has-text("使用 LinuxDO 登录"), button:has-text("使用 LinuxDO 继续")'
            ).count() > 0
            if has_login_button:
                return False
            # 没有登录按钮，等待并检查是否跳转到控制台
            page.wait_for_timeout(1500)
            return '/console' in page.url
        
        return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """LinuxDO OAuth 登录流程"""
        logger.info("开始 AnyRouter OAuth 登录")
        
        try:
            # 阶段 1: 打开 OAuth 窗口
            auth_page = self._open_oauth_window(page)
            if not auth_page:
                logger.error("未能打开 OAuth 窗口")
                return False
            
            # 阶段 2: LinuxDO 认证（如需要）
            if not self._authenticate_linuxdo(auth_page):
                logger.error("LinuxDO 认证失败")
                return False
            
            # 阶段 3: 授权确认
            if not self._confirm_oauth_consent(auth_page):
                logger.error("授权确认失败")
                return False
            
            # 最终验证
            return self._verify_oauth_success(page)
            
        except Exception as exc:
            logger.error(f"OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(
                page, 'anyrouter_oauth_error.png'
            )
            return False

    def _open_oauth_window(self, page: Page) -> Optional[Page]:
        """打开 OAuth 授权窗口"""
        # 导航到登录页
        page.goto('https://anyrouter.top/login', timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        
        # 关闭弹窗
        self._close_popup_if_exists(page)
        
        # 点击 OAuth 按钮并捕获新窗口
        oauth_buttons = (
            'role=button[name="使用 LinuxDO 继续"]',
            'role=button[name="使用 LinuxDO 登录"]',
            'text=使用 LinuxDO 继续',
        )
        
        for selector in oauth_buttons:
            try:
                with page.expect_popup(timeout=10000) as popup_info:
                    page.locator(selector).first.click(timeout=5000)
                auth_page = popup_info.value
                auth_page.wait_for_load_state('domcontentloaded')
                logger.info(f"OAuth 窗口已打开: {auth_page.url}")
                return auth_page
            except Exception:
                continue
        
        logger.warning("未找到可用的 OAuth 按钮")
        return None

    def _authenticate_linuxdo(self, auth_page: Page) -> bool:
        """在 LinuxDO 授权页进行认证"""
        # 验证页面域名
        if 'linux.do' not in auth_page.url:
            logger.error(f"授权页域名异常: {auth_page.url}")
            return False
        
        # 检查是否需要登录
        login_input = auth_page.locator(
            '#login-account-name, input[name="login"]'
        )
        if login_input.count() == 0:
            logger.info("已登录 LinuxDO，跳过认证")
            return True
        
        # 获取凭据
        email, password = self._get_credentials()
        if not email or not password:
            logger.error("未提供 LinuxDO 凭据")
            return False
        
        # 填写登录表单
        logger.info(f"填写 LinuxDO 登录信息: {email[:3]}***{email[-10:]}")
        login_input.first.fill(email)
        
        password_input = auth_page.locator(
            '#login-account-password, input[name="password"]'
        ).first
        password_input.fill(password)
        
        # 提交表单
        submit_btn = auth_page.locator(
            'form:has(#login-account-name) button[type="submit"]'
        )
        if submit_btn.count() > 0:
            submit_btn.first.click(timeout=3000)
        else:
            password_input.press('Enter')
        
        auth_page.wait_for_timeout(2000)
        logger.info("LinuxDO 认证完成")
        return True

    def _confirm_oauth_consent(self, auth_page: Page) -> bool:
        """确认 OAuth 授权"""
        # 如果不在 LinuxDO 域，说明已跳转，无需授权
        if 'linux.do' not in auth_page.url:
            logger.info("已跳转，跳过授权确认")
            return True
        
        # 勾选"记住授权"
        remember_checkbox = auth_page.locator(
            'role=checkbox[name="记住这次授权"]'
        )
        if remember_checkbox.count() > 0:
            try:
                remember_checkbox.first.check(timeout=1000)
                logger.info("已勾选记住授权")
            except Exception:
                pass
        
        # 点击"允许"
        allow_buttons = (
            'role=link[name="允许"]',
            'role=button[name="允许"]',
            'text=允许',
        )
        
        for selector in allow_buttons:
            try:
                auth_page.locator(selector).first.click(timeout=5000)
                logger.info("已点击允许授权")
                auth_page.wait_for_timeout(2000)
                return True
            except Exception:
                continue
        
        logger.warning("未找到允许按钮，可能已自动跳转")
        return True

    def _verify_oauth_success(self, page: Page) -> bool:
        """验证 OAuth 登录成功"""
        page.bring_to_front()
        page.wait_for_timeout(2000)
        
        # 检查是否已跳转到控制台
        for _ in range(3):
            if self.verify_login(page):
                logger.info("OAuth 登录成功")
                return True
            page.wait_for_timeout(1000)
        
        # 尝试刷新页面
        if '/login' in page.url:
            logger.info("仍在登录页，尝试刷新...")
            page.reload(wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            if self.verify_login(page):
                logger.info("刷新后登录成功")
                return True
        
        logger.error(f"登录验证失败，当前 URL: {page.url}")
        return False

    def _close_popup_if_exists(self, page: Page) -> None:
        """关闭公告弹窗（如存在）"""
        popup_selectors = (
            'role=button[name="Close Today"]',
            'role=button[name="Close Notice"]',
        )
        for selector in popup_selectors:
            try:
                page.locator(selector).first.click(timeout=1000)
            except Exception:
                pass
        page.wait_for_timeout(300)

    def _get_credentials(self) -> tuple[str, str]:
        """获取 LinuxDO 凭据"""
        try:
            cfg = UnifiedConfigManager()
            creds = cfg.get_credentials('anyrouter', fallback_env=True)
            return creds.get('email', ''), creds.get('password', '')
        except Exception:
            return (
                os.getenv('ANYROUTER_EMAIL') or os.getenv('LINUXDO_EMAIL', ''),
                os.getenv('ANYROUTER_PASSWORD') or os.getenv('LINUXDO_PASSWORD', ''),
            )

    def do_login(self, page: Page, **_credentials) -> bool:
        """执行登录"""
        return self.login_with_linuxdo_oauth(page)

    def after_login(self, page: Page, **_credentials) -> None:
        """登录后导航到 API 令牌页"""
        try:
            if '/console/token' not in page.url:
                page.goto('https://anyrouter.top/console/token', timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(1000)
            page.wait_for_load_state('networkidle')
        except Exception as exc:
            logger.warning(f"导航到令牌页失败: {exc}")


def login_to_anyrouter(*, use_cookie: bool = True, headless: bool = False) -> bool:
    """AnyRouter 登录入口函数"""
    automation = AnyrouterLogin(headless=headless)
    try:
        return automation.run(use_cookie=use_cookie, verify_url='https://anyrouter.top/console/token')
    except Exception as exc:
        logger.error(f"运行异常: {exc}")
        return False
