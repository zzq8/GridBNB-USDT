# Docker 安装和 GridBNB 部署完整指南

## 🐳 第一步：安装 Docker Desktop

### Windows 用户

1. **下载 Docker Desktop**
   - 访问：https://www.docker.com/products/docker-desktop/
   - 点击 "Download for Windows"
   - 下载 `Docker Desktop Installer.exe`

2. **安装 Docker Desktop**
   - 双击运行安装程序
   - 勾选 "Use WSL 2 instead of Hyper-V" (推荐)
   - 完成安装后重启计算机

3. **启动 Docker Desktop**
   - 从开始菜单启动 Docker Desktop
   - 等待 Docker 引擎启动完成
   - 看到绿色状态图标表示启动成功

4. **验证安装**
   ```cmd
   docker --version
   docker-compose --version
   ```

### 系统要求
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 16299 或更高)
- 或 Windows 11 64-bit
- 启用 Hyper-V 和容器功能
- 至少 4GB RAM

## 🚀 第二步：部署 GridBNB 交易机器人

### 方法一：使用启动脚本 (推荐)

1. **打开命令提示符或 PowerShell**
   - 按 `Win + R`，输入 `cmd` 或 `powershell`
   - 导航到项目目录：
     ```cmd
     cd D:\GridBNB-USDT
     ```

2. **运行启动脚本**
   ```cmd
   start-with-nginx.bat
   ```

### 方法二：手动部署

1. **检查配置文件**
   ```cmd
   # 确保以下文件存在：
   dir .env
   dir docker-compose.yml
   dir nginx\nginx.conf
   ```

2. **创建必要目录**
   ```cmd
   mkdir data
   mkdir nginx\logs
   ```

3. **启动服务**
   ```cmd
   docker-compose up -d --build
   ```

4. **检查状态**
   ```cmd
   docker-compose ps
   ```

## 🌐 第三步：访问 Web 界面

启动成功后，打开浏览器访问：
- **主要访问地址**: http://localhost
- **备用访问地址**: http://localhost:8080

## 📊 第四步：监控和管理

### 查看日志
```cmd
# 查看所有服务日志
docker-compose logs -f

# 查看机器人日志
docker-compose logs -f gridbnb-bot

# 查看 Nginx 日志
docker-compose logs -f nginx
```

### 管理命令
```cmd
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新并重启
docker-compose up -d --build
```

## 🔧 故障排除

### Docker 相关问题

1. **Docker Desktop 启动失败**
   - 确保 Windows 功能中启用了 "Hyper-V" 和 "容器"
   - 重启计算机
   - 以管理员身份运行 Docker Desktop

2. **WSL 2 相关问题**
   - 更新 WSL 2：`wsl --update`
   - 设置默认版本：`wsl --set-default-version 2`

3. **端口冲突**
   ```cmd
   # 检查端口占用
   netstat -ano | findstr :80
   netstat -ano | findstr :8080
   ```

### 应用相关问题

1. **容器启动失败**
   ```cmd
   # 查看详细错误
   docker-compose logs gridbnb-bot
   ```

2. **无法访问 Web 界面**
   - 检查防火墙设置
   - 确认容器状态：`docker-compose ps`
   - 检查端口映射是否正确

3. **配置文件错误**
   - 检查 `.env` 文件格式
   - 验证 API 密钥是否正确
   - 确认交易对配置是否有效

## 📈 性能优化建议

### Docker 设置
1. **资源分配**
   - 在 Docker Desktop 设置中分配足够的 CPU 和内存
   - 推荐：至少 2GB RAM，2 CPU 核心

2. **存储优化**
   - 定期清理未使用的镜像：`docker image prune`
   - 清理未使用的容器：`docker container prune`

### 系统优化
1. **关闭不必要的服务**
2. **确保足够的磁盘空间**
3. **定期重启 Docker Desktop**

## 🔒 安全建议

1. **网络安全**
   - 配置防火墙规则
   - 使用强密码保护 Web 界面
   - 考虑使用 VPN 访问

2. **数据安全**
   - 定期备份交易数据
   - 保护 API 密钥安全
   - 监控异常交易活动

## 📞 获取帮助

如果遇到问题，请按以下顺序排查：

1. **检查 Docker 状态**
   ```cmd
   docker --version
   docker-compose --version
   docker ps
   ```

2. **检查服务状态**
   ```cmd
   docker-compose ps
   docker-compose logs
   ```

3. **检查配置文件**
   - 验证 `.env` 文件内容
   - 检查 `docker-compose.yml` 语法
   - 确认 `nginx.conf` 配置正确

4. **重新部署**
   ```cmd
   docker-compose down
   docker-compose up -d --build
   ```

## 🎯 下一步

部署成功后，您可以：
1. 监控交易机器人的运行状态
2. 通过 Web 界面查看交易数据
3. 根据需要调整策略参数
4. 设置监控和告警

祝您使用愉快！🚀
