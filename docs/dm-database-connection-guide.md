# 达梦数据库连接指南

本文档介绍如何在 QueryWeaver 中连接和使用达梦数据库（DM Database）。

## 概述

达梦数据库（DM Database）是一款国产关系型数据库管理系统，广泛应用于政府、金融、电信等行业。QueryWeaver 支持达梦数据库 8.0 及以上版本，可以通过自然语言查询达梦数据库中的数据。

## 前置要求

### 1. 达梦数据库驱动

QueryWeaver 使用 `dmPython` 作为达梦数据库的 Python 驱动。该驱动已包含在项目依赖中，无需额外安装。

如果您需要手动安装驱动，请参考 [数据库驱动安装指南](database-drivers-installation.md)。

### 2. 数据库访问权限

确保您的数据库用户具有以下权限：

- **连接权限**: 能够连接到目标数据库
- **查询权限**: 能够执行 SELECT 查询
- **系统表访问权限**: 能够查询以下系统表以提取模式信息
  - `DBA_TABLES` - 表信息
  - `DBA_TAB_COLUMNS` - 列信息
  - `DBA_CONSTRAINTS` - 约束信息
  - `DBA_CONS_COLUMNS` - 约束列信息
  - `DBA_INDEXES` - 索引信息

推荐使用具有 `DBA` 或 `RESOURCE` 角色的用户账号。

### 3. 网络连接

确保 QueryWeaver 服务器能够访问达梦数据库服务器：

- 默认端口: `5236`
- 确保防火墙允许该端口的连接
- 如果使用云数据库，确保安全组规则允许访问

## 连接 URL 格式

达梦数据库的连接 URL 格式如下：

```
dm://username:password@host:port/database
```

### 参数说明

- `username`: 数据库用户名
- `password`: 数据库密码
- `host`: 数据库服务器地址（IP 或域名）
- `port`: 数据库端口（默认 5236）
- `database`: 数据库名称

### 连接示例

#### 本地数据库连接

```
dm://SYSDBA:SYSDBA@localhost:5236/TESTDB
```

#### 远程数据库连接

```
dm://dbuser:SecurePass123@192.168.1.100:5236/PRODUCTION
```

#### 使用域名连接

```
dm://app_user:MyPassword@dm-server.example.com:5236/APP_DB
```

## 在 QueryWeaver 中连接达梦数据库

### 方法 1: 通过 Web 界面连接

1. 访问 QueryWeaver Web 界面: http://localhost:5000
2. 点击 "连接数据库" 按钮
3. 选择数据库类型: "达梦数据库 (DM)"
4. 填写连接信息:
   - 主机地址: `192.168.1.100`
   - 端口: `5236`
   - 数据库名: `TESTDB`
   - 用户名: `SYSDBA`
   - 密码: `SYSDBA`
5. 点击 "连接" 按钮
6. 等待模式加载完成

### 方法 2: 通过 REST API 连接

使用 POST 请求连接数据库：

```bash
curl -X POST "http://localhost:5000/api/database/connect" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/TESTDB"
  }'
```

### 方法 3: 通过 MCP 协议连接

如果您使用 MCP 客户端，可以调用 `connect_database` 工具：

```json
{
  "name": "connect_database",
  "arguments": {
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/TESTDB"
  }
}
```

## 模式加载过程

连接达梦数据库后，QueryWeaver 会自动执行以下步骤：

1. **验证连接**: 测试数据库连接是否成功
2. **提取表信息**: 从 `DBA_TABLES` 查询所有用户表
3. **提取列信息**: 从 `DBA_TAB_COLUMNS` 查询每个表的列定义
4. **提取约束信息**: 从 `DBA_CONSTRAINTS` 和 `DBA_CONS_COLUMNS` 查询主键和外键
5. **提取索引信息**: 从 `DBA_INDEXES` 查询索引定义
6. **采样数据**: 为每个列提取最多 3 个示例值
7. **生成描述**: 使用 AI 模型生成表和列的自然语言描述
8. **构建图谱**: 将模式信息加载到 FalkorDB 图数据库
9. **创建向量索引**: 为语义搜索创建向量嵌入

整个过程通常需要 10-60 秒，具体取决于数据库的大小和复杂度。

## 查询达梦数据库

连接成功后，您可以使用自然语言查询数据库：

### 示例查询

**查询用户数量**
```
有多少个用户？
```

生成的 SQL:
```sql
SELECT COUNT(*) AS "用户数量" FROM "USERS"
```

**查询最近的订单**
```
显示最近 10 条订单
```

生成的 SQL:
```sql
SELECT * FROM "ORDERS" ORDER BY "ORDER_DATE" DESC LIMIT 10
```

**关联查询**
```
查询每个用户的订单总金额
```

生成的 SQL:
```sql
SELECT 
  "U"."USERNAME" AS "用户名",
  SUM("O"."TOTAL_AMOUNT") AS "订单总金额"
FROM "USERS" "U"
LEFT JOIN "ORDERS" "O" ON "U"."ID" = "O"."USER_ID"
GROUP BY "U"."USERNAME"
```

## 达梦数据库特性支持

### 数据类型映射

QueryWeaver 支持以下达梦数据库数据类型：

| 达梦类型 | 映射类型 | 说明 |
|---------|---------|------|
| INT, INTEGER | 整数 | 32 位整数 |
| BIGINT | 长整数 | 64 位整数 |
| DECIMAL, NUMERIC | 小数 | 精确数值 |
| FLOAT, DOUBLE | 浮点数 | 近似数值 |
| CHAR, VARCHAR | 字符串 | 定长/变长字符串 |
| TEXT, CLOB | 文本 | 大文本对象 |
| DATE | 日期 | 日期类型 |
| TIME | 时间 | 时间类型 |
| TIMESTAMP | 时间戳 | 日期时间类型 |
| BLOB | 二进制 | 大二进制对象 |

### SQL 方言支持

QueryWeaver 会根据达梦数据库的 SQL 方言生成查询：

- **标识符引用**: 使用双引号 `"TABLE_NAME"`
- **字符串字面量**: 使用单引号 `'string value'`
- **日期格式**: 使用 `TO_DATE()` 函数
- **分页**: 使用 `LIMIT` 和 `OFFSET` 子句
- **字符串连接**: 使用 `||` 操作符

### 限制和注意事项

1. **只读查询**: 默认情况下，QueryWeaver 只允许 SELECT 查询，不支持 INSERT、UPDATE、DELETE 等修改操作
2. **查询超时**: 默认查询超时时间为 30 秒
3. **结果集限制**: 默认最多返回 1000 行结果
4. **大对象类型**: BLOB 和 CLOB 类型的列不会被采样
5. **系统表**: 不会提取系统表和临时表的信息

## 性能优化建议

### 1. 索引优化

确保常用查询字段有适当的索引：

```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_users_email ON USERS(EMAIL);
CREATE INDEX idx_orders_date ON ORDERS(ORDER_DATE);
```

### 2. 统计信息更新

定期更新表的统计信息以优化查询计划：

```sql
-- 更新表统计信息
ANALYZE TABLE USERS;
ANALYZE TABLE ORDERS;
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

## 故障排查

如果遇到连接或查询问题，请参考 [故障排查指南](troubleshooting-guide.md)。

常见问题：

1. **连接超时**: 检查网络连接和防火墙设置
2. **权限不足**: 确保用户具有必要的系统表查询权限
3. **驱动错误**: 确认 dmPython 驱动已正确安装
4. **字符编码**: 确保数据库和客户端使用相同的字符编码（推荐 UTF-8）

## 安全建议

1. **使用专用账号**: 为 QueryWeaver 创建专用的数据库账号，不要使用 SYSDBA
2. **最小权限原则**: 只授予必要的查询权限，不要授予修改权限
3. **密码安全**: 使用强密码，定期更换密码
4. **网络隔离**: 在生产环境中，确保数据库服务器不直接暴露在公网
5. **审计日志**: 启用数据库审计日志，记录所有查询操作

## 相关文档

- [数据库驱动安装指南](database-drivers-installation.md)
- [数据库支持快速入门](database-support-quickstart.md)
- [SQL 标识符引用规则](SQL_IDENTIFIER_QUOTING.md)
- [故障排查指南](troubleshooting-guide.md)

## 技术支持

如果您在使用达梦数据库时遇到问题，可以通过以下方式获取帮助：

- GitHub Issues: https://github.com/FalkorDB/QueryWeaver/issues
- Discord 社区: https://discord.gg/b32KEzMzce
- 邮件支持: support@falkordb.com

---

最后更新: 2025-01-15
