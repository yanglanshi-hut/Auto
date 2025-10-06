#!/usr/bin/env python3
"""Auto 登录自动化的统一命令行入口。

使用示例：
  python -m src anyrouter           # 登录 anyrouter
  python -m src linuxdo             # 登录 linuxdo
  python -m src openi               # 根据配置登录所有 OpenI 用户
  python -m src openi --user yls    # 登录指定的 OpenI 用户
  python -m src --help              # 显示帮助

该 CLI 作为对位于 `src/sites/<site>/login.py` 的各站点脚本的轻量封装，
不修改这些模块，并转发通用选项例如 `--headless` 与 `--no-cookie`。
"""

from __future__ import annotations

import sys
import io

# 设置全局 UTF-8 编码（必须在所有 import 之前）
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
from typing import Optional


def _add_common_options(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: off)",
    )
    sp.add_argument(
        "--no-cookie",
        dest="no_cookie",
        action="store_true",
        help="Do not attempt cookie login (default: use cookies if available)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="Unified CLI for Auto login automation (Playwright)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="site", metavar="site", required=True)

    # anyrouter 子命令
    sp_any = subparsers.add_parser(
        "anyrouter",
        help="Login to anyrouter via LinuxDO OAuth",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_any)
    sp_any.set_defaults(handler=_handle_anyrouter)

    # linuxdo 子命令
    sp_ld = subparsers.add_parser(
        "linuxdo",
        help="Login to linuxdo forum",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_ld)
    # 为保持范围最小，这里不直接暴露账号密码参数。
    sp_ld.set_defaults(handler=_handle_linuxdo)

    # openi 子命令
    sp_openi = subparsers.add_parser(
        "openi",
        help="Login to OpenI; supports multi-user or a specific user",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_openi)
    sp_openi.add_argument(
        "--user",
        dest="user",
        help="Specific OpenI username from config/users.json (default: all users)",
    )
    sp_openi.set_defaults(handler=_handle_openi)

    return parser


def _handle_anyrouter(args: argparse.Namespace) -> int:
    try:
        from src.sites.anyrouter.login import login_to_anyrouter
    except Exception as exc:  # pragma: no cover - 导入错误路径
        print(f"Failed to import anyrouter login module: {exc}")
        return 2

    use_cookie = not args.no_cookie
    ok = False
    try:
        ok = login_to_anyrouter(use_cookie=use_cookie, headless=args.headless)
    except SystemExit as e:  # 允许底层脚本有意退出
        return int(e.code) if e.code is not None else 1
    except Exception as exc:
        print(f"anyrouter login failed: {exc}")
        ok = False
    return 0 if ok else 1


def _handle_linuxdo(args: argparse.Namespace) -> int:
    try:
        from src.sites.linuxdo.login import login_to_linuxdo
    except Exception as exc:  # pragma: no cover - 覆盖率忽略
        print(f"Failed to import linuxdo login module: {exc}")
        return 2

    use_cookie = not args.no_cookie
    ok = False
    try:
        # 这里不暴露邮箱/密码；优先尝试使用 Cookie 登录
        ok = login_to_linuxdo(use_cookie=use_cookie, headless=args.headless)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    except Exception as exc:
        print(f"linuxdo login failed: {exc}")
        ok = False
    return 0 if ok else 1


def _handle_openi(args: argparse.Namespace) -> int:
    # 若未指定具体用户，则调用现有的多用户主流程
    if not args.user:
        try:
            from src.sites.openi.runner import main as openi_main
        except Exception as exc:  # pragma: no cover - 覆盖率忽略
            print(f"Failed to import openi login module: {exc}")
            return 2

        try:
            openi_main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 1
        except Exception as exc:
            print(f"openi login (all users) failed: {exc}")
            return 1

    # 指定用户：加载配置并仅为该用户运行 OpeniLogin
    try:
        from src.sites.openi.config import load_config
        from src.sites.openi.login import OpeniLogin
    except Exception as exc:  # pragma: no cover - 覆盖率忽略
        print(f"Failed to import openi utilities: {exc}")
        return 2

    try:
        cfg = load_config()
    except Exception as exc:
        print(f"Failed to load OpenI config: {exc}")
        return 1

    username: str = args.user
    users = cfg.get("users", []) or []
    user_entry = next((u for u in users if u.get("username") == username), None)
    if not user_entry:
        print(
            f"User '{username}' not found in config/users.json. "
            f"Available users: {', '.join(u.get('username','?') for u in users) or 'none'}"
        )
        return 1

    config = cfg.get("config", {})
    task_name: str = config.get("task_name", "image")
    run_duration: int = int(config.get("run_duration", 15))
    cookie_expire_days: int = int(config.get("cookie_expire_days", 30))

    use_cookie = not args.no_cookie

    try:
        automation = OpeniLogin(
            username=username,
            headless=args.headless,
            task_name=task_name,
            run_duration=run_duration,
            use_cookies=use_cookie,
            cookie_expire_days=cookie_expire_days,
        )
        ok = automation.run(
            use_cookie=use_cookie,
            verify_url='https://git.openi.org.cn/dashboard',
            cookie_expire_days=cookie_expire_days,
            password=user_entry.get("password"),
        )
        return 0 if ok else 1
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    except Exception as exc:
        print(f"openi login (user {username}) failed: {exc}")
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return int(handler(args))


if __name__ == "__main__":
    sys.exit(main())
