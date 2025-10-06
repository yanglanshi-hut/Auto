"""Run OpenI automation for one or more users (CLI entry)."""

from __future__ import annotations

import time

from src.core.logger import setup_logger
from src.core.paths import get_project_paths
from src.sites.openi.config import load_config
from src.sites.openi.login import OpeniLogin


logger = setup_logger("openi.runner", get_project_paths().logs / "openi_automation.log")


def main() -> None:
    """主函数：加载配置并依次处理所有用户。"""
    logger.info("=" * 60)
    logger.info("OpenI 平台多用户自动化脚本")
    logger.info("=" * 60)

    try:
        config_data = load_config()
        users = config_data['users']
        config = config_data.get('config', {})

        task_name = config.get('task_name', 'image')
        run_duration = config.get('run_duration', 15)
        headless = config.get('headless', False)
        use_cookies = config.get('use_cookies', True)
        cookie_expire_days = config.get('cookie_expire_days', 7)

        total_users = len(users)
        success_count = 0
        failed_users = []

        logger.info(f"\n共有 {total_users} 个用户需要处理")
        logger.info(f"任务配置: task_name={task_name}, run_duration={run_duration}s, headless={headless}")
        logger.info(f"Cookie 配置: use_cookies={use_cookies}, expire_days={cookie_expire_days}")
        logger.info("=" * 60)

        for index, user in enumerate(users, 1):
            username = user['username']
            password = user['password']

            logger.info(f"\n[{index}/{total_users}] 正在处理用户: {username}")
            logger.info("-" * 60)

            automation = OpeniLogin(
                username=username,
                headless=headless,
                task_name=task_name,
                run_duration=run_duration,
                use_cookies=use_cookies,
                cookie_expire_days=cookie_expire_days,
            )

            try:
                success = automation.run(
                    use_cookie=use_cookies,
                    verify_url='https://git.openi.org.cn/dashboard',
                    cookie_expire_days=cookie_expire_days,
                    password=password,
                )
            except Exception:
                success = False

            if success:
                success_count += 1
            else:
                failed_users.append(username)

            if index < total_users:
                logger.info("\n等待 3 秒后处理下一个用户...")
                time.sleep(3)

        logger.info("\n" + "=" * 60)
        logger.info("执行完成！汇总报告")
        logger.info("=" * 60)
        logger.info(f"总用户数: {total_users}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {len(failed_users)}")

        if failed_users:
            logger.warning(f"失败用户列表: {', '.join(failed_users)}")

        logger.info("=" * 60)

    except FileNotFoundError as exc:
        logger.error(f"\n{exc}")
    except Exception as exc:
        logger.error(f"\n发生错误: {exc}")
        raise


__all__ = ["main"]

