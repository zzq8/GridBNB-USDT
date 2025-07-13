#!/bin/bash

# GridBNB Trading Bot - Docker Compose 启动脚本
# 包含 Nginx 反向代理

echo "🚀 启动 GridBNB 交易机器人 (带 Nginx 反向代理)"
echo "=================================================="

# 检查必要文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env 文件不存在"
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: docker-compose.yml 文件不存在"
    exit 1
fi

if [ ! -f "nginx/nginx.conf" ]; then
    echo "❌ 错误: nginx/nginx.conf 文件不存在"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data
mkdir -p nginx/logs

# 停止现有容器（如果存在）
echo "🛑 停止现有容器..."
docker-compose down

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "✅ 服务启动完成！"
echo "=================================================="
echo "🌐 Web 访问地址:"
echo "   - 通过 Nginx (推荐): http://localhost"
echo "   - 直接访问 (调试用): http://localhost:8080"
echo ""
echo "📊 服务状态:"
echo "   - 查看所有容器: docker-compose ps"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 查看机器人日志: docker-compose logs -f gridbnb-bot"
echo "   - 查看 Nginx 日志: docker-compose logs -f nginx"
echo ""
echo "🛠️ 管理命令:"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 更新代码: docker-compose up -d --build"
echo ""
echo "📝 日志文件位置:"
echo "   - Nginx 访问日志: ./nginx/logs/access.log"
echo "   - Nginx 错误日志: ./nginx/logs/error.log"
echo "   - 交易机器人日志: ./trading_system.log"
echo "=================================================="
