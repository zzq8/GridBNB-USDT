#!/bin/bash

# GridBNB Trading Bot - 简单更新脚本
# 用于安全更新GitHub代码并重启服务

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 GridBNB Trading Bot 更新脚本${NC}"
echo "=================================="

# 1. 检查当前目录是否为项目目录
if [ ! -f "docker-compose.yml" ] || [ ! -f ".env" ]; then
    echo -e "${RED}❌ 错误: 请在GridBNB项目目录中运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 当前目录: $(pwd)${NC}"

# 2. 备份配置文件
echo -e "${YELLOW}💾 备份配置文件...${NC}"
cp .env .env.backup
echo "✅ .env文件已备份为 .env.backup"

# 3. 检查Git状态
echo -e "${YELLOW}🔍 检查Git状态...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  检测到本地修改，将暂存这些更改${NC}"
    git stash push -m "Auto stash before update $(date)"
    STASHED=true
else
    STASHED=false
fi

# 4. 拉取最新代码
echo -e "${YELLOW}📥 拉取最新代码...${NC}"
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ 代码已是最新版本"
    UPDATE_NEEDED=false
else
    echo "🔄 发现新版本，开始更新..."
    git pull origin main
    UPDATE_NEEDED=true
    echo "✅ 代码更新完成"
fi

# 5. 恢复配置文件
echo -e "${YELLOW}🔧 恢复配置文件...${NC}"
if [ -f ".env.backup" ]; then
    cp .env.backup .env
    echo "✅ 配置文件已恢复"
else
    echo -e "${RED}❌ 备份文件不存在，请检查.env配置${NC}"
fi

# 6. 重新构建并启动服务
echo -e "${YELLOW}🐳 重新构建并启动Docker服务...${NC}"
docker-compose down
echo "✅ 服务已停止"

docker-compose up -d --build
echo "✅ 服务重新构建并启动"

# 7. 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 15

# 8. 检查服务状态
echo -e "${YELLOW}🔍 检查服务状态...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务运行正常"
    
    # 显示服务状态
    echo ""
    echo "📊 服务状态:"
    docker-compose ps
    
    # 显示最新日志
    echo ""
    echo "📝 最新日志 (最近5行):"
    docker-compose logs --tail=5 gridbnb-bot
    
else
    echo -e "${RED}❌ 服务启动异常，请检查日志${NC}"
    echo "查看日志命令: docker-compose logs"
    exit 1
fi

# 9. 清理备份文件
echo -e "${YELLOW}🧹 清理临时文件...${NC}"
rm -f .env.backup
echo "✅ 临时文件已清理"

# 10. 显示更新结果
echo ""
echo -e "${GREEN}🎉 更新完成！${NC}"
echo "=================================="

if [ "$UPDATE_NEEDED" = true ]; then
    echo "✅ 代码已更新到最新版本"
else
    echo "ℹ️  代码已是最新版本，仅重启了服务"
fi

echo "✅ 配置文件保持不变"
echo "✅ Docker服务已重启"
echo "✅ 服务运行正常"

if [ "$STASHED" = true ]; then
    echo ""
    echo -e "${YELLOW}💡 提示: 本地修改已暂存，如需恢复请运行: git stash pop${NC}"
fi

echo ""
echo "🌐 访问地址:"
echo "   - Web界面: http://$(hostname -I | awk '{print $1}')"
echo "   - 本地访问: http://localhost"

echo ""
echo "📊 常用命令:"
echo "   - 查看状态: docker-compose ps"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 重启服务: docker-compose restart"

echo ""
echo -e "${GREEN}更新脚本执行完成！${NC}"
