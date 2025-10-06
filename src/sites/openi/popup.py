"""Popup handling utilities for the OpenI site.

Encapsulates the logic to dismiss various modal dialogs that may appear
on dashboard and cloud task pages.
"""

from __future__ import annotations

from playwright.sync_api import Page

from src.core.logger import setup_logger
from src.core.paths import get_project_paths


logger = setup_logger("openi.popup", get_project_paths().logs / "openi_automation.log")


class PopupHandler:
    """Dismiss common popups shown on OpenI pages.

    Methods are defensive and will quietly do nothing if the expected
    elements are not present.
    """

    def close_popup(self, page: Page) -> None:
        """Attempt to close any visible popups on the current page."""
        # Try the "do not remind again" checkbox if present
        try:
            no_reminder_checkbox = page.locator('input[name="notRemindAgain"]').first
            if no_reminder_checkbox.is_visible():
                no_reminder_checkbox.click()
                logger.info("  - 已勾选'不再提醒'")
        except Exception:
            pass

        # Try to click any buttons or elements labeled "关闭"
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

