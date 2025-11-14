#!/bin/bash
# GridBNB-USDT 启动脚本 (Linux/Mac)
# 企业级启动方式，自动处理路径问题

echo "================================================"
echo "GridBNB-USDT 多币种网格交易机器人"
echo "================================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "[信息] 检测到虚拟环境，正在激活..."
    source .venv/bin/activate
else
    echo "[警告] 未检测到虚拟环境"
fi

# 检查配置文件
echo "[信息] 配置改由 Web 控制台管理，无需 config/.env"

echo "[信息] 正在启动交易机器人..."
echo ""

# 使用企业级启动方式
python src/main.py
