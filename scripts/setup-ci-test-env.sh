#!/bin/bash

# QueryWeaver CI 测试环境快速设置脚本
# 用于在本地快速启动测试数据库环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}QueryWeaver CI 测试环境设置${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${YELLOW}步骤 1/5: 停止现有的测试容器...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

echo -e "${YELLOW}步骤 2/5: 启动测试数据库容器...${NC}"
docker-compose -f docker-compose.test.yml up -d
echo -e "${GREEN}✓ 完成${NC}"
echo ""

echo -e "${YELLOW}步骤 3/5: 等待数据库就绪...${NC}"
echo "等待 FalkorDB..."
until docker exec queryweaver-test-falkordb redis-cli ping 2>/dev/null | grep -q PONG; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

echo "等待 PostgreSQL..."
until docker exec queryweaver-test-postgres pg_isready -U testuser 2>/dev/null | grep -q "accepting connections"; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

echo "等待 MySQL..."
until docker exec queryweaver-test-mysql mysqladmin ping -h localhost -u testuser -ptestpass 2>/dev/null | grep -q "mysqld is alive"; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

echo "等待 Kingbase..."
until docker exec queryweaver-test-kingbase pg_isready -U testuser 2>/dev/null | grep -q "accepting connections"; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"
echo ""

echo -e "${YELLOW}步骤 4/5: 验证数据库连接...${NC}"

# 验证 PostgreSQL
if docker exec queryweaver-test-postgres psql -U testuser -d testdb -c "SELECT 1;" &>/dev/null; then
    echo -e "PostgreSQL: ${GREEN}✓ 连接成功${NC}"
else
    echo -e "PostgreSQL: ${RED}✗ 连接失败${NC}"
fi

# 验证 MySQL
if docker exec queryweaver-test-mysql mysql -u testuser -ptestpass testdb -e "SELECT 1;" &>/dev/null; then
    echo -e "MySQL: ${GREEN}✓ 连接成功${NC}"
else
    echo -e "MySQL: ${RED}✗ 连接失败${NC}"
fi

# 验证 Kingbase
if docker exec queryweaver-test-kingbase psql -U testuser -d testdb -c "SELECT 1;" &>/dev/null; then
    echo -e "Kingbase: ${GREEN}✓ 连接成功${NC}"
else
    echo -e "Kingbase: ${RED}✗ 连接失败${NC}"
fi

# 验证 FalkorDB
if docker exec queryweaver-test-falkordb redis-cli ping &>/dev/null; then
    echo -e "FalkorDB: ${GREEN}✓ 连接成功${NC}"
else
    echo -e "FalkorDB: ${RED}✗ 连接失败${NC}"
fi
echo ""

echo -e "${YELLOW}步骤 5/5: 显示连接信息...${NC}"
echo ""
echo -e "${GREEN}测试数据库连接信息:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PostgreSQL:"
echo "  URL: postgresql://testuser:testpass@localhost:5432/testdb"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  User: testuser"
echo "  Password: testpass"
echo "  Database: testdb"
echo ""
echo "MySQL:"
echo "  URL: mysql://testuser:testpass@localhost:3306/testdb"
echo "  Host: localhost"
echo "  Port: 3306"
echo "  User: testuser"
echo "  Password: testpass"
echo "  Database: testdb"
echo ""
echo "Kingbase (PostgreSQL 兼容):"
echo "  URL: kingbase://testuser:testpass@localhost:54321/testdb"
echo "  Host: localhost"
echo "  Port: 54321"
echo "  User: testuser"
echo "  Password: testpass"
echo "  Database: testdb"
echo ""
echo "FalkorDB:"
echo "  URL: redis://localhost:6379"
echo "  Host: localhost"
echo "  Port: 6379"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}测试环境设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "现在可以运行测试："
echo ""
echo "  # 运行所有单元测试"
echo "  make test-unit"
echo ""
echo "  # 运行覆盖率测试"
echo "  pipenv run pytest tests/ -k \"not e2e\" --cov=api --cov-report=html"
echo ""
echo "  # 运行特定数据库的测试"
echo "  pipenv run pytest tests/loaders/test_postgres_loader.py -v"
echo ""
echo "停止测试环境："
echo "  docker-compose -f docker-compose.test.yml down"
echo ""
echo "查看容器日志："
echo "  docker-compose -f docker-compose.test.yml logs -f"
echo ""
