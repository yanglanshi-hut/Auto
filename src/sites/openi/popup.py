"""OpenI 站点的弹窗处理工具。

封装在仪表盘和云脑任务页面上可能出现的各类模态对话框的关闭逻辑。
"""

from __future__ import annotations

from playwright.sync_api import Page

from src.core.logger import setup_logger
from src.core.paths import get_project_paths


logger = setup_logger("openi.popup", get_project_paths().logs / "openi_automation.log")


class PopupHandler:
    """关闭 OpenI 页面上的常见弹窗。

    方法以防御性方式实现：当不存在预期元素时将静默忽略。
    """

    def close_popup(self, page: Page) -> None:
        """尝试关闭当前页面上可见的弹窗。"""
        # 若存在“不要再次提醒”复选框则尝试勾选
        try:
            no_reminder_checkbox = page.locator('input[name="notRemindAgain"]').first
            if no_reminder_checkbox.is_visible():
                no_reminder_checkbox.click()
                logger.info("  - 已勾选'不再提醒'")
        except Exception:
            pass

        # 尝试点击标注为“关闭”的按钮或元素
        try:
            close_buttons = page.get_by_text('关闭').all()
            if close_buttons:
                for button in close_buttons:
                    try:
                        if button.is_visible():
                            button.click()
                            logger.info("  - 已点击关闭按钮")
                            page.wait_for_timeout(500)
                            break
                    except Exception:
                        continue
        except Exception:
            pass


__all__ = ["PopupHandler"]

