#!/bin/bash
# 每日自动运行脚本 (Linux)
# 用于定时执行 AnyRouter, OpenI, ShareYourCC 自动化任务

# 设置项目路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

# 设置日志目录
LOG_DIR="$PROJECT_DIR/data/logs"
mkdir -p "$LOG_DIR"

# 设置日期
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# 激活虚拟环境（如果使用）
# source venv/bin/activate

echo "========================================"
echo "开始每日自动化任务: $DATE"
echo "========================================"

# 1. 运行 AnyRouter
echo ""
echo ">>> 运行 AnyRouter..."
python -m src anyrouter --headless > "$LOG_DIR/anyrouter_$DATE.log" 2>&1
ANYROUTER_EXIT=$?
if [ $ANYROUTER_EXIT -eq 0 ]; then
    echo "✅ AnyRouter 完成"
else
    echo "❌ AnyRouter 失败 (exit code: $ANYROUTER_EXIT)"
fi

# 2. 运行 OpenI
echo ""
echo ">>> 运行 OpenI..."
python -m src openi --headless > "$LOG_DIR/openi_$DATE.log" 2>&1
OPENI_EXIT=$?
if [ $OPENI_EXIT -eq 0 ]; then
    echo "✅ OpenI 完成"
else
    echo "❌ OpenI 失败 (exit code: $OPENI_EXIT)"
fi

# 3. 运行 ShareYourCC
echo ""
echo ">>> 运行 ShareYourCC..."
python -m src shareyourcc --headless > "$LOG_DIR/shareyourcc_$DATE.log" 2>&1
SHAREYOURCC_EXIT=$?
if [ $SHAREYOURCC_EXIT -eq 0 ]; then
    echo "✅ ShareYourCC 完成"
else
    echo "❌ ShareYourCC 失败 (exit code: $SHAREYOURCC_EXIT)"
fi

# 汇总结果
echo ""
echo "========================================"
echo "任务完成: $DATE"
echo "AnyRouter: $([ $ANYROUTER_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "OpenI: $([ $OPENI_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "ShareYourCC: $([ $SHAREYOURCC_EXIT -eq 0 ] && echo '✅' || echo '❌')"
echo "========================================"

# 清理旧日志（保留最近 30 天）
find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete

# 退出码：任何一个失败就返回 1
if [ $ANYROUTER_EXIT -ne 0 ] || [ $OPENI_EXIT -ne 0 ] || [ $SHAREYOURCC_EXIT -ne 0 ]; then
    exit 1
fi

exit 0
