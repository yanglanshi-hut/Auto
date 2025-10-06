"""OpenI 站点的云脑任务交互。

本模块提供 `CloudTaskManager`，封装查看仪表盘信息、导航至云脑任务页面，
以及启动或停止任务的逻辑。
"""

from __future__ import annotations

import time
from typing import Optional

from playwright.sync_api import Page

from src.core.logger import setup_logger
from src.core.paths import get_project_paths


logger = setup_logger("openi.cloud_task", get_project_paths().logs / "openi_automation.log")


class CloudTaskManager:
    """OpenI 云脑任务的高层操作封装。"""

    def __init__(self, task_name: str, run_duration: int = 5) -> None:
        self.task_name = task_name
        self.run_duration = run_duration

    # ----- 仪表盘辅助 -----
    def show_dashboard_info(self, page: Page) -> None:
        logger.info("\n用户仪表盘信息")
        try:
            contributions = page.get_by_text('total contributions in the last 12 months')
            if contributions.is_visible():
                logger.info(f"  - {contributions.inner_text()}")
        except Exception:
            pass

        try:
            projects_heading = page.get_by_role('heading', name='项目列表')
            if projects_heading.is_visible():
                logger.info("  - 项目列表已加载")
        except Exception:
            pass

    # ----- 导航与弹窗 -----
    def navigate_to_cloud_task(self, page: Page) -> None:
        logger.info("\n导航到云脑任务页面...")
        page.get_by_role('link', name='云脑任务').click()
        page.wait_for_url('**/cloudbrains', timeout=30000)
        logger.info("已进入云脑任务页面")

        logger.info("检查并关闭云脑任务页面弹窗...")
        page.wait_for_timeout(2000)

        logger.info("\n云脑任务信息:")
        try:
            task_count = page.get_by_text('共 3 个')
            if task_count.is_visible():
                logger.info(f"  - {task_count.inner_text()}")
        except Exception:
            pass

        logger.info("  - 任务列表已加载")

    # ----- 任务基础操作 -----
    def wait_for_task_status(self, page: Page, target_status: str, timeout: int = 30) -> bool:
        logger.info(f"等待任务状态变为 {target_status}...")
        for _ in range(timeout):
            time.sleep(1)
            try:
                status_cell = page.locator(f'td:has-text("{target_status}")').first
                if status_cell.is_visible():
                    logger.info(f"  - 任务状态已变为 {target_status}")
                    return True
            except Exception:
                continue
        logger.warning(f"  - 等待超时，未能在 {timeout} 秒内变为 {target_status} 状态")
        return False

    def get_task_status(self, page: Page) -> Optional[str]:
        try:
            status_cell = page.locator(
                'td:has-text("RUNNING"), td:has-text("STOPPED"), td:has-text("WAITING"), td:has-text("STOPPING")'
            ).first
            if status_cell.is_visible():
                return status_cell.inner_text().strip()
        except Exception:
            pass
        return None

    def stop_task(self, page: Page, *, wait_for_stopped: bool = True, timeout: int = 30) -> bool:
        try:
            logger.info("点击停止按钮...")
            stop_button = page.get_by_role('link', name='停止')
            stop_button.click()
            logger.info("  - 已点击停止按钮")

            if wait_for_stopped:
                return self.wait_for_task_status(page, 'STOPPED', timeout)
            return True
        except Exception as exc:
            logger.error(f"停止任务失败: {exc}")
            return False

    # ----- 高层流程 -----
    def handle_cloud_task(self, page: Page) -> None:
        logger.info(f"\n搜索任务 '{self.task_name}'...")
        search_input = page.get_by_role('textbox', name='搜索任务名称')
        search_input.fill(self.task_name)
        search_input.press('Enter')
        page.wait_for_timeout(2000)
        logger.info("搜索完成")

        logger.info("\n检查任务状态...")
        page.wait_for_timeout(2000)
        task_status = self.get_task_status(page)
        if task_status:
            logger.info(f"  - 当前任务状态 {task_status}")

        if task_status == 'RUNNING':
            logger.info("\n任务正在运行，需要先停止...")
            self.stop_task(page, wait_for_stopped=True, timeout=30)
            task_status = 'STOPPED'

        if task_status in ['STOPPED', None]:
            logger.info("\n点击'再次调试'按钮...")
            page.wait_for_timeout(3000)
            try:
                debug_again_button = page.get_by_role('link', name='再次调试')
                debug_again_button.wait_for(state='visible', timeout=10000)
                if debug_again_button.is_enabled():
                    debug_again_button.click()
                    logger.info("  - 已点击'再次调试'")
                else:
                    logger.warning("  - '再次调试'按钮被禁用，跳过任务启动")
                    return
            except Exception as exc:
                logger.error(f"  - 无法点击'再次调试'按钮: {exc}")
                return

            page.wait_for_timeout(5000)
            running_ok = self.wait_for_task_status(page, 'RUNNING', timeout=60)

            if running_ok:
                logger.info(f"\n任务运行中，等待{self.run_duration}秒...")
                time.sleep(self.run_duration)
            else:
                logger.warning("\n任务启动超时，尝试停止任务...")

            self.stop_task(page, wait_for_stopped=False)
            page.wait_for_timeout(2000)
            logger.info("任务操作完成")


__all__ = ["CloudTaskManager"]

