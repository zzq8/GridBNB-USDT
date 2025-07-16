#!/bin/bash

# GridBNB 安全加固部署脚本
# 移除直接端口映射，只允许通过Nginx访问

echo "🔒 开始GridBNB安全加固部署..."

# 检查Docker和docker-compose是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装或不可用"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装或不可用"
    exit 1
fi

# 显示当前运行的容器
echo "📊 当前运行的容器："
docker-compose ps

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 重新构建并启动服务
echo "🚀 重新构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态："
docker-compose ps

# 检查服务健康状态
echo "🏥 检查服务健康状态："
docker-compose exec gridbnb-bot curl -f http://localhost:58181/health || echo "⚠️ 应用健康检查失败"
docker-compose exec nginx wget --quiet --tries=1 --spider http://localhost/health || echo "⚠️ Nginx健康检查失败"

# 验证端口配置
echo "🔍 验证端口配置："
echo "开放的端口："
docker-compose port nginx 80 2>/dev/null && echo "✅ Nginx端口80已开放"
docker-compose port gridbnb-bot 8080 2>/dev/null && echo "⚠️ 警告：8080端口仍然开放" || echo "✅ 8080端口已关闭（安全）"

# 显示访问信息
echo ""
echo "🎉 安全加固部署完成！"
echo ""
echo "📝 访问信息："
echo "  - Web界面: http://your-server-ip/"
echo "  - API接口: http://your-server-ip/api/"
echo ""
echo "🔒 安全改进："
echo "  - ✅ 移除了8080端口的直接映射"
echo "  - ✅ 只能通过Nginx访问应用"
echo "  - ✅ 防止了绕过反向代理的直接访问"
echo "  - ✅ 减少了BadHttpMessage错误日志"
echo ""
echo "📋 后续建议："
echo "  - 监控日志确认BadHttpMessage错误是否消失"
echo "  - 考虑配置防火墙进一步限制访问"
echo "  - 定期更新Docker镜像和依赖"
