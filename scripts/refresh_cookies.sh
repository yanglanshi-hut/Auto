#!/bin/bash
# 刷新所有用户的Cookie（可配合--dry-run/--force使用）
cd "$(dirname "$0")/.."
source /root/miniconda3/bin/activate auto
python scripts/refresh_all_cookies.py "$@"

