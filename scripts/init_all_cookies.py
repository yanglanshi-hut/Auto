#!/usr/bin/env python3
"""批量初始化多用户 Cookie 的脚本。

- 读取 config/users.json
- 为各站点/用户执行一次登录以生成 Cookie
  * linuxdo: 通过 `xvfb-run python -m src linuxdo`
  * openi:   直接调用 OpeniLogin 执行账号密码登录

使用示例：
  python scripts/init_all_cookies.py
  python scripts/init_all_cookies.py --site linuxdo
  python scripts/init_all_cookies.py --site openi --user yls
"""

from __future__ import annotations

import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List
import sys
import os

# 允许脚本直接运行时找到本地 src 包
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.config import UnifiedConfigManager
from src.core.paths import get_project_paths


def setup_logging() -> Path:
    """配置同时输出到终端和文件的日志。

    日志文件：logs/cookie_init_YYYYMMDD_HHMMSS.log
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = get_project_paths().logs
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"cookie_init_{ts}.log"

    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # 控制台
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(sh)

    # 文件
    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(fh)

    return log_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化所有用户的 Cookie")
    parser.add_argument("--site", help="仅处理指定站点，例如 openi 或 linuxdo")
    parser.add_argument("--user", help="仅处理指定用户名/邮箱")
    return parser.parse_args()


def load_users_from_config(cfg_mgr: UnifiedConfigManager) -> Dict:
    """使用 UnifiedConfigManager 读取配置原始数据。"""
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
            # openi 使用 username，linuxdo 使用 email
            uname = u.get("username")
            email = u.get("email")
            if user_key not in (uname, email):
                continue
        result.append(u)
    return result


def run_linuxdo() -> bool:
    """通过子进程运行 linuxdo 登录以生成 Cookie。"""
    project_root = get_project_paths().root
    cmd = ["xvfb-run", "python", "-m", "src", "linuxdo"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            timeout=180,
            check=False,
        )
        return proc.returncode == 0
    except FileNotFoundError:
        logging.warning("未找到 xvfb-run，回退为直接运行 python -m src linuxdo")
        try:
            proc = subprocess.run(
                ["python", "-m", "src", "linuxdo"],
                cwd=str(project_root),
                timeout=180,
                check=False,
            )
            return proc.returncode == 0
        except Exception as exc:  # noqa: BLE001
            logging.error(f"运行 linuxdo 登录失败: {exc}")
            return False
    except Exception as exc:  # noqa: BLE001
        logging.error(f"运行 linuxdo 登录失败: {exc}")
        return False


def run_openi(user: Dict, config_data: Dict) -> bool:
    """直接调用 OpeniLogin 初始化 Cookie。"""
    try:
        from src.sites.openi.login import OpeniLogin
        from src.sites.openi.config import load_config
    except Exception as exc:  # pragma: no cover
        logging.error(f"导入 OpenI 模块失败: {exc}")
        return False

    # 允许按需求加载配置（与现有实现保持一致）
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
    cookie_expire_days = int(cfg_config.get("cookie_expire_days", 30))

    try:
        automation = OpeniLogin(
            username=username,
            headless=True,
            task_name=task_name,
            run_duration=run_duration,
            use_cookies=True,
            cookie_expire_days=cookie_expire_days,
        )
        # 为初始化 Cookie，若不存在 Cookie 会自动走账密并保存
        ok = automation.run(
            use_cookie=True,
            verify_url="https://git.openi.org.cn/dashboard",
            cookie_expire_days=cookie_expire_days,
            password=password,
        )
        return bool(ok)
    except Exception as exc:  # noqa: BLE001
        logging.error(f"OpenI 用户 {username} 初始化失败: {exc}")
        return False


def main() -> int:
    args = parse_args()
    log_file = setup_logging()
    logging.info(f"日志文件: {log_file}")

    cfg_mgr = UnifiedConfigManager()
    data = load_users_from_config(cfg_mgr)
    users = data.get("users", []) or []
    if not users:
        logging.error("配置中未找到任何用户（users 为空）")
        return 1

    targets = filter_users(users, args.site, args.user)
    if not targets:
        logging.warning("没有匹配到需要处理的用户")
        return 0

    success, failed = 0, 0
    for idx, user in enumerate(targets, 1):
        site = str(user.get("site", "")).lower()
        who = user.get("username") or user.get("email") or "<unknown>"
        logging.info(f"[{idx}/{len(targets)}] 开始处理: site={site}, 用户={who}")

        try:
            if site == "linuxdo":
                ok = run_linuxdo()
            elif site == "openi":
                ok = run_openi(user, data)
            else:
                logging.warning(f"未知站点，跳过: {site}")
                ok = False
        except Exception as exc:  # noqa: BLE001
            logging.error(f"处理用户 {who} 出错: {exc}")
            ok = False

        if ok:
            logging.info(f"处理成功: {who}")
            success += 1
        else:
            logging.error(f"处理失败: {who}")
            failed += 1

    logging.info(f"完成。成功 {success} 个，失败 {failed} 个")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
