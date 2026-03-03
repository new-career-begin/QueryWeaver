# 数据库支持快速开始

本文档提供快速开始使用 QueryWeaver 支持的各种数据库的指南。

## 支持的数据库

QueryWeaver 目前支持以下数据库：

| 数据库类型 | URL 前缀 | 默认端口 | 驱动 |
|-----------|---------|---------|------|
| PostgreSQL | `postgresql://` 或 `postgres://` | 5432 | psycopg2-binary |
| MySQL | `mysql://` | 3306 | pymysql |
| 达梦数据库 | `dm://` | 5236 | dmPython |
| 人大金仓 | `kingbase://` 或 `postgresql://` | 54321 | psycopg2-binary |

## 快速安装

### 安装所有数据库驱动

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 pipenv
pipenv install
```

### 安装特定数据库驱动

```bash
# PostgreSQL / 人大金仓
pip install psycopg2-binary

# MySQL
pip install pymysql

# 达梦数据库
pip install dmPython
```

## 连接示例

### PostgreSQL

```python
# 连接 URL 格式
connection_url = "postgresql://username:password@localhost:5432/database_name"

# 示例
connection_url = "postgresql://postgres:mypassword@localhost:5432/mydb"
```

### MySQL

```python
# 连接 URL 格式
connection_url = "mysql://username:password@localhost:3306/database_name"

# 示例
connection_url = "mysql://root:mypassword@localhost:3306/mydb"
```

### 达梦数据库

```python
# 连接 URL 格式
connection_url = "dm://username:password@localhost:5236/database_name"

# 示例（使用默认用户）
connection_url = "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
```

**注意事项**:
- 达梦数据库默认端口为 5236
- 默认管理员用户名和密码通常为 `SYSDBA/SYSDBA`
- 确保达梦数据库服务已启动

### 人大金仓数据库

```python
# 连接 URL 格式（推荐使用 kingbase:// 前缀）
connection_url = "kingbase://username:password@localhost:54321/database_name"

# 或使用 PostgreSQL 兼容格式
connection_url = "postgresql://username:password@localhost:54321/database_name"

# 示例（使用默认用户）
connection_url = "kingbase://system:manager@localhost:54321/test"
```

**注意事项**:
- 人大金仓数据库默认端口为 54321
- 默认管理员用户名和密码通常为 `system/manager`
- 人大金仓基于 PostgreSQL，因此可以使用 PostgreSQL 的大部分功能

## 在 QueryWeaver 中使用

### 通过 API 连接数据库

```python
import requests

# API 端点
api_url = "http://localhost:8000/api/database/load"

# 请求数据
data = {
    "connection_url": "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
}

# 发送请求
response = requests.post(api_url, json=data)

# 处理响应
if response.status_code == 200:
    print("数据库模式加载成功")
else:
    print(f"加载失败: {response.json()}")
```

### 通过 Python 代码连接

```python
from api.core.schema_loader import load_schema

# 加载数据库模式
async def load_database():
    user_id = "user_123"
    connection_url = "dm://SYSDBA:SYSDBA@localhost:5236/DAMENG"
    
    async for success, message in load_schema(user_id, connection_url):
        print(f"{'✓' if success else '✗'} {message}")

# 运行
import asyncio
asyncio.run(load_database())
```

## 验证连接

### 使用 Python 脚本验证

创建一个测试脚本 `test_connection.py`:

```python
#!/usr/bin/env python3
"""数据库连接测试脚本"""

def test_dm_connection():
    """测试达梦数据库连接"""
    try:
        import dmPython
        conn = dmPython.connect(
            user="SYSDBA",
            password="SYSDBA",
            server="localhost",
            port=5236
        )
        print("✓ 达梦数据库连接成功")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 达梦数据库连接失败: {e}")
        return False

def test_kingbase_connection():
    """测试人大金仓数据库连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=54321,
            database="test",
            user="system",
            password="manager"
        )
        print("✓ 人大金仓数据库连接成功")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 人大金仓数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试数据库连接...\n")
    
    dm_ok = test_dm_connection()
    kingbase_ok = test_kingbase_connection()
    
    print("\n测试结果:")
    print(f"达梦数据库: {'通过' if dm_ok else '失败'}")
    print(f"人大金仓数据库: {'通过' if kingbase_ok else '失败'}")
```

运行测试:

```bash
python test_connection.py
```

## 常见问题

### 1. 驱动安装失败

**问题**: `pip install dmPython` 失败

**解决方案**:
- 确保使用 Python 3.7+ 版本
- 检查网络连接
- 尝试使用国内镜像源: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple dmPython`

### 2. 连接被拒绝

**问题**: `Connection refused` 或 `由于目标计算机积极拒绝，无法连接`

**解决方案**:
- 检查数据库服务是否启动
- 确认端口号是否正确
- 检查防火墙设置
- 确认数据库配置允许远程连接

### 3. 认证失败

**问题**: `Authentication failed` 或 `密码认证失败`

**解决方案**:
- 确认用户名和密码是否正确
- 检查用户是否有访问权限
- 对于达梦数据库，确认用户名大小写（通常为大写）

### 4. 数据库不存在

**问题**: `database "xxx" does not exist`

**解决方案**:
- 确认数据库名称是否正确
- 使用数据库管理工具创建数据库
- 检查用户是否有访问该数据库的权限

## 性能优化提示

1. **使用连接池**: QueryWeaver 内部已实现连接池，无需额外配置

2. **限制查询结果**: 对于大表，建议使用 LIMIT 限制返回行数

3. **创建索引**: 在常用查询列上创建索引可以显著提高性能

4. **定期刷新模式**: 当数据库结构发生变化时，及时刷新图数据库模式

## 安全建议

1. **使用环境变量**: 不要在代码中硬编码数据库密码

```python
import os

connection_url = os.getenv("DATABASE_URL")
```

2. **最小权限原则**: 为 QueryWeaver 创建只读用户

```sql
-- PostgreSQL / 人大金仓
CREATE USER queryweaver WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO queryweaver;

-- MySQL
CREATE USER 'queryweaver'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT ON mydb.* TO 'queryweaver'@'localhost';

-- 达梦数据库
CREATE USER queryweaver IDENTIFIED BY "secure_password";
GRANT SELECT ANY TABLE TO queryweaver;
```

3. **使用 SSL/TLS**: 在生产环境中启用加密连接

## 下一步

- 阅读完整的[数据库驱动安装指南](./database-drivers-installation.md)
- 查看[达梦数据库连接指南](./dm-database-connection-guide.md)
- 查看[人大金仓数据库连接指南](./kingbase-database-connection-guide.md)
- 查看[故障排查指南](./troubleshooting-guide.md)
- 了解[API 数据库类型说明](./api-database-types.md)

## 获取帮助

如果您遇到问题：

1. 查看[故障排查文档](./troubleshooting.md)
2. 在 [GitHub Issues](https://github.com/your-repo/QueryWeaver/issues) 提问
3. 加入 Discord 社区讨论

---

**提示**: 本文档提供快速开始指南。详细信息请参考[完整的数据库驱动安装指南](./database-drivers-installation.md)。
