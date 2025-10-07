"""ShareYourCC OAuth 通用辅助方法"""

from typing import Optional
from playwright.sync_api import Page
from src.core.logger import setup_logger
from src.core.paths import get_project_paths

logger = setup_logger("shareyourcc_oauth", get_project_paths().logs / "shareyourcc.log")


def click_oauth_button(page: Page, provider: str) -> Optional[Page]:
    """通用 OAuth 按钮点击方法
    
    Args:
        page: Playwright 页面对象
        provider: OAuth 提供商 ('linuxdo', 'google', 'github')
    
    Returns:
        OAuth 授权页面（可能是新窗口或当前页面）
    """
    provider_names = {
        'linuxdo': ['LINUX DO', 'LinuxDo', '使用 LINUX DO 登录'],
        'google': ['GOOGLE', 'Google', '使用 GOOGLE 登录', '使用 Google 登录'],
        'github': ['GITHUB', 'GitHub', '使用 GITHUB 登录', '使用 GitHub 登录'],
    }
    
    names = provider_names.get(provider.lower(), [])
    if not names:
        logger.error(f"不支持的 OAuth 提供商: {provider}")
        return None
    
    logger.info(f"点击 {provider} OAuth 按钮...")
    
    # 等待对话框内容加载完成
    page.wait_for_timeout(2000)
    
    # 构建选择器（优先在 dialog 内查找）
    oauth_selectors = []
    for name in names:
        oauth_selectors.extend([
            f'dialog button:has-text("{name}")',  # 优先对话框内的按钮
            f'[role="dialog"] button:has-text("{name}")',  # ARIA 对话框
            f'.modal button:has-text("{name}")',  # 模态框内
            f'button:has-text("{name}")',  # 普通按钮
        ])
    
    # 尝试点击并捕获新窗口
    for selector in oauth_selectors:
        try:
            button = page.locator(selector).first
            if button.count() > 0:
                logger.info(f"找到 {provider} OAuth 按钮: {selector}")
                
                # 确保按钮可见并可点击
                try:
                    button.scroll_into_view_if_needed(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                
                # 尝试捕获新窗口
                try:
                    with page.expect_popup(timeout=5000) as popup_info:
                        button.click(timeout=5000, force=False)
                    
                    auth_page = popup_info.value
                    auth_page.wait_for_load_state('domcontentloaded')
                    logger.info(f"{provider} OAuth 在新窗口打开: {auth_page.url}")
                    return auth_page
                except Exception as popup_exc:
                    logger.debug(f"没有新窗口弹出: {popup_exc}")
                    # 没有新窗口，检查是否在当前页面跳转
                    page.wait_for_timeout(3000)
                    page.wait_for_load_state('domcontentloaded', timeout=10000)
                    
                    current_url = page.url
                    if '/oauth' in current_url or '/auth' in current_url or 'github.com' in current_url or 'google.com' in current_url or 'linux.do' in current_url:
                        logger.info(f"{provider} OAuth 在当前页面打开: {current_url}")
                        return page
                    
                    logger.warning(f"点击后页面未跳转，当前 URL: {current_url}")
        except Exception as exc:
            logger.debug(f"尝试选择器 {selector} 失败: {exc}")
            continue
    
    logger.warning(f"未找到 {provider} OAuth 按钮")
    return None


def confirm_google_oauth_consent(auth_page: Page) -> bool:
    """确认 Google OAuth 授权
    
    注意：Google OAuth 已授权的应用会自动跳转，无需手动确认。
    只有首次授权时才需要点击确认按钮。
    """
    if 'google.com' not in auth_page.url and 'accounts.google.com' not in auth_page.url:
        logger.info("已跳转离开 Google，授权完成")
        return True
    
    logger.info("在 Google OAuth 页面，检查是否需要授权...")
    
    # 等待页面加载和可能的自动跳转
    max_wait = 10  # 最多等待 10 秒
    for i in range(max_wait):
        auth_page.wait_for_timeout(1000)
        
        # 检查是否已经跳转离开 Google
        if 'google.com' not in auth_page.url and 'accounts.google.com' not in auth_page.url:
            logger.info(f"Google 自动跳转完成（{i+1}秒后）")
            return True
    
    # 如果还在 Google 页面，说明可能需要手动授权（首次授权）
    logger.info("Google 未自动跳转，可能需要手动授权（首次授权或需要重新授权）")
    logger.warning("请在浏览器中手动完成 Google 授权")
    
    # 等待用户手动操作或自动跳转
    for i in range(30):  # 等待最多 30 秒
        auth_page.wait_for_timeout(1000)
        if 'google.com' not in auth_page.url and 'accounts.google.com' not in auth_page.url:
            logger.info(f"Google 授权完成（手动操作后 {i+1}秒）")
            return True
    
    logger.warning("Google 授权超时，但继续执行")
    return True


def confirm_github_oauth_consent(auth_page: Page) -> bool:
    """确认 GitHub OAuth 授权
    
    注意：GitHub OAuth 已授权的应用会自动跳转，无需手动确认。
    只有首次授权或权限更新时才需要点击 Authorize 按钮。
    """
    if 'github.com' not in auth_page.url:
        logger.info("已跳转离开 GitHub，授权完成")
        return True
    
    logger.info("在 GitHub OAuth 页面，检查是否需要授权...")
    
    # 等待页面加载和可能的自动跳转
    max_wait = 10  # 最多等待 10 秒
    for i in range(max_wait):
        auth_page.wait_for_timeout(1000)
        
        # 检查是否已经跳转离开 GitHub
        if 'github.com' not in auth_page.url:
            logger.info(f"GitHub 自动跳转完成（{i+1}秒后）")
            return True
        
        # 检查是否有授权按钮（首次授权）
        authorize_selectors = [
            'button[type="submit"]:has-text("Authorize")',
            'button:has-text("Authorize")',
            'input[type="submit"][value*="Authorize"]',
            'button[name="authorize"]',
        ]
        
        for selector in authorize_selectors:
            try:
                button = auth_page.locator(selector).first
                if button.count() > 0:
                    logger.info(f"发现授权按钮（首次授权），点击: {selector}")
                    button.click(timeout=3000)
                    auth_page.wait_for_timeout(2000)
                    # 点击后继续等待跳转
                    break
            except Exception:
                continue
    
    # 最终检查是否跳转成功
    if 'github.com' not in auth_page.url:
        logger.info("GitHub 授权完成")
        return True
    
    logger.warning("GitHub 仍在授权页面，可能需要手动操作")
    # 继续等待一段时间
    for i in range(20):
        auth_page.wait_for_timeout(1000)
        if 'github.com' not in auth_page.url:
            logger.info(f"GitHub 授权完成（额外等待 {i+1}秒后）")
            return True
    
    logger.warning("GitHub 授权超时，但继续执行")
    return True


def confirm_linuxdo_oauth_consent(auth_page: Page) -> bool:
    """确认 LinuxDO OAuth 授权"""
    if 'linux.do' not in auth_page.url:
        logger.info("已跳转，跳过 LinuxDO 授权确认")
        return True
    
    # 勾选"记住授权"
    remember_checkbox = auth_page.locator('role=checkbox[name="记住这次授权"]')
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
