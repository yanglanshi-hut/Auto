"""ShareYourCC 登录自动化脚本"""

from __future__ import annotations

import os
from typing import Optional

from playwright.sync_api import Page

from src.core.base import LoginAutomation
from src.core.config import UnifiedConfigManager
from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.sites.shareyourcc.oauth_helpers import (
    click_oauth_button,
    confirm_google_oauth_consent,
    confirm_github_oauth_consent,
    confirm_linuxdo_oauth_consent,
)

logger = setup_logger("shareyourcc", get_project_paths().logs / "shareyourcc.log")


class ShareyourccLogin(LoginAutomation):
    """ShareYourCC 登录自动化实现"""

    def __init__(self, *, headless: bool = False) -> None:
        super().__init__('shareyourcc', headless=headless)

    def try_cookie_login(
        self,
        page: Page,
        *,
        verify_url: Optional[str] = None,
        expire_days: Optional[int] = None,
        login_type: Optional[str] = None,
        email: Optional[str] = None,
    ) -> bool:
        """尝试使用 Cookie 快速登录（带元数据匹配）"""
        cookie_path = self.cookie_manager.get_cookie_path(self.site_name)
        if not cookie_path.exists():
            logger.info(f"Cookie 文件不存在: {cookie_path}")
            return False

        # 构建必需的元数据
        required_metadata = {}
        if login_type:
            required_metadata['login_type'] = login_type
        if email and login_type == 'credentials':
            # credentials 模式需要匹配邮箱
            required_metadata['email'] = email

        logger.info(f"尝试使用 Cookie 快速登录（login_type={login_type}, email={email if login_type=='credentials' else 'N/A'}）...")
        success = super().try_cookie_login(
            page, 
            verify_url=verify_url, 
            expire_days=expire_days,
            required_metadata=required_metadata if required_metadata else None
        )
        if success:
            logger.info("Cookie 登录成功")
        else:
            if required_metadata:
                logger.info(f"Cookie 不匹配或已过期（需要: {required_metadata}），需要重新登录")
            else:
                logger.info("Cookie 已过期，需要重新登录")
        return success

    def verify_login(self, page: Page) -> bool:
        """验证是否已登录 ShareYourCC"""
        try:
            page.wait_for_timeout(1000)
            current_url = page.url

            # 检查是否在仪表板页面
            if '/dashboard' in current_url or '/console' in current_url:
                logger.info("已登录，在仪表板页面")
                return True

            # 检查是否有用户菜单按钮（已登录的标志）
            user_menu_selectors = [
                'button[aria-label*="用户菜单"]',
                'button:has-text("个人中心")',
                'button:has-text("我的账户")',
                '[data-testid="user-menu"]',
                'button[aria-label*="user menu"]',
            ]
            for selector in user_menu_selectors:
                if page.locator(selector).count() > 0:
                    logger.info(f"已登录，检测到用户菜单: {selector}")
                    return True

            # 检查是否有登录按钮（未登录的标志）
            login_button_count = page.locator('header button:has-text("登录"), nav button:has-text("登录")').count()
            if login_button_count > 0:
                logger.info("检测到登录按钮，未登录")
                return False

            # 检查是否有登录对话框
            if page.locator('dialog:has-text("登录")').count() > 0:
                logger.info("检测到登录对话框，未登录")
                return False

            # 检查页面内容中是否有明显的登录后元素
            # 比如 "获取API密钥" 按钮在登录后应该可以直接访问
            if '/api-keys' in current_url or '/tokens' in current_url:
                logger.info("已登录，在 API 密钥页面")
                return True

            # 默认判断：在首页且没有登录按钮即认为已登录
            if current_url == 'https://shareyour.cc/' or current_url.startswith('https://shareyour.cc/?'):
                # 检查顶部导航是否有登录按钮
                nav_login_button = page.locator('header button:has-text("登录"), nav button:has-text("登录")')
                has_login_button = nav_login_button.count() > 0
                if not has_login_button:
                    logger.info("首页未检测到登录按钮，判定为已登录")
                    return True

            logger.info(f"无法确定登录状态，当前 URL: {current_url}")
            return False

        except Exception as exc:
            logger.warning(f"验证登录时出错: {exc}")
            return self._fallback_verify_login(page)

    def _fallback_verify_login(self, page: Page) -> bool:
        """异常情况下的登录验证回退逻辑"""
        try:
            # 简单判断：没有登录按钮即认为已登录
            return page.locator('button:has-text("登录")').count() == 0
        except Exception:
            return False

    def _navigate_to_login_page(self, page: Page) -> bool:
        """导航到登录页面（支持页面跳转和对话框两种方式）"""
        try:
            # 检查是否已在登录页面
            current_url = page.url
            if '/login' in current_url or '/auth' in current_url:
                logger.info(f"已在登录页面: {current_url}")
                return True

            # 检查是否已经打开登录对话框
            if page.locator('dialog:has-text("登录")').count() > 0:
                logger.info("登录对话框已打开")
                return True

            # 等待页面完全加载
            page.wait_for_load_state('networkidle', timeout=10000)
            page.wait_for_timeout(1000)

            # 点击登录按钮 - 多种选择器
            logger.info("点击登录按钮...")
            login_selectors = [
                'button:has-text("登录")',
                'button:text("登录")',
                'header button:has-text("登录")',
            ]

            clicked = False
            for selector in login_selectors:
                try:
                    login_button = page.locator(selector).first
                    if login_button.count() > 0:
                        login_button.click(timeout=10000)
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                logger.error("未找到登录按钮")
                return False

            # 等待跳转或对话框打开
            page.wait_for_timeout(3000)
            page.wait_for_load_state('domcontentloaded', timeout=10000)

            # 检查是否跳转到登录页面或对话框打开
            current_url = page.url
            if '/login' in current_url or '/auth' in current_url:
                logger.info(f"已跳转到登录页面: {current_url}")
                return True

            if page.locator('dialog:has-text("登录")').count() > 0:
                logger.info("登录对话框已打开")
                return True

            logger.warning(f"登录页面/对话框状态不明确，当前 URL: {current_url}")
            return True  # 继续尝试

        except Exception as exc:
            logger.error(f"导航到登录页面失败: {exc}")
            return False

    def login_with_google_oauth(self, page: Page) -> bool:
        """Google OAuth 登录流程"""
        logger.info("开始 Google OAuth 登录")
        
        try:
            # 先检查是否已经登录
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            
            if self.verify_login(page):
                logger.info("ShareYourCC 已登录，无需重新登录")
                return True
            
            # 阶段 0: 确保 Google 已登录
            if not self._ensure_google_logged_in(page):
                logger.error("无法确保 Google 登录状态")
                return False
            
            # 返回 ShareYourCC 首页
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            
            # 导航到登录页面
            if not self._navigate_to_login_page(page):
                logger.error("无法导航到登录页面")
                return False
            
            # 阶段 1: 点击 Google OAuth 按钮
            auth_page = self._click_google_oauth_button(page)
            if not auth_page:
                logger.error("未能打开 Google OAuth 窗口")
                return False
            
            # 阶段 2: Google 授权确认（如果需要）
            if not self._confirm_google_oauth_consent(auth_page):
                logger.error("Google 授权确认失败")
                return False
            
            # 最终验证
            return self._verify_oauth_success(page)
            
        except Exception as exc:
            logger.error(f"Google OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(page, 'shareyourcc_google_oauth_error.png')
            return False
    
    def login_with_github_oauth(self, page: Page) -> bool:
        """GitHub OAuth 登录流程"""
        logger.info("开始 GitHub OAuth 登录")
        
        try:
            # 先检查是否已经登录
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            
            if self.verify_login(page):
                logger.info("ShareYourCC 已登录，无需重新登录")
                return True
            
            # 阶段 0: 确保 GitHub 已登录
            if not self._ensure_github_logged_in(page):
                logger.error("无法确保 GitHub 登录状态")
                return False
            
            # 返回 ShareYourCC 首页
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            
            # 导航到登录页面
            if not self._navigate_to_login_page(page):
                logger.error("无法导航到登录页面")
                return False
            
            # 阶段 1: 点击 GitHub OAuth 按钮
            auth_page = self._click_github_oauth_button(page)
            if not auth_page:
                logger.error("未能打开 GitHub OAuth 窗口")
                return False
            
            # 阶段 2: GitHub 授权确认（如果需要）
            if not self._confirm_github_oauth_consent(auth_page):
                logger.error("GitHub 授权确认失败")
                return False
            
            # 最终验证
            return self._verify_oauth_success(page)
            
        except Exception as exc:
            logger.error(f"GitHub OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(page, 'shareyourcc_github_oauth_error.png')
            return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """使用 LinuxDo OAuth 登录"""
        logger.info("开始 LinuxDo OAuth 登录")

        try:
            # 先检查是否已经登录
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            
            if self.verify_login(page):
                logger.info("ShareYourCC 已登录，无需重新登录")
                return True
            
            # 阶段 0: 确保 LinuxDO 已登录
            if not self._ensure_linuxdo_logged_in(page):
                logger.error("无法确保 LinuxDO 登录状态")
                return False

            # 返回 ShareYourCC 首页
            page.goto('https://shareyour.cc/', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)

            # 导航到登录页面
            if not self._navigate_to_login_page(page):
                logger.error("无法导航到登录页面")
                return False

            # 阶段 1: 点击 LinuxDo OAuth 按钮（处理新窗口或页面跳转）
            auth_page = self._click_linuxdo_oauth_button(page)
            if not auth_page:
                logger.error("未能打开 LinuxDo OAuth 窗口")
                return False

            # 阶段 2: 授权确认
            if not self._confirm_oauth_consent(auth_page):
                logger.error("授权确认失败")
                return False

            # 最终验证
            return self._verify_oauth_success(page)

        except Exception as exc:
            logger.error(f"LinuxDo OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(page, 'shareyourcc_oauth_error.png')
            return False

    def _click_linuxdo_oauth_button(self, page: Page) -> Optional[Page]:
        """点击 LinuxDo OAuth 按钮"""
        return click_oauth_button(page, 'linuxdo')
    
    def _click_google_oauth_button(self, page: Page) -> Optional[Page]:
        """点击 Google OAuth 按钮"""
        return click_oauth_button(page, 'google')
    
    def _click_github_oauth_button(self, page: Page) -> Optional[Page]:
        """点击 GitHub OAuth 按钮"""
        return click_oauth_button(page, 'github')

    def _ensure_google_logged_in(self, page: Page) -> bool:
        """确保 Google 已登录
        
        注意：目前假设用户已在浏览器中登录 Google，
        或者 OAuth 流程会自动处理登录。
        """
        logger.info("检查 Google 登录状态...")
        logger.info("Google OAuth 将在授权页面自动处理登录")
        return True
    
    def _ensure_github_logged_in(self, page: Page) -> bool:
        """确保 GitHub 已登录
        
        注意：目前假设用户已在浏览器中登录 GitHub，
        或者 OAuth 流程会自动处理登录。
        """
        logger.info("检查 GitHub 登录状态...")
        logger.info("GitHub OAuth 将在授权页面自动处理登录")
        return True
    
    def _ensure_linuxdo_logged_in(self, page: Page) -> bool:
        """确保 LinuxDO 已登录（优先使用 Cookie，失败则调用登录流程）
        
        自动从统一配置中读取 LinuxDO 凭据，无需额外配置。
        """
        from src.sites.linuxdo.login import LinuxdoLogin

        logger.info("检查 LinuxDO 登录状态...")

        # 尝试加载 LinuxDO Cookie
        context = page.context
        if self.cookie_manager.load_cookies(context, 'linuxdo', expire_days=30):
            logger.info("发现有效的 LinuxDO Cookie，尝试验证...")
            try:
                page.goto('https://linux.do/', timeout=30000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(1000)

                # 检查是否已登录
                if page.locator('input[name="login"]').count() == 0:
                    logger.info("LinuxDO Cookie 有效，已登录")
                    # 返回原页面
                    page.goto('https://shareyour.cc/', timeout=30000)
                    page.wait_for_load_state('domcontentloaded')
                    return True
                logger.info("LinuxDO Cookie 已过期")
            except Exception as exc:
                logger.warning(f"验证 LinuxDO Cookie 失败: {exc}")
        else:
            logger.info("未找到有效的 LinuxDO Cookie")

        # Cookie 无效或不存在，执行完整登录
        logger.info("需要重新登录 LinuxDO")
        
        # 从统一配置中读取 LinuxDO 凭据
        try:
            cfg = UnifiedConfigManager()
            linuxdo_creds = cfg.get_credentials('linuxdo', fallback_env=True)
            email = linuxdo_creds.get('email', '')
            password = linuxdo_creds.get('password', '')
        except Exception as exc:
            logger.warning(f"从配置读取 LinuxDO 凭据失败: {exc}")
            email = ''
            password = ''
        
        if not email or not password:
            logger.error("未在配置或环境变量中找到 LinuxDO 凭据")
            logger.info("请在 config/users.json 中添加 LinuxDO 用户或设置环境变量 LINUXDO_EMAIL 和 LINUXDO_PASSWORD")
            return False

        # 创建 LinuxdoLogin 实例并复用浏览器
        linuxdo_automation = LinuxdoLogin(headless=False)
        linuxdo_automation.browser_manager = self.browser_manager
        linuxdo_automation.page = page

        try:
            success = linuxdo_automation.do_login(page, email=email, password=password)
            if success:
                # 保存 LinuxDO Cookie
                linuxdo_automation.cookie_manager.save_cookies(context, 'linuxdo')
                logger.info("LinuxDO 登录成功并保存 Cookie")
                # 返回原页面
                page.goto('https://shareyour.cc/', timeout=30000)
                page.wait_for_load_state('domcontentloaded')
                return True
            logger.error("LinuxDO 登录失败")
            return False
        except Exception as exc:
            logger.error(f"LinuxDO 登录异常: {exc}")
            return False

    def _confirm_oauth_consent(self, auth_page: Page) -> bool:
        """确认 LinuxDO OAuth 授权（向后兼容）"""
        return confirm_linuxdo_oauth_consent(auth_page)
    
    def _confirm_google_oauth_consent(self, auth_page: Page) -> bool:
        """确认 Google OAuth 授权"""
        return confirm_google_oauth_consent(auth_page)
    
    def _confirm_github_oauth_consent(self, auth_page: Page) -> bool:
        """确认 GitHub OAuth 授权"""
        return confirm_github_oauth_consent(auth_page)

    def _verify_oauth_success(self, page: Page) -> bool:
        """验证 OAuth 登录成功"""
        logger.info("等待 OAuth 回调完成...")
        
        # 等待OAuth回调完成（跳转回 ShareYourCC）
        max_wait = 30  # 最多等待30秒
        for _ in range(max_wait):
            current_url = page.url
            
            # 如果已经回到 ShareYourCC 域名
            if 'shareyour.cc' in current_url:
                logger.info(f"已回到 ShareYourCC: {current_url}")
                page.wait_for_timeout(2000)
                break
                
            # 如果还在授权页面，继续等待
            if 'linux.do' in current_url or 'connect.linux.do' in current_url:
                page.wait_for_timeout(1000)
                continue
                
            # 其他情况也等待
            page.wait_for_timeout(1000)
        
        # 确保在 ShareYourCC 页面
        if 'shareyour.cc' not in page.url:
            logger.warning(f"OAuth 超时，当前 URL: {page.url}")
            # 尝试导航回首页
            page.goto('https://shareyour.cc/', timeout=30000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
        
        # 检查是否已登录
        for _ in range(5):
            if self.verify_login(page):
                logger.info("OAuth 登录成功")
                return True
            page.wait_for_timeout(1000)

        # 尝试刷新页面
        logger.info("尝试刷新页面...")
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        if self.verify_login(page):
            logger.info("刷新后登录成功")
            return True

        logger.error(f"登录验证失败，当前 URL: {page.url}")
        return False

    def _get_credentials(self) -> tuple[str, str]:
        """获取登录凭据"""
        try:
            cfg = UnifiedConfigManager()
            creds = cfg.get_credentials('shareyourcc', fallback_env=True)
            return creds.get('email', ''), creds.get('password', '')
        except Exception:
            return (
                os.getenv('SHAREYOURCC_EMAIL', ''),
                os.getenv('SHAREYOURCC_PASSWORD', ''),
            )



    def do_login(self, page: Page, **credentials) -> bool:
        """执行登录（根据 login_type 选择登录方式）
        
        支持的 login_type:
        - 'linuxdo_oauth': 使用 LinuxDo OAuth 登录（默认）
        - 'google_oauth': 使用 Google OAuth 登录
        - 'github_oauth': 使用 GitHub OAuth 登录
        """
        # 打开首页并等待加载
        logger.info("正在打开 ShareYourCC 首页...")
        page.goto('https://shareyour.cc/', timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)

        login_type = credentials.get('login_type', 'linuxdo_oauth').lower()
        
        # LinuxDo OAuth 登录
        if login_type == 'linuxdo_oauth':
            logger.info("使用 LinuxDo OAuth 登录模式")
            return self.login_with_linuxdo_oauth(page)
        
        # Google OAuth 登录
        elif login_type == 'google_oauth':
            logger.info("使用 Google OAuth 登录模式")
            return self.login_with_google_oauth(page)
        
        # GitHub OAuth 登录
        elif login_type == 'github_oauth':
            logger.info("使用 GitHub OAuth 登录模式")
            return self.login_with_github_oauth(page)
        
        # 未知类型，使用默认 LinuxDo OAuth
        else:
            logger.warning(f"未知的 login_type: {login_type}，使用默认的 LinuxDo OAuth")
            return self.login_with_linuxdo_oauth(page)

    def after_login(self, page: Page, **_credentials) -> None:
        """登录后处理：关闭弹窗、签到、抽奖"""
        try:
            current_url = page.url
            logger.info(f"登录后 URL: {current_url}")

            # 导航到仪表板
            if '/dashboard' not in current_url:
                logger.info("导航到仪表板...")
                page.goto('https://shareyour.cc/dashboard', timeout=60000)
                page.wait_for_load_state('domcontentloaded')

            logger.info("等待页面和弹窗加载...")
            # 等待时间增加，确保页面内容和弹窗都加载完成
            page.wait_for_timeout(3000)

            # 关闭可能存在的弹窗
            self._close_popup_dialogs(page)

            # 执行签到
            self._do_daily_checkin(page)

            # 执行抽奖（直接导航到抽奖页面）
            self._do_lucky_draw(page)

            logger.info("登录后操作完成")

        except Exception as exc:
            logger.error(f"登录后处理出错: {exc}")

    def _close_popup_dialogs(self, page: Page) -> None:
        """关闭所有弹窗"""
        logger.info("检查并关闭弹窗...")
        
        # 等待页面完全加载和弹窗显示
        try:
            # 等待网络空闲状态
            page.wait_for_load_state('networkidle', timeout=10000)
            logger.info("页面网络已空闲")
        except Exception:
            logger.debug("等待网络空闲超时，继续检查弹窗")
        
        # 额外等待弹窗动画
        logger.info("等待弹窗加载...")
        page.wait_for_timeout(3000)
        
        # 常见的弹窗关闭按钮选择器
        # 优先匹配"系统公告"弹窗的关闭按钮（根据截图）
        close_selectors = [
            # 系统公告弹窗特定选择器
            'div:has-text("系统公告") >> button:has-text("×")',
            'div:has-text("系统公告") >> button',
            '[class*="modal"]:has-text("系统公告") >> button',
            '[class*="dialog"]:has-text("系统公告") >> button',
            # 通用关闭按钮选择器
            'button[aria-label="关闭"]',
            'button[aria-label="Close"]',
            'button:has-text("×")',
            'button:has-text("关闭")',
            'button.close',
            '[data-dismiss="modal"]',
            'dialog button[aria-label="Close"]',
            '.modal-close',
            '.dialog-close',
            '[role="dialog"] button',
            '.Dialog button:has-text("关闭")',
            'div[role="dialog"] button[aria-label]',
            # X 按钮图标
            'button[class*="close"]',
            'button svg[class*="close"]',
            '[class*="Modal"] button[class*="close"]',
        ]

        closed_count = 0
        for selector in close_selectors:
            try:
                close_buttons = page.locator(selector)
                count = close_buttons.count()
                if count > 0:
                    logger.info(f"发现 {count} 个弹窗关闭按钮 ({selector})，尝试关闭...")
                    for i in range(count):
                        try:
                            button = close_buttons.nth(i)
                            # 检查按钮是否可见
                            if button.is_visible():
                                button.click(timeout=1000)
                                closed_count += 1
                                logger.info(f"已关闭弹窗 {closed_count}")
                                page.wait_for_timeout(500)
                        except Exception as e:
                            logger.debug(f"关闭弹窗失败: {e}")
                            continue
            except Exception:
                continue

        if closed_count > 0:
            logger.info(f"共关闭 {closed_count} 个弹窗")
        else:
            logger.info("未发现需要关闭的弹窗")

    def _do_daily_checkin(self, page: Page) -> None:
        """执行每日签到"""
        logger.info("开始执行签到...")

        try:
            # 等待快捷操作区域加载
            page.wait_for_timeout(1000)
            
            # 查找签到按钮的多种选择器
            # 根据截图，签到可能是卡片形式，需要点击整个卡片区域
            checkin_selectors = [
                # 卡片式按钮
                'div:has-text("每日签到"):has-text("获取随机奖励")',
                'div:has-text("每日签到")',
                '[class*="card"]:has-text("每日签到")',
                '[class*="Card"]:has-text("每日签到")',
                # 传统按钮
                'button:has-text("签到")',
                'button:has-text("可签到")',
                'button:has-text("每日签到")',
                'button:has-text("已签到")',
                # 其他可能的形式
                'a:has-text("每日签到")',
                '[role="button"]:has-text("每日签到")',
                '.checkin',
                '[data-testid*="checkin"]',
            ]

            clicked = False
            for selector in checkin_selectors:
                try:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        logger.info(f"找到签到元素: {selector} (共{count}个)")
                        # 尝试点击第一个可见的元素
                        for i in range(count):
                            element = elements.nth(i)
                            try:
                                if element.is_visible():
                                    # 滚动到元素位置
                                    element.scroll_into_view_if_needed(timeout=2000)
                                    page.wait_for_timeout(300)
                                    element.click(timeout=5000)
                                    clicked = True
                                    logger.info(f"签到元素已点击 (索引{i})")
                                    page.wait_for_timeout(2000)
                                    break
                            except Exception as e:
                                logger.debug(f"点击签到元素{i}失败: {e}")
                                continue
                        if clicked:
                            break
                except Exception as exc:
                    logger.debug(f"尝试选择器 {selector} 失败: {exc}")
                    continue

            if not clicked:
                logger.warning("未找到签到按钮，可能今天已签到或页面结构变化")
            else:
                logger.info("签到操作完成")

        except Exception as exc:
            logger.error(f"签到操作失败: {exc}")

    def _do_lucky_draw(self, page: Page) -> None:
        """执行幸运抽奖"""
        logger.info("开始执行抽奖...")

        try:
            # 直接导航到抽奖页面
            logger.info("导航到抽奖页面...")
            page.goto('https://shareyour.cc/dashboard/lottery', timeout=30000)
            page.wait_for_load_state('domcontentloaded', timeout=10000)
            page.wait_for_timeout(2000)
            logger.info(f"当前页面: {page.url}")
            
            # 在抽奖页面查找并点击"开始抽奖"按钮
            draw_button_clicked = False
            
            # 抽奖页面的按钮选择器
            draw_button_selectors = [
                'button:has-text("开始抽奖")',
                'button:has-text("抽奖")',
                'button:has-text("立即抽奖")',
                '[class*="button"]:has-text("开始抽奖")',
                '[class*="btn"]:has-text("开始抽奖")',
                '[class*="Button"]:has-text("开始抽奖")',
                'div[role="button"]:has-text("开始抽奖")',
                'a:has-text("开始抽奖")',
            ]
            
            logger.info("查找开始抽奖按钮...")
            for btn_selector in draw_button_selectors:
                try:
                    elements = page.locator(btn_selector)
                    count = elements.count()
                    if count > 0:
                        logger.info(f"找到开始抽奖按钮: {btn_selector} (共{count}个)")
                        for i in range(count):
                            btn = elements.nth(i)
                            try:
                                if btn.is_visible():
                                    btn.scroll_into_view_if_needed(timeout=2000)
                                    page.wait_for_timeout(300)
                                    btn.click(timeout=5000)
                                    draw_button_clicked = True
                                    logger.info(f"开始抽奖按钮已点击 (索引{i})")
                                    break
                            except Exception as e:
                                logger.debug(f"点击按钮{i}失败: {e}")
                                continue
                        if draw_button_clicked:
                            break
                except Exception as e:
                    logger.debug(f"选择器 {btn_selector} 失败: {e}")
                    continue
            
            if not draw_button_clicked:
                logger.warning("未找到开始抽奖按钮，可能今天已抽奖")
            else:
                # 等待3秒查看抽奖结果
                logger.info("等待抽奖结果...")
                page.wait_for_timeout(5000)
                logger.info("抽奖操作完成")
            
            # 返回仪表板
            logger.info("返回仪表板...")
            page.goto('https://shareyour.cc/dashboard', timeout=30000)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(1000)

        except Exception as exc:
            logger.error(f"抽奖操作失败: {exc}")


    def run(
        self,
        *,
        use_cookie: bool = True,
        verify_url: Optional[str] = None,
        cookie_expire_days: Optional[int] = None,
        **credentials,
    ) -> bool:
        """执行完整的登录流程（支持元数据匹配）"""
        login_success = False
        self.logged_in_with_cookies = False

        expire_days = self.cookie_expire_days if cookie_expire_days is None else cookie_expire_days
        login_type = credentials.get('login_type', '')
        email = credentials.get('email', '')
        password = credentials.get('password', '')

        try:
            self.browser = self.browser_manager.launch(headless=self.headless, **self.browser_kwargs)
            self.context = self.browser.new_context(**self.context_kwargs)
            self.page = self.context.new_page()

            # 尝试 Cookie 登录（带元数据匹配）
            if use_cookie and self.try_cookie_login(
                self.page, 
                verify_url=verify_url, 
                expire_days=expire_days,
                login_type=login_type,
                email=email
            ):
                login_success = True
                self.logged_in_with_cookies = True
            else:
                # Cookie 不匹配或失效，执行正常登录
                login_success = self.do_login(self.page, **credentials)
                self.logged_in_with_cookies = False
                
                # 登录成功后保存 Cookie（带元数据）
                if login_success and use_cookie:
                    metadata = {'login_type': login_type} if login_type else {}
                    if email and login_type == 'credentials':
                        metadata['email'] = email
                    self.cookie_manager.save_cookies(self.context, self.site_name, metadata=metadata)
                    logger.info(f"Cookie 已保存（元数据: {metadata}）")

            if login_success:
                self.after_login(self.page, **credentials)

            return login_success
        except Exception:
            self.browser_manager.save_error_screenshot(self.page, self._error_screenshot_path())
            raise
        finally:
            try:
                if self.context is not None:
                    self.context.close()
            except Exception:
                pass

            self.browser_manager.close(self.browser)
            self.browser = None
            self.context = None
            self.page = None


def login_to_shareyourcc(
    *,
    email: Optional[str] = None,
    password: Optional[str] = None,
    use_cookie: bool = True,
    headless: bool = False,
    login_type: Optional[str] = None,
) -> bool:
    """ShareYourCC 登录入口函数"""
    # 如果未提供凭据，尝试从统一配置中获取（带环境变量回退）
    if not email or not password:
        try:
            config_mgr = UnifiedConfigManager()
            creds = config_mgr.get_credentials('shareyourcc', fallback_env=True)
            email = email or creds.get('email', '')
            password = password or creds.get('password', '')
            login_type = login_type or creds.get('login_type', '')
        except Exception:
            pass

    automation = ShareyourccLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://shareyour.cc/',
            email=email,
            password=password,
            login_type=login_type,
        )
    except Exception as exc:
        logger.error(f"发生异常: {exc}")
        automation.browser_manager.save_error_screenshot(
            automation.page,
            'shareyourcc_error_screenshot.png',
        )
        return False


if __name__ == "__main__":
    # 优先从统一配置获取凭据，带环境变量回退
    try:
        cfg = UnifiedConfigManager()
        _creds = cfg.get_credentials('shareyourcc', fallback_env=True)
        EMAIL = _creds.get('email', '')
        PASSWORD = _creds.get('password', '')
        LOGIN_TYPE = _creds.get('login_type', '')
    except Exception:
        import os
        EMAIL = os.getenv('SHAREYOURCC_EMAIL', '')
        PASSWORD = os.getenv('SHAREYOURCC_PASSWORD', '')
        LOGIN_TYPE = os.getenv('SHAREYOURCC_LOGIN_TYPE', '')

    USE_COOKIE = True   # 是否优先使用 cookie 登录
    HEADLESS = False    # 是否无头模式运行

    # 根据 login_type 决定提示信息
    if LOGIN_TYPE == 'linuxdo_oauth':
        logger.info("使用 LinuxDo OAuth 登录模式")
    elif LOGIN_TYPE == 'google_oauth':
        logger.info("使用 Google OAuth 登录模式")
    elif LOGIN_TYPE == 'github_oauth':
        logger.info("使用 GitHub OAuth 登录模式")
    else:
        logger.warning(f"未知的 login_type: {LOGIN_TYPE}，使用默认的 LinuxDo OAuth")
        LOGIN_TYPE = 'linuxdo_oauth'

    # 创建 automation 实例并运行（Cookie 会自动匹配元数据）
    automation = ShareyourccLogin(headless=HEADLESS)
    success = automation.run(
        use_cookie=USE_COOKIE,  # 启用 Cookie，会自动匹配 login_type 和 email
        verify_url='https://shareyour.cc/',
        email=EMAIL,
        password=PASSWORD,
        login_type=LOGIN_TYPE,
    )
    
    if not success:
        logger.error("登录失败")
        import sys
        sys.exit(1)
