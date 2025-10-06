"""自动化项目的日志工具。

提供 `setup_logger(name, log_file)` 用于在各模块间统一日志配置，
避免重复样板代码。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Union


def setup_logger(name: str, log_file: Union[str, Path]) -> logging.Logger:
    """创建或获取已配置的 logger。

    - 同时绑定输出到 stdout 的 StreamHandler 与写入 `log_file` 的 FileHandler。
    - 幂等：对同一 logger 的重复调用不会重复添加处理器。
    - 确保 `log_file` 的父目录已存在。
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    log_path = Path(log_file)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # 构建一致的日志格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # 仅在未添加的情况下绑定处理器
    handler_types = {type(h) for h in logger.handlers}

    if logging.StreamHandler not in handler_types:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    if logging.FileHandler not in handler_types:
        try:
            fh = logging.FileHandler(str(log_path), encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            # 若文件无法打开，仅保留 stdout 处理器。
            pass

    return logger
