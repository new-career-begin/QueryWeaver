# QueryWeaver 故障排查指南

本文档提供 QueryWeaver 常见问题的诊断和解决方案，特别关注达梦数据库和人大金仓数据库的连接和使用问题。

## 目录

- [连接问题](#连接问题)
- [模式加载问题](#模式加载问题)
- [查询执行问题](#查询执行问题)
- [性能问题](#性能问题)
- [驱动安装问题](#驱动安装问题)
- [权限问题](#权限问题)
- [字符编码问题](#字符编码问题)
- [日志和调试](#日志和调试)

---

## 连接问题

### 问题 1: 连接超时

**症状**:
```
ConnectionError: Connection timeout
连接超时，无法连接到数据库服务器
```

**可能原因**:
1. 数据库服务未启动
2. 网络不可达
3. 防火墙阻止连接
4. 端口号错误

**解决方案**:

#### 检查数据库服务状态

**达梦数据库**:
```bash
# Linux
systemctl status DmServiceDMSERVER

# Windows
# 在服务管理器中查看 DmServiceDMSERVER 服务状态
```

**人大金仓数据库**:
```bash
# Linux
systemctl status kingbase

# 或检查进程
ps aux | grep kingbase
```

#### 检查网络连接

```bash
# 测试端口是否可达
telnet <host> <port>

# 或使用 nc
nc -zv <host> <port>

# 达梦数据库默认端口 5236
telnet 192.168.1.100 5236

# 人大金仓数据库默认端口 54321
telnet 192.168.1.100 54321
```

#### 检查防火墙规则

**Linux (firewalld)**:
```bash
# 查看开放的端口
sudo firewall-cmd --list-ports

# 开放达梦数据库端口
sudo firewall-cmd --permanent --add-port=5236/tcp
sudo firewall-cmd --reload

# 开放人大金仓数据库端口
sudo firewall-cmd --permanent --add-port=54321/tcp
sudo firewall-cmd --reload
```

**Windows**:
```powershell
# 查看防火墙规则
netsh advfirewall firewall show rule name=all

# 添加入站规则
netsh advfirewall firewall add rule name="DM Database" dir=in action=allow protocol=TCP localport=5236
netsh advfirewall firewall add rule name="Kingbase Database" dir=in action=allow protocol=TCP localport=54321
```

#### 验证连接 URL 格式

确保连接 URL 格式正确：

```python
# 达梦数据库
dm://username:password@host:5236/database

# 人大金仓数据库
kingbase://username:password@host:54321/database
```

---

### 问题 2: 认证失败

**症状**:
```
AuthenticationError: Authentication failed for user "xxx"
用户 "xxx" 认证失败
```

**可能原因**:
1. 用户名或密码错误
2. 用户不存在
3. 密码包含特殊字符未正确编码
4. 用户账号被锁定

**解决方案**:

#### 验证用户凭证

**达梦数据库**:
```sql
-- 使用 DM 管理工具或 disql 连接测试
./disql SYSDBA/SYSDBA@localhost:5236

-- 查看用户信息
SELECT USERNAME, ACCOUNT_STATUS FROM DBA_USERS WHERE USERNAME = 'YOUR_USER';

-- 重置密码
ALTER USER your_user IDENTIFIED BY "NewPassword123";
```

**人大金仓数据库**:
```sql
-- 使用 ksql 连接测试
ksql -h localhost -p 54321 -U system -d test

-- 查看用户信息
SELECT usename, valuntil FROM pg_user WHERE usename = 'your_user';

-- 重置密码
ALTER USER your_user WITH PASSWORD 'NewPassword123';
```

#### 处理特殊字符

如果密码包含特殊字符，需要进行 URL 编码：

```python
from urllib.parse import quote_plus

password = "P@ssw0rd!#"
encoded_password = quote_plus(password)

# 使用编码后的密码
connection_url = f"dm://user:{encoded_password}@host:5236/db"
```

常见特殊字符编码：
- `@` → `%40`
- `#` → `%23`
- `!` → `%21`
- `$` → `%24`
- `%` → `%25`

---

### 问题 3: 数据库不存在

**症状**:
```
DatabaseError: database "xxx" does not exist
数据库 "xxx" 不存在
```

**解决方案**:

#### 查看可用数据库

**达梦数据库**:
```sql
-- 连接到默认数据库
./disql SYSDBA/SYSDBA@localhost:5236

-- 查看所有数据库
SELECT NAME FROM V$DATABASE;
```

**人大金仓数据库**:
```sql
-- 连接到 postgres 数据库
ksql -h localhost -p 54321 -U system -d postgres

-- 查看所有数据库
\l
-- 或
SELECT datname FROM pg_database;
```

#### 创建数据库

**达梦数据库**:
```sql
CREATE DATABASE mydb;
```

**人大金仓数据库**:
```sql
CREATE DATABASE mydb OWNER system ENCODING 'UTF8';
```

---

## 模式加载问题

### 问题 4: 模式提取失败

**症状**:
```
SchemaExtractionError: Failed to extract schema information
模式提取失败，无法获取表信息
```

**可能原因**:
1. 用户缺少系统表查询权限
2. 数据库中没有用户表
3. 表结构损坏

**解决方案**:

#### 检查权限

**达梦数据库**:
```sql
-- 授予系统表查询权限
GRANT SELECT ANY DICTIONARY TO your_user;

-- 或授予特定系统表权限
GRANT SELECT ON DBA_TABLES TO your_user;
GRANT SELECT ON DBA_TAB_COLUMNS TO your_user;
GRANT SELECT ON DBA_CONSTRAINTS TO your_user;
GRANT SELECT ON DBA_CONS_COLUMNS TO your_user;
```

**人大金仓数据库**:
```sql
-- 授予 information_schema 访问权限
GRANT USAGE ON SCHEMA information_schema TO your_user;

-- 授予系统表查询权限
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO your_user;
```

#### 验证表是否存在

**达梦数据库**:
```sql
-- 查看用户表
SELECT TABLE_NAME FROM DBA_TABLES WHERE OWNER = 'YOUR_SCHEMA';
```

**人大金仓数据库**:
```sql
-- 查看用户表
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

---

### 问题 5: 外键关系提取失败

**症状**:
```
部分表的外键关系未被识别
```

**可能原因**:
1. 外键约束未正确定义
2. 外键约束被禁用
3. 使用了非标准的外键定义

**解决方案**:

#### 检查外键约束

**达梦数据库**:
```sql
-- 查看外键约束
SELECT 
    c.CONSTRAINT_NAME,
    c.TABLE_NAME,
    cc.COLUMN_NAME,
    c.R_CONSTRAINT_NAME
FROM DBA_CONSTRAINTS c
JOIN DBA_CONS_COLUMNS cc ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
WHERE c.CONSTRAINT_TYPE = 'R'
AND c.OWNER = 'YOUR_SCHEMA';
```

**人大金仓数据库**:
```sql
-- 查看外键约束
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

#### 手动创建外键约束

如果外键关系未定义，可以手动创建：

```sql
-- 添加外键约束
ALTER TABLE orders
ADD CONSTRAINT fk_orders_users
FOREIGN KEY (user_id) REFERENCES users(id);
```

---

## 查询执行问题

### 问题 6: SQL 语法错误

**症状**:
```
SQLSyntaxError: syntax error near "xxx"
SQL 语法错误
```

**可能原因**:
1. 生成的 SQL 不符合目标数据库方言
2. 标识符引用不正确
3. 保留字未正确处理

**解决方案**:

#### 检查标识符引用

确保标识符使用正确的引号：

**达梦数据库和人大金仓数据库**:
```sql
-- 正确：使用双引号
SELECT "user_id", "username" FROM "users";

-- 错误：使用反引号（MySQL 风格）
SELECT `user_id`, `username` FROM `users`;
```

#### 检查保留字

如果表名或列名是 SQL 保留字，必须使用引号：

```sql
-- 表名是保留字
SELECT * FROM "order";  -- 正确
SELECT * FROM order;    -- 错误

-- 列名是保留字
SELECT "user", "date" FROM "users";  -- 正确
SELECT user, date FROM users;        -- 错误
```

#### 查看生成的 SQL

在 QueryWeaver 界面中查看生成的 SQL，手动验证语法：

```python
# 在日志中查看生成的 SQL
logger.info(f"Generated SQL: {sql_query}")
```

---

### 问题 7: 查询超时

**症状**:
```
QueryTimeoutError: Query execution timeout
查询执行超时
```

**可能原因**:
1. 查询涉及大表且没有索引
2. 复杂的关联查询
3. 数据库负载过高
4. 超时设置过短

**解决方案**:

#### 优化查询

添加适当的索引：

```sql
-- 为常用查询列创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

#### 调整超时设置

在 `.env` 文件中调整超时时间：

```bash
# 查询超时时间（秒）
QUERY_TIMEOUT=60
```

#### 限制结果集大小

确保查询包含 LIMIT 子句：

```sql
-- 添加 LIMIT 限制
SELECT * FROM large_table LIMIT 1000;
```

---

### 问题 8: 数据类型转换错误

**症状**:
```
TypeError: Object of type datetime is not JSON serializable
日期时间类型无法序列化
```

**解决方案**:

这个问题通常由 QueryWeaver 自动处理，但如果仍然出现，可以检查：

#### 验证序列化逻辑

确保 `_serialize_value()` 方法正确处理所有数据类型：

```python
# 在 dm_loader.py 或 kingbase_loader.py 中
@staticmethod
def _serialize_value(value):
    """将非 JSON 可序列化的值转换为可序列化格式"""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    elif isinstance(value, datetime.time):
        return value.isoformat()
    elif isinstance(value, decimal.Decimal):
        return float(value)
    return value
```

---

## 性能问题

### 问题 9: 模式加载缓慢

**症状**:
```
模式加载时间超过 5 分钟
```

**可能原因**:
1. 数据库包含大量表
2. 表包含大量列
3. 网络延迟高
4. 示例值采样耗时

**解决方案**:

#### 减少采样数量

修改示例值采样逻辑：

```python
# 减少示例值数量
sample_size = 1  # 从 3 减少到 1
```

#### 跳过大表

对于超大表，可以跳过示例值采样：

```python
# 检查表大小
if table_row_count > 1000000:
    # 跳过示例值采样
    sample_values = []
```

#### 使用连接池

确保使用连接池以减少连接开销：

```python
# 在 .env 中配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

---

### 问题 10: 查询响应慢

**症状**:
```
查询执行时间超过 10 秒
```

**解决方案**:

#### 分析查询计划

**达梦数据库**:
```sql
-- 查看执行计划
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
```

**人大金仓数据库**:
```sql
-- 查看执行计划
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

#### 更新统计信息

**达梦数据库**:
```sql
-- 更新表统计信息
ANALYZE TABLE users;
```

**人大金仓数据库**:
```sql
-- 更新表统计信息
ANALYZE users;
```

---

## 驱动安装问题

### 问题 11: dmPython 安装失败

**症状**:
```
ERROR: Could not find a version that satisfies the requirement dmPython
```

**解决方案**:

#### 检查 Python 版本

```bash
# dmPython 需要 Python 3.7+
python --version
```

#### 使用国内镜像源

```bash
# 使用清华镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple dmPython

# 或使用阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ dmPython
```

#### 手动下载安装

如果 pip 安装失败，可以从达梦官网下载驱动包手动安装。

---

### 问题 12: psycopg2 安装失败

**症状**:
```
ERROR: Failed building wheel for psycopg2
```

**解决方案**:

#### 安装二进制版本

```bash
# 使用预编译的二进制版本
pip install psycopg2-binary
```

#### 安装系统依赖

**Ubuntu/Debian**:
```bash
sudo apt-get install libpq-dev python3-dev
pip install psycopg2
```

**CentOS/RHEL**:
```bash
sudo yum install postgresql-devel python3-devel
pip install psycopg2
```

---

## 权限问题

### 问题 13: 权限不足

**症状**:
```
PermissionError: permission denied for table xxx
对表 xxx 的访问权限不足
```

**解决方案**:

#### 授予查询权限

**达梦数据库**:
```sql
-- 授予所有表的查询权限
GRANT SELECT ANY TABLE TO your_user;

-- 或授予特定表权限
GRANT SELECT ON schema.table_name TO your_user;
```

**人大金仓数据库**:
```sql
-- 授予 schema 使用权限
GRANT USAGE ON SCHEMA public TO your_user;

-- 授予所有表的查询权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;

-- 授予未来创建的表的权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO your_user;
```

---

## 字符编码问题

### 问题 14: 中文乱码

**症状**:
```
查询结果中的中文显示为乱码或问号
```

**解决方案**:

#### 检查数据库字符集

**达梦数据库**:
```sql
-- 查看数据库字符集
SELECT SF_GET_PARA_VALUE(1, 'UNICODE_FLAG');

-- 查看表字符集
SELECT TABLE_NAME, CHARACTER_SET_NAME 
FROM DBA_TABLES 
WHERE OWNER = 'YOUR_SCHEMA';
```

**人大金仓数据库**:
```sql
-- 查看数据库编码
SELECT datname, encoding FROM pg_database;

-- 查看客户端编码
SHOW client_encoding;

-- 设置客户端编码
SET client_encoding = 'UTF8';
```

#### 在连接 URL 中指定编码

```python
# 人大金仓数据库
connection_url = "kingbase://user:pass@host:54321/db?client_encoding=utf8"
```

---

## 日志和调试

### 启用详细日志

在 `.env` 文件中启用调试日志：

```bash
# 设置日志级别
LOG_LEVEL=DEBUG

# 启用 SQL 日志
LOG_SQL=true
```

### 查看日志文件

```bash
# 查看应用日志
tail -f logs/queryweaver.log

# 查看错误日志
tail -f logs/error.log
```

### 使用 Python 调试

```python
# 在代码中添加调试输出
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Connection URL: {connection_url}")
logger.debug(f"Query: {sql_query}")
logger.debug(f"Result: {result}")
```

### 数据库日志

**达梦数据库**:
```bash
# 查看 DM 日志
tail -f /dm8/log/DAMENG/DAMENG01.log
```

**人大金仓数据库**:
```bash
# 查看 Kingbase 日志
tail -f /opt/Kingbase/ES/V8/data/log/kingbase.log
```

---

## 获取帮助

如果以上解决方案无法解决您的问题，请通过以下方式获取帮助：

### 1. 收集诊断信息

在报告问题时，请提供以下信息：

```bash
# 系统信息
uname -a

# Python 版本
python --version

# 已安装的包
pip list | grep -E "dmPython|psycopg2|QueryWeaver"

# 数据库版本
# 达梦数据库
./disql SYSDBA/SYSDBA@localhost:5236 -e "SELECT * FROM V\$VERSION;"

# 人大金仓数据库
ksql -h localhost -p 54321 -U system -d test -c "SELECT version();"

# 错误日志
tail -n 100 logs/error.log
```

### 2. 联系支持

- **GitHub Issues**: https://github.com/FalkorDB/QueryWeaver/issues
- **Discord 社区**: https://discord.gg/b32KEzMzce
- **邮件支持**: support@falkordb.com

### 3. 提供复现步骤

在报告问题时，请提供：

1. 完整的错误消息
2. 连接 URL 格式（隐藏敏感信息）
3. 数据库版本和配置
4. 复现问题的步骤
5. 相关的日志输出

---

## 相关文档

- [达梦数据库连接指南](dm-database-connection-guide.md)
- [人大金仓数据库连接指南](kingbase-database-connection-guide.md)
- [数据库驱动安装指南](database-drivers-installation.md)
- [数据库支持快速入门](database-support-quickstart.md)

---

最后更新: 2025-01-15
