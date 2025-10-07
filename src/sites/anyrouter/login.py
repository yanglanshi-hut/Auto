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
        if not success:
            logger.info("Cookie 验证失败，需要重新 OAuth 授权（这是正常行为）")
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
            # 阶段 0: 确保 LinuxDO 已登录（加载 Cookie 或执行登录）
            if not self._ensure_linuxdo_logged_in(page):
                logger.error("无法确保 LinuxDO 登录状态")
                return False
            
            # 阶段 1: 打开 OAuth 窗口
            auth_page = self._open_oauth_window(page)
            if not auth_page:
                logger.error("未能打开 OAuth 窗口")
                return False
            
            # 阶段 2: 授权确认
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
        page.wait_for_timeout(300)
        
        # 点击 OAuth 按钮并捕获新窗口
        oauth_buttons = (
            'button:has-text("使用 LinuxDO 继续")',
            'button:has-text("使用 LinuxDO 登录")',
            'text=使用 LinuxDO 继续',
            'text=使用 LinuxDO 登录',
            'role=button[name="使用 LinuxDO 继续"]',
            'role=button[name="使用 LinuxDO 登录"]',
        )
        
        for selector in oauth_buttons:
            try:
                with page.expect_popup(timeout=3000) as popup_info:
                    page.locator(selector).first.click(timeout=5000)
                auth_page = popup_info.value
                auth_page.wait_for_load_state('domcontentloaded')
                logger.info(f"OAuth 窗口已打开: {auth_page.url}")
                return auth_page
            except Exception:
                continue
        
        # 第一次未找到按钮，尝试刷新页面
        logger.info("未找到 OAuth 按钮，尝试刷新页面...")
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(300)
        self._close_popup_if_exists(page)
        page.wait_for_timeout(300)
        
        # 再次尝试查找并点击按钮
        for selector in oauth_buttons:
            try:
                with page.expect_popup(timeout=3000) as popup_info:
                    page.locator(selector).first.click(timeout=5000)
                auth_page = popup_info.value
                auth_page.wait_for_load_state('domcontentloaded')
                logger.info(f"OAuth 窗口已打开: {auth_page.url}")
                return auth_page
            except Exception:
                continue
        
        logger.warning("刷新后仍未找到可用的 OAuth 按钮")
        return None

    def _ensure_linuxdo_logged_in(self, page: Page) -> bool:
        """确保 LinuxDO 已登录（优先使用 Cookie，失败则调用登录流程）"""
        from src.sites.linuxdo.login import LinuxdoLogin
        
        logger.info("检查 LinuxDO 登录状态...")
        
        # 尝试加载 LinuxDO Cookie
        context = page.context
        if self.cookie_manager.load_cookies(context, 'linuxdo', expire_days=30):
            logger.info("发现有效的 LinuxDO Cookie，尝试验证...")
            try:
                # 验证 Cookie 是否有效
                page.goto('https://linux.do/', timeout=30000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(1000)
                
                # 检查是否已登录（没有登录表单即为已登录）
                if page.locator('input[name="login"]').count() == 0:
                    logger.info("LinuxDO Cookie 有效，已登录")
                    return True
                logger.info("LinuxDO Cookie 已过期")
            except Exception as exc:
                logger.warning(f"验证 LinuxDO Cookie 失败: {exc}")
        else:
            logger.info("未找到有效的 LinuxDO Cookie")
        
        # Cookie 无效或不存在，执行完整登录
        logger.info("需要重新登录 LinuxDO")
        email, password = self._get_credentials()
        if not email or not password:
            logger.error("未提供 LinuxDO 凭据")
            return False
        
        # 创建 LinuxdoLogin 实例并复用浏览器
        linuxdo_automation = LinuxdoLogin(headless=False)
        linuxdo_automation.browser_manager = self.browser_manager
        linuxdo_automation.page = page
        
        try:
            success = linuxdo_automation.do_login(page, email=email, password=password)
            if success:
                # 保存 LinuxDO Cookie
                linuxdo_automation.cookie_manager.save_cookies(
                    context, 'linuxdo'
                )
                logger.info("LinuxDO 登录成功并保存 Cookie")
                return True
            logger.error("LinuxDO 登录失败")
            return False
        except Exception as exc:
            logger.error(f"LinuxDO 登录异常: {exc}")
            return False

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
                remember_checkbox.first.check(timeout=300)
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
            page.wait_for_timeout(300)
        
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
            'text=今日关闭',
            'text=关闭公告',
            'button:has-text("今日关闭")',
            'button:has-text("关闭公告")',
        )
        for selector in popup_selectors:
            try:
                page.locator(selector).first.click(timeout=300)
                logger.info(f"成功关闭弹窗: {selector}")
                break
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
                page.wait_for_timeout(300)
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
