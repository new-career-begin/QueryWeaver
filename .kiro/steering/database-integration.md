---
inclusion: fileMatch
fileMatchPattern: "api/loaders/**/*.py"
---

# 数据库集成开发规范

## 数据库加载器架构

### 基础加载器接口
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLoader(ABC):
    """
    数据库加载器基类
    
    所有数据库加载器必须继承此类并实现抽象方法
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        初始化加载器
        
        Args:
            connection_params: 数据库连接参数
                - host: 主机地址
                - port: 端口号
                - database: 数据库名
                - user: 用户名
                - password: 密码
        """
        self.connection_params = connection_params
        self.connection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """
        建立数据库连接
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            表名列表
        """
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            表结构字典，包含：
            - columns: 列信息列表
            - primary_keys: 主键列表
            - foreign_keys: 外键列表
            - indexes: 索引列表
        """
        pass
    
    @abstractmethod
    async def get_sample_data(
        self, 
        table_name: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取表的示例数据
        
        Args:
            table_name: 表名
            limit: 返回行数限制
            
        Returns:
            示例数据列表
        """
        pass
    
    @abstractmethod
    async def get_column_statistics(
        self, 
        table_name: str, 
        column_name: str
    ) -> Dict[str, Any]:
        """
        获取列的统计信息
        
        Args:
            table_name: 表名
            column_name: 列名
            
        Returns:
            统计信息字典，包含：
            - distinct_count: 唯一值数量
            - null_count: NULL 值数量
            - min_value: 最小值
            - max_value: 最大值
            - sample_values: 示例值
        """
        pass
```

## PostgreSQL 加载器实现

### 连接管理
```python
import asyncpg
from typing import List, Dict, Any

class PostgresLoader(BaseLoader):
    """PostgreSQL 数据库加载器"""
    
    async def connect(self) -> None:
        """
        建立 PostgreSQL 连接
        
        使用 asyncpg 进行异步连接
        """
        try:
            self.connection = await asyncpg.connect(
                host=self.connection_params['host'],
                port=self.connection_params.get('port', 5432),
                database=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                timeout=30  # 连接超时 30 秒
            )
            logger.info(
                f"成功连接到 PostgreSQL: "
                f"{self.connection_params['database']}"
            )
        except Exception as e:
            logger.error(f"PostgreSQL 连接失败: {str(e)}")
            raise ConnectionError(f"无法连接到数据库: {str(e)}")
    
    async def disconnect(self) -> None:
        """关闭 PostgreSQL 连接"""
        if self.connection:
            await self.connection.close()
            logger.info("PostgreSQL 连接已关闭")
```

### 模式提取
```python
async def get_tables(self) -> List[str]:
    """
    获取所有用户表
    
    排除系统表和视图
    """
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    
    rows = await self.connection.fetch(query)
    return [row['table_name'] for row in rows]

async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
    """
    获取 PostgreSQL 表的完整结构
    
    包括列、主键、外键、索引信息
    """
    # 获取列信息
    columns = await self._get_columns(table_name)
    
    # 获取主键
    primary_keys = await self._get_primary_keys(table_name)
    
    # 获取外键
    foreign_keys = await self._get_foreign_keys(table_name)
    
    # 获取索引
    indexes = await self._get_indexes(table_name)
    
    return {
        "table_name": table_name,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "indexes": indexes
    }

async def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
    """获取表的列信息"""
    query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = $1
        ORDER BY ordinal_position
    """
    
    rows = await self.connection.fetch(query, table_name)
    
    return [
        {
            "name": row['column_name'],
            "type": row['data_type'],
            "max_length": row['character_maximum_length'],
            "nullable": row['is_nullable'] == 'YES',
            "default": row['column_default'],
            "position": row['ordinal_position']
        }
        for row in rows
    ]

async def _get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
    """获取表的外键约束"""
    query = """
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = $1
    """
    
    rows = await self.connection.fetch(query, table_name)
    
    return [
        {
            "constraint_name": row['constraint_name'],
            "column": row['column_name'],
            "referenced_table": row['foreign_table_name'],
            "referenced_column": row['foreign_column_name']
        }
        for row in rows
    ]
```

### 数据采样和统计
```python
async def get_sample_data(
    self, 
    table_name: str, 
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    获取表的示例数据
    
    使用 TABLESAMPLE 提高大表采样性能
    """
    # 对于大表使用 TABLESAMPLE
    query = f"""
        SELECT *
        FROM {self._quote_identifier(table_name)}
        TABLESAMPLE SYSTEM (1)
        LIMIT $1
    """
    
    try:
        rows = await self.connection.fetch(query, limit)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"TABLESAMPLE 失败，使用普通查询: {str(e)}")
        # 降级到普通查询
        query = f"""
            SELECT *
            FROM {self._quote_identifier(table_name)}
            LIMIT $1
        """
        rows = await self.connection.fetch(query, limit)
        return [dict(row) for row in rows]

async def get_column_statistics(
    self, 
    table_name: str, 
    column_name: str
) -> Dict[str, Any]:
    """
    获取列的统计信息
    
    包括唯一值数量、NULL 数量、示例值等
    """
    quoted_table = self._quote_identifier(table_name)
    quoted_column = self._quote_identifier(column_name)
    
    # 获取基本统计
    query = f"""
        SELECT
            COUNT(DISTINCT {quoted_column}) as distinct_count,
            COUNT(*) - COUNT({quoted_column}) as null_count,
            COUNT(*) as total_count,
            MIN({quoted_column})::text as min_value,
            MAX({quoted_column})::text as max_value
        FROM {quoted_table}
    """
    
    stats = await self.connection.fetchrow(query)
    
    # 获取示例值
    sample_query = f"""
        SELECT DISTINCT {quoted_column}
        FROM {quoted_table}
        WHERE {quoted_column} IS NOT NULL
        LIMIT 10
    """
    
    samples = await self.connection.fetch(sample_query)
    
    return {
        "distinct_count": stats['distinct_count'],
        "null_count": stats['null_count'],
        "total_count": stats['total_count'],
        "min_value": stats['min_value'],
        "max_value": stats['max_value'],
        "sample_values": [row[0] for row in samples],
        "uniqueness_ratio": (
            stats['distinct_count'] / stats['total_count']
            if stats['total_count'] > 0 else 0
        )
    }

def _quote_identifier(self, identifier: str) -> str:
    """
    安全地引用标识符
    
    防止 SQL 注入，处理特殊字符
    """
    # 移除危险字符
    safe_identifier = identifier.replace('"', '""')
    return f'"{safe_identifier}"'
```

## MySQL 加载器实现

### 连接和查询
```python
import aiomysql
from typing import List, Dict, Any

class MySQLLoader(BaseLoader):
    """MySQL 数据库加载器"""
    
    async def connect(self) -> None:
        """建立 MySQL 连接"""
        try:
            self.connection = await aiomysql.connect(
                host=self.connection_params['host'],
                port=self.connection_params.get('port', 3306),
                db=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                charset='utf8mb4',
                autocommit=True
            )
            logger.info(
                f"成功连接到 MySQL: "
                f"{self.connection_params['database']}"
            )
        except Exception as e:
            logger.error(f"MySQL 连接失败: {str(e)}")
            raise ConnectionError(f"无法连接到数据库: {str(e)}")
    
    async def get_tables(self) -> List[str]:
        """获取所有表名"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """获取 MySQL 表结构"""
        columns = await self._get_columns(table_name)
        primary_keys = await self._get_primary_keys(table_name)
        foreign_keys = await self._get_foreign_keys(table_name)
        indexes = await self._get_indexes(table_name)
        
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes
        }
    
    async def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取列信息"""
        query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY,
                EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, (table_name,))
            rows = await cursor.fetchall()
            
            return [
                {
                    "name": row[0],
                    "type": row[1],
                    "max_length": row[2],
                    "nullable": row[3] == 'YES',
                    "default": row[4],
                    "key": row[5],
                    "extra": row[6]
                }
                for row in rows
            ]
```

## 图数据库构建

### 模式到图的转换
```python
from api.extensions import db

async def build_graph_from_schema(
    graph_id: str,
    database_name: str,
    loader: BaseLoader
) -> None:
    """
    从数据库模式构建图数据库
    
    图结构：
    - Database 节点：数据库信息
    - Table 节点：表信息
    - Column 节点：列信息
    - BELONGS_TO 关系：列属于表
    - REFERENCES 关系：外键引用
    
    Args:
        graph_id: 图数据库标识
        database_name: 数据库名称
        loader: 数据库加载器实例
    """
    graph = db.select_graph(graph_id)
    
    # 1. 创建数据库节点
    await graph.query(
        """
        MERGE (d:Database {name: $name})
        SET d.description = $description,
            d.url = $url,
            d.created_at = timestamp()
        """,
        {
            "name": database_name,
            "description": f"{database_name} 数据库",
            "url": loader.connection_params.get('host', 'localhost')
        }
    )
    
    # 2. 获取所有表
    tables = await loader.get_tables()
    
    # 3. 为每个表创建节点和关系
    for table_name in tables:
        await _create_table_node(graph, loader, table_name)
    
    logger.info(f"图数据库构建完成: {graph_id}, 共 {len(tables)} 个表")

async def _create_table_node(
    graph,
    loader: BaseLoader,
    table_name: str
) -> None:
    """
    创建表节点及其列节点
    
    Args:
        graph: 图数据库实例
        loader: 数据库加载器
        table_name: 表名
    """
    # 获取表结构
    schema = await loader.get_table_schema(table_name)
    
    # 生成表描述（使用 LLM）
    table_description = await generate_table_description(
        table_name, 
        schema['columns']
    )
    
    # 生成表描述的向量嵌入
    embedding = Config.EMBEDDING_MODEL.embed([table_description])[0]
    
    # 创建表节点
    foreign_keys_str = json.dumps(schema['foreign_keys'])
    
    await graph.query(
        """
        MERGE (t:Table {name: $name})
        SET t.description = $description,
            t.foreign_keys = $foreign_keys,
            t.embedding = vecf32($embedding)
        """,
        {
            "name": table_name,
            "description": table_description,
            "foreign_keys": foreign_keys_str,
            "embedding": embedding
        }
    )
    
    # 创建列节点
    for column in schema['columns']:
        await _create_column_node(graph, table_name, column)
    
    # 创建外键关系
    for fk in schema['foreign_keys']:
        await _create_foreign_key_relationship(graph, table_name, fk)

async def _create_column_node(
    graph,
    table_name: str,
    column: Dict[str, Any]
) -> None:
    """
    创建列节点
    
    Args:
        graph: 图数据库实例
        table_name: 表名
        column: 列信息字典
    """
    # 生成列描述
    column_description = await generate_column_description(
        table_name,
        column['name'],
        column['type']
    )
    
    # 生成列描述的向量嵌入
    embedding = Config.EMBEDDING_MODEL.embed([column_description])[0]
    
    # 创建列节点并建立关系
    await graph.query(
        """
        MATCH (t:Table {name: $table_name})
        MERGE (c:Column {name: $column_name, table: $table_name})
        SET c.description = $description,
            c.type = $data_type,
            c.nullable = $nullable,
            c.key = $key,
            c.embedding = vecf32($embedding)
        MERGE (c)-[:BELONGS_TO]->(t)
        """,
        {
            "table_name": table_name,
            "column_name": column['name'],
            "description": column_description,
            "data_type": column['type'],
            "nullable": column.get('nullable', True),
            "key": column.get('key', ''),
            "embedding": embedding
        }
    )

async def _create_foreign_key_relationship(
    graph,
    table_name: str,
    foreign_key: Dict[str, Any]
) -> None:
    """
    创建外键关系
    
    Args:
        graph: 图数据库实例
        table_name: 源表名
        foreign_key: 外键信息
    """
    await graph.query(
        """
        MATCH (c1:Column {name: $column, table: $table})
        MATCH (c2:Column {name: $ref_column, table: $ref_table})
        MERGE (c1)-[:REFERENCES {
            constraint_name: $constraint_name
        }]->(c2)
        """,
        {
            "table": table_name,
            "column": foreign_key['column'],
            "ref_table": foreign_key['referenced_table'],
            "ref_column": foreign_key['referenced_column'],
            "constraint_name": foreign_key.get('constraint_name', '')
        }
    )
```

## 智能描述生成

### 使用 LLM 生成描述
```python
async def generate_table_description(
    table_name: str,
    columns: List[Dict[str, Any]]
) -> str:
    """
    使用 LLM 生成表的自然语言描述
    
    Args:
        table_name: 表名
        columns: 列信息列表
        
    Returns:
        表的描述文本
    """
    column_info = ", ".join([
        f"{col['name']} ({col['type']})"
        for col in columns[:10]  # 限制列数
    ])
    
    prompt = f"""
    根据以下信息，生成一个简洁的表描述（1-2 句话）：
    
    表名：{table_name}
    列：{column_info}
    
    描述应该说明这个表存储什么类型的数据，用于什么目的。
    使用中文，不要包含技术细节。
    """
    
    response = await call_llm(prompt, temperature=0.3)
    return response.strip()

async def generate_column_description(
    table_name: str,
    column_name: str,
    data_type: str
) -> str:
    """
    生成列的描述
    
    Args:
        table_name: 表名
        column_name: 列名
        data_type: 数据类型
        
    Returns:
        列的描述文本
    """
    prompt = f"""
    为数据库列生成简短描述（一句话）：
    
    表：{table_name}
    列：{column_name}
    类型：{data_type}
    
    描述这个列存储什么信息。使用中文。
    """
    
    response = await call_llm(prompt, temperature=0.3)
    return response.strip()
```

## 错误处理和重试

### 连接重试机制
```python
import asyncio
from typing import Callable, TypeVar, Any

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> T:
    """
    带指数退避的重试机制
    
    Args:
        func: 要执行的异步函数
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
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(
                f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}"
            )
            
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= backoff_factor
    
    raise last_exception

# 使用示例
async def connect_with_retry(loader: BaseLoader) -> None:
    """带重试的数据库连接"""
    await retry_with_backoff(
        loader.connect,
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0
    )
```
