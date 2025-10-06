#!/usr/bin/env python3
"""批量刷新多用户 Cookie 的脚本。

- 检测各用户 Cookie 文件年龄
- 超过阈值(>20天)或 --force 时触发登录刷新
- 支持 --dry-run 仅检测不执行刷新
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# 允许脚本直接执行时找到本地 src 包
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.config import UnifiedConfigManager  # noqa: E402
from src.core.cookies import CookieManager  # noqa: E402
from src.core.paths import get_project_paths  # noqa: E402


def setup_logging() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = get_project_paths().logs
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"cookie_refresh_{ts}.log"

    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(sh)

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(fh)

    return log_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="刷新所有用户的 Cookie")
    parser.add_argument("--force", action="store_true", help="强制刷新所有 Cookie（忽略年龄检查）")
    parser.add_argument("--dry-run", action="store_true", help="仅检测，不执行刷新")
    parser.add_argument("--site", help="仅处理指定站点，例如 openi 或 linuxdo")
    parser.add_argument("--user", help="仅处理指定用户名/邮箱")
    return parser.parse_args()


def load_users(cfg_mgr: UnifiedConfigManager) -> Dict:
    data = cfg_mgr._load_once()
    if not isinstance(data, dict):
        return {"users": [], "config": {}}
    return data


def filter_users(users: Iterable[Dict], site: str | None, user_key: str | None) -> List[Dict]:
    result: List[Dict] = []
    for u in users:
        if not isinstance(u, dict):
            continue
        s = str(u.get("site", "")).lower()
        if site and s != site.lower():
            continue
        if user_key:
            uname = u.get("username")
            email = u.get("email")
            if user_key not in (uname, email):
                continue
        result.append(u)
    return result


def cookie_info_for_user(user: Dict) -> Tuple[str, Path]:
    cm = CookieManager()
    site = str(user.get("site", "")).lower()
    if site == "openi":
        username = user.get("username") or ""
        site_name = f"openi_{username}"
    else:
        site_name = site or ""
    return site, cm.get_cookie_path(site_name)


def file_age_days(path: Path) -> float:
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)
    delta = datetime.now() - mtime
    return delta.total_seconds() / 86400.0


def refresh_linuxdo(cookie_expire_override: int = 0) -> bool:
    """使用 xvfb-run 包装统一 CLI，强制忽略旧 Cookie。"""
    import subprocess

    cmd = ["xvfb-run", "python", "-m", "src", "linuxdo", "--no-cookie"]
    try:
        res = subprocess.run(cmd, cwd=str(get_project_paths().root), timeout=180, check=False)
        return res.returncode == 0
    except FileNotFoundError:
        logging.error("未找到 xvfb-run，请先安装：apt-get update && apt-get install -y xvfb")
        return False
    except subprocess.TimeoutExpired:
        logging.error("LinuxDO 刷新超时 (180s)")
        return False


def refresh_openi(user: Dict, config_data: Dict, cookie_expire_override: int = 0) -> bool:
    try:
        from src.sites.openi.login import OpeniLogin
        from src.sites.openi.config import load_config
    except Exception as exc:  # pragma: no cover
        logging.error(f"导入 OpenI 模块失败: {exc}")
        return False

    try:
        cfg = load_config()
        cfg_config = cfg.get("config", {})
    except Exception:
        cfg_config = config_data.get("config", {}) if isinstance(config_data, dict) else {}

    username = user.get("username")
    password = user.get("password")
    if not username or not password:
        logging.error("缺少 OpenI 用户名或密码")
        return False

    task_name = cfg_config.get("task_name", "image")
    run_duration = int(cfg_config.get("run_duration", 15))
    default_expire = int(cfg_config.get("cookie_expire_days", 30))

    try:
        automation = OpeniLogin(
            username=username,
            headless=True,
            task_name=task_name,
            run_duration=run_duration,
            use_cookies=True,
            cookie_expire_days=default_expire,
        )
        ok = automation.run(
            use_cookie=False,
            verify_url="https://git.openi.org.cn/dashboard",
            cookie_expire_days=cookie_expire_override,
            password=password,
        )
        return bool(ok)
    except Exception as exc:  # noqa: BLE001
        logging.error(f"刷新 OpenI 用户 {username} Cookie 失败: {exc}")
        return False


def main() -> int:
    args = parse_args()
    log_file = setup_logging()
    logging.info(f"日志文件: {log_file}")

    cfg_mgr = UnifiedConfigManager()
    data = load_users(cfg_mgr)
    users = data.get("users", []) or []
    if not users:
        logging.error("配置中未找到任何用户（users 为空）")
        return 1

    targets = filter_users(users, args.site, args.user)
    if not targets:
        logging.warning("没有匹配到需要处理的用户")
        return 0

    refreshed, skipped, failed = 0, 0, 0
    for idx, user in enumerate(targets, 1):
        site, cookie_path = cookie_info_for_user(user)
        who = user.get("username") or user.get("email") or "<unknown>"
        logging.info(f"[{idx}/{len(targets)}] 检查: site={site}, 用户={who}")

        if not cookie_path.exists():
            logging.info("Cookie 文件不存在，视为需要刷新")
            need_refresh = True
            age = None
        else:
            age = file_age_days(cookie_path)
            logging.info(f"Cookie 文件: {cookie_path}，年龄约 {age:.1f} 天")
            need_refresh = age > 20.0 or args.force

        if args.dry_run:
            logging.info("[Dry-Run] %s", "准备刷新" if need_refresh else "跳过")
            skipped += 0 if need_refresh else 1
            refreshed += 1 if need_refresh else 0
            continue

        if not need_refresh:
            logging.info("年龄未超过阈值，跳过")
            skipped += 1
            continue

        try:
            if site == "linuxdo":
                ok = refresh_linuxdo(cookie_expire_override=0)
            elif site == "openi":
                ok = refresh_openi(user, data, cookie_expire_override=0)
            else:
                logging.warning(f"未知站点，跳过: {site}")
                ok = False
        except Exception as exc:  # noqa: BLE001
            logging.error(f"刷新用户 {who} 出错: {exc}")
            ok = False

        if ok:
            logging.info("刷新完成")
            refreshed += 1
        else:
            logging.error("刷新失败")
            failed += 1

    logging.info(f"完成。刷新 {refreshed} 个，跳过 {skipped} 个，失败 {failed} 个")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
