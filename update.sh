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

# 2. 检查配置文件
echo -e "${YELLOW}🔍 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ 错误: .env文件不存在，请先配置${NC}"
    exit 1
fi
echo "✅ .env配置文件存在"

# 3. 检查Git状态
echo -e "${YELLOW}📋 检查Git状态...${NC}"
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

    # 自动恢复update.sh的执行权限
    echo -e "${YELLOW}🔧 恢复update.sh执行权限...${NC}"
    chmod +x update.sh
    echo "✅ update.sh执行权限已恢复"
fi

# 5. 恢复本地修改 (如果有暂存)
if [ "$STASHED" = true ]; then
    echo -e "${YELLOW}🔄 恢复本地个性化修改...${NC}"
    if git stash pop; then
        echo "✅ 本地修改已恢复"
    else
        echo -e "${YELLOW}⚠️  恢复本地修改时出现冲突，请手动解决${NC}"
        echo "💡 查看冲突: git status"
        echo "💡 解决后继续: git add . && git stash drop"
    fi
fi

# 6. 验证配置文件
echo -e "${YELLOW}🔧 验证配置文件...${NC}"
if [ -f ".env" ]; then
    echo "✅ .env配置文件完好无损"
else
    echo -e "${RED}❌ 错误: .env文件丢失${NC}"
    exit 1
fi

# 7. 重新构建并启动服务
echo -e "${YELLOW}🐳 重新构建并启动Docker服务...${NC}"
docker-compose down
echo "✅ 服务已停止"

docker-compose up -d --build
echo "✅ 服务重新构建并启动"

# 8. 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 15

# 9. 检查服务状态
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

# 10. 显示更新结果
echo ""
echo -e "${GREEN}🎉 更新完成！${NC}"
echo "=================================="

if [ "$UPDATE_NEEDED" = true ]; then
    echo "✅ 代码已更新到最新版本"
else
    echo "ℹ️  代码已是最新版本，仅重启了服务"
fi

echo "✅ .env配置文件未受影响"
echo "✅ Docker服务已重启"
echo "✅ 服务运行正常"



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
