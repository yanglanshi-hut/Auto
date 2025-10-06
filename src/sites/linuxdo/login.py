"""
Linux.do 论坛登录自动化脚本
使用 Playwright 自动登录 Linux.do 论坛，支持 Cookie 登录和快速登录
"""

import time
from typing import Optional

# 统一通过 `python -m src` 启动，无需修改 sys.path

from playwright.sync_api import Page
from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.core.config import UnifiedConfigManager

logger = setup_logger("linuxdo", get_project_paths().logs / "linuxdo.log")


class LinuxdoLogin(LoginAutomation):
    """Linux.do 登录自动化实现。"""

    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('linuxdo', headless=headless)

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
    ) -> bool:
        cookie_path = self.cookie_manager.get_cookie_path(self.site_name)
        if not cookie_path.exists():
            logger.info(f"Cookie 文件不存在: {cookie_path}")
            return False

        logger.info("尝试使用 Cookie 快速登录...")
        success = super().try_cookie_login(page, verify_url=verify_url, expire_days=expire_days)
        if success:
            logger.info("Cookie 登录成功")
        else:
            logger.info("Cookie 已过期，需要重新登录")
        return success

    def verify_login(self, page: Page) -> bool:
        try:
            page.wait_for_timeout(2000)
            current_url = page.url
            if '/login' not in current_url:
                logger.info("已登录，URL 已跳转")
                return True

            login_form = page.locator('form, input[name="login"], input[placeholder*="邮箱"]')
            if login_form.count() == 0:
                logger.info("已登录，无登录表单")
                return True

            welcome_text = page.locator('text=欢迎回来')
            if welcome_text.count() == 0:
                logger.info("已登录，未发现欢迎文本")
                return True

            return False
        except Exception as exc:
            logger.warning(f"验证登录时出错: {exc}")
            try:
                if '/login' not in page.url:
                    return True
            except Exception:
                pass
            return False

    def _submit_login_form(self, page: Page, password_input) -> bool:
        """尝试多种方式提交登录表单"""
        submit_strategies = [
            lambda: page.locator('form:has(#login-account-name) button[type="submit"], form:has(input[name="login"]) button[type="submit"]').first.click(timeout=10000),
            lambda: page.locator('button:has-text("登录"):visible, #login-button.login:visible, .login-button:visible, button:has-text("Log in"):visible, button:has-text("Login"):visible').first.click(timeout=8000),
            lambda: password_input.press('Enter'),
        ]

        for strategy in submit_strategies:
            try:
                strategy()
                return True
            except Exception:
                continue
        return False

    def login_with_credentials(self, page: Page, email: str, password: str) -> bool:
        logger.info("使用账号密码登录...")

        logger.info("点击登录按钮...")
        page.locator('#login-button').click()

        logger.info(f"填写账号: {email}")
        page.locator('#login-account-name, input[name="login"]').fill(email)

        logger.info("填写密码...")
        password_input = page.locator('#login-account-password, input[name="password"]').first
        password_input.fill(password)

        logger.info("提交登录...")
        if not self._submit_login_form(page, password_input):
            logger.error("未能找到可用的提交按钮")
            return False

        logger.info("等待登录完成...")
        page.wait_for_timeout(3000)

        if self.verify_login(page):
            logger.info("登录成功")
            return True

        logger.error("登录失败，正在保存截图...")
        return False

    def do_login(self, page: Page, **credentials) -> bool:
        email = credentials.get('email')
        password = credentials.get('password')
        if not email or not password:
            logger.error("未提供登录凭据，无法登录")
            return False

        logger.info("正在打开 LinuxDO 登录页面...")
        page.goto('https://linux.do/login', timeout=60000)
        page.wait_for_load_state('domcontentloaded')

        success = self.login_with_credentials(page, email, password)
        if not success:
            self.browser_manager.save_error_screenshot(page, 'linuxdo_login_failed.png')
        return success

    def after_login(self, page: Page, **_credentials) -> None:
        try:
            current_url = page.url
            if 'chrome-error' in current_url or 'about:' in current_url:
                logger.warning("页面 URL 异常，尝试重新载入首页...")
                try:
                    page.goto('https://linux.do/', timeout=60000, wait_until='domcontentloaded')
                    page.wait_for_timeout(2000)
                    current_url = page.url
                except Exception:
                    pass

            logger.info("论坛首页已加载")
            logger.info(f"当前 URL: {current_url}")

            logger.info("保留会话，等待 3 秒以稳定会话状态...")
            page.wait_for_timeout(3000)
        except Exception as exc:
            logger.error(f"登录后处理出错: {exc}")


def login_to_linuxdo(
    *,
    email: Optional[str] = None,
    password: Optional[str] = None,
    use_cookie: bool = True,
    headless: bool = False,
) -> bool:
    # 如果未提供凭据，尝试从统一配置中获取（带环境变量回退）
    if not email or not password:
        try:
            config_mgr = UnifiedConfigManager()
            creds = config_mgr.get_credentials('linuxdo', fallback_env=True)
            email = email or creds.get('email', '')
            password = password or creds.get('password', '')
        except Exception:
            # 忽略配置读取异常；env 回退已在配置管理器中处理
            pass

    automation = LinuxdoLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://linux.do/',
            email=email,
            password=password,
        )
    except Exception as exc:
        logger.error(f"发生异常: {exc}")
        automation.browser_manager.save_error_screenshot(
            automation.page,
            'linuxdo_error_screenshot.png',
        )
        return False


if __name__ == "__main__":
    # 优先从统一配置获取凭据，带环境变量回退（ANYROUTER/ LINUXDO 均可）
    try:
        cfg = UnifiedConfigManager()
        _creds = cfg.get_credentials('linuxdo', fallback_env=True)
        EMAIL = _creds.get('email', '')
        PASSWORD = _creds.get('password', '')
    except Exception:
        import os  # 最后兜底到环境变量（保持向后兼容）
        EMAIL = os.getenv('LINUXDO_EMAIL', '')
        PASSWORD = os.getenv('LINUXDO_PASSWORD', '')

    USE_COOKIE = True   # 是否优先使用 cookie 登录
    HEADLESS = False    # 是否无头模式运行

    if not EMAIL or not PASSWORD:
        logger.warning("未在配置或环境变量中找到 LinuxDO 凭据")
        logger.warning("如果没有有效的 Cookie，登录将失败")
        logger.info("可设置: export LINUXDO_EMAIL='your_email' LINUXDO_PASSWORD='your_password'")

    login_to_linuxdo(
        email=EMAIL,
        password=PASSWORD,
        use_cookie=USE_COOKIE,
        headless=HEADLESS,
    )
