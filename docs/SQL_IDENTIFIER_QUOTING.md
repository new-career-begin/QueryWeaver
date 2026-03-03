# SQL 标识符引用处理文档

## 概述

本文档描述了 QueryWeaver 中 SQL 标识符引用处理的实现，特别是针对达梦数据库（DM Database）和人大金仓数据库（KingbaseES）的支持。

## 背景

在 SQL 中，某些标识符（表名、列名等）需要使用引号来正确处理：

1. **包含特殊字符**：如连字符、空格、点号等
2. **SQL 保留字**：如 SELECT、TABLE、USER 等
3. **以数字开头**：如 123table
4. **包含大小写字母**：某些数据库区分大小写

不同的数据库使用不同的引用字符：
- **MySQL/MariaDB**：使用反引号 `` ` ``
- **PostgreSQL/SQLite/SQL Server/达梦/人大金仓**：使用双引号 `"`

## 功能特性

### 1. 数据库类型检测

`DatabaseSpecificQuoter.get_quote_char(db_type)` 方法根据数据库类型返回正确的引用字符。

```python
from api.sql_utils.sql_sanitizer import DatabaseSpecificQuoter

# 达梦数据库使用双引号
quote_char = DatabaseSpecificQuoter.get_quote_char('dm')
print(quote_char)  # 输出: "

# 人大金仓数据库使用双引号
quote_char = DatabaseSpecificQuoter.get_quote_char('kingbase')
print(quote_char)  # 输出: "

# MySQL 使用反引号
quote_char = DatabaseSpecificQuoter.get_quote_char('mysql')
print(quote_char)  # 输出: `
```

### 2. 标识符引用需求检测

`DatabaseSpecificQuoter.needs_quoting(identifier, db_type)` 方法检查标识符是否需要引用。

```python
# 包含特殊字符 - 需要引用
needs = DatabaseSpecificQuoter.needs_quoting('user-data', 'dm')
print(needs)  # 输出: True

# 普通标识符 - 不需要引用
needs = DatabaseSpecificQuoter.needs_quoting('users', 'dm')
print(needs)  # 输出: False

# SQL 保留字 - 需要引用
needs = DatabaseSpecificQuoter.needs_quoting('SELECT', 'kingbase')
print(needs)  # 输出: True

# 包含大写字母 - 需要引用（达梦和人大金仓）
needs = DatabaseSpecificQuoter.needs_quoting('UserData', 'dm')
print(needs)  # 输出: True
```

### 3. 标识符引用

`DatabaseSpecificQuoter.quote_identifier(identifier, db_type)` 方法为标识符添加引号。

```python
# 达梦数据库
quoted = DatabaseSpecificQuoter.quote_identifier('user-data', 'dm')
print(quoted)  # 输出: "user-data"

# 人大金仓数据库
quoted = DatabaseSpecificQuoter.quote_identifier('order items', 'kingbase')
print(quoted)  # 输出: "order items"

# 包含引号的标识符会被转义
quoted = DatabaseSpecificQuoter.quote_identifier('user"data', 'dm')
print(quoted)  # 输出: "user""data"
```

### 4. 标识符转义

`DatabaseSpecificQuoter.escape_identifier(identifier, db_type)` 方法转义标识符中的特殊字符。

```python
# 达梦数据库 - 双引号转义为两个双引号
escaped = DatabaseSpecificQuoter.escape_identifier('user"data', 'dm')
print(escaped)  # 输出: user""data

# 人大金仓数据库 - 双引号转义为两个双引号
escaped = DatabaseSpecificQuoter.escape_identifier('order"items', 'kingbase')
print(escaped)  # 输出: order""items

# MySQL - 反引号转义为两个反引号
escaped = DatabaseSpecificQuoter.escape_identifier('user`data', 'mysql')
print(escaped)  # 输出: user``data
```

### 5. 自动引用 SQL 查询

`DatabaseSpecificQuoter.auto_quote_identifiers_for_db(sql_query, known_tables, db_type)` 方法自动为 SQL 查询中的标识符添加引号。

```python
# 达梦数据库
sql = "SELECT * FROM user-data WHERE id = 1"
known_tables = {'user-data'}
result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
    sql, known_tables, 'dm'
)
print(result)  # 输出: SELECT * FROM "user-data" WHERE id = 1
print(modified)  # 输出: True

# 人大金仓数据库 - 多表 JOIN
sql = "SELECT * FROM order-items JOIN user-data ON order-items.user_id = user-data.id"
known_tables = {'order-items', 'user-data'}
result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
    sql, known_tables, 'kingbase'
)
print(result)
# 输出: SELECT * FROM "order-items" JOIN "user-data" ON "order-items".user_id = "user-data".id
```

## 引用规则

### 达梦数据库（DM Database）

1. **引用字符**：双引号 `"`
2. **转义规则**：双引号转义为两个双引号 `""`
3. **需要引用的情况**：
   - 包含特殊字符（连字符、空格、点号等）
   - SQL 保留字
   - 以数字开头
   - 包含大写字母

**示例**：

```sql
-- 包含连字符的表名
SELECT * FROM "user-data" WHERE id = 1;

-- 包含双引号的标识符
SELECT * FROM "user""data" WHERE id = 1;

-- SQL 保留字
SELECT * FROM "TABLE" WHERE "USER" = 'admin';

-- 包含大写字母
SELECT * FROM "UserData" WHERE "UserId" = 1;
```

### 人大金仓数据库（KingbaseES）

人大金仓基于 PostgreSQL，因此遵循相同的引用规则：

1. **引用字符**：双引号 `"`
2. **转义规则**：双引号转义为两个双引号 `""`
3. **需要引用的情况**：
   - 包含特殊字符（连字符、空格、点号等）
   - SQL 保留字
   - 以数字开头
   - 包含大写字母

**示例**：

```sql
-- 包含空格的表名
SELECT * FROM "order items" WHERE id = 1;

-- 包含连字符的表名
SELECT * FROM "user-data" WHERE id = 1;

-- 多表 JOIN
SELECT * 
FROM "order-items" 
JOIN "user-data" ON "order-items"."user_id" = "user-data"."id";
```

## 使用场景

### 场景 1：数据库模式提取

在提取数据库模式时，自动为包含特殊字符的表名和列名添加引号：

```python
from api.loaders.dm_loader import DM_Loader

# 提取表信息时，自动处理特殊字符
cursor.execute("""
    SELECT DISTINCT "{col_name}"
    FROM "{table_name}"
    WHERE "{col_name}" IS NOT NULL
""")
```

### 场景 2：SQL 查询生成

在生成 SQL 查询时，根据数据库类型自动添加引号：

```python
from api.sql_utils.sql_sanitizer import DatabaseSpecificQuoter

# 生成的 SQL 查询
sql = "SELECT * FROM user-data WHERE id = 1"

# 自动添加引号
known_tables = {'user-data'}
result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
    sql, known_tables, 'dm'
)

# 执行查询
DM_Loader.execute_sql_query(result, db_url)
```

### 场景 3：查询验证

在执行查询前，验证并修正标识符引用：

```python
def validate_and_fix_query(sql: str, db_type: str, known_tables: set) -> str:
    """
    验证并修正 SQL 查询中的标识符引用
    
    Args:
        sql: 原始 SQL 查询
        db_type: 数据库类型
        known_tables: 已知的表名集合
        
    Returns:
        修正后的 SQL 查询
    """
    result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
        sql, known_tables, db_type
    )
    
    if modified:
        logging.info(f"SQL 查询已修正: {sql} -> {result}")
    
    return result
```

## SQL 保留字列表

以下是常见的 SQL 保留字，使用时需要引用：

```
SELECT, FROM, WHERE, JOIN, LEFT, RIGHT, INNER, OUTER, ON, AS, AND, OR, NOT,
IN, BETWEEN, LIKE, IS, NULL, ORDER, BY, GROUP, HAVING, LIMIT, OFFSET,
INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TABLE, INTO, VALUES, SET,
COUNT, SUM, AVG, MAX, MIN, DISTINCT, ALL, UNION, INTERSECT, EXCEPT,
CASE, WHEN, THEN, ELSE, END, CAST, ASC, DESC, INDEX, KEY, PRIMARY,
FOREIGN, UNIQUE, CHECK, DEFAULT, CONSTRAINT, REFERENCES, CASCADE, RESTRICT,
VIEW, TRIGGER, PROCEDURE, FUNCTION, SCHEMA, DATABASE, USER, GRANT, REVOKE,
COMMIT, ROLLBACK, TRANSACTION, BEGIN
```

## 特殊字符列表

以下特殊字符在标识符中出现时需要引用：

```
- (连字符)
  (空格)
. (点号)
@ (at符号)
# (井号)
$ (美元符号)
% (百分号)
^ (插入符)
& (and符号)
* (星号)
( ) (括号)
+ (加号)
= (等号)
[ ] (方括号)
{ } (花括号)
| (竖线)
\ (反斜杠)
: (冒号)
; (分号)
" (双引号)
' (单引号)
< > (尖括号)
, (逗号)
? (问号)
/ (斜杠)
```

## 测试

### 运行单元测试

```bash
# 运行所有标识符引用测试
python -m pytest tests/test_sql_identifier_quoting.py -v

# 运行特定测试类
python -m pytest tests/test_sql_identifier_quoting.py::TestDatabaseSpecificQuoter -v

# 运行验证脚本
python tests/verify_identifier_quoting.py
```

### 测试覆盖

单元测试覆盖以下场景：

1. ✅ 不同数据库类型的引用字符
2. ✅ 特殊字符检测
3. ✅ SQL 保留字检测
4. ✅ 以数字开头的标识符
5. ✅ 包含大写字母的标识符
6. ✅ 标识符引用
7. ✅ 引号转义
8. ✅ 自动引用 SQL 查询
9. ✅ 多表 JOIN 查询
10. ✅ 边界情况（空标识符、Unicode 字符等）

## 最佳实践

### 1. 始终使用参数化查询

虽然标识符引用可以防止某些 SQL 注入，但仍应使用参数化查询：

```python
# 好的做法
cursor.execute(
    'SELECT * FROM "users" WHERE id = %s',
    (user_id,)
)

# 避免字符串拼接
# 不好的做法
cursor.execute(
    f'SELECT * FROM "users" WHERE id = {user_id}'
)
```

### 2. 在模式提取时使用引号

在提取数据库模式时，始终为标识符添加引号：

```python
# 达梦数据库
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = :table_name
""", {"table_name": table_name})

# 使用引号访问列
cursor.execute(f'SELECT DISTINCT "{col_name}" FROM "{table_name}"')
```

### 3. 验证生成的 SQL

在执行生成的 SQL 前，验证标识符引用：

```python
def execute_generated_sql(sql: str, db_type: str, known_tables: set):
    """执行生成的 SQL 查询"""
    # 自动修正标识符引用
    fixed_sql, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
        sql, known_tables, db_type
    )
    
    if modified:
        logging.info(f"SQL 已修正: {sql} -> {fixed_sql}")
    
    # 执行查询
    return execute_query(fixed_sql)
```

### 4. 记录引用操作

记录标识符引用操作，便于调试：

```python
import logging

def quote_and_log(identifier: str, db_type: str) -> str:
    """引用标识符并记录"""
    needs = DatabaseSpecificQuoter.needs_quoting(identifier, db_type)
    
    if needs:
        quoted = DatabaseSpecificQuoter.quote_identifier(identifier, db_type)
        logging.debug(f"标识符已引用: {identifier} -> {quoted} ({db_type})")
        return quoted
    
    return identifier
```

## 故障排查

### 问题 1：查询失败，提示表不存在

**症状**：执行查询时报错 "table does not exist"

**原因**：表名包含特殊字符但未引用

**解决方案**：

```python
# 检查表名是否需要引用
needs = DatabaseSpecificQuoter.needs_quoting('user-data', 'dm')
print(needs)  # True

# 添加引号
quoted = DatabaseSpecificQuoter.quote_identifier('user-data', 'dm')
print(quoted)  # "user-data"

# 使用引用后的表名
sql = f'SELECT * FROM {quoted} WHERE id = 1'
```

### 问题 2：引号转义不正确

**症状**：标识符包含引号时查询失败

**原因**：引号未正确转义

**解决方案**：

```python
# 使用 quote_identifier 方法，自动处理转义
identifier = 'user"data'
quoted = DatabaseSpecificQuoter.quote_identifier(identifier, 'dm')
print(quoted)  # "user""data"
```

### 问题 3：大小写敏感问题

**症状**：查询在某些数据库上失败

**原因**：达梦和人大金仓对大小写敏感

**解决方案**：

```python
# 包含大写字母的标识符需要引用
identifier = 'UserData'
quoted = DatabaseSpecificQuoter.quote_identifier(identifier, 'dm')
print(quoted)  # "UserData"

# 或者统一使用小写
identifier = identifier.lower()  # 'userdata'
```

## 参考资料

- [达梦数据库 SQL 参考手册](https://eco.dameng.com/document/dm/zh-cn/sql-dev/dmpl-sql.html)
- [人大金仓数据库文档](https://help.kingbase.com.cn/)
- [PostgreSQL 标识符引用规则](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS)
- [MySQL 标识符引用规则](https://dev.mysql.com/doc/refman/8.0/en/identifiers.html)

## 更新日志

### 2025-01-15
- ✅ 实现达梦数据库标识符引用支持
- ✅ 实现人大金仓数据库标识符引用支持
- ✅ 添加特殊字符和保留字检测
- ✅ 实现引号转义逻辑
- ✅ 添加自动引用 SQL 查询功能
- ✅ 完成单元测试覆盖
