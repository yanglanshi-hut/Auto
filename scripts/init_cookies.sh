#!/bin/bash
# 初始化所有用户的Cookie（使用xvfb处理Cloudflare）
cd "$(dirname "$0")/.."
source /root/miniconda3/bin/activate auto
python scripts/init_all_cookies.py "$@"

