#!/bin/bash

# CI 配置验证脚本
# 验证所有 CI 相关文件是否正确配置

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}QueryWeaver CI 配置验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 检查函数
check_file() {
    local file=$1
    local description=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        echo -e "  ${YELLOW}缺失文件: $file${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        echo -e "  ${YELLOW}缺失目录: $dir${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo -e "${YELLOW}检查 GitHub Actions 工作流...${NC}"
check_file ".github/workflows/database-tests.yml" "数据库测试工作流"
check_file ".github/workflows/dm-database-tests.yml" "达梦数据库专项测试工作流"
check_file ".github/workflows/coverage-report.yml" "代码覆盖率报告工作流"
check_file ".github/README.md" "GitHub Actions 说明文档"
echo ""

echo -e "${YELLOW}检查测试环境配置...${NC}"
check_file "docker-compose.test.yml" "Docker Compose 测试配置"
check_directory "tests/fixtures" "测试数据目录"
check_file "tests/fixtures/postgres-init.sql" "PostgreSQL 初始化脚本"
check_file "tests/fixtures/mysql-init.sql" "MySQL 初始化脚本"
check_file "tests/fixtures/kingbase-init.sql" "Kingbase 初始化脚本"
echo ""

echo -e "${YELLOW}检查文档...${NC}"
check_file "docs/CI_CONFIGURATION.md" "CI 配置详细文档"
check_file "docs/CI_SETUP_SUMMARY.md" "CI 配置总结文档"
echo ""

echo -e "${YELLOW}检查脚本...${NC}"
check_file "scripts/setup-ci-test-env.sh" "测试环境设置脚本 (Linux/macOS)"
check_file "scripts/setup-ci-test-env.bat" "测试环境设置脚本 (Windows)"
check_file "scripts/verify-ci-setup.sh" "CI 配置验证脚本"
echo ""

echo -e "${YELLOW}检查依赖配置...${NC}"
check_file "Pipfile" "Python 依赖配置"
check_file "pytest.ini" "pytest 配置"
echo ""

echo -e "${YELLOW}验证 Pipfile 内容...${NC}"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if grep -q "pytest-cov" Pipfile; then
    echo -e "${GREEN}✓${NC} pytest-cov 已添加到 Pipfile"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} pytest-cov 未添加到 Pipfile"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if grep -q "pytest-xdist" Pipfile; then
    echo -e "${GREEN}✓${NC} pytest-xdist 已添加到 Pipfile"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} pytest-xdist 未添加到 Pipfile"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if grep -q "coverage" Pipfile; then
    echo -e "${GREEN}✓${NC} coverage 已添加到 Pipfile"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} coverage 未添加到 Pipfile"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

echo -e "${YELLOW}检查 Docker 环境...${NC}"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠${NC} Docker 未安装（本地测试需要）"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠${NC} Docker Compose 未安装（本地测试需要）"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

echo -e "${YELLOW}检查 Python 环境...${NC}"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} Python 未安装"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v pipenv &> /dev/null; then
    echo -e "${GREEN}✓${NC} pipenv 已安装"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠${NC} pipenv 未安装（运行测试需要）"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# 显示总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}验证总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "总检查项: $TOTAL_CHECKS"
echo -e "${GREEN}通过: $PASSED_CHECKS${NC}"
echo -e "${RED}失败: $FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！CI 配置完整。${NC}"
    echo ""
    echo "下一步："
    echo "  1. 安装依赖: pipenv sync --dev"
    echo "  2. 启动测试环境: bash scripts/setup-ci-test-env.sh"
    echo "  3. 运行测试: make test-unit"
    echo ""
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED_CHECKS 项检查失败${NC}"
    echo ""
    echo "请检查上述失败项并修复。"
    echo ""
    exit 1
fi
