# API 数据库类型说明

本文档说明 QueryWeaver REST API 和 MCP 协议中新增的数据库类型支持。

## 概述

QueryWeaver API 现已支持以下数据库类型：

- `postgresql` - PostgreSQL 数据库
- `mysql` - MySQL 数据库
- `dm` - 达梦数据库 (DM Database)
- `kingbase` - 人大金仓数据库 (KingbaseES)

## REST API 更新

### 连接数据库端点

**端点**: `POST /api/database/connect`

**请求体**:
```json
{
  "connection_url": "string"
}
```

**支持的连接 URL 格式**:

#### PostgreSQL
```
postgresql://username:password@host:port/database
postgres://username:password@host:port/database
```

#### MySQL
```
mysql://username:password@host:port/database
```

#### 达梦数据库
```
dm://username:password@host:port/database
```

#### 人大金仓数据库
```
kingbase://username:password@host:port/database
postgresql://username:password@host:port/database
```

**示例请求**:

```bash
# 连接达梦数据库
curl -X POST "http://localhost:5000/api/database/connect" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
  }'

# 连接人大金仓数据库
curl -X POST "http://localhost:5000/api/database/connect" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "kingbase://system:manager@localhost:54321/test"
  }'
```

**响应**:

成功响应 (200 OK):
```json
{
  "status": "success",
  "message": "数据库连接成功",
  "graph_id": "user_123_DAMENG",
  "database_type": "dm",
  "tables_count": 15
}
```

错误响应 (400 Bad Request):
```json
{
  "status": "error",
  "message": "连接失败: 无法连接到数据库服务器",
  "error_code": "CONNECTION_ERROR"
}
```

### 加载数据库模式端点

**端点**: `POST /api/database/load`

**请求体**:
```json
{
  "connection_url": "string"
}
```

**响应**: 流式响应，返回模式加载进度

**示例**:

```bash
curl -X POST "http://localhost:5000/api/database/load" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
  }' \
  --no-buffer
```

**流式响应格式**:

```json
{"status": true, "message": "正在连接数据库..."}
{"status": true, "message": "正在提取表信息..."}
{"status": true, "message": "正在提取列信息..."}
{"status": true, "message": "正在构建图谱..."}
{"status": true, "message": "模式加载完成"}
```

### 查询数据库端点

**端点**: `POST /graphs/{graph_id}`

**请求体**:
```json
{
  "chat": ["自然语言查询"],
  "result": [],
  "instructions": "可选的查询指令"
}
```

**数据库类型自动识别**:

系统会根据 `graph_id` 自动识别数据库类型，并使用相应的 SQL 方言生成查询。

**示例**:

```bash
# 查询达梦数据库
curl -X POST "http://localhost:5000/graphs/user_123_DAMENG" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat": ["查询所有用户"]
  }'

# 查询人大金仓数据库
curl -X POST "http://localhost:5000/graphs/user_123_test" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat": ["显示最近10条订单"]
  }'
```

**响应**:

```json
{
  "type": "sql",
  "sql": "SELECT * FROM \"USERS\"",
  "database_type": "dm"
}
```

### 刷新数据库模式端点

**端点**: `POST /api/database/refresh`

**请求体**:
```json
{
  "graph_id": "string"
}
```

**示例**:

```bash
curl -X POST "http://localhost:5000/api/database/refresh" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "user_123_DAMENG"
  }'
```

## MCP 协议更新

### connect_database 工具

**描述**: 连接到数据库并加载模式

**参数**:
```json
{
  "connection_url": {
    "type": "string",
    "description": "数据库连接 URL",
    "required": true
  }
}
```

**支持的数据库类型**:
- PostgreSQL: `postgresql://` 或 `postgres://`
- MySQL: `mysql://`
- 达梦数据库: `dm://`
- 人大金仓数据库: `kingbase://` 或 `postgresql://`

**示例调用**:

```json
{
  "name": "connect_database",
  "arguments": {
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
  }
}
```

**返回**:

```json
{
  "status": "success",
  "graph_id": "user_123_DAMENG",
  "database_type": "dm",
  "tables": [
    {
      "name": "USERS",
      "columns": ["ID", "USERNAME", "EMAIL"]
    }
  ]
}
```

### query_database 工具

**描述**: 使用自然语言查询数据库

**参数**:
```json
{
  "graph_id": {
    "type": "string",
    "description": "数据库图 ID",
    "required": true
  },
  "query": {
    "type": "string",
    "description": "自然语言查询",
    "required": true
  }
}
```

**示例调用**:

```json
{
  "name": "query_database",
  "arguments": {
    "graph_id": "user_123_DAMENG",
    "query": "查询所有用户"
  }
}
```

**返回**:

```json
{
  "sql": "SELECT * FROM \"USERS\"",
  "database_type": "dm",
  "results": [
    {"ID": 1, "USERNAME": "alice", "EMAIL": "alice@example.com"},
    {"ID": 2, "USERNAME": "bob", "EMAIL": "bob@example.com"}
  ],
  "execution_time": 0.123
}
```

### list_databases 工具

**描述**: 列出所有已连接的数据库

**参数**: 无

**返回**:

```json
{
  "databases": [
    {
      "graph_id": "user_123_DAMENG",
      "database_type": "dm",
      "database_name": "DAMENG",
      "tables_count": 15,
      "connected_at": "2025-01-15T10:30:00Z"
    },
    {
      "graph_id": "user_123_test",
      "database_type": "kingbase",
      "database_name": "test",
      "tables_count": 8,
      "connected_at": "2025-01-15T11:00:00Z"
    }
  ]
}
```

### database_schema 工具

**描述**: 获取数据库模式信息

**参数**:
```json
{
  "graph_id": {
    "type": "string",
    "description": "数据库图 ID",
    "required": true
  }
}
```

**返回**:

```json
{
  "graph_id": "user_123_DAMENG",
  "database_type": "dm",
  "tables": [
    {
      "name": "USERS",
      "description": "用户表",
      "columns": [
        {
          "name": "ID",
          "type": "INT",
          "nullable": false,
          "key": "PRIMARY KEY"
        },
        {
          "name": "USERNAME",
          "type": "VARCHAR(50)",
          "nullable": false,
          "key": "NONE"
        }
      ],
      "foreign_keys": []
    }
  ]
}
```

## 数据库类型识别

### URL 前缀映射

系统根据连接 URL 的前缀自动识别数据库类型：

| URL 前缀 | 数据库类型 | 加载器类 |
|---------|----------|---------|
| `postgresql://` 或 `postgres://` | PostgreSQL | PostgresLoader |
| `mysql://` | MySQL | MySQLLoader |
| `dm://` | 达梦数据库 | DM_Loader |
| `kingbase://` | 人大金仓 | Kingbase_Loader |

### 特殊情况

**人大金仓数据库**:
- 支持 `kingbase://` 前缀（推荐）
- 也支持 `postgresql://` 前缀（兼容模式）
- 系统会根据端口号（54321）和其他特征自动识别为人大金仓数据库

## SQL 方言差异

不同数据库类型生成的 SQL 查询会有所不同：

### 标识符引用

**PostgreSQL / 达梦 / 人大金仓**:
```sql
SELECT "user_id", "username" FROM "users"
```

**MySQL**:
```sql
SELECT `user_id`, `username` FROM `users`
```

### 分页

**PostgreSQL / 达梦 / 人大金仓**:
```sql
SELECT * FROM "users" LIMIT 10 OFFSET 20
```

**MySQL**:
```sql
SELECT * FROM `users` LIMIT 20, 10
```

### 日期函数

**PostgreSQL / 人大金仓**:
```sql
SELECT * FROM "orders" WHERE "order_date" >= CURRENT_DATE - INTERVAL '7 days'
```

**MySQL**:
```sql
SELECT * FROM `orders` WHERE `order_date` >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
```

**达梦数据库**:
```sql
SELECT * FROM "ORDERS" WHERE "ORDER_DATE" >= SYSDATE - 7
```

## 错误代码

API 返回的错误代码说明：

| 错误代码 | 说明 | HTTP 状态码 |
|---------|------|-----------|
| `INVALID_URL` | 连接 URL 格式无效 | 400 |
| `UNSUPPORTED_DATABASE` | 不支持的数据库类型 | 400 |
| `CONNECTION_ERROR` | 数据库连接失败 | 500 |
| `AUTHENTICATION_ERROR` | 认证失败 | 401 |
| `SCHEMA_EXTRACTION_ERROR` | 模式提取失败 | 500 |
| `QUERY_EXECUTION_ERROR` | 查询执行失败 | 500 |
| `TIMEOUT_ERROR` | 操作超时 | 504 |

## 性能考虑

### 连接池

系统为每种数据库类型维护独立的连接池：

- 默认池大小: 10
- 最大溢出: 20
- 连接超时: 30 秒
- 查询超时: 30 秒

### 缓存策略

- 模式信息缓存在 FalkorDB 图数据库中
- 查询结果不缓存（保证数据实时性）
- 向量嵌入缓存在图节点中

### 限制

- 单次查询最多返回 1000 行
- 模式加载超时: 5 分钟
- 查询执行超时: 30 秒

## 安全性

### 认证

所有 API 端点都需要认证：

```bash
# 使用 Bearer Token
curl -H "Authorization: Bearer YOUR_API_TOKEN" ...
```

### 权限

- 用户只能访问自己连接的数据库
- 默认只允许 SELECT 查询
- 危险操作（INSERT/UPDATE/DELETE）需要额外确认

### 数据保护

- 连接 URL 中的密码在日志中会被脱敏
- 数据库凭证加密存储
- 所有通信使用 HTTPS（生产环境）

## 示例代码

### Python 客户端

```python
import requests

class QueryWeaverClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def connect_database(self, connection_url):
        """连接数据库"""
        response = requests.post(
            f"{self.base_url}/api/database/connect",
            headers=self.headers,
            json={"connection_url": connection_url}
        )
        return response.json()
    
    def query_database(self, graph_id, query):
        """查询数据库"""
        response = requests.post(
            f"{self.base_url}/graphs/{graph_id}",
            headers=self.headers,
            json={"chat": [query]}
        )
        return response.json()

# 使用示例
client = QueryWeaverClient("http://localhost:5000", "YOUR_API_TOKEN")

# 连接达梦数据库
result = client.connect_database("dm://SYSDBA:SYSDBA@localhost:5236/DAMENG")
print(f"连接成功，图 ID: {result['graph_id']}")

# 查询数据
query_result = client.query_database(result['graph_id'], "查询所有用户")
print(f"生成的 SQL: {query_result['sql']}")
```

### JavaScript 客户端

```javascript
class QueryWeaverClient {
  constructor(baseUrl, apiToken) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json'
    };
  }

  async connectDatabase(connectionUrl) {
    const response = await fetch(`${this.baseUrl}/api/database/connect`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ connection_url: connectionUrl })
    });
    return response.json();
  }

  async queryDatabase(graphId, query) {
    const response = await fetch(`${this.baseUrl}/graphs/${graphId}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ chat: [query] })
    });
    return response.json();
  }
}

// 使用示例
const client = new QueryWeaverClient('http://localhost:5000', 'YOUR_API_TOKEN');

// 连接人大金仓数据库
const result = await client.connectDatabase('kingbase://system:manager@localhost:54321/test');
console.log(`连接成功，图 ID: ${result.graph_id}`);

// 查询数据
const queryResult = await client.queryDatabase(result.graph_id, '显示最近10条订单');
console.log(`生成的 SQL: ${queryResult.sql}`);
```

## 相关文档

- [达梦数据库连接指南](dm-database-connection-guide.md)
- [人大金仓数据库连接指南](kingbase-database-connection-guide.md)
- [数据库驱动安装指南](database-drivers-installation.md)
- [故障排查指南](troubleshooting-guide.md)
- [REST API 完整文档](https://app.queryweaver.ai/docs)

---

最后更新: 2025-01-15
