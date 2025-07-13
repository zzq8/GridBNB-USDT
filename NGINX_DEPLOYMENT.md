# GridBNB Trading Bot - Nginx 反向代理部署指南

## 🎯 概述

本指南介绍如何使用 Docker Compose 部署带有 Nginx 反向代理的 GridBNB 交易机器人。这种部署方式提供了更好的性能、安全性和可扩展性。

## 📁 项目结构

```
GridBNB-USDT/
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # 机器人镜像构建文件
├── .env                       # 环境变量配置
├── nginx/
│   ├── nginx.conf            # Nginx 配置文件
│   └── logs/                 # Nginx 日志目录
├── data/                     # 持久化数据目录
├── start-with-nginx.sh       # Linux/Mac 启动脚本
├── start-with-nginx.bat      # Windows 启动脚本
└── ... (其他项目文件)
```

## 🚀 快速启动

### Windows 用户
```bash
# 双击运行或在命令行执行
start-with-nginx.bat
```

### Linux/Mac 用户
```bash
# 给脚本执行权限
chmod +x start-with-nginx.sh

# 运行启动脚本
./start-with-nginx.sh
```

### 手动启动
```bash
# 创建必要目录
mkdir -p data nginx/logs

# 启动服务
docker-compose up -d --build

# 查看状态
docker-compose ps
```

## 🌐 访问方式

启动成功后，您可以通过以下方式访问：

- **推荐方式**: http://localhost (通过 Nginx 反向代理)
- **直接访问**: http://localhost:8080 (直接访问机器人服务，用于调试)

## 🔧 配置说明

### Nginx 配置特性

- ✅ **反向代理**: 将 80 端口请求转发到机器人服务
- ✅ **负载均衡**: 支持多实例部署
- ✅ **静态文件缓存**: 优化前端资源加载
- ✅ **Gzip 压缩**: 减少传输数据量
- ✅ **安全头**: 增强 Web 安全性
- ✅ **健康检查**: 自动监控服务状态
- ✅ **日志记录**: 详细的访问和错误日志

### Docker Compose 特性

- ✅ **服务隔离**: 机器人和 Nginx 在独立容器中运行
- ✅ **自动重启**: 容器异常退出时自动重启
- ✅ **数据持久化**: 交易数据和日志持久保存
- ✅ **网络隔离**: 内部网络确保服务间安全通信
- ✅ **健康检查**: 自动监控容器健康状态

## 📊 监控和管理

### 查看服务状态
```bash
# 查看所有容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f gridbnb-bot
docker-compose logs -f nginx
```

### 管理命令
```bash
# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 更新代码并重启
docker-compose up -d --build

# 查看资源使用情况
docker stats
```

### 日志文件位置
- **Nginx 访问日志**: `./nginx/logs/access.log`
- **Nginx 错误日志**: `./nginx/logs/error.log`
- **机器人日志**: `./trading_system.log`
- **Docker 日志**: `docker-compose logs`

## 🔒 安全配置

### 基本安全措施
1. **防火墙配置**: 只开放必要的端口 (80, 443)
2. **访问控制**: 在 `.env` 中配置 `WEB_USER` 和 `WEB_PASSWORD`
3. **定期更新**: 保持 Docker 镜像和系统更新

### 生产环境建议
1. **HTTPS 配置**: 配置 SSL 证书启用 HTTPS
2. **域名绑定**: 将 `server_name _` 改为具体域名
3. **访问限制**: 配置 IP 白名单或 VPN 访问
4. **日志轮转**: 配置日志轮转避免磁盘空间不足

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :80
   # 或者修改 docker-compose.yml 中的端口映射
   ```

2. **容器启动失败**
   ```bash
   # 查看详细错误信息
   docker-compose logs gridbnb-bot
   docker-compose logs nginx
   ```

3. **无法访问 Web 界面**
   ```bash
   # 检查容器状态
   docker-compose ps
   # 检查网络连接
   curl -I http://localhost
   ```

4. **数据丢失**
   ```bash
   # 确保数据目录正确挂载
   ls -la ./data/
   # 检查 docker-compose.yml 中的 volumes 配置
   ```

## 📈 性能优化

### Nginx 优化
- 调整 `worker_processes` 和 `worker_connections`
- 启用 HTTP/2 (需要 HTTPS)
- 配置适当的缓存策略

### Docker 优化
- 限制容器资源使用
- 使用多阶段构建减小镜像大小
- 配置适当的重启策略

## 🔄 更新和维护

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 备份数据
```bash
# 备份交易数据
cp -r ./data/ ./backup/data-$(date +%Y%m%d)/

# 备份配置文件
cp .env ./backup/env-$(date +%Y%m%d).backup
```

### 清理资源
```bash
# 清理未使用的镜像
docker image prune

# 清理未使用的容器
docker container prune

# 清理未使用的网络
docker network prune
```

---

## 📞 支持

如果您在部署过程中遇到问题，请检查：
1. Docker 和 Docker Compose 是否正确安装
2. `.env` 文件配置是否正确
3. 防火墙和端口配置是否正确
4. 系统资源是否充足

祝您交易愉快！🎯
