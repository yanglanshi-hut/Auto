"""
Linux.do Forum Login Automation Script
使用 Playwright 自动登录 Linux.do 论坛，支持 Cookie 登录和快速登录
"""

import sys
import time
from pathlib import Path
from typing import Optional

# 将项目根目录加入 Python 路径
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from playwright.sync_api import Page
from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths

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

    def login_with_credentials(self, page: Page, email: str, password: str) -> bool:
        logger.info("使用账号密码登录...")

        logger.info("点击登录按钮...")
        login_button = page.locator('#login-button')
        login_button.click()

        logger.info(f"填写账号: {email}")
        email_input = page.locator('#login-account-name, input[name=\"login\"]')
        email_input.fill(email)

        logger.info("填写密码...")
        password_input = page.locator('#login-account-password, input[name=\"password\"]').first
        password_input.fill(password)

        logger.info("提交登录...")
        submitted = False
        # 优先在表单内选择提交按钮
        try:
            submit_in_form = page.locator('form:has(#login-account-name) button[type=\"submit\"], form:has(input[name=\"login\"]) button[type=\"submit\"]').first
            submit_in_form.wait_for(state='visible', timeout=10000)
            submit_in_form.click()
            submitted = True
        except Exception:
            # 否则尝试通过常见选择器点击
            try:
                submit_button = page.locator('button:has-text("登录"):visible, #login-button.login:visible, .login-button:visible, button:has-text("Log in"):visible, button:has-text("Login"):visible').first
                submit_button.wait_for(state='visible', timeout=8000)
                submit_button.click()
                submitted = True
            except Exception:
                # 最后一步，尝试使用回车提交
                try:
                    password_input.press('Enter')
                    submitted = True
                except Exception:
                    submitted = False

        if not submitted:
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
    import os

    # 从环境变量读取凭据（避免硬编码）
    # 使用方法: export LINUXDO_EMAIL="your_email" LINUXDO_PASSWORD="your_password"
    EMAIL = os.getenv('LINUXDO_EMAIL', '')     # 邮箱/用户名
    PASSWORD = os.getenv('LINUXDO_PASSWORD', '')  # 密码
    USE_COOKIE = True                # 是否优先使用 cookie 登录
    HEADLESS = False                 # 是否无头模式运行

    if not EMAIL or not PASSWORD:
        logger.warning("未设置 LINUXDO_EMAIL 或 LINUXDO_PASSWORD 环境变量")
        logger.warning("如果没有有效的 Cookie，登录将失败")
        logger.info("请使用: export LINUXDO_EMAIL='your_email' LINUXDO_PASSWORD='your_password'")

    login_to_linuxdo(
        email=EMAIL,
        password=PASSWORD,
        use_cookie=USE_COOKIE,
        headless=HEADLESS,
    )
