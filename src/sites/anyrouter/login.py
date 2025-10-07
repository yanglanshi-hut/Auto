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
    """AnyRouter 登录自动化类（支持多用户）"""
    
    def __init__(self, *, headless: bool = False, login_type: Optional[str] = None) -> None:
        # 根据 login_type 设置不同的 site_name，以区分不同登录方式的 Cookie
        # 例如：anyrouter_credentials, anyrouter_github_oauth, anyrouter_linuxdo_oauth
        if login_type:
            site_name = f'anyrouter_{login_type}'
        else:
            site_name = 'anyrouter'
        
        super().__init__(site_name, headless=headless)
        self.login_type = login_type

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

    def login_with_credentials(self, page: Page, email: str, password: str) -> bool:
        """使用邮箱密码登录"""
        logger.info(f"使用邮箱密码登录: {email}")
        
        try:
            # 导航到登录页
            page.goto('https://anyrouter.top/login', timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            self._close_popup_if_exists(page)
            page.wait_for_timeout(500)
            
            # 填写邮箱
            logger.info("填写邮箱...")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="邮箱"]',
                'input[placeholder*="Email"]',
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = page.locator(selector).first
                    if email_input.count() > 0:
                        email_input.fill(email)
                        email_filled = True
                        break
                except Exception:
                    continue
            
            if not email_filled:
                logger.error("未找到邮箱输入框")
                return False
            
            page.wait_for_timeout(300)
            
            # 填写密码
            logger.info("填写密码...")
            password_input = page.locator('input[type="password"]').first
            password_input.fill(password)
            page.wait_for_timeout(300)
            
            # 提交登录
            logger.info("提交登录...")
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    page.locator(selector).first.click(timeout=5000)
                    submitted = True
                    break
                except Exception:
                    continue
            
            if not submitted:
                logger.error("未找到登录提交按钮")
                return False
            
            logger.info("等待登录完成...")
            page.wait_for_timeout(3000)
            
            # 验证登录结果
            if self.verify_login(page):
                logger.info("登录成功")
                return True
            
            logger.error("登录失败")
            return False
            
        except Exception as exc:
            logger.error(f"邮箱密码登录失败: {exc}")
            return False

    def login_with_github_oauth(self, page: Page) -> bool:
        """GitHub OAuth 登录流程"""
        logger.info("开始 GitHub OAuth 登录")
        
        try:
            # 阶段 0: 确保 GitHub 已登录
            if not self._ensure_github_logged_in(page):
                logger.error("无法确保 GitHub 登录状态")
                return False
            
            # 阶段 1: 打开 OAuth 窗口
            auth_page = self._open_github_oauth_window(page)
            if not auth_page:
                logger.error("未能打开 GitHub OAuth 窗口")
                return False
            
            # 阶段 2: 授权确认（如果需要）
            if not self._confirm_github_oauth_consent(auth_page):
                logger.error("GitHub 授权确认失败")
                return False
            
            # 最终验证
            return self._verify_oauth_success(page)
            
        except Exception as exc:
            logger.error(f"GitHub OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(
                page, 'anyrouter_github_oauth_error.png'
            )
            return False

    def login_with_linuxdo_oauth(self, page: Page) -> bool:
        """LinuxDO OAuth 登录流程"""
        logger.info("开始 LinuxDO OAuth 登录")
        
        try:
            # 阶段 0: 确保 LinuxDO 已登录（加载 Cookie 或执行登录）
            if not self._ensure_linuxdo_logged_in(page):
                logger.error("无法确保 LinuxDO 登录状态")
                return False
            
            # 阶段 1: 打开 OAuth 窗口
            auth_page = self._open_linuxdo_oauth_window(page)
            if not auth_page:
                logger.error("未能打开 LinuxDO OAuth 窗口")
                return False
            
            # 阶段 2: 授权确认
            if not self._confirm_linuxdo_oauth_consent(auth_page):
                logger.error("LinuxDO 授权确认失败")
                return False
            
            # 最终验证
            return self._verify_oauth_success(page)
            
        except Exception as exc:
            logger.error(f"LinuxDO OAuth 流程异常: {exc}", exc_info=True)
            self.browser_manager.save_error_screenshot(
                page, 'anyrouter_oauth_error.png'
            )
            return False

    def _open_github_oauth_window(self, page: Page) -> Optional[Page]:
        """打开 GitHub OAuth 授权窗口"""
        page.goto('https://anyrouter.top/login', timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        self._close_popup_if_exists(page)
        page.wait_for_timeout(300)
        
        oauth_buttons = (
            'button:has-text("使用 GitHub 继续")',
            'button:has-text("使用 GitHub 登录")',
            'text=使用 GitHub 继续',
            'text=使用 GitHub 登录',
            'role=button[name="使用 GitHub 继续"]',
            'role=button[name="使用 GitHub 登录"]',
        )
        
        for selector in oauth_buttons:
            try:
                with page.expect_popup(timeout=3000) as popup_info:
                    page.locator(selector).first.click(timeout=5000)
                auth_page = popup_info.value
                auth_page.wait_for_load_state('domcontentloaded')
                logger.info(f"GitHub OAuth 窗口已打开: {auth_page.url}")
                return auth_page
            except Exception:
                continue
        
        logger.warning("未找到 GitHub OAuth 按钮")
        return None

    def _open_linuxdo_oauth_window(self, page: Page) -> Optional[Page]:
        """打开 LinuxDO OAuth 授权窗口"""
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

    def _ensure_github_logged_in(self, page: Page) -> bool:
        """确保 GitHub 已登录（优先使用 Cookie，失败则调用登录流程）"""
        from src.sites.github.login import GithubLogin
        
        logger.info("检查 GitHub 登录状态...")
        
        # 尝试加载 GitHub Cookie
        context = page.context
        if self.cookie_manager.load_cookies(context, 'github', expire_days=30):
            logger.info("发现有效的 GitHub Cookie，尝试验证...")
            try:
                page.goto('https://github.com/', timeout=30000)
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(1000)
                
                # 检查是否已登录
                if page.locator('meta[name="user-login"]').count() > 0:
                    logger.info("GitHub Cookie 有效，已登录")
                    return True
                logger.info("GitHub Cookie 已过期")
            except Exception as exc:
                logger.warning(f"验证 GitHub Cookie 失败: {exc}")
        else:
            logger.info("未找到有效的 GitHub Cookie")
        
        # Cookie 无效或不存在，执行完整登录
        logger.info("需要重新登录 GitHub")
        
        # 从统一配置中读取 GitHub 凭据
        try:
            cfg = UnifiedConfigManager()
            github_creds = cfg.get_credentials('github', fallback_env=True)
            username = github_creds.get('username', '')
            password = github_creds.get('password', '')
        except Exception as exc:
            logger.warning(f"从配置读取 GitHub 凭据失败: {exc}")
            username = ''
            password = ''
        
        if not username or not password:
            logger.error("未在配置或环境变量中找到 GitHub 凭据")
            logger.info("请在 config/users.json 中添加 GitHub 用户或设置环境变量")
            return False
        
        # 创建 GithubLogin 实例并复用浏览器
        github_automation = GithubLogin(headless=False)
        github_automation.browser_manager = self.browser_manager
        github_automation.page = page
        
        try:
            success = github_automation.do_login(page, username=username, password=password)
            if success:
                github_automation.cookie_manager.save_cookies(context, 'github')
                logger.info("GitHub 登录成功并保存 Cookie")
                return True
            logger.error("GitHub 登录失败")
            return False
        except Exception as exc:
            logger.error(f"GitHub 登录异常: {exc}")
            return False

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
            logger.info("请在 config/users.json 中添加 LinuxDO 用户或设置环境变量")
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

    def _confirm_github_oauth_consent(self, auth_page: Page) -> bool:
        """确认 GitHub OAuth 授权"""
        # 如果不在 GitHub 域，说明已跳转，无需授权
        if 'github.com' not in auth_page.url:
            logger.info("已跳转，跳过 GitHub 授权确认")
            return True
        
        # 检查是否需要授权（首次授权或权限更新）
        authorize_selectors = [
            'button[type="submit"]:has-text("Authorize")',
            'button:has-text("Authorize")',
            'input[type="submit"][value*="Authorize"]',
        ]
        
        for selector in authorize_selectors:
            try:
                auth_page.locator(selector).first.click(timeout=5000)
                logger.info("已点击 GitHub 授权")
                auth_page.wait_for_timeout(2000)
                return True
            except Exception:
                continue
        
        logger.info("GitHub 无需授权或已自动跳转")
        return True

    def _confirm_linuxdo_oauth_consent(self, auth_page: Page) -> bool:
        """确认 LinuxDO OAuth 授权"""
        # 如果不在 LinuxDO 域，说明已跳转，无需授权
        if 'linux.do' not in auth_page.url:
            logger.info("已跳转，跳过 LinuxDO 授权确认")
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
        
        closed_count = 0
        for selector in popup_selectors:
            try:
                buttons = page.locator(selector)
                count = buttons.count()
                if count > 0:
                    for i in range(count):
                        try:
                            button = buttons.nth(i)
                            if button.is_visible():
                                button.click(timeout=1000)
                                closed_count += 1
                                logger.info(f"成功关闭弹窗 {closed_count}: {selector}")
                                page.wait_for_timeout(500)
                        except Exception:
                            continue
            except Exception:
                pass
        
        if closed_count > 0:
            logger.info(f"✅ 共关闭 {closed_count} 个弹窗")
            # 重要：关闭弹窗后刷新页面，确保登录对话框能正确显示
            logger.info("刷新页面以重新加载第三方认证界面...")
            page.reload(wait_until='domcontentloaded')
            page.wait_for_timeout(2000)

    def _get_credentials(self) -> tuple[str, str]:
        """获取 AnyRouter 凭据"""
        try:
            cfg = UnifiedConfigManager()
            creds = cfg.get_credentials('anyrouter', fallback_env=True)
            return creds.get('email', ''), creds.get('password', '')
        except Exception:
            return (
                os.getenv('ANYROUTER_EMAIL', ''),
                os.getenv('ANYROUTER_PASSWORD', ''),
            )

    def do_login(self, page: Page, **credentials) -> bool:
        """执行登录（根据 login_type 选择登录方式）
        
        支持的 login_type:
        - 'credentials': 使用 AnyRouter 邮箱密码登录
        - 'github_oauth': 使用 GitHub OAuth 登录（复用 GitHub 登录状态）
        - 'linuxdo_oauth': 使用 LinuxDo OAuth 登录（复用 LinuxDo 登录状态，默认）
        """
        login_type = credentials.get('login_type', 'linuxdo_oauth').lower()
        
        # 方式1: 使用邮箱密码登录
        if login_type == 'credentials':
            email = credentials.get('email')
            password = credentials.get('password')
            if not email or not password:
                logger.error("login_type 为 'credentials' 但未提供邮箱或密码")
                return False
            logger.info("使用邮箱密码登录模式")
            return self.login_with_credentials(page, email, password)
        
        # 方式2: 使用 GitHub OAuth 登录
        elif login_type == 'github_oauth':
            logger.info("使用 GitHub OAuth 登录模式")
            return self.login_with_github_oauth(page)
        
        # 方式3: 使用 LinuxDo OAuth 登录（默认）
        else:
            logger.info("使用 LinuxDo OAuth 登录模式")
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


def login_to_anyrouter(*, use_cookie: bool = True, headless: bool = False, **credentials) -> bool:
    """AnyRouter 登录入口函数"""
    automation = AnyrouterLogin(headless=headless)
    try:
        return automation.run(
            use_cookie=use_cookie,
            verify_url='https://anyrouter.top/console/token',
            **credentials
        )
    except Exception as exc:
        logger.error(f"运行异常: {exc}")
        return False


if __name__ == "__main__":
    # 优先从统一配置获取凭据，带环境变量回退
    try:
        cfg = UnifiedConfigManager()
        _creds = cfg.get_credentials('anyrouter', fallback_env=True)
        EMAIL = _creds.get('email', '')
        PASSWORD = _creds.get('password', '')
        LOGIN_TYPE = _creds.get('login_type', 'linuxdo_oauth')
    except Exception:
        import os
        EMAIL = os.getenv('ANYROUTER_EMAIL', '')
        PASSWORD = os.getenv('ANYROUTER_PASSWORD', '')
        LOGIN_TYPE = os.getenv('ANYROUTER_LOGIN_TYPE', 'linuxdo_oauth')

    USE_COOKIE = True   # 是否优先使用 cookie 登录
    HEADLESS = False    # 是否无头模式运行

    # 根据 login_type 决定是否需要凭据和是否使用 Cookie
    if LOGIN_TYPE == 'credentials':
        logger.info("使用邮箱密码登录模式")
        # credentials 模式：如果配置了凭据，强制重新登录以确保使用正确的登录方式
        if EMAIL and PASSWORD:
            use_cookie = False  # 强制使用邮箱密码登录，不使用之前的 OAuth Cookie
            logger.info("检测到凭据配置，将强制使用邮箱密码登录（跳过 Cookie）")
        else:
            use_cookie = USE_COOKIE
            logger.warning("credentials 模式但未提供凭据")
    elif LOGIN_TYPE in ('github_oauth', 'linuxdo_oauth'):
        logger.info(f"使用 {LOGIN_TYPE} 登录模式")
        # OAuth 可以使用 Cookie
        use_cookie = USE_COOKIE
    else:
        # 未指定或其他类型，使用默认行为
        use_cookie = USE_COOKIE
        if not EMAIL or not PASSWORD:
            logger.warning("未在配置或环境变量中找到 AnyRouter 凭据")
            logger.warning("将使用默认的 LinuxDo OAuth 登录")
            logger.info("可设置: export ANYROUTER_EMAIL='your_email' ANYROUTER_PASSWORD='your_password'")

    # 运行登录
    success = login_to_anyrouter(
        use_cookie=use_cookie,
        headless=HEADLESS,
        email=EMAIL,
        password=PASSWORD,
        login_type=LOGIN_TYPE,
    )
    
    if not success:
        logger.error("登录失败")
        import sys
        sys.exit(1)
