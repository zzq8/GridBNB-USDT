#!/bin/bash

# GridBNB Trading Bot - Ubuntu/Linux 部署脚本
# 专为 Ubuntu 服务器优化

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统环境..."

    # 检查Ubuntu版本
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            log_warning "检测到非Ubuntu系统: $PRETTY_NAME"
        else
            log_success "Ubuntu系统检测: $PRETTY_NAME"
        fi
    fi

    # 检查内存
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 1 ]; then
        log_warning "内存不足1GB，建议至少512MB可用内存"
    else
        log_success "内存检查通过: ${MEMORY_GB}GB"
    fi

    # 检查磁盘空间
    DISK_AVAIL=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$DISK_AVAIL" -lt 1 ]; then
        log_error "磁盘空间不足，至少需要1GB可用空间"
        exit 1
    else
        log_success "磁盘空间检查通过: ${DISK_AVAIL}GB可用"
    fi
}

# 安装Docker
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_info "Docker未安装，开始安装..."

        # 更新包索引
        sudo apt-get update

        # 安装必要的包
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # 添加Docker官方GPG密钥
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

        # 设置稳定版仓库
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # 安装Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io

        # 将当前用户添加到docker组
        sudo usermod -aG docker $USER

        log_success "Docker安装完成"
        log_warning "请重新登录以使docker组权限生效，或运行: newgrp docker"
    else
        log_success "Docker已安装: $(docker --version)"
    fi
}

# 安装Docker Compose
install_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_info "Docker Compose未安装，开始安装..."

        # 下载最新版本的Docker Compose
        DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
        sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

        # 添加执行权限
        sudo chmod +x /usr/local/bin/docker-compose

        log_success "Docker Compose安装完成: $(docker-compose --version)"
    else
        log_success "Docker Compose已安装: $(docker-compose --version)"
    fi
}

# 主函数
main() {
    echo "🚀 GridBNB Trading Bot - Ubuntu/Linux 部署脚本"
    echo "=================================================="

    check_root
    check_system
    install_docker
    install_docker_compose

    # 检查必要文件
    log_info "检查项目文件..."
    for file in ".env" "docker-compose.yml" "nginx/nginx.conf"; do
        if [ ! -f "$file" ]; then
            log_error "文件不存在: $file"
            exit 1
        fi
    done
    log_success "项目文件检查完成"

    # 创建必要的目录
    log_info "创建必要的目录..."
    mkdir -p data nginx/logs

    # 设置权限
    chmod 755 data nginx/logs

    # 停止现有容器
    log_info "停止现有容器..."
    docker-compose down 2>/dev/null || true

    # 构建并启动服务
    log_info "构建并启动服务..."
    docker-compose up -d --build

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 15

    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose ps

    # 显示访问信息
    echo ""
    log_success "🎉 GridBNB交易机器人部署完成！"
    echo "=================================================="
    echo "🌐 访问地址:"
    echo "   - Web界面: http://$(hostname -I | awk '{print $1}')"
    echo "   - 本地访问: http://localhost"
    echo "   - 调试端口: http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📊 管理命令:"
    echo "   - 查看状态: docker-compose ps"
    echo "   - 查看日志: docker-compose logs -f"
    echo "   - 重启服务: docker-compose restart"
    echo "   - 停止服务: docker-compose down"
    echo "   - 更新代码: git pull && docker-compose up -d --build"
    echo ""
    echo "📝 日志位置:"
    echo "   - 应用日志: ./trading_system.log"
    echo "   - Nginx日志: ./nginx/logs/"
    echo "   - Docker日志: docker-compose logs"
    echo ""
    echo "🔧 故障排除:"
    echo "   - 检查端口: sudo netstat -tlnp | grep :80"
    echo "   - 检查防火墙: sudo ufw status"
    echo "   - 重启Docker: sudo systemctl restart docker"
    echo "=================================================="
}

# 运行主函数
main "$@"
