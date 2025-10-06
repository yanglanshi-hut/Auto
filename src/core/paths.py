"""Centralized project path management.

This module exposes a single `ProjectPaths` dataclass and a helper
`get_project_paths()` function that returns a singleton instance.

Design goals:
- Detect the project root once at import time for performance.
- Provide stable, backwards-compatible directories for data/config.
- Keep path joins out of business logic for simplicity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _detect_project_root(start: Path) -> Path:
    """Detect the project root directory.

    The project root is defined as the directory that contains both
    `src/` and `config/` directories. If not found, fall back to the
    third parent of this file (matching the expected layout) or the
    filesystem root of the provided path.
    """
    for parent in [start, *start.parents]:
        if (parent / "src").exists() and (parent / "config").exists():
            return parent
    # Expected structure: <root>/src/core/paths.py -> parents[2] == <root>/src/core
    # parents[3] should be <root>/
    try:
        return start.resolve().parents[3]
    except Exception:
        return start.resolve()


@dataclass(frozen=True)
class ProjectPaths:
    """Dataclass grouping commonly used project directories.

    Attributes:
        root: Project root directory.
        src:  Source code directory (root / 'src').
        data: Data directory (root / 'data').
        config: Config directory (root / 'config').
        cookies: Cookie storage directory (data / 'cookies').
        logs: Log output directory (data / 'logs').
        screenshots: Screenshot output directory (data / 'screenshots').
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

# Construct the paths once at import time to satisfy the performance constraint.
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
    """Return the lazily created, process-wide `ProjectPaths` instance."""
    return _PATHS_SINGLETON

