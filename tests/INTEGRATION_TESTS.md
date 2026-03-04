# 达梦和人大金仓数据库集成测试指南

## 概述

本目录包含达梦数据库和人大金仓数据库的端到端集成测试。这些测试需要真实的数据库实例才能运行。

## 测试文件

### 1. test_dm_integration.py
达梦数据库端到端集成测试，包括：
- 连接测试
- 模式提取测试
- 查询执行测试
- 完整的加载流程测试

### 2. test_kingbase_integration.py
人大金仓数据库端到端集成测试，包括：
- 连接测试（支持 kingbase:// 和 postgresql:// 前缀）
- 模式提取测试
- 查询执行测试
- 完整的加载流程测试

### 3. test_error_scenarios_integration.py
错误场景集成测试，包括：
- 连接失败场景
- 查询失败场景
- 模式提取失败场景
- 错误恢复能力测试

## 环境准备

### 1. 安装依赖

```bash
# 安装达梦数据库驱动
pip install dmPython

# 安装人大金仓数据库驱动（使用 PostgreSQL 驱动）
pip install psycopg2-binary

# 安装测试依赖
pip install pytest pytest-asyncio
```

### 2. 准备测试数据库

#### 达梦数据库

1. 安装达梦数据库 8.0 或更高版本
2. 创建测试数据库实例
3. 确保数据库服务正在运行
4. 记录连接信息：
   - 主机地址
   - 端口（默认 5236）
   - 用户名（如 SYSDBA）
   - 密码
   - 数据库名

#### 人大金仓数据库

1. 安装人大金仓数据库 V8 或更高版本
2. 创建测试数据库实例
3. 确保数据库服务正在运行
4. 记录连接信息：
   - 主机地址
   - 端口（默认 54321）
   - 用户名（如 SYSTEM）
   - 密码
   - 数据库名

### 3. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 达梦数据库连接 URL
export DM_TEST_URL="dm://SYSDBA:password@192.168.1.100:5236/TESTDB"

# 人大金仓数据库连接 URL（支持两种格式）
export KINGBASE_TEST_URL="kingbase://SYSTEM:password@192.168.1.101:54321/TEST"
# 或
export KINGBASE_TEST_URL="postgresql://SYSTEM:password@192.168.1.101:54321/TEST"
```

**注意**：
- 请将上述示例中的主机地址、端口、用户名、密码和数据库名替换为实际值
- 确保数据库用户有足够的权限创建和删除表
- 测试会自动创建和清理测试表，不会影响现有数据

## 运行测试

### 运行所有集成测试

```bash
# 运行所有集成测试
pytest tests/test_dm_integration.py tests/test_kingbase_integration.py tests/test_error_scenarios_integration.py -v

# 显示详细输出
pytest tests/test_dm_integration.py tests/test_kingbase_integration.py tests/test_error_scenarios_integration.py -v -s
```

### 运行特定数据库的测试

```bash
# 只运行达梦数据库测试
pytest tests/test_dm_integration.py -v -s

# 只运行人大金仓数据库测试
pytest tests/test_kingbase_integration.py -v -s

# 只运行错误场景测试
pytest tests/test_error_scenarios_integration.py -v -s
```

### 运行特定测试用例

```bash
# 运行达梦数据库连接测试
pytest tests/test_dm_integration.py::TestDMIntegration::test_dm_connection_success -v

# 运行人大金仓数据库模式提取测试
pytest tests/test_kingbase_integration.py::TestKingbaseIntegration::test_kingbase_extract_tables_info -v

# 运行错误场景测试
pytest tests/test_error_scenarios_integration.py::TestDMErrorScenarios::test_dm_invalid_connection_url_formats -v
```

## 测试覆盖范围

### 达梦数据库测试

✅ 连接管理
- URL 解析
- 连接建立
- 连接验证

✅ 模式提取
- 表信息提取
- 列信息提取
- 主键识别
- 外键识别
- 关系提取

✅ 查询执行
- SELECT 查询
- JOIN 查询
- 聚合查询
- 结果序列化

✅ 模式修改检测
- DDL 操作识别
- DML 操作区分

✅ 端到端流程
- 完整的加载流程
- 进度消息验证

### 人大金仓数据库测试

✅ 连接管理
- URL 格式转换（kingbase:// → postgresql://）
- 连接建立
- 连接验证

✅ 模式提取
- 表信息提取
- 列信息提取
- 主键识别
- 外键识别
- 关系提取

✅ 查询执行
- SELECT 查询
- JOIN 查询
- 聚合查询
- 结果序列化

✅ 模式修改检测
- DDL 操作识别
- DML 操作区分

✅ 端到端流程
- 完整的加载流程
- 进度消息验证

### 错误场景测试

✅ 连接错误
- 无效 URL 格式
- 连接超时
- 认证失败
- 连接被拒绝

✅ 查询错误
- SQL 语法错误
- 表不存在
- 权限不足

✅ 模式提取错误
- 部分表提取失败
- 关系提取失败

✅ 错误恢复
- 继续处理剩余表
- 错误日志记录
- 并发错误处理

## 测试数据

测试会自动创建以下测试表：

### test_users（用户表）
- id: 主键
- username: 用户名
- email: 电子邮箱
- created_at: 创建时间
- balance: 余额

### test_orders（订单表）
- id: 主键
- user_id: 用户ID（外键 → test_users.id）
- order_date: 订单日期
- total_amount: 订单总额

### test_order_items（订单项表）
- id: 主键
- order_id: 订单ID（外键 → test_orders.id）
- product_name: 商品名称
- quantity: 数量
- price: 单价

测试数据包括：
- 3 个用户
- 3 个订单
- 4 个订单项

**注意**：测试完成后会自动清理所有测试表和数据。

## 跳过测试

如果没有配置相应的数据库连接 URL，测试会自动跳过：

```bash
# 没有配置 DM_TEST_URL 时
pytest tests/test_dm_integration.py -v
# 输出: SKIPPED [1] 达梦数据库集成测试需要设置 DM_TEST_URL 环境变量

# 没有配置 KINGBASE_TEST_URL 时
pytest tests/test_kingbase_integration.py -v
# 输出: SKIPPED [1] 人大金仓数据库集成测试需要设置 KINGBASE_TEST_URL 环境变量
```

## 故障排查

### 1. 连接失败

**问题**：无法连接到数据库

**解决方案**：
- 检查数据库服务是否正在运行
- 验证主机地址和端口是否正确
- 确认用户名和密码是否正确
- 检查防火墙设置
- 验证网络连接

```bash
# 测试达梦数据库连接
telnet 192.168.1.100 5236

# 测试人大金仓数据库连接
telnet 192.168.1.101 54321
```

### 2. 驱动未安装

**问题**：ImportError: No module named 'dmPython' 或 'psycopg2'

**解决方案**：
```bash
# 安装达梦数据库驱动
pip install dmPython

# 安装人大金仓数据库驱动
pip install psycopg2-binary
```

### 3. 权限不足

**问题**：权限错误或无法创建表

**解决方案**：
- 确保数据库用户有 CREATE TABLE 权限
- 确保数据库用户有 DROP TABLE 权限
- 确保数据库用户有 INSERT/SELECT 权限

```sql
-- 达梦数据库授权示例
GRANT CREATE TABLE TO test_user;
GRANT DROP ANY TABLE TO test_user;

-- 人大金仓数据库授权示例
GRANT CREATE ON SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
```

### 4. 测试超时

**问题**：测试运行时间过长或超时

**解决方案**：
- 检查网络延迟
- 增加超时时间
- 使用本地数据库实例进行测试

### 5. 端口冲突

**问题**：端口已被占用

**解决方案**：
- 修改数据库配置使用不同的端口
- 更新环境变量中的端口号

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      # 如果使用 Docker 容器运行数据库
      dm-database:
        image: dm8:latest
        ports:
          - 5236:5236
        env:
          DM_PASSWORD: password
      
      kingbase-database:
        image: kingbase:latest
        ports:
          - 54321:54321
        env:
          KINGBASE_PASSWORD: password
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install dmPython psycopg2-binary pytest pytest-asyncio
      
      - name: Run integration tests
        env:
          DM_TEST_URL: dm://SYSDBA:password@localhost:5236/TESTDB
          KINGBASE_TEST_URL: kingbase://SYSTEM:password@localhost:54321/TEST
        run: |
          pytest tests/test_dm_integration.py -v
          pytest tests/test_kingbase_integration.py -v
          pytest tests/test_error_scenarios_integration.py -v
```

## 最佳实践

1. **使用专用测试数据库**：不要在生产数据库上运行集成测试
2. **定期运行测试**：在每次代码变更后运行集成测试
3. **监控测试性能**：记录测试执行时间，及时发现性能问题
4. **保持测试数据最小化**：只创建必要的测试数据
5. **清理测试数据**：确保测试后清理所有测试数据
6. **使用环境变量**：不要在代码中硬编码数据库凭证
7. **文档化测试场景**：为每个测试用例添加清晰的文档说明

## 参考资料

- [达梦数据库官方文档](https://eco.dameng.com/document/dm/zh-cn/start/index.html)
- [人大金仓数据库官方文档](https://help.kingbase.com.cn/)
- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)

## 联系支持

如果遇到问题，请：
1. 查看本文档的故障排查部分
2. 检查测试日志获取详细错误信息
3. 在项目 GitHub 仓库提交 Issue
4. 联系项目维护者获取帮助
