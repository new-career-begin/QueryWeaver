# 数据库驱动安装指南

本文档说明如何安装和配置 QueryWeaver 支持的各种数据库驱动。

## 概述

QueryWeaver 支持以下数据库类型：

- **PostgreSQL** - 使用 `psycopg2-binary` 驱动
- **MySQL** - 使用 `pymysql` 驱动
- **达梦数据库 (DM Database)** - 使用 `dmPython` 驱动
- **人大金仓数据库 (KingbaseES)** - 使用 `psycopg2-binary` 驱动（兼容 PostgreSQL）

## 安装方法

### 方法一：使用 Pipenv（推荐）

如果您使用 Pipenv 管理依赖：

```bash
# 安装所有依赖（包括数据库驱动）
pipenv install

# 或者单独安装特定驱动
pipenv install psycopg2-binary  # PostgreSQL / 人大金仓
pipenv install pymysql           # MySQL
pipenv install dmPython          # 达梦数据库
```

### 方法二：使用 pip

如果您使用 pip 管理依赖：

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者单独安装特定驱动
pip install psycopg2-binary  # PostgreSQL / 人大金仓
pip install pymysql           # MySQL
pip install dmPython          # 达梦数据库
```

## 数据库驱动详细说明

### 1. PostgreSQL 驱动 (psycopg2-binary)

**用途**: 连接 PostgreSQL 数据库

**版本要求**: ~=2.9.11

**安装**:
```bash
pip install psycopg2-binary
```

**连接 URL 格式**:
```
postgresql://username:password@host:port/database
# 或
postgres://username:password@host:port/database
```

**示例**:
```
postgresql://admin:password123@localhost:5432/mydb
```

**注意事项**:
- `psycopg2-binary` 是预编译版本，无需系统依赖
- 如果需要从源码编译，可以使用 `psycopg2`（需要 PostgreSQL 开发库）

### 2. MySQL 驱动 (pymysql)

**用途**: 连接 MySQL 数据库

**版本要求**: ~=1.1.0

**安装**:
```bash
pip install pymysql
```

**连接 URL 格式**:
```
mysql://username:password@host:port/database
```

**示例**:
```
mysql://root:password123@localhost:3306/mydb
```

**注意事项**:
- PyMySQL 是纯 Python 实现，无需额外系统依赖
- 支持 MySQL 5.5+ 和 MariaDB

### 3. 达梦数据库驱动 (dmPython)

**用途**: 连接达梦数据库 (DM Database)

**版本要求**: ~=2.3.0

**安装**:
```bash
pip install dmPython
```

**连接 URL 格式**:
```
dm://username:password@host:port/database
```

**示例**:
```
dm://SYSDBA:SYSDBA@localhost:5236/DAMENG
```

**默认端口**: 5236

**注意事项**:
- dmPython 是达梦官方提供的 Python 数据库驱动
- 支持达梦数据库 DM7 和 DM8 版本
- 需要确保达梦数据库服务已启动
- 默认用户名和密码通常为 `SYSDBA/SYSDBA`

**常见问题**:

1. **安装失败**
   ```
   错误: Could not find a version that satisfies the requirement dmPython
   ```
   解决方案: 确保使用 Python 3.7+ 版本，并检查网络连接

2. **连接失败**
   ```
   错误: [Errno 10061] 由于目标计算机积极拒绝，无法连接
   ```
   解决方案: 
   - 检查达梦数据库服务是否启动
   - 确认端口号是否正确（默认 5236）
   - 检查防火墙设置

### 4. 人大金仓数据库驱动 (psycopg2-binary)

**用途**: 连接人大金仓数据库 (KingbaseES)

**版本要求**: ~=2.9.11

**安装**:
```bash
pip install psycopg2-binary
```

**连接 URL 格式**:
```
kingbase://username:password@host:port/database
# 或使用 PostgreSQL 兼容格式
postgresql://username:password@host:port/database
```

**示例**:
```
kingbase://system:manager@localhost:54321/test
# 或
postgresql://system:manager@localhost:54321/test
```

**默认端口**: 54321

**注意事项**:
- 人大金仓数据库基于 PostgreSQL，因此使用相同的驱动
- 支持 KingbaseES V8 及以上版本
- 默认用户名和密码通常为 `system/manager`
- 可以使用 `kingbase://` 或 `postgresql://` 前缀

**常见问题**:

1. **连接超时**
   ```
   错误: could not connect to server: Connection timed out
   ```
   解决方案:
   - 检查人大金仓数据库服务是否启动
   - 确认端口号是否正确（默认 54321）
   - 检查 `kingbase.conf` 中的 `listen_addresses` 配置

2. **认证失败**
   ```
   错误: FATAL: password authentication failed for user "system"
   ```
   解决方案:
   - 确认用户名和密码是否正确
   - 检查 `kb_hba.conf` 文件的认证配置

## 验证安装

安装完成后，可以使用以下 Python 代码验证驱动是否正确安装：

### 验证 PostgreSQL 驱动

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="your_password"
    )
    print("✓ PostgreSQL 驱动安装成功")
    conn.close()
except Exception as e:
    print(f"✗ PostgreSQL 驱动测试失败: {e}")
```

### 验证 MySQL 驱动

```python
import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        database="mysql",
        user="root",
        password="your_password"
    )
    print("✓ MySQL 驱动安装成功")
    conn.close()
except Exception as e:
    print(f"✗ MySQL 驱动测试失败: {e}")
```

### 验证达梦数据库驱动

```python
import dmPython

try:
    conn = dmPython.connect(
        user="SYSDBA",
        password="SYSDBA",
        server="localhost",
        port=5236
    )
    print("✓ 达梦数据库驱动安装成功")
    conn.close()
except Exception as e:
    print(f"✗ 达梦数据库驱动测试失败: {e}")
```

### 验证人大金仓数据库驱动

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=54321,
        database="test",
        user="system",
        password="manager"
    )
    print("✓ 人大金仓数据库驱动安装成功")
    conn.close()
except Exception as e:
    print(f"✗ 人大金仓数据库驱动测试失败: {e}")
```

## 在 QueryWeaver 中使用

安装驱动后，您可以在 QueryWeaver 中使用相应的数据库连接 URL：

```python
from api.core.schema_loader import load_schema

# PostgreSQL
await load_schema("user_id", "postgresql://user:pass@host:5432/db")

# MySQL
await load_schema("user_id", "mysql://user:pass@host:3306/db")

# 达梦数据库
await load_schema("user_id", "dm://user:pass@host:5236/db")

# 人大金仓数据库
await load_schema("user_id", "kingbase://user:pass@host:54321/db")
```

## 故障排查

### 通用问题

1. **模块未找到错误**
   ```
   ModuleNotFoundError: No module named 'xxx'
   ```
   解决方案: 重新安装对应的驱动包

2. **版本冲突**
   ```
   ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
   ```
   解决方案: 使用虚拟环境隔离依赖

3. **权限错误**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   解决方案: 使用 `--user` 标志或在虚拟环境中安装

### 数据库特定问题

#### 达梦数据库

1. **驱动版本不兼容**
   - 确保 dmPython 版本与达梦数据库版本兼容
   - DM7 使用 dmPython 2.x
   - DM8 使用 dmPython 2.3+

2. **字符编码问题**
   - 达梦数据库默认使用 GB18030 编码
   - 可以在连接时指定编码: `charset='utf8'`

#### 人大金仓数据库

1. **SSL 连接问题**
   - 如果启用了 SSL，需要在连接参数中指定: `sslmode='require'`
   - 或禁用 SSL: `sslmode='disable'`

2. **模式 (Schema) 问题**
   - 人大金仓支持多个模式
   - 默认模式为 `public`
   - 可以在连接 URL 中指定: `?options=-csearch_path=myschema`

## 性能优化建议

1. **使用连接池**
   - 对于高并发场景，建议使用连接池
   - QueryWeaver 内部已实现连接池管理

2. **调整超时设置**
   - 根据网络环境调整连接超时和查询超时
   - 默认超时为 30 秒

3. **批量操作**
   - 对于大量数据操作，使用批量插入/更新
   - 减少网络往返次数

## 安全建议

1. **不要在代码中硬编码密码**
   - 使用环境变量存储数据库凭证
   - 使用配置文件并添加到 `.gitignore`

2. **使用最小权限原则**
   - 为 QueryWeaver 创建专用数据库用户
   - 仅授予必要的权限（通常只需 SELECT 权限）

3. **启用 SSL/TLS 连接**
   - 在生产环境中使用加密连接
   - 防止数据在传输过程中被窃取

## 更多资源

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [达梦数据库官方文档](https://eco.dameng.com/document/dm/zh-cn/start/index.html)
- [人大金仓数据库官方文档](https://help.kingbase.com.cn/v8/)
- [QueryWeaver 项目文档](../README.md)

## 获取帮助

如果您在安装或使用数据库驱动时遇到问题，可以：

1. 查看本文档的故障排查部分
2. 在 GitHub 上提交 Issue
3. 加入 Discord 社区讨论
4. 查看数据库官方文档

---

**最后更新**: 2025-01-15
**版本**: 1.0.0
