#!/usr/bin/env python3
"""配置文件格式迁移工具

自动将旧格式配置转换为推荐的新格式（site-based users数组）。

支持的迁移：
- 格式2（统一凭据格式）→ 格式1（推荐格式）
- 格式3（旧版 OpenI 格式）→ 格式1

特性：
- 自动备份原配置文件
- 幂等操作（可重复执行）
- 详细的迁移日志
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def detect_project_root() -> Path:
    """检测项目根目录"""
    script_path = Path(__file__).resolve()
    # scripts/migrate_config.py -> 向上两级到项目根
    return script_path.parent.parent


def detect_format(data: Dict) -> str:
    """检测配置格式

    返回:
        "format1" - 推荐格式（site-based users数组）
        "format2" - 统一凭据格式（credentials字典）
        "format3" - 旧版 OpenI 格式（无site字段的users数组）
        "unknown" - 无法识别
    """
    if not isinstance(data, dict):
        return "unknown"

    # 格式2：存在 credentials 字典
    if "credentials" in data:
        return "format2"

    # 格式1或3：存在 users 数组
    users = data.get("users")
    if isinstance(users, list) and users:
        # 格式1：users中有site字段
        if any(isinstance(u, dict) and "site" in u for u in users):
            return "format1"
        # 格式3：users中没有site字段（旧版OpenI）
        if all(isinstance(u, dict) and "site" not in u for u in users):
            return "format3"

    return "unknown"


def migrate_format2_to_format1(data: Dict) -> Dict:
    """格式2 → 格式1：credentials字典 → site-based users数组"""
    credentials = data.get("credentials", {})
    old_config = data.get("config", {})

    new_users = []

    # 遍历所有站点的凭据
    for site, user_list in credentials.items():
        if not isinstance(user_list, list):
            continue
        for user in user_list:
            if isinstance(user, dict):
                new_user = {"site": site, **user}
                new_users.append(new_user)

    # 合并全局配置（从各站点配置中提取共同参数）
    global_config = {}
    if isinstance(old_config, dict):
        # 提取 openi 配置作为全局默认值
        openi_config = old_config.get("openi", {})
        if isinstance(openi_config, dict):
            global_config.update(openi_config)

        # 提取其他站点的通用配置
        for site_config in old_config.values():
            if isinstance(site_config, dict):
                for key in ("cookie_expire_days", "headless", "use_cookies"):
                    if key in site_config and key not in global_config:
                        global_config[key] = site_config[key]

    return {
        "config": global_config,
        "users": new_users,
    }


def migrate_format3_to_format1(data: Dict) -> Dict:
    """格式3 → 格式1：旧版OpenI格式 → site-based users数组"""
    users = data.get("users", [])
    config = data.get("config", {})

    # 将所有用户标记为 openi 站点
    new_users = []
    for user in users:
        if isinstance(user, dict):
            new_user = {"site": "openi", **user}
            new_users.append(new_user)

    return {
        "config": config if isinstance(config, dict) else {},
        "users": new_users,
    }


def backup_config(config_path: Path) -> Optional[Path]:
    """备份配置文件"""
    if not config_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.name}.backup_{timestamp}"

    try:
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"警告: 备份失败 - {e}", file=sys.stderr)
        return None


def migrate_config_file(config_path: Path, dry_run: bool = False) -> bool:
    """执行配置文件迁移

    参数:
        config_path: 配置文件路径
        dry_run: True时只检测不修改

    返回:
        是否需要迁移（或已迁移）
    """
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return False

    # 读取原配置
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件 - {e}", file=sys.stderr)
        return False

    # 检测格式
    fmt = detect_format(data)
    print(f"检测到配置格式: {fmt}")

    if fmt == "format1":
        print("✓ 已是推荐格式，无需迁移")
        return False

    if fmt == "unknown":
        print("警告: 无法识别配置格式，跳过迁移", file=sys.stderr)
        return False

    # 执行迁移
    if fmt == "format2":
        new_data = migrate_format2_to_format1(data)
        print("执行迁移: 格式2 → 格式1（统一凭据格式 → site-based数组）")
    elif fmt == "format3":
        new_data = migrate_format3_to_format1(data)
        print("执行迁移: 格式3 → 格式1（旧版OpenI → site-based数组）")
    else:
        return False

    if dry_run:
        print("\n[DRY RUN] 迁移后的配置预览:")
        print(json.dumps(new_data, ensure_ascii=False, indent=2))
        return True

    # 备份原文件
    backup_path = backup_config(config_path)
    if backup_path:
        print(f"✓ 已备份原配置: {backup_path}")

    # 写入新配置
    try:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 已写入新格式配置: {config_path}")
        return True
    except Exception as e:
        print(f"错误: 写入配置文件失败 - {e}", file=sys.stderr)
        if backup_path and backup_path.exists():
            print(f"请手动从备份恢复: {backup_path}", file=sys.stderr)
        return False


def main(dry_run: bool = False) -> int:
    """主函数"""
    root = detect_project_root()
    config_path = root / "config" / "users.json"

    print(f"配置迁移工具")
    print(f"项目根目录: {root}")
    print(f"配置文件: {config_path}")
    print("-" * 60)

    if dry_run:
        print("[DRY RUN 模式] 仅检测，不修改文件\n")

    success = migrate_config_file(config_path, dry_run=dry_run)

    if success and not dry_run:
        print("\n✓ 迁移完成！")
        print("提示: 原配置已备份，如有问题可手动恢复")
        return 0
    elif success and dry_run:
        print("\n提示: 使用 --apply 参数执行实际迁移")
        return 0
    else:
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="配置文件格式迁移工具")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅检测格式，不修改文件",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行实际迁移（默认为dry-run）",
    )

    args = parser.parse_args()

    # 默认为 dry-run，除非指定 --apply
    dry_run = not args.apply

    sys.exit(main(dry_run=dry_run))
