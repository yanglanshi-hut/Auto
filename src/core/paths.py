"""集中管理项目路径。

本模块提供一个 `ProjectPaths` 数据类和辅助函数 `get_project_paths()`，
用于返回单例实例。

设计目标：
- 在导入时仅检测一次项目根目录以提高性能。
- 为数据/配置提供稳定、向后兼容的目录。
- 将路径拼接从业务逻辑中剥离以保持简单。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _detect_project_root(start: Path) -> Path:
    """检测项目根目录。

    项目根目录被定义为同时包含 `src/` 和 `config/` 目录的路径。
    若未找到，则回退到该文件的第三级父目录（符合预期布局），
    或者回退到所提供路径的文件系统根。
    """
    for parent in [start, *start.parents]:
        if (parent / "src").exists() and (parent / "config").exists():
            return parent
    # 期望的结构：<root>/src/core/paths.py -> parents[2] == <root>/src/core
    # parents[3] 应为 <root>/
    try:
        return start.resolve().parents[3]
    except Exception:
        return start.resolve()


@dataclass(frozen=True)
class ProjectPaths:
    """聚合项目中常用目录的数据类。

    属性:
        root: 项目根目录。
        src:  源码目录（root / 'src'）。
        data: 数据目录（root / 'data'）。
        config: 配置目录（root / 'config'）。
        cookies: Cookie 存储目录（data / 'cookies'）。
        logs: 日志输出目录（data / 'logs'）。
        screenshots: 截图输出目录（data / 'screenshots'）。
    """

    root: Path
    src: Path
    data: Path
    config: Path
    cookies: Path
    logs: Path
    screenshots: Path


_HERE = Path(__file__).resolve()
_ROOT = _detect_project_root(_HERE)

# 在导入时构建路径以满足性能约束。
_PATHS_SINGLETON = ProjectPaths(
    root=_ROOT,
    src=_ROOT / "src",
    data=_ROOT / "data",
    config=_ROOT / "config",
    cookies=_ROOT / "data" / "cookies",
    logs=_ROOT / "data" / "logs",
    screenshots=_ROOT / "data" / "screenshots",
)


def get_project_paths() -> ProjectPaths:
    """返回进程范围内惰性创建的 `ProjectPaths` 实例。"""
    return _PATHS_SINGLETON

