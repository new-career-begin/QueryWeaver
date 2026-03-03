# 人大金仓数据库连接指南

本文档介绍如何在 QueryWeaver 中连接和使用人大金仓数据库（KingbaseES）。

## 概述

人大金仓数据库（KingbaseES）是一款基于 PostgreSQL 的国产关系型数据库管理系统，广泛应用于政府、金融、能源等行业。QueryWeaver 支持人大金仓数据库 V8 及以上版本，可以通过自然语言查询人大金仓数据库中的数据。

## 前置要求

### 1. 人大金仓数据库驱动

人大金仓数据库基于 PostgreSQL，因此 QueryWeaver 使用 `psycopg2` 作为数据库驱动。该驱动已包含在项目依赖中，无需额外安装。

如果您需要手动安装驱动，请参考 [数据库驱动安装指南](database-drivers-installation.md)。

### 2. 数据库访问权限

确保您的数据库用户具有以下权限：

- **连接权限**: 能够连接到目标数据库
- **查询权限**: 能够执行 SELECT 查询
- **系统表访问权限**: 能够查询以下系统表以提取模式信息
  - `information_schema.tables` - 表信息
  - `information_schema.columns` - 列信息
  - `information_schema.table_constraints` - 约束信息
  - `information_schema.key_column_usage` - 键列信息
  - `pg_indexes` - 索引信息

推荐使用具有 `CONNECT` 和 `SELECT` 权限的用户账号。

### 3. 网络连接

确保 QueryWeaver 服务器能够访问人大金仓数据库服务器：

- 默认端口: `54321`
- 确保防火墙允许该端口的连接
- 如果使用云数据库，确保安全组规则允许访问

## 连接 URL 格式

人大金仓数据库支持两种连接 URL 格式：

### 格式 1: 使用 kingbase 协议（推荐）

```
kingbase://username:password@host:port/database
```

### 格式 2: 使用 postgresql 协议（兼容）

```
postgresql://username:password@host:port/database
```

> **注意**: 两种格式都可以使用，QueryWeaver 会自动识别并正确处理。推荐使用 `kingbase://` 前缀以明确标识数据库类型。

### 参数说明

- `username`: 数据库用户名
- `password`: 数据库密码
- `host`: 数据库服务器地址（IP 或域名）
- `port`: 数据库端口（默认 54321）
- `database`: 数据库名称

### 连接示例

#### 本地数据库连接

```
kingbase://system:manager@localhost:54321/test
```

#### 远程数据库连接

```
kingbase://dbuser:SecurePass123@192.168.1.100:54321/production
```

#### 使用域名连接

```
kingbase://app_user:MyPassword@kingbase-server.example.com:54321/app_db
```

#### 使用 PostgreSQL 兼容格式

```
postgresql://system:manager@localhost:54321/test
```

## 在 QueryWeaver 中连接人大金仓数据库

### 方法 1: 通过 Web 界面连接

1. 访问 QueryWeaver Web 界面: http://localhost:5000
2. 点击 "连接数据库" 按钮
3. 选择数据库类型: "人大金仓数据库 (KingbaseES)"
4. 填写连接信息:
   - 主机地址: `192.168.1.100`
   - 端口: `54321`
   - 数据库名: `test`
   - 用户名: `system`
   - 密码: `manager`
5. 点击 "连接" 按钮
6. 等待模式加载完成

### 方法 2: 通过 REST API 连接

使用 POST 请求连接数据库：

```bash
curl -X POST "http://localhost:5000/api/database/connect" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "kingbase://system:manager@localhost:54321/test"
  }'
```

### 方法 3: 通过 MCP 协议连接

如果您使用 MCP 客户端，可以调用 `connect_database` 工具：

```json
{
  "name": "connect_database",
  "arguments": {
    "connection_url": "kingbase://system:manager@localhost:54321/test"
  }
}
```

## 模式加载过程

连接人大金仓数据库后，QueryWeaver 会自动执行以下步骤：

1. **验证连接**: 测试数据库连接是否成功
2. **提取表信息**: 从 `information_schema.tables` 查询所有用户表
3. **提取列信息**: 从 `information_schema.columns` 查询每个表的列定义
4. **提取约束信息**: 从 `information_schema.table_constraints` 查询主键和外键
5. **提取索引信息**: 从 `pg_indexes` 查询索引定义
6. **采样数据**: 为每个列提取最多 3 个示例值
7. **生成描述**: 使用 AI 模型生成表和列的自然语言描述
8. **构建图谱**: 将模式信息加载到 FalkorDB 图数据库
9. **创建向量索引**: 为语义搜索创建向量嵌入

整个过程通常需要 10-60 秒，具体取决于数据库的大小和复杂度。

## 查询人大金仓数据库

连接成功后，您可以使用自然语言查询数据库：

### 示例查询

**查询用户数量**
```
有多少个用户？
```

生成的 SQL:
```sql
SELECT COUNT(*) AS "用户数量" FROM "users"
```

**查询最近的订单**
```
显示最近 10 条订单
```

生成的 SQL:
```sql
SELECT * FROM "orders" ORDER BY "order_date" DESC LIMIT 10
```

**关联查询**
```
查询每个用户的订单总金额
```

生成的 SQL:
```sql
SELECT 
  "u"."username" AS "用户名",
  SUM("o"."total_amount") AS "订单总金额"
FROM "users" "u"
LEFT JOIN "orders" "o" ON "u"."id" = "o"."user_id"
GROUP BY "u"."username"
```

**时间范围查询**
```
查询本月的订单
```

生成的 SQL:
```sql
SELECT * FROM "orders"
WHERE "order_date" >= DATE_TRUNC('month', CURRENT_DATE)
  AND "order_date" < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
```

## 人大金仓数据库特性支持

### 数据类型映射

QueryWeaver 支持以下人大金仓数据库数据类型：

| 人大金仓类型 | 映射类型 | 说明 |
|------------|---------|------|
| INTEGER, INT | 整数 | 32 位整数 |
| BIGINT | 长整数 | 64 位整数 |
| SMALLINT | 短整数 | 16 位整数 |
| DECIMAL, NUMERIC | 小数 | 精确数值 |
| REAL, FLOAT4 | 单精度浮点 | 32 位浮点数 |
| DOUBLE PRECISION, FLOAT8 | 双精度浮点 | 64 位浮点数 |
| CHAR, VARCHAR | 字符串 | 定长/变长字符串 |
| TEXT | 文本 | 无限长文本 |
| DATE | 日期 | 日期类型 |
| TIME | 时间 | 时间类型 |
| TIMESTAMP | 时间戳 | 日期时间类型 |
| BOOLEAN | 布尔 | 真/假值 |
| JSON, JSONB | JSON | JSON 数据 |
| ARRAY | 数组 | 数组类型 |
| UUID | UUID | 通用唯一标识符 |

### SQL 方言支持

QueryWeaver 会根据人大金仓数据库的 SQL 方言生成查询：

- **标识符引用**: 使用双引号 `"table_name"`
- **字符串字面量**: 使用单引号 `'string value'`
- **日期函数**: 支持 `DATE_TRUNC()`, `EXTRACT()`, `AGE()` 等
- **分页**: 使用 `LIMIT` 和 `OFFSET` 子句
- **字符串连接**: 使用 `||` 操作符
- **窗口函数**: 支持 `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()` 等
- **CTE**: 支持 `WITH` 子句（公共表表达式）
- **JSON 操作**: 支持 `->`, `->>`, `@>` 等 JSON 操作符

### PostgreSQL 兼容性

人大金仓数据库基于 PostgreSQL，因此支持大部分 PostgreSQL 的特性：

- **事务**: 支持 ACID 事务
- **视图**: 支持普通视图和物化视图
- **触发器**: 支持触发器和存储过程
- **全文搜索**: 支持全文搜索功能
- **扩展**: 支持部分 PostgreSQL 扩展

### 限制和注意事项

1. **只读查询**: 默认情况下，QueryWeaver 只允许 SELECT 查询，不支持 INSERT、UPDATE、DELETE 等修改操作
2. **查询超时**: 默认查询超时时间为 30 秒
3. **结果集限制**: 默认最多返回 1000 行结果
4. **大对象类型**: BYTEA 和大文本类型的列不会被采样
5. **系统表**: 不会提取系统表和临时表的信息
6. **扩展兼容性**: 部分 PostgreSQL 扩展可能不被支持

## 性能优化建议

### 1. 索引优化

确保常用查询字段有适当的索引：

```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_date ON orders(order_date);

-- 为 JSON 字段创建 GIN 索引
CREATE INDEX idx_users_metadata ON users USING GIN(metadata);
```

### 2. 统计信息更新

定期更新表的统计信息以优化查询计划：

```sql
-- 更新表统计信息
ANALYZE users;
ANALYZE orders;

-- 或更新整个数据库
ANALYZE;
```

### 3. 连接池配置

对于高并发场景，建议配置适当的连接池大小：

```python
# 在 .env 文件中配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 4. 查询缓存

QueryWeaver 会缓存模式信息，避免重复查询系统表。如果数据库结构发生变化，可以手动刷新模式：

```bash
curl -X POST "http://localhost:5000/api/database/refresh" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "your_database_name"
  }'
```

### 5. 使用物化视图

对于复杂的聚合查询，可以创建物化视图：

```sql
-- 创建物化视图
CREATE MATERIALIZED VIEW user_order_summary AS
SELECT 
  u.id,
  u.username,
  COUNT(o.id) AS order_count,
  SUM(o.total_amount) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username;

-- 刷新物化视图
REFRESH MATERIALIZED VIEW user_order_summary;
```

## 故障排查

如果遇到连接或查询问题，请参考 [故障排查指南](troubleshooting-guide.md)。

常见问题：

1. **连接超时**: 检查网络连接和防火墙设置
2. **权限不足**: 确保用户具有必要的系统表查询权限
3. **驱动错误**: 确认 psycopg2 驱动已正确安装
4. **字符编码**: 确保数据库和客户端使用相同的字符编码（推荐 UTF-8）
5. **SSL 连接**: 如果需要 SSL 连接，在连接 URL 中添加 `?sslmode=require`

### SSL 连接配置

如果您的人大金仓数据库要求 SSL 连接，可以在连接 URL 中添加 SSL 参数：

```
kingbase://user:pass@host:54321/db?sslmode=require
```

支持的 SSL 模式：
- `disable`: 不使用 SSL
- `allow`: 优先使用非 SSL，失败时尝试 SSL
- `prefer`: 优先使用 SSL，失败时使用非 SSL（默认）
- `require`: 必须使用 SSL
- `verify-ca`: 必须使用 SSL 并验证服务器证书
- `verify-full`: 必须使用 SSL 并验证服务器证书和主机名

## 安全建议

1. **使用专用账号**: 为 QueryWeaver 创建专用的数据库账号，不要使用 system 账号
2. **最小权限原则**: 只授予必要的查询权限，不要授予修改权限
3. **密码安全**: 使用强密码，定期更换密码
4. **网络隔离**: 在生产环境中，确保数据库服务器不直接暴露在公网
5. **审计日志**: 启用数据库审计日志，记录所有查询操作
6. **SSL 加密**: 在生产环境中启用 SSL 连接加密

### 创建只读用户示例

```sql
-- 创建只读用户
CREATE USER queryweaver_readonly WITH PASSWORD 'SecurePassword123';

-- 授予连接权限
GRANT CONNECT ON DATABASE your_database TO queryweaver_readonly;

-- 授予 schema 使用权限
GRANT USAGE ON SCHEMA public TO queryweaver_readonly;

-- 授予所有表的查询权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO queryweaver_readonly;

-- 授予未来创建的表的查询权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO queryweaver_readonly;
```

## 与 PostgreSQL 的差异

虽然人大金仓数据库基于 PostgreSQL，但仍有一些差异需要注意：

1. **默认端口**: 人大金仓使用 54321，PostgreSQL 使用 5432
2. **系统表**: 部分系统表的结构可能有所不同
3. **扩展**: 不是所有 PostgreSQL 扩展都被支持
4. **函数**: 部分内置函数可能有差异
5. **配置参数**: 部分配置参数名称或默认值可能不同

## 相关文档

- [数据库驱动安装指南](database-drivers-installation.md)
- [数据库支持快速入门](database-support-quickstart.md)
- [SQL 标识符引用规则](SQL_IDENTIFIER_QUOTING.md)
- [故障排查指南](troubleshooting-guide.md)
- [PostgreSQL 加载器文档](postgres_loader.md)

## 技术支持

如果您在使用人大金仓数据库时遇到问题，可以通过以下方式获取帮助：

- GitHub Issues: https://github.com/FalkorDB/QueryWeaver/issues
- Discord 社区: https://discord.gg/b32KEzMzce
- 邮件支持: support@falkordb.com

---

最后更新: 2025-01-15
