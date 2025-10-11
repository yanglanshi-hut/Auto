#!/usr/bin/env python3
"""Auto 登录自动化的统一命令行入口。

使用示例：
  python -m src anyrouter           # 登录 anyrouter
  python -m src linuxdo             # 登录 linuxdo
  python -m src shareyourcc         # 登录 shareyourcc
  python -m src github              # 登录 github
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
        help="在无头模式下运行浏览器（默认：关闭）",
    )
    sp.add_argument(
        "--no-cookie",
        dest="no_cookie",
        action="store_true",
        help="不尝试使用Cookie登录（默认：如果有Cookie则使用）",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="Auto 登录自动化统一命令行界面 (基于 Playwright)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="site", metavar="站点", required=True)

    # anyrouter 子命令
    sp_any = subparsers.add_parser(
        "anyrouter",
        help="通过 LinuxDO OAuth 登录 AnyRouter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_any)
    sp_any.add_argument(
        "--user",
        dest="user",
        help="指定 config/users.json 中的 login_type（例如：'github_oauth'、'linuxdo_oauth'、'credentials'）",
    )
    sp_any.set_defaults(handler=_handle_anyrouter)

    # linuxdo 子命令
    sp_ld = subparsers.add_parser(
        "linuxdo",
        help="登录 LinuxDO 论坛",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_ld)
    # 为保持范围最小，这里不直接暴露账号密码参数。
    sp_ld.set_defaults(handler=_handle_linuxdo)

    # openi 子命令
    sp_openi = subparsers.add_parser(
        "openi",
        help="登录 OpenI；支持多用户或指定用户",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_openi)
    sp_openi.add_argument(
        "--user",
        dest="user",
        help="指定 config/users.json 中的 OpenI 用户名（默认：所有用户）",
    )
    sp_openi.set_defaults(handler=_handle_openi)

    # shareyourcc 子命令
    sp_sycc = subparsers.add_parser(
        "shareyourcc",
        help="通过邮箱/密码或 LinuxDO OAuth 登录 ShareYourCC",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_sycc)
    sp_sycc.set_defaults(handler=_handle_shareyourcc)

    # github 子命令
    sp_gh = subparsers.add_parser(
        "github",
        help="登录 GitHub",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common_options(sp_gh)
    sp_gh.set_defaults(handler=_handle_github)

    return parser


def _handle_anyrouter(args: argparse.Namespace) -> int:
    """处理 AnyRouter 登录（支持多用户配置）"""
    try:
        from src.sites.anyrouter.login import AnyrouterLogin
        from src.core.config import UnifiedConfigManager
    except Exception as exc:
        print(f"导入 AnyRouter 登录模块失败: {exc}")
        return 2

    use_cookie = not args.no_cookie
    
    try:
        # 获取所有 AnyRouter 用户配置
        config_mgr = UnifiedConfigManager()
        all_users = config_mgr.get_all_users('anyrouter')
        
        # 如果没有配置文件中的用户，尝试从环境变量获取
        if not all_users:
            env_creds = config_mgr.get_credentials('anyrouter', fallback_env=True)
            if env_creds:
                all_users = [env_creds]
            else:
                print("未找到 AnyRouter 用户配置")
                print("请在 config/users.json 中添加 AnyRouter 配置")
                return 1
        
        # 如果指定了 --user，只处理该 login_type 的用户
        if args.user:
            target_login_type = args.user.lower()
            filtered_users = [
                u for u in all_users 
                if u.get('login_type', 'linuxdo_oauth').lower() == target_login_type
            ]
            
            if not filtered_users:
                print(f"未找到 login_type 为 '{args.user}' 的 AnyRouter 用户")
                available_types = set(u.get('login_type', 'linuxdo_oauth') for u in all_users)
                print(f"可用的 login_type: {', '.join(available_types)}")
                return 1
            
            all_users = filtered_users
            print(f"使用单用户模式，login_type: {args.user}")
        
        print(f"找到 {len(all_users)} 个 AnyRouter 用户配置")
        
        # 循环处理每个用户
        failed_count = 0
        for idx, user_config in enumerate(all_users, 1):
            login_type = user_config.get('login_type', 'linuxdo_oauth')
            email = user_config.get('email', 'N/A')
            print(f"\n{'='*60}")
            print(f"[{idx}/{len(all_users)}] 处理 AnyRouter 用户 (login_type: {login_type}, email: {email})")
            print(f"{'='*60}")
            
            try:
                # 创建实例时传递 login_type，以区分不同用户的 Cookie
                automation = AnyrouterLogin(headless=args.headless, login_type=login_type)
                ok = automation.run(
                    use_cookie=use_cookie,
                    verify_url='https://anyrouter.top/console/token',
                    **user_config
                )
                
                if ok:
                    print(f"✅ 用户 {idx} 登录成功 (login_type: {login_type})")
                else:
                    print(f"❌ 用户 {idx} 登录失败 (login_type: {login_type})")
                    failed_count += 1
                    
            except SystemExit as e:
                print(f"❌ 用户 {idx} 登录异常退出 (login_type: {login_type})")
                failed_count += 1
            except Exception as exc:
                print(f"❌ 用户 {idx} 登录失败: {exc}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"完成！成功: {len(all_users) - failed_count}/{len(all_users)}, 失败: {failed_count}")
        print(f"{'='*60}\n")
        
        return 0 if failed_count == 0 else 1
        
    except Exception as exc:
        print(f"AnyRouter 多用户登录失败: {exc}")
        return 1


def _handle_linuxdo(args: argparse.Namespace) -> int:
    try:
        from src.sites.linuxdo.login import login_to_linuxdo
    except Exception as exc:  # pragma: no cover - 覆盖率忽略
        print(f"导入 LinuxDO 登录模块失败: {exc}")
        return 2

    use_cookie = not args.no_cookie
    ok = False
    try:
        # 这里不暴露邮箱/密码；优先尝试使用 Cookie 登录
        ok = login_to_linuxdo(use_cookie=use_cookie, headless=args.headless)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    except Exception as exc:
        print(f"LinuxDO 登录失败: {exc}")
        ok = False
    return 0 if ok else 1


def _handle_shareyourcc(args: argparse.Namespace) -> int:
    """处理 ShareYourCC 登录（支持多用户配置）"""
    try:
        from src.sites.shareyourcc.login import ShareyourccLogin
        from src.core.config import UnifiedConfigManager
    except Exception as exc:
        print(f"导入 ShareYourCC 登录模块失败: {exc}")
        return 2

    use_cookie = not args.no_cookie
    
    try:
        # 获取所有 ShareYourCC 用户配置
        config_mgr = UnifiedConfigManager()
        all_users = config_mgr.get_all_users('shareyourcc')
        
        # 如果没有配置文件中的用户，尝试从环境变量获取
        if not all_users:
            env_creds = config_mgr.get_credentials('shareyourcc', fallback_env=True)
            if env_creds:
                all_users = [env_creds]
            else:
                print("未找到 ShareYourCC 用户配置")
                print("请在 config/users.json 中添加 ShareYourCC 配置")
                return 1
        
        print(f"找到 {len(all_users)} 个 ShareYourCC 用户配置")
        
        # 循环处理每个用户
        failed_count = 0
        for idx, user_config in enumerate(all_users, 1):
            login_type = user_config.get('login_type', 'linuxdo_oauth')
            print(f"\n{'='*60}")
            print(f"[{idx}/{len(all_users)}] 处理 ShareYourCC 用户 (login_type: {login_type})")
            print(f"{'='*60}")
            
            try:
                # 创建实例时传递 login_type，以区分不同用户的 Cookie
                automation = ShareyourccLogin(headless=args.headless, login_type=login_type)
                ok = automation.run(
                    use_cookie=use_cookie,
                    verify_url='https://shareyour.cc/',
                    **user_config
                )
                
                if ok:
                    print(f"✅ 用户 {idx} 登录成功 (login_type: {login_type})")
                else:
                    print(f"❌ 用户 {idx} 登录失败 (login_type: {login_type})")
                    failed_count += 1
                    
            except SystemExit as e:
                print(f"❌ 用户 {idx} 登录异常退出 (login_type: {login_type})")
                failed_count += 1
            except Exception as exc:
                print(f"❌ 用户 {idx} 登录失败: {exc}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"完成！成功: {len(all_users) - failed_count}/{len(all_users)}, 失败: {failed_count}")
        print(f"{'='*60}\n")
        
        return 0 if failed_count == 0 else 1
        
    except Exception as exc:
        print(f"shareyourcc multi-user 登录失败: {exc}")
        return 1


def _handle_github(args: argparse.Namespace) -> int:
    try:
        from src.sites.github.login import login_to_github
    except Exception as exc:
        print(f"导入 github login module: {exc}")
        return 2

    use_cookie = not args.no_cookie
    ok = False
    try:
        ok = login_to_github(use_cookie=use_cookie, headless=args.headless)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    except Exception as exc:
        print(f"github 登录失败: {exc}")
        ok = False
    return 0 if ok else 1


def _handle_openi(args: argparse.Namespace) -> int:
    # 若未指定具体用户，则调用现有的多用户主流程
    if not args.user:
        try:
            from src.sites.openi.runner import main as openi_main
        except Exception as exc:  # pragma: no cover - 覆盖率忽略
            print(f"导入 openi login module: {exc}")
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
        print(f"导入 openi utilities: {exc}")
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
