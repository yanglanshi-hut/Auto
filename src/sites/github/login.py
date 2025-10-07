"""GitHub 登录自动化脚本"""

from __future__ import annotations

import os
from typing import Optional

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.config import UnifiedConfigManager
from src.core.logger import setup_logger
from src.core.paths import get_project_paths

logger = setup_logger("github", get_project_paths().logs / "github.log")


class GithubLogin(LoginAutomation):
    """GitHub 登录自动化实现"""

    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('github', headless=headless)

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
        """验证是否已登录 GitHub"""
        try:
            page.wait_for_timeout(2000)
            current_url = page.url

            # 检查是否在登录页面
            if '/login' in current_url or '/session' in current_url:
                # 检查是否有登录表单
                if page.locator('#login_field, input[name="login"]').count() > 0:
                    logger.info("仍在登录页面")
                    return False

            # 检查是否有用户导航栏（已登录的标志）
            if page.locator('meta[name="user-login"]').count() > 0:
                logger.info("已登录，检测到用户元标签")
                return True

            # 检查头像按钮（已登录的标志）
            if page.locator('button[aria-label*="Open user navigation"], summary[aria-label*="View profile"]').count() > 0:
                logger.info("已登录，检测到用户导航按钮")
                return True

            # 检查是否有登录表单（未登录的标志）
            if page.locator('#login_field, input[name="login"]').count() > 0:
                logger.info("检测到登录表单，未登录")
                return False

            # 默认判断：不在登录页面即认为已登录
            if '/login' not in current_url and '/session' not in current_url:
                logger.info("不在登录页面，判定为已登录")
                return True

            return False

        except Exception as exc:
            logger.warning(f"验证登录时出错: {exc}")
            return self._fallback_verify_login(page)

    def _fallback_verify_login(self, page: Page) -> bool:
        """异常情况下的登录验证回退逻辑"""
        try:
            return '/login' not in page.url and '/session' not in page.url
        except Exception:
            return False

    def login_with_credentials(self, page: Page, username: str, password: str) -> bool:
        """使用用户名密码登录"""
        logger.info(f"使用账号密码登录: {username}")

        # 填写用户名
        logger.info("填写用户名...")
        username_input = page.locator('#login_field, input[name="login"]').first
        username_input.fill(username)

        # 填写密码
        logger.info("填写密码...")
        password_input = page.locator('#password, input[name="password"]').first
        password_input.fill(password)

        # 提交登录
        logger.info("提交登录...")
        if not self._submit_login_form(page, password_input):
            logger.error("未能找到可用的提交按钮")
            return False

        logger.info("等待登录完成...")
        page.wait_for_timeout(3000)

        # 检查是否需要 2FA 验证
        if self._handle_2fa_if_needed(page):
            logger.info("2FA 验证完成")

        # 验证登录结果
        if self.verify_login(page):
            logger.info("登录成功")
            return True

        logger.error("登录失败")
        return False

    def _submit_login_form(self, page: Page, password_input) -> bool:
        """尝试多种方式提交登录表单"""
        submit_strategies = [
            lambda: page.locator('input[type="submit"][value="Sign in"]').first.click(timeout=5000),
            lambda: page.locator('button[type="submit"]:has-text("Sign in")').first.click(timeout=5000),
            lambda: password_input.press('Enter'),
        ]

        for strategy in submit_strategies:
            try:
                strategy()
                return True
            except Exception:
                continue
        return False

    def _handle_2fa_if_needed(self, page: Page) -> bool:
        """处理 2FA 验证（如果需要）"""
        try:
            page.wait_for_timeout(2000)
            
            # 检查是否出现 2FA 输入框
            if page.locator('#app_totp, input[name="app_otp"]').count() > 0:
                logger.warning("检测到 2FA 验证要求")
                logger.warning("请在浏览器中手动输入 2FA 验证码")
                logger.warning("等待 60 秒以完成 2FA 验证...")
                
                # 等待 2FA 验证完成（60秒超时）
                try:
                    page.wait_for_url(lambda url: '/login' not in url and '/sessions/two-factor' not in url, timeout=60000)
                    logger.info("2FA 验证完成")
                    return True
                except Exception:
                    logger.error("2FA 验证超时")
                    return False
            
            return True
        except Exception as exc:
            logger.warning(f"处理 2FA 时出错: {exc}")
            return True

    def do_login(self, page: Page, **credentials) -> bool:
        """执行登录"""
        username = credentials.get('username') or credentials.get('email')
        password = credentials.get('password')
        
        if not username or not password:
            logger.error("未提供登录凭据，无法登录")
            return False

        logger.info("正在打开 GitHub 登录页面...")
        page.goto('https://github.com/login', timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(1000)

        success = self.login_with_credentials(page, username, password)
        if not success:
            self.browser_manager.save_error_screenshot(page, 'github_login_failed.png')
        return success

    def after_login(self, page: Page, **_credentials) -> None:
        """登录后处理"""
        try:
            current_url = page.url
            logger.info(f"登录后 URL: {current_url}")
            
            # 如果在其他页面，导航到主页
            if current_url == 'https://github.com/':
                logger.info("已在主页")
            else:
                logger.info("导航到主页...")
                page.goto('https://github.com/', timeout=60000)
                page.wait_for_load_state('domcontentloaded')
            
            logger.info("等待会话稳定...")
            page.wait_for_timeout(2000)
            
        except Exception as exc:
            logger.error(f"登录后处理出错: {exc}")


def login_to_github(
    *,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_cookie: bool = True,
    headless: bool = False,
) -> bool:
    """GitHub 登录入口函数"""
    # 如果未提供凭据，尝试从统一配置中获取（带环境变量回退）
    if not username or not password:
        try:
            config_mgr = UnifiedConfigManager()
            creds = config_mgr.get_credentials('github', fallback_env=True)
            username = username or creds.get('username') or creds.get('email', '')
            password = password or creds.get('password', '')
        except Exception:
            # 忽略配置读取异常；env 回退已在配置管理器中处理
            pass

    automation = GithubLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://github.com/',
            username=username,
            password=password,
        )
    except Exception as exc:
        logger.error(f"发生异常: {exc}")
        automation.browser_manager.save_error_screenshot(
            automation.page,
            'github_error_screenshot.png',
        )
        return False


if __name__ == "__main__":
    # 优先从统一配置获取凭据，带环境变量回退
    try:
        cfg = UnifiedConfigManager()
        _creds = cfg.get_credentials('github', fallback_env=True)
        USERNAME = _creds.get('username') or _creds.get('email', '')
        PASSWORD = _creds.get('password', '')
    except Exception:
        import os
        USERNAME = os.getenv('GITHUB_USERNAME') or os.getenv('GITHUB_EMAIL', '')
        PASSWORD = os.getenv('GITHUB_PASSWORD', '')

    USE_COOKIE = True   # 是否优先使用 cookie 登录
    HEADLESS = False    # 是否无头模式运行

    if not USERNAME or not PASSWORD:
        logger.warning("未在配置或环境变量中找到 GitHub 凭据")
        logger.warning("如果没有有效的 Cookie，登录将失败")
        logger.info("可设置: export GITHUB_USERNAME='your_username' GITHUB_PASSWORD='your_password'")

    login_to_github(
        username=USERNAME,
        password=PASSWORD,
        use_cookie=USE_COOKIE,
        headless=HEADLESS,
    )
