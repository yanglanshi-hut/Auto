#!/usr/bin/env python3
"""配置迁移脚本：将旧格式迁移为统一的新格式

新格式（目标）：
{
  "users": [
    {"site": "openi", "username": "xxx", "password": "xxx"},
    {"site": "linuxdo", "email": "xxx", "password": "xxx"},
    {"site": "anyrouter", "email": "xxx", "password": "xxx"}
  ],
  "defaults": {
    "cookie_expire_days": 30,
    "headless": true
  },
  "sites": {
    "openi": {"task_name": "image", "run_duration": 15}
  }
}

支持迁移的旧格式：
- 旧版 OpenI 单站点格式（users 无 site 字段、config 为顶层 OpenI 配置）
- 统一凭据格式（credentials[site] = [...]，config 为按站点映射）

使用示例：
  python scripts/migrate_config.py                # 就地迁移，自动备份为 users.json.backup
  python scripts/migrate_config.py --dry-run      # 仅打印迁移结果，不写回
  python scripts/migrate_config.py -i cfg.json -o out.json --no-backup
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

# 允许脚本直接执行时找到本地 src
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.paths import get_project_paths  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "将 config/users.json 旧格式迁移为统一新格式："
            "包含 users 数组 + defaults + sites（三段式）。"
        )
    )
    default_path = get_project_paths().config / "users.json"
    parser.add_argument(
        "-i", "--input", default=str(default_path), help="输入配置文件路径（默认：config/users.json）"
    )
    parser.add_argument(
        "-o", "--output", default=str(default_path), help="输出配置文件路径（默认：覆盖输入）"
    )
    parser.add_argument("--dry-run", action="store_true", help="仅输出迁移结果，不写回文件")
    parser.add_argument("--no-backup", action="store_true", help="不生成 .backup 备份文件（默认生成）")
    parser.add_argument("--indent", type=int, default=2, help="输出 JSON 缩进（默认 2）")
    return parser.parse_args()


def load_json(path: Path) -> Dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def migrate(old: Dict) -> Dict:
    """将旧数据字典迁移为新结构。"""
    new: Dict = {"users": [], "defaults": {}, "sites": {}}

    # 1) users
    users: List[Dict] = []
    if isinstance(old.get("users"), list):
        # 若已有 users 数组：若缺少 site 字段，则默认 openi
        for u in old["users"]:
            if not isinstance(u, dict):
                continue
            if "site" not in u:
                v = dict(u)
                v["site"] = "openi"
                users.append(v)
            else:
                users.append(dict(u))
    elif isinstance(old.get("credentials"), dict):
        creds: Dict = old["credentials"]
        for site, items in creds.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                v = dict(item)
                v["site"] = str(site).lower()
                users.append(v)
    new["users"] = users

    # 2) defaults（仅挑选我们关心的键）
    defaults: Dict = {}
    # 旧版有时把 cookie_expire_days/headless 放在顶层 config
    if isinstance(old.get("defaults"), dict):
        defaults.update({k: v for k, v in old["defaults"].items() if k in {"cookie_expire_days", "headless"}})
    if isinstance(old.get("config"), dict):
        defaults.update({k: v for k, v in old["config"].items() if k in {"cookie_expire_days", "headless"}})
    if "cookie_expire_days" not in defaults:
        defaults["cookie_expire_days"] = 30
    if "headless" not in defaults:
        defaults["headless"] = True
    new["defaults"] = defaults

    # 3) sites（仅迁移 openi 关键项）
    sites: Dict = {}
    # 统一站点映射：config[site] = { ... }
    if isinstance(old.get("config"), dict):
        cfg = old["config"]
        site_cfg = cfg.get("openi") if isinstance(cfg.get("openi"), dict) else None
        if site_cfg:
            sites["openi"] = {
                k: site_cfg[k]
                for k in ("task_name", "run_duration")
                if k in site_cfg
            }
    # 旧版 openi 顶层 config：{task_name, run_duration, ...}
    if not sites.get("openi") and isinstance(old.get("config"), dict):
        top = old["config"]
        if any(k in top for k in ("task_name", "run_duration")):
            sites["openi"] = {
                k: top[k]
                for k in ("task_name", "run_duration")
                if k in top
            }
    new["sites"] = sites

    return new


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)

    old = load_json(in_path)
    new = migrate(old)

    if args.dry_run:
        print(json.dumps(new, ensure_ascii=False, indent=args.indent))
        return 0

    # 就地覆盖时先备份
    if in_path.resolve() == out_path.resolve() and not args.no_backup:
        backup = in_path.with_suffix(in_path.suffix + ".backup")
        try:
            shutil.copy2(str(in_path), str(backup))
            print(f"已备份旧文件到: {backup}")
        except Exception as e:  # noqa: BLE001
            print(f"备份失败（继续迁移）: {e}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(new, fh, ensure_ascii=False, indent=args.indent)
    print(f"已写入新配置到: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

