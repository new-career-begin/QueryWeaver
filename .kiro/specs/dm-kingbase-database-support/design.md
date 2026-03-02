# 设计文档：达梦和人大金仓数据库支持

## 概述

本设计文档描述了为 QueryWeaver 项目添加达梦数据库(DM Database)和人大金仓数据库(KingbaseES)支持的技术实现方案。该功能将扩展 QueryWeaver 对国产数据库的支持，使用户能够通过自然语言查询这些数据库。

### 设计目标

1. **可扩展性**: 遵循现有的 BaseLoader 架构，确保新数据库加载器易于集成
2. **一致性**: 保持与现有 PostgreSQL 和 MySQL 加载器相同的接口和行为模式
3. **性能**: 优化模式提取和查询执行性能，支持大型数据库
4. **可靠性**: 提供完善的错误处理和重试机制
5. **可维护性**: 代码结构清晰，文档完整，易于维护和扩展

### 技术选型

- **达梦数据库驱动**: `dmPython` - 达梦官方 Python 数据库驱动
- **人大金仓数据库驱动**: `psycopg2` - 由于人大金仓基于 PostgreSQL，可复用 psycopg2 驱动
- **异步支持**: 使用 Python asyncio 实现异步数据库操作
- **连接池**: 复用现有的连接管理机制
- **向量嵌入**: 使用 LiteLLM 的嵌入模型生成表和列的语义向量

## 架构

### 系统架构图

```
用户请求
    ↓
API 路由层 (database.py)
    ↓
模式加载器 (schema_loader.py)
    ↓
    ├─→ URL 解析和数据库类型检测
    ↓
数据库加载器层
    ├─→ DM_Loader (dm_loader.py)
    ├─→ Kingbase_Loader (kingbase_loader.py)
    ├─→ Postgres_Loader (postgres_loader.py)
    └─→ MySQL_Loader (mysql_loader.py)
    ↓
    ├─→ 连接管理
    ├─→ 模式提取
    └─→ 查询执行
    ↓
图加载器 (graph_loader.py)
    ↓
    ├─→ 向量嵌入生成
    ├─→ 图节点创建
    └─→ 关系创建
    ↓
FalkorDB 图数据库
```

### 类层次结构

```
BaseLoader (抽象基类)
    ├─→ PostgresLoader
    ├─→ MySQLLoader
    ├─→ DM_Loader (新增)
    └─→ Kingbase_Loader (新增)
```

### 数据流

1. **连接阶段**:
   - 用户提供数据库连接 URL
   - schema_loader 解析 URL 并识别数据库类型
   - 实例化对应的数据库加载器
   - 建立数据库连接

2. **模式提取阶段**:
   - 查询 information_schema 或系统表获取表列表
   - 对每个表提取列信息、主键、外键、索引
   - 提取列的示例值用于增强描述
   - 使用 LLM 生成表和列的自然语言描述

3. **图构建阶段**:
   - 将表和列信息转换为图节点
   - 生成向量嵌入
   - 创建 BELONGS_TO 和 REFERENCES 关系
   - 存储到 FalkorDB

4. **查询执行阶段**:
   - 接收生成的 SQL 查询
   - 执行查询并获取结果
   - 序列化结果为 JSON 格式
   - 返回给用户

## 组件和接口

### 1. DM_Loader 类

达梦数据库加载器，继承自 BaseLoader。

#### 类定义

```python
class DM_Loader(BaseLoader):
    """
    达梦数据库加载器
    
    负责连接达梦数据库、提取模式信息和执行查询
    """
    
    # DDL 操作关键字
    SCHEMA_MODIFYING_OPERATIONS = {
        'CREATE', 'ALTER', 'DROP', 'RENAME', 'TRUNCATE'
    }
    
    # 模式修改操作的正则模式
    SCHEMA_PATTERNS = [
        r'^\s*CREATE\s+TABLE',
        r'^\s*ALTER\s+TABLE',
        r'^\s*DROP\s+TABLE',
        # ... 其他模式
    ]
```

#### 核心方法

##### load() - 异步生成器

```python
@staticmethod
async def load(prefix: str, connection_url: str) -> AsyncGenerator[tuple[bool, str], None]:
    """
    加载达梦数据库模式到图数据库
    
    Args:
        prefix: 用户 ID 前缀
        connection_url: 达梦数据库连接 URL
                       格式: dm://username:password@host:port/database
    
    Yields:
        tuple[bool, str]: (成功标志, 进度消息)
    
    工作流程:
        1. 解析连接 URL
        2. 建立数据库连接
        3. 提取表信息
        4. 提取关系信息
        5. 加载到图数据库
        6. 关闭连接
    """
```

##### extract_tables_info() - 提取表信息

```python
@staticmethod
def extract_tables_info(cursor) -> Dict[str, Any]:
    """
    从达梦数据库提取表和列信息
    
    Args:
        cursor: 数据库游标
    
    Returns:
        Dict[str, Any]: 表信息字典
        {
            "table_name": {
                "description": "表描述",
                "columns": {
                    "column_name": {
                        "type": "数据类型",
                        "null": "是否可空",
                        "key": "键类型",
                        "description": "列描述",
                        "default": "默认值",
                        "sample_values": ["示例值1", "示例值2"]
                    }
                },
                "foreign_keys": [
                    {
                        "constraint_name": "约束名",
                        "column": "源列",
                        "referenced_table": "引用表",
                        "referenced_column": "引用列"
                    }
                ],
                "col_descriptions": ["列描述1", "列描述2", ...]
            }
        }
    
    实现细节:
        - 查询 DBA_TABLES 获取表列表
        - 查询 DBA_TAB_COLUMNS 获取列信息
        - 查询 DBA_CONSTRAINTS 和 DBA_CONS_COLUMNS 获取约束信息
        - 使用 TABLESAMPLE 或 ORDER BY RANDOM() 获取示例值
    """
```

##### extract_columns_info() - 提取列信息

```python
@staticmethod
def extract_columns_info(cursor, table_name: str) -> Dict[str, Any]:
    """
    提取指定表的列信息
    
    Args:
        cursor: 数据库游标
        table_name: 表名
    
    Returns:
        Dict[str, Any]: 列信息字典
    
    查询字段:
        - COLUMN_NAME: 列名
        - DATA_TYPE: 数据类型
        - NULLABLE: 是否可空
        - DATA_DEFAULT: 默认值
        - COMMENTS: 列注释
        - 主键标识
        - 外键标识
    """
```

##### extract_foreign_keys() - 提取外键

```python
@staticmethod
def extract_foreign_keys(cursor, table_name: str) -> List[Dict[str, str]]:
    """
    提取指定表的外键约束
    
    Args:
        cursor: 数据库游标
        table_name: 表名
    
    Returns:
        List[Dict[str, str]]: 外键列表
    
    查询来源:
        - DBA_CONSTRAINTS: 约束信息
        - DBA_CONS_COLUMNS: 约束列信息
    """
```

##### extract_relationships() - 提取关系

```python
@staticmethod
def extract_relationships(cursor) -> Dict[str, List[Dict[str, str]]]:
    """
    提取数据库中所有表之间的外键关系
    
    Args:
        cursor: 数据库游标
    
    Returns:
        Dict[str, List[Dict[str, str]]]: 关系字典
        {
            "constraint_name": [
                {
                    "from": "源表",
                    "to": "目标表",
                    "source_column": "源列",
                    "target_column": "目标列",
                    "note": "约束说明"
                }
            ]
        }
    """
```

##### execute_sql_query() - 执行查询

```python
@staticmethod
def execute_sql_query(sql_query: str, db_url: str) -> List[Dict[str, Any]]:
    """
    在达梦数据库上执行 SQL 查询
    
    Args:
        sql_query: SQL 查询语句
        db_url: 数据库连接 URL
    
    Returns:
        List[Dict[str, Any]]: 查询结果列表
    
    处理逻辑:
        - SELECT 查询: 返回结果集
        - INSERT/UPDATE/DELETE: 返回影响行数
        - DDL 操作: 返回操作状态
        - 错误处理: 抛出自定义异常
    
    Raises:
        DM_ConnectionError: 连接错误
        DM_QueryError: 查询执行错误
    """
```

##### _serialize_value() - 值序列化

```python
@staticmethod
def _serialize_value(value):
    """
    将非 JSON 可序列化的值转换为可序列化格式
    
    Args:
        value: 原始值
    
    Returns:
        JSON 可序列化的值
    
    转换规则:
        - datetime.date/datetime: 转换为 ISO 8601 字符串
        - datetime.time: 转换为 ISO 8601 时间字符串
        - decimal.Decimal: 转换为浮点数
        - None: 保持为 None
        - 其他: 保持原值
    """
```

##### _execute_sample_query() - 执行示例查询

```python
@staticmethod
def _execute_sample_query(
    cursor, table_name: str, col_name: str, sample_size: int = 3
) -> List[Any]:
    """
    获取列的随机示例值
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        col_name: 列名
        sample_size: 示例数量
    
    Returns:
        List[Any]: 示例值列表
    
    实现策略:
        - 使用 DISTINCT 去重
        - 使用 ORDER BY RANDOM() 随机排序
        - 限制返回数量
        - 过滤 NULL 值
    """
```

##### is_schema_modifying_query() - 检测模式修改

```python
@staticmethod
def is_schema_modifying_query(sql_query: str) -> Tuple[bool, str]:
    """
    检测 SQL 查询是否修改数据库模式
    
    Args:
        sql_query: SQL 查询语句
    
    Returns:
        Tuple[bool, str]: (是否修改模式, 操作类型)
    
    检测方法:
        1. 提取第一个关键字
        2. 检查是否在 SCHEMA_MODIFYING_OPERATIONS 中
        3. 使用正则表达式精确匹配
    """
```

##### refresh_graph_schema() - 刷新图模式

```python
@staticmethod
async def refresh_graph_schema(graph_id: str, db_url: str) -> Tuple[bool, str]:
    """
    刷新图数据库中的模式信息
    
    Args:
        graph_id: 图数据库 ID
        db_url: 数据库连接 URL
    
    Returns:
        Tuple[bool, str]: (成功标志, 消息)
    
    工作流程:
        1. 删除现有图数据
        2. 重新连接数据库
        3. 重新提取模式
        4. 重新加载到图数据库
    """
```

#### 异常类

```python
class DM_QueryError(Exception):
    """达梦数据库查询执行错误"""
    pass

class DM_ConnectionError(Exception):
    """达梦数据库连接错误"""
    pass
```

### 2. Kingbase_Loader 类

人大金仓数据库加载器，继承自 BaseLoader。

#### 设计考虑

人大金仓数据库基于 PostgreSQL，因此可以复用大部分 PostgreSQL 的实现。主要差异：

1. **连接 URL 格式**: 支持 `kingbase://` 前缀
2. **系统表查询**: 可能需要适配特定的系统表
3. **数据类型映射**: 处理人大金仓特有的数据类型
4. **SQL 方言**: 处理可能的 SQL 语法差异

#### 类定义

```python
class Kingbase_Loader(BaseLoader):
    """
    人大金仓数据库加载器
    
    基于 PostgreSQL 实现，适配人大金仓特性
    """
    
    # 继承 PostgreSQL 的大部分实现
    # 重写需要适配的方法
```

#### 核心方法

大部分方法与 PostgresLoader 相同，主要重写以下方法：

##### load() - 适配连接 URL

```python
@staticmethod
async def load(prefix: str, connection_url: str) -> AsyncGenerator[tuple[bool, str], None]:
    """
    加载人大金仓数据库模式到图数据库
    
    Args:
        prefix: 用户 ID 前缀
        connection_url: 人大金仓数据库连接 URL
                       格式: kingbase://username:password@host:port/database
                       或: postgresql://username:password@host:port/database
    
    Yields:
        tuple[bool, str]: (成功标志, 进度消息)
    
    特殊处理:
        - 将 kingbase:// 转换为 postgresql:// 用于 psycopg2
        - 检测人大金仓特定的系统表
        - 适配数据类型映射
    """
```

##### _parse_connection_url() - URL 解析

```python
@staticmethod
def _parse_connection_url(connection_url: str) -> str:
    """
    解析人大金仓连接 URL
    
    Args:
        connection_url: 原始连接 URL
    
    Returns:
        str: psycopg2 兼容的连接 URL
    
    转换规则:
        kingbase://user:pass@host:port/db
        → postgresql://user:pass@host:port/db
    """
```

### 3. schema_loader 模块更新

#### URL 类型检测增强

```python
def _step_detect_db_type(steps_counter: int, url: str) -> tuple[type[BaseLoader], dict[str, str]]:
    """
    检测数据库类型并选择加载器
    
    Args:
        steps_counter: 步骤计数器
        url: 数据库连接 URL
    
    Returns:
        tuple[type[BaseLoader], dict[str, str]]: (加载器类, 进度消息)
    
    支持的 URL 前缀:
        - postgres:// 或 postgresql:// → PostgresLoader
        - mysql:// → MySQLLoader
        - dm:// → DM_Loader
        - kingbase:// → Kingbase_Loader
    
    Raises:
        InvalidArgumentError: 不支持的数据库类型
    """
```

### 4. 数据库驱动集成

#### dmPython 驱动使用

```python
import dmPython

# 连接示例
conn = dmPython.connect(
    user='username',
    password='password',
    server='host',
    port=5236,  # 达梦默认端口
    database='database_name'
)

# 游标操作
cursor = conn.cursor()
cursor.execute("SELECT * FROM table_name")
results = cursor.fetchall()
```

#### psycopg2 驱动复用

```python
import psycopg2

# 人大金仓使用 PostgreSQL 协议
conn = psycopg2.connect(
    host='host',
    port=54321,  # 人大金仓默认端口
    database='database_name',
    user='username',
    password='password'
)
```

## 数据模型

### 数据库连接信息

```python
@dataclass
class DatabaseConnection:
    """数据库连接信息"""
    db_type: str  # 'dm', 'kingbase', 'postgresql', 'mysql'
    host: str
    port: int
    database: str
    user: str
    password: str
    
    def to_url(self) -> str:
        """转换为连接 URL"""
        return f"{self.db_type}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
```

### 表信息模型

```python
@dataclass
class TableInfo:
    """表信息模型"""
    name: str
    description: str
    columns: Dict[str, ColumnInfo]
    foreign_keys: List[ForeignKeyInfo]
    col_descriptions: List[str]  # 用于批量嵌入
```

### 列信息模型

```python
@dataclass
class ColumnInfo:
    """列信息模型"""
    name: str
    type: str
    nullable: bool
    key_type: str  # 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE KEY', 'NONE'
    description: str
    default: Optional[str]
    sample_values: List[str]
```

### 外键信息模型

```python
@dataclass
class ForeignKeyInfo:
    """外键信息模型"""
    constraint_name: str
    column: str
    referenced_table: str
    referenced_column: str
```

### 关系信息模型

```python
@dataclass
class RelationshipInfo:
    """关系信息模型"""
    from_table: str
    to_table: str
    source_column: str
    target_column: str
    constraint_name: str
    note: str
```

### 图节点模型

#### Table 节点

```cypher
(:Table {
    name: string,              // 表名
    description: string,       // 表描述
    embedding: vector,         // 向量嵌入
    foreign_keys: string       // JSON 格式的外键列表
})
```

#### Column 节点

```cypher
(:Column {
    name: string,              // 列名
    type: string,              // 数据类型
    nullable: string,          // 是否可空
    key_type: string,          // 键类型
    description: string,       // 列描述（包含示例值）
    embedding: vector          // 向量嵌入
})
```

#### Database 节点

```cypher
(:Database {
    name: string,              // 数据库名
    description: string,       // 数据库描述
    url: string                // 连接 URL（脱敏）
})
```

### 图关系模型

#### BELONGS_TO 关系

```cypher
(:Column)-[:BELONGS_TO]->(:Table)
```

表示列属于某个表。

#### REFERENCES 关系

```cypher
(:Column)-[:REFERENCES {
    rel_name: string,          // 约束名称
    note: string               // 约束说明
}]->(:Column)
```

表示外键引用关系。

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### 属性 1：数据库类型识别

*对于任意*有效的数据库连接 URL，系统应该正确识别数据库类型并返回对应的加载器类

**验证：需求 1.1, 4.1**

### 属性 2：连接建立成功

*对于任意*有效的数据库连接参数，加载器应该能够成功建立连接并返回连接对象

**验证：需求 1.2, 4.2**

### 属性 3：连接失败错误处理

*对于任意*无效的数据库连接参数（错误的主机、端口、凭证等），系统应该返回包含失败原因的清晰错误信息

**验证：需求 1.3, 4.3**

### 属性 4：URL 格式解析

*对于任意*符合标准格式的数据库连接 URL，系统应该正确解析出所有组件（协议、用户名、密码、主机、端口、数据库名）

**验证：需求 1.4, 4.4, 4.5**

### 属性 5：连接日志记录

*对于任意*成功的数据库连接，系统应该记录包含用户 ID、数据库名称和连接时间的日志条目

**验证：需求 1.5, 4.6**

### 属性 6：表信息提取完整性

*对于任意*数据库，提取的表列表应该包含所有用户表，且每个表信息包含表名和注释

**验证：需求 2.1, 5.1**

### 属性 7：列信息提取完整性

*对于任意*表，提取的列信息应该包含所有列，且每列信息包含列名、数据类型、是否可空、默认值和注释

**验证：需求 2.2, 5.2**

### 属性 8：主键识别准确性

*对于任意*包含主键的表，所有主键列应该被标记为 PRIMARY KEY

**验证：需求 2.3, 5.3**

### 属性 9：外键识别准确性

*对于任意*包含外键的表，所有外键列应该被标记为 FOREIGN KEY

**验证：需求 2.4, 5.4**

### 属性 10：外键信息完整性

*对于任意*外键约束，提取的外键信息应该包含约束名称、源列、引用表和引用列

**验证：需求 2.5, 5.5**

### 属性 11：索引信息提取

*对于任意*包含索引的表，提取的索引信息应该包含所有索引的名称、索引列和索引类型

**验证：需求 2.6, 5.6**

### 属性 12：示例值数量限制

*对于任意*列，提取的示例值数量应该不超过 3 个

**验证：需求 2.7, 5.7**

### 属性 13：错误恢复能力

*对于任意*包含多个表的数据库，当某个表提取失败时，系统应该记录错误日志并继续处理其他表

**验证：需求 2.8, 5.8**

### 属性 14：查询执行正确性

*对于任意*有效的 SELECT 查询，系统应该使用正确的数据库驱动执行查询并返回结果

**验证：需求 3.1, 6.1**

### 属性 15：查询结果格式

*对于任意*SELECT 查询的结果，返回的数据结构应该包含列名和数据行

**验证：需求 3.2, 6.2**

### 属性 16：日期时间序列化

*对于任意*包含日期时间类型的查询结果，所有日期时间值应该被序列化为 ISO 8601 格式字符串

**验证：需求 3.3, 6.3**

### 属性 17：DECIMAL 类型转换

*对于任意*包含 DECIMAL 类型的查询结果，所有 DECIMAL 值应该被转换为浮点数

**验证：需求 3.4, 6.4**

### 属性 18：查询错误处理

*对于任意*无效的 SQL 查询，系统应该返回包含数据库错误信息的错误响应

**验证：需求 3.6, 6.6**

### 属性 19：查询性能日志

*对于任意*执行的查询，系统应该记录包含执行时间和返回行数的日志条目

**验证：需求 3.7, 6.7**

### 属性 20：Table 节点创建

*对于任意*提取的表，图数据库中应该存在对应的 Table 节点，包含表名、描述和向量嵌入

**验证：需求 7.1**

### 属性 21：Column 节点创建

*对于任意*提取的列，图数据库中应该存在对应的 Column 节点，包含列名、数据类型、描述和向量嵌入

**验证：需求 7.2**

### 属性 22：BELONGS_TO 关系创建

*对于任意*列节点，应该存在一条 BELONGS_TO 关系连接该列到其所属的表

**验证：需求 7.3**

### 属性 23：REFERENCES 关系创建

*对于任意*外键约束，应该存在一条 REFERENCES 关系连接源列到目标列

**验证：需求 7.4**

### 属性 24：描述生成非空性

*对于任意*表或列，LLM 生成的自然语言描述应该为非空字符串

**验证：需求 7.5**

### 属性 25：向量嵌入维度

*对于任意*生成的向量嵌入，其维度应该等于嵌入模型的向量大小

**验证：需求 7.6**

### 属性 26：进度消息流式输出

*对于任意*模式加载过程，系统应该流式返回进度消息，每条消息包含当前步骤描述

**验证：需求 7.7**

### 属性 27：模式修改检测

*对于任意*SQL 查询，系统应该正确检测查询是否包含模式修改操作（CREATE、ALTER、DROP、TRUNCATE）

**验证：需求 8.1**

### 属性 28：自动刷新触发

*对于任意*包含模式修改操作的查询，系统应该在执行后自动触发模式刷新流程

**验证：需求 8.2**

### 属性 29：手动刷新完整性

*对于任意*手动刷新请求，系统应该清除现有图数据并重新加载完整的数据库模式

**验证：需求 8.3**

### 属性 30：标识符引用规则

*对于任意*生成的 SQL 查询，达梦和人大金仓数据库的标识符应该使用双引号引用

**验证：需求 9.1, 9.2**

### 属性 31：特殊字符标识符引用

*对于任意*包含特殊字符或空格的标识符，系统应该强制使用引号

**验证：需求 9.3**

### 属性 32：保留字标识符引用

*对于任意*SQL 保留字作为标识符，系统应该使用引号

**验证：需求 9.4**

### 属性 33：引号转义

*对于任意*包含引号字符的标识符，系统应该正确转义引号（双引号转义为两个双引号）

**验证：需求 9.5**

### 属性 34：连接错误日志

*对于任意*连接错误，系统应该记录包含数据库类型、主机地址和错误详情的结构化日志

**验证：需求 10.1**

### 属性 35：查询错误日志

*对于任意*查询错误，系统应该记录包含 SQL 语句和数据库错误消息的结构化日志

**验证：需求 10.2**

### 属性 36：模式提取错误日志

*对于任意*模式提取错误，系统应该记录包含表名和错误详情的结构化日志

**验证：需求 10.3**

### 属性 37：结构化日志格式

*对于任意*日志条目，应该包含时间戳、日志级别、事件类型和详细信息字段

**验证：需求 10.4**

### 属性 38：错误消息安全性

*对于任意*向用户返回的错误消息，应该是用户友好的且不包含敏感信息（如密码、内部路径）

**验证：需求 10.5**

### 属性 39：性能指标记录

*对于任意*数据库操作，系统应该记录包含连接时间、查询执行时间的性能指标

**验证：需求 10.6**

## 错误处理

### 错误类型和处理策略

#### 1. 连接错误

**错误场景**:
- 无效的主机地址或端口
- 错误的用户名或密码
- 数据库不存在
- 网络不可达
- 连接超时

**处理策略**:
```python
try:
    conn = dmPython.connect(...)
except dmPython.Error as e:
    logger.error(json.dumps({
        "event": "connection_error",
        "db_type": "dm",
        "host": host,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }))
    raise DM_ConnectionError(f"无法连接到达梦数据库: {host}:{port}")
```

**用户消息**: "无法连接到数据库，请检查连接参数和网络连接"

#### 2. 查询执行错误

**错误场景**:
- SQL 语法错误
- 表或列不存在
- 权限不足
- 查询超时
- 数据类型不匹配

**处理策略**:
```python
try:
    cursor.execute(sql_query)
except dmPython.DatabaseError as e:
    logger.error(json.dumps({
        "event": "query_error",
        "sql": sql_query,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }))
    raise DM_QueryError(f"查询执行失败: {str(e)}")
```

**用户消息**: "查询执行失败，请检查 SQL 语法"

#### 3. 模式提取错误

**错误场景**:
- 系统表访问权限不足
- 表结构损坏
- 特殊字符处理失败
- 大表超时

**处理策略**:
```python
for table_name in tables:
    try:
        columns_info = extract_columns_info(cursor, table_name)
    except Exception as e:
        logger.error(json.dumps({
            "event": "schema_extraction_error",
            "table": table_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))
        # 继续处理其他表
        continue
```

**用户消息**: "部分表提取失败，已跳过"

#### 4. 图数据库错误

**错误场景**:
- FalkorDB 连接失败
- 向量索引创建失败
- 节点创建失败
- 关系创建失败

**处理策略**:
```python
try:
    await graph.query(cypher_query, params)
except Exception as e:
    logger.error(json.dumps({
        "event": "graph_error",
        "query": cypher_query,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }))
    raise InternalError("图数据库操作失败")
```

**用户消息**: "模式加载失败，请稍后重试"

### 重试机制

对于临时性错误（如网络超时、连接池耗尽），实现指数退避重试：

```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    带指数退避的重试机制
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff_factor: 退避因子
    
    Returns:
        函数执行结果
    
    Raises:
        最后一次尝试的异常
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except (ConnectionError, TimeoutError) as e:
            last_exception = e
            logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= backoff_factor
    
    raise last_exception
```

### 错误日志格式

所有错误日志使用统一的 JSON 格式：

```json
{
    "event": "error_type",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "level": "ERROR",
    "user_id": "user_123",
    "db_type": "dm",
    "context": {
        "table": "users",
        "sql": "SELECT * FROM users",
        "host": "192.168.1.100"
    },
    "error": {
        "type": "DM_QueryError",
        "message": "Table 'users' doesn't exist",
        "stack_trace": "..."
    }
}
```

## 测试策略

### 单元测试

#### 测试框架
- **pytest**: Python 测试框架
- **pytest-asyncio**: 异步测试支持
- **unittest.mock**: 模拟对象

#### 测试覆盖范围

1. **URL 解析测试**
```python
@pytest.mark.parametrize("url,expected", [
    ("dm://user:pass@host:5236/db", ("dm", "user", "pass", "host", 5236, "db")),
    ("kingbase://user:pass@host:54321/db", ("kingbase", "user", "pass", "host", 54321, "db")),
])
def test_parse_connection_url(url, expected):
    """测试连接 URL 解析"""
    result = parse_connection_url(url)
    assert result == expected
```

2. **模式提取测试**
```python
@pytest.mark.asyncio
async def test_extract_tables_info(mock_cursor):
    """测试表信息提取"""
    # 模拟数据库返回
    mock_cursor.fetchall.return_value = [
        ("users", "用户表"),
        ("orders", "订单表")
    ]
    
    result = DM_Loader.extract_tables_info(mock_cursor)
    
    assert len(result) == 2
    assert "users" in result
    assert "orders" in result
```

3. **查询执行测试**
```python
@pytest.mark.asyncio
async def test_execute_sql_query(mock_connection):
    """测试 SQL 查询执行"""
    sql = "SELECT * FROM users LIMIT 10"
    
    result = DM_Loader.execute_sql_query(sql, "dm://user:pass@host:5236/db")
    
    assert isinstance(result, list)
    assert len(result) > 0
```

4. **错误处理测试**
```python
@pytest.mark.asyncio
async def test_connection_error_handling():
    """测试连接错误处理"""
    invalid_url = "dm://invalid:invalid@nonexistent:5236/db"
    
    with pytest.raises(DM_ConnectionError) as exc_info:
        async for _ in DM_Loader.load("test", invalid_url):
            pass
    
    assert "无法连接" in str(exc_info.value)
```

5. **值序列化测试**
```python
@pytest.mark.parametrize("value,expected", [
    (datetime.datetime(2025, 1, 15, 10, 30), "2025-01-15T10:30:00"),
    (decimal.Decimal("123.45"), 123.45),
    (None, None),
])
def test_serialize_value(value, expected):
    """测试值序列化"""
    result = DM_Loader._serialize_value(value)
    assert result == expected
```

### 属性测试

使用 Hypothesis 进行属性测试，验证通用属性：

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_identifier_quoting_property(identifier):
    """
    属性测试：所有标识符都应该被正确引用
    
    属性：对于任意标识符，引用后的标识符应该：
    1. 以双引号开始和结束
    2. 内部的双引号被转义为两个双引号
    """
    quoted = quote_identifier(identifier)
    
    assert quoted.startswith('"')
    assert quoted.endswith('"')
    assert '""' in quoted if '"' in identifier else True
```

```python
@given(st.lists(st.text(), min_size=1, max_size=10))
def test_table_extraction_completeness(table_names):
    """
    属性测试：表提取的完整性
    
    属性：对于任意表列表，提取的表数量应该等于数据库中的表数量
    """
    # 创建测试数据库
    mock_db = create_mock_database(table_names)
    
    # 提取表信息
    result = DM_Loader.extract_tables_info(mock_db.cursor())
    
    assert len(result) == len(table_names)
    assert set(result.keys()) == set(table_names)
```

### 集成测试

#### 测试环境
- **Docker Compose**: 启动测试数据库容器
- **测试数据**: 预定义的测试数据集

#### 端到端测试流程

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_dm_database_end_to_end():
    """
    达梦数据库端到端集成测试
    
    测试流程：
    1. 启动达梦数据库容器
    2. 创建测试表和数据
    3. 连接数据库
    4. 提取模式
    5. 加载到图数据库
    6. 执行查询
    7. 验证结果
    8. 清理资源
    """
    # 1. 启动数据库容器
    container = await start_dm_container()
    
    try:
        # 2. 创建测试数据
        await create_test_schema(container)
        
        # 3. 连接并加载模式
        url = f"dm://test:test@localhost:{container.port}/testdb"
        success = False
        async for status, message in DM_Loader.load("test_user", url):
            if status:
                success = True
        
        assert success
        
        # 4. 验证图数据库
        graph = db.select_graph("test_user_testdb")
        result = await graph.query("MATCH (t:Table) RETURN count(t) as count")
        assert result.result_set[0][0] > 0
        
        # 5. 执行查询
        sql = "SELECT * FROM users LIMIT 10"
        query_result = DM_Loader.execute_sql_query(sql, url)
        assert len(query_result) > 0
        
    finally:
        # 6. 清理
        await container.stop()
```

### 测试数据

#### 测试数据库模式

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    balance DECIMAL(10, 2)
);

-- 订单表
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    order_date TIMESTAMP,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 订单项表
CREATE TABLE order_items (
    id INT PRIMARY KEY,
    order_id INT,
    product_name VARCHAR(100),
    quantity INT,
    price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

#### 测试数据集

```python
TEST_USERS = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "balance": 100.50},
    {"id": 2, "username": "bob", "email": "bob@example.com", "balance": 250.75},
    {"id": 3, "username": "charlie", "email": "charlie@example.com", "balance": 50.00},
]

TEST_ORDERS = [
    {"id": 1, "user_id": 1, "order_date": "2025-01-10", "total_amount": 99.99},
    {"id": 2, "user_id": 2, "order_date": "2025-01-12", "total_amount": 149.99},
]
```

### 性能测试

#### 测试指标
- 连接建立时间: < 1 秒
- 模式提取时间: < 5 秒（100 个表）
- 查询执行时间: < 2 秒（简单查询）
- 图加载时间: < 10 秒（100 个表）

#### 性能测试用例

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_schema_extraction_performance():
    """测试模式提取性能"""
    # 创建包含 100 个表的数据库
    db = create_large_test_database(table_count=100)
    
    start_time = time.time()
    result = DM_Loader.extract_tables_info(db.cursor())
    elapsed = time.time() - start_time
    
    assert len(result) == 100
    assert elapsed < 5.0  # 应该在 5 秒内完成
```

### 测试配置

#### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: 单元测试
    integration: 集成测试
    performance: 性能测试
    dm: 达梦数据库测试
    kingbase: 人大金仓数据库测试
```

#### 测试覆盖率目标

- 代码覆盖率: ≥ 80%
- 分支覆盖率: ≥ 70%
- 核心功能覆盖率: 100%

### 持续集成

#### GitHub Actions 工作流

```yaml
name: Database Loader Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      dm-database:
        image: dm8:latest
        ports:
          - 5236:5236
      
      kingbase-database:
        image: kingbase:latest
        ports:
          - 54321:54321
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv install --dev
      
      - name: Run unit tests
        run: pipenv run pytest tests/ -m unit
      
      - name: Run integration tests
        run: pipenv run pytest tests/ -m integration
      
      - name: Generate coverage report
        run: pipenv run pytest --cov=api/loaders --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```
