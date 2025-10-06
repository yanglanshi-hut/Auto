"""
OpenI 平台登录自动化脚本
使用 Playwright 自动登录启智AI开源社区平台
"""

from __future__ import annotations

from typing import Optional

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.sites.openi.popup import PopupHandler
from src.sites.openi.cloud_task import CloudTaskManager


logger = setup_logger("openi", get_project_paths().logs / "openi_automation.log")


class OpeniLogin(LoginAutomation):
    """OpenI 多用户登录自动化实现。"""

    def __init__(
        self,
        username: str,
        *,
        headless: bool = False,
        task_name: str = 'image',
        run_duration: int = 15,
        use_cookies: bool = True,
        cookie_expire_days: int = 30,
    ) -> None:
        self.username = username
        self.task_name = task_name
        self.run_duration = run_duration
        self.use_cookies = use_cookies
        self.cookie_expire_days = cookie_expire_days

        # 修复 site_name（移除多级前缀，避免嵌套）
        site_name = f"openi_{username}"

        super().__init__(
            site_name=site_name,
            headless=headless,
            browser_kwargs={'slow_mo': 500},
            cookie_expire_days=cookie_expire_days,
        )

        self._popup = PopupHandler()
        self._cloud = CloudTaskManager(task_name=self.task_name, run_duration=self.run_duration)

    # 为简化实现，Cookie 登录沿用基类实现

    def verify_login(self, page: Page) -> bool:
        try:
            user_menu = page.get_by_role('menu', name='个人信息和配置')
            if user_menu.is_visible(timeout=5000):
                logger.info("Cookie 验证成功，已登录")
                return True
            logger.warning("Cookie 验证失败，需要重新登录")
            return False
        except Exception as exc:
            logger.warning(f"Cookie 验证失败: {exc}")
            return False

    def do_login(self, page: Page, **credentials) -> bool:
        password = credentials.get('password')
        if not password:
            logger.error("未提供密码，无法登录")
            return False

        try:
            logger.info("正在访问 OpenI 平台...")
            page.goto('https://git.openi.org.cn/', timeout=30000)
            logger.info(f"  - 当前 URL: {page.url}")
            page.wait_for_load_state('domcontentloaded')
            logger.info("  - 页面加载完成")

            logger.info("点击登录按钮...")
            page.get_by_role('link', name=' 登录').click()
            page.wait_for_load_state('domcontentloaded')

            logger.info(f"填写用户名 {self.username}")
            username_input = page.get_by_role('textbox', name='用户名/邮箱/手机号')
            username_input.wait_for(state='visible', timeout=10000)
            username_input.fill(self.username)

            logger.info("填写密码...")
            password_input = page.get_by_role('textbox', name='密码')
            password_input.wait_for(state='visible', timeout=10000)
            password_input.fill(password)

            logger.info("提交登录表单...")
            login_button = page.get_by_role('button', name='登录')
            login_button.wait_for(state='visible', timeout=10000)
            login_button.click()

            logger.info("等待登录完成...")
            try:
                page.wait_for_url('**/dashboard', timeout=30000)
            except Exception:
                logger.warning(f"等待跳转超时，当前URL: {page.url}")
                if 'dashboard' not in page.url:
                    raise

            logger.info("检查并关闭仪表盘弹窗...")
            page.wait_for_timeout(2000)
            self._popup.close_popup(page)

            if self.verify_login(page):
                logger.info(f"登录成功！欢迎 {self.username}")
                return True

            logger.warning("登录验证失败")
            return False
        except Exception as exc:
            logger.error(f"用户 {self.username} 登录失败: {exc}")
            if not self.browser_manager.save_error_screenshot(page, f'error_screenshot_{self.username}.png'):
                logger.warning("无法保存登录失败截图")
            return False

    def after_login(self, page: Page, **_credentials) -> None:
        try:
            if self.logged_in_with_cookies:
                logger.info("检查并关闭仪表盘弹窗...")
                page.wait_for_timeout(2000)
                self._popup.close_popup(page)

            self._cloud.show_dashboard_info(page)
            self._cloud.navigate_to_cloud_task(page)
            self._popup.close_popup(page)
            self._cloud.handle_cloud_task(page)

            logger.info(f"\n用户 {self.username} 执行成功")
        except Exception as exc:
            logger.error(f"用户 {self.username} 执行失败: {exc}")
            if not self.browser_manager.save_error_screenshot(page, f'error_screenshot_{self.username}.png'):
                logger.warning("无法保存错误截图")
            raise
