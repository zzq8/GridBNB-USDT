@echo off
chcp 65001 >nul

echo 🚀 启动 GridBNB 交易机器人 (带 Nginx 反向代理)
echo ==================================================

REM 检查必要文件
if not exist ".env" (
    echo ❌ 错误: .env 文件不存在
    pause
    exit /b 1
)

if not exist "docker-compose.yml" (
    echo ❌ 错误: docker-compose.yml 文件不存在
    pause
    exit /b 1
)

if not exist "nginx\nginx.conf" (
    echo ❌ 错误: nginx\nginx.conf 文件不存在
    pause
    exit /b 1
)

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist "data" mkdir data
if not exist "nginx\logs" mkdir nginx\logs

REM 停止现有容器（如果存在）
echo 🛑 停止现有容器...
docker-compose down

REM 构建并启动服务
echo 🔨 构建并启动服务...
docker-compose up -d --build

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

REM 显示访问信息
echo.
echo ✅ 服务启动完成！
echo ==================================================
echo 🌐 Web 访问地址:
echo    - 通过 Nginx (推荐): http://localhost
echo    - 直接访问 (调试用): http://localhost:8080
echo.
echo 📊 服务状态:
echo    - 查看所有容器: docker-compose ps
echo    - 查看日志: docker-compose logs -f
echo    - 查看机器人日志: docker-compose logs -f gridbnb-bot
echo    - 查看 Nginx 日志: docker-compose logs -f nginx
echo.
echo 🛠️ 管理命令:
echo    - 停止服务: docker-compose down
echo    - 重启服务: docker-compose restart
echo    - 更新代码: docker-compose up -d --build
echo.
echo 📝 日志文件位置:
echo    - Nginx 访问日志: .\nginx\logs\access.log
echo    - Nginx 错误日志: .\nginx\logs\error.log
echo    - 交易机器人日志: .\trading_system.log
echo ==================================================

pause
