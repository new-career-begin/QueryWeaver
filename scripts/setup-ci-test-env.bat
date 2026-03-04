@echo off
REM QueryWeaver CI 测试环境快速设置脚本 (Windows)
REM 用于在本地快速启动测试数据库环境

setlocal enabledelayedexpansion

echo ========================================
echo QueryWeaver CI 测试环境设置
echo ========================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未安装
    echo 请先安装 Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    exit /b 1
)

REM 检查 Docker Compose 是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker Compose 未安装
    echo Docker Desktop 应该已包含 Docker Compose
    exit /b 1
)

echo 步骤 1/5: 停止现有的测试容器...
docker-compose -f docker-compose.test.yml down -v >nul 2>&1
echo 完成
echo.

echo 步骤 2/5: 启动测试数据库容器...
docker-compose -f docker-compose.test.yml up -d
if errorlevel 1 (
    echo 错误: 启动容器失败
    exit /b 1
)
echo 完成
echo.

echo 步骤 3/5: 等待数据库就绪...
echo 等待 FalkorDB...
:wait_falkordb
docker exec queryweaver-test-falkordb redis-cli ping >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_falkordb
)
echo   完成

echo 等待 PostgreSQL...
:wait_postgres
docker exec queryweaver-test-postgres pg_isready -U testuser >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_postgres
)
echo   完成

echo 等待 MySQL...
:wait_mysql
docker exec queryweaver-test-mysql mysqladmin ping -h localhost -u testuser -ptestpass >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_mysql
)
echo   完成

echo 等待 Kingbase...
:wait_kingbase
docker exec queryweaver-test-kingbase pg_isready -U testuser >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_kingbase
)
echo   完成
echo.

echo 步骤 4/5: 验证数据库连接...
docker exec queryweaver-test-postgres psql -U testuser -d testdb -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL: 连接失败
) else (
    echo PostgreSQL: 连接成功
)

docker exec queryweaver-test-mysql mysql -u testuser -ptestpass testdb -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo MySQL: 连接失败
) else (
    echo MySQL: 连接成功
)

docker exec queryweaver-test-kingbase psql -U testuser -d testdb -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo Kingbase: 连接失败
) else (
    echo Kingbase: 连接成功
)

docker exec queryweaver-test-falkordb redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo FalkorDB: 连接失败
) else (
    echo FalkorDB: 连接成功
)
echo.

echo 步骤 5/5: 显示连接信息...
echo.
echo 测试数据库连接信息:
echo ========================================
echo.
echo PostgreSQL:
echo   URL: postgresql://testuser:testpass@localhost:5432/testdb
echo   Host: localhost
echo   Port: 5432
echo   User: testuser
echo   Password: testpass
echo   Database: testdb
echo.
echo MySQL:
echo   URL: mysql://testuser:testpass@localhost:3306/testdb
echo   Host: localhost
echo   Port: 3306
echo   User: testuser
echo   Password: testpass
echo   Database: testdb
echo.
echo Kingbase (PostgreSQL 兼容):
echo   URL: kingbase://testuser:testpass@localhost:54321/testdb
echo   Host: localhost
echo   Port: 54321
echo   User: testuser
echo   Password: testpass
echo   Database: testdb
echo.
echo FalkorDB:
echo   URL: redis://localhost:6379
echo   Host: localhost
echo   Port: 6379
echo.
echo ========================================
echo.
echo 测试环境设置完成！
echo.
echo 现在可以运行测试：
echo.
echo   # 运行所有单元测试
echo   make test-unit
echo.
echo   # 运行覆盖率测试
echo   pipenv run pytest tests/ -k "not e2e" --cov=api --cov-report=html
echo.
echo 停止测试环境：
echo   docker-compose -f docker-compose.test.yml down
echo.
echo 查看容器日志：
echo   docker-compose -f docker-compose.test.yml logs -f
echo.

endlocal
