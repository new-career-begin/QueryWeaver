---
inclusion: fileMatch
fileMatchPattern: "api/{core,graph,agents}/**/*.py"
---

# Text2SQL 开发规范

## 核心概念

### Text2SQL 工作流程
```
用户自然语言查询
    ↓
1. 查询分析 (Analysis Agent)
    ↓
2. 相关性检测 (Relevancy Agent)
    ↓
3. 图数据库模式检索 (Graph-based Schema Retrieval)
    ↓
4. LLM SQL 生成 (Text-to-SQL Generation)
    ↓
5. SQL 清理和验证 (SQL Sanitizer)
    ↓
6. 查询执行
    ↓
7. 结果格式化 (Response Formatter)
    ↓
8. 后续问题生成 (Follow-up Agent)
```

## 图数据库模式检索

### 向量嵌入搜索
```python
from typing import List, Dict, Any
from api.config import Config

async def find_relevant_tables(
    graph_id: str,
    user_query: str,
    query_history: List[str],
    db_description: str
) -> List[Dict[str, Any]]:
    """
    使用向量嵌入查找相关表
    
    工作原理:
    1. 使用 LLM 生成表和列的描述
    2. 将描述转换为向量嵌入
    3. 在图数据库中进行向量相似度搜索
    4. 查找关联表（外键关系）
    5. 查找连接表（最短路径）
    
    Args:
        graph_id: 图数据库标识
        user_query: 用户当前查询
        query_history: 历史查询列表
        db_description: 数据库描述
        
    Returns:
        相关表的列表，包含表名、描述、列信息
    """
    # 1. 生成表和列描述
    descriptions = await generate_descriptions(
        user_query, 
        query_history, 
        db_description
    )
    
    # 2. 生成向量嵌入
    embeddings = Config.EMBEDDING_MODEL.embed(descriptions)
    
    # 3. 向量搜索
    tables = await vector_search_tables(graph_id, embeddings)
    
    # 4. 扩展相关表
    expanded_tables = await expand_related_tables(graph_id, tables)
    
    return expanded_tables
```

### 图查询优化
```python
async def find_connecting_tables(
    graph_id: str,
    table_names: List[str]
) -> List[Dict[str, Any]]:
    """
    查找连接多个表的中间表
    
    使用 Cypher 查询找到表之间的最短路径，
    识别可能需要的连接表（如多对多关系的中间表）
    
    Args:
        graph_id: 图数据库标识
        table_names: 需要连接的表名列表
        
    Returns:
        连接表列表
    """
    graph = db.select_graph(graph_id)
    
    # 生成表对组合
    pairs = list(combinations(table_names, 2))
    
    # Cypher 查询：查找最短路径上的所有表
    query = """
    UNWIND $pairs AS pair
    MATCH (a:Table {name: pair[0]})
    MATCH (b:Table {name: pair[1]})
    WITH a, b
    MATCH p = allShortestPaths((a)-[*..6]-(b))
    UNWIND nodes(p) AS path_node
    WITH DISTINCT path_node
    WHERE 'Table' IN labels(path_node)
    MATCH (col:Column)-[:BELONGS_TO]->(path_node)
    RETURN path_node.name, path_node.description, 
           collect({
               columnName: col.name,
               dataType: col.type,
               keyType: col.key
           }) AS columns
    """
    
    result = await graph.query(query, {"pairs": pairs}, timeout=500)
    return result.result_set
```

## LLM Prompt 工程

### 系统提示词设计
```python
# 查找相关表的提示词
FIND_SYSTEM_PROMPT = """
你是一个专业的数据库模式分析专家。

任务：分析用户的自然语言查询，生成可能相关的表和列的描述。

输入：
- 数据库描述：{db_description}
- 历史查询：{previous_queries}
- 当前查询：{user_query}

输出要求：
1. 生成最多 5 个相关表的描述
2. 生成最多 5 个相关列的描述
3. 描述要通用，不要包含具体值
4. 按相关性排序

输出格式：
{{
    "tables_descriptions": [
        {{"name": "表名", "description": "表的用途描述"}},
        ...
    ],
    "columns_descriptions": [
        {{"name": "列名", "description": "列的用途描述"}},
        ...
    ]
}}
"""

# Text-to-SQL 生成提示词
TEXT_TO_SQL_PROMPT = """
你是一个专业的 SQL 查询生成专家。

任务：根据自然语言问题和数据库模式生成准确的 SQL 查询。

重要规则：
1. 仅返回 SQL 查询，不要包含解释
2. 使用标准 SQL 语法
3. 不要添加注释
4. WHERE 子句使用用户提供的确切值
5. 如果缺少值，字符串用 "TBD"，数字用 1111
6. 仅基于提供的外键创建 JOIN
7. 不要创建不存在的表连接

数据库描述：{db_description}

数据库模式：
{schema}

历史查询：
{previous_queries}

当前问题：{user_query}

分析步骤：
1. 理解用户意图
2. 识别相关表和列
3. 确定需要的连接
4. 构建 SQL 查询
"""
```

### 结构化输出
```python
from pydantic import BaseModel
from litellm import completion

class TableDescription(BaseModel):
    """表描述模型"""
    name: str
    description: str

class ColumnDescription(BaseModel):
    """列描述模型"""
    name: str
    description: str

class Descriptions(BaseModel):
    """描述集合模型"""
    tables_descriptions: List[TableDescription]
    columns_descriptions: List[ColumnDescription]

async def generate_descriptions(
    user_query: str,
    previous_queries: List[str],
    db_description: str
) -> Descriptions:
    """
    使用 LLM 生成结构化的表和列描述
    
    Args:
        user_query: 用户查询
        previous_queries: 历史查询
        db_description: 数据库描述
        
    Returns:
        结构化的描述对象
    """
    response = completion(
        model=Config.COMPLETION_MODEL,
        response_format=Descriptions,  # 强制结构化输出
        messages=[
            {
                "role": "system",
                "content": FIND_SYSTEM_PROMPT.format(
                    db_description=db_description
                )
            },
            {
                "role": "user",
                "content": json.dumps({
                    "previous_user_queries": previous_queries,
                    "user_query": user_query
                })
            }
        ],
        temperature=0,  # 确保输出稳定
    )
    
    json_data = json.loads(response.choices[0].message.content)
    return Descriptions(**json_data)
```

## SQL 安全和清理

### SQL 注入防护
```python
from api.sql_utils.sql_sanitizer import sanitize_sql

def validate_and_sanitize_sql(sql: str, user_id: str) -> str:
    """
    验证和清理 SQL 查询
    
    安全检查：
    1. 移除注释
    2. 检测危险操作（DROP, TRUNCATE, ALTER）
    3. 验证语法
    4. 限制查询复杂度
    
    Args:
        sql: 原始 SQL 查询
        user_id: 用户标识（用于日志）
        
    Returns:
        清理后的 SQL 查询
        
    Raises:
        ValueError: 当 SQL 包含危险操作时
    """
    # 清理 SQL
    cleaned_sql = sanitize_sql(sql)
    
    # 检测危险操作
    dangerous_keywords = [
        'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 
        'DELETE', 'UPDATE', 'INSERT', 'GRANT', 'REVOKE'
    ]
    
    sql_upper = cleaned_sql.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            logger.warning(
                f"用户 {user_id} 尝试执行危险操作: {keyword}"
            )
            raise ValueError(
                f"不允许执行 {keyword} 操作，仅支持 SELECT 查询"
            )
    
    return cleaned_sql
```

### 查询结果限制
```python
async def execute_query_with_limits(
    sql: str,
    max_rows: int = 1000,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    执行查询并应用限制
    
    限制：
    1. 最大返回行数
    2. 查询超时时间
    3. 内存使用限制
    
    Args:
        sql: SQL 查询
        max_rows: 最大返回行数
        timeout: 超时时间（秒）
        
    Returns:
        查询结果字典
    """
    # 添加 LIMIT 子句（如果没有）
    if 'LIMIT' not in sql.upper():
        sql = f"{sql.rstrip(';')} LIMIT {max_rows}"
    
    start_time = time.time()
    
    try:
        # 使用超时执行查询
        result = await asyncio.wait_for(
            execute_sql(sql),
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        return {
            "sql": sql,
            "data": result,
            "row_count": len(result),
            "execution_time": execution_time,
            "truncated": len(result) >= max_rows
        }
    except asyncio.TimeoutError:
        logger.error(f"查询超时: {sql}")
        raise ValueError(f"查询执行超过 {timeout} 秒，已取消")
```

## Agent 系统

### 相关性检测 Agent
```python
async def check_query_relevance(
    user_query: str,
    db_description: str
) -> Dict[str, Any]:
    """
    检测查询是否与数据库相关
    
    防止用户提出与数据库无关的问题
    
    Args:
        user_query: 用户查询
        db_description: 数据库描述
        
    Returns:
        相关性检测结果
    """
    prompt = f"""
    数据库描述：{db_description}
    
    用户问题：{user_query}
    
    判断这个问题是否与数据库相关。
    如果不相关，生成一个礼貌的回复，说明你只能回答与数据库相关的问题。
    
    返回 JSON 格式：
    {{
        "is_relevant": true/false,
        "reason": "判断理由",
        "suggested_response": "如果不相关，给用户的回复"
    }}
    """
    
    response = await call_llm(prompt)
    return json.loads(response)
```

### 后续问题生成 Agent
```python
async def generate_follow_up_questions(
    user_query: str,
    sql_result: Dict[str, Any],
    db_schema: List[Dict[str, Any]]
) -> List[str]:
    """
    基于查询结果生成后续问题建议
    
    帮助用户深入探索数据
    
    Args:
        user_query: 原始用户查询
        sql_result: SQL 执行结果
        db_schema: 数据库模式
        
    Returns:
        后续问题列表
    """
    prompt = f"""
    用户刚才问了：{user_query}
    
    查询返回了 {sql_result['row_count']} 行数据。
    
    基于这个结果，生成 3-5 个有意义的后续问题，
    帮助用户更深入地探索数据。
    
    可用的表：{[t['name'] for t in db_schema]}
    
    返回 JSON 数组格式：
    ["问题1", "问题2", "问题3"]
    """
    
    response = await call_llm(prompt)
    return json.loads(response)
```

## 对话记忆管理

### 短期记忆
```python
class ConversationMemory:
    """对话记忆管理器"""
    
    def __init__(self, max_length: int = 5):
        """
        初始化记忆管理器
        
        Args:
            max_length: 保留的最大对话轮数
        """
        self.max_length = max_length
        self.history: List[Dict[str, str]] = []
    
    def add_exchange(self, user_query: str, sql: str, result_summary: str):
        """
        添加一轮对话
        
        Args:
            user_query: 用户查询
            sql: 生成的 SQL
            result_summary: 结果摘要
        """
        self.history.append({
            "query": user_query,
            "sql": sql,
            "summary": result_summary,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持最大长度限制
        if len(self.history) > self.max_length:
            self.history = self.history[-self.max_length:]
    
    def get_context(self) -> str:
        """
        获取对话上下文字符串
        
        Returns:
            格式化的对话历史
        """
        if not self.history:
            return "这是第一次对话。"
        
        context_parts = []
        for i, exchange in enumerate(self.history, 1):
            context_parts.append(
                f"查询 {i}: {exchange['query']}\n"
                f"SQL: {exchange['sql']}\n"
                f"结果: {exchange['summary']}"
            )
        
        return "\n\n".join(context_parts)
```

### 长期记忆（Graphiti）
```python
from api.memory.graphiti_tool import GraphitiMemory

async def store_long_term_memory(
    user_id: str,
    query: str,
    sql: str,
    result: Dict[str, Any]
):
    """
    将重要的查询存储到长期记忆
    
    使用 Graphiti 构建用户的查询知识图谱
    
    Args:
        user_id: 用户标识
        query: 用户查询
        sql: 生成的 SQL
        result: 查询结果
    """
    memory = GraphitiMemory(user_id)
    
    # 提取关键信息
    entities = extract_entities(query, result)
    relationships = extract_relationships(sql)
    
    # 存储到知识图谱
    await memory.add_episode(
        content=f"用户查询: {query}",
        entities=entities,
        relationships=relationships,
        metadata={
            "sql": sql,
            "row_count": result.get("row_count", 0),
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 性能优化

### 并发查询优化
```python
async def parallel_table_search(
    graph_id: str,
    embeddings: List[List[float]]
) -> List[Dict[str, Any]]:
    """
    并发执行多个向量搜索
    
    使用 asyncio.gather 提高性能
    
    Args:
        graph_id: 图数据库标识
        embeddings: 向量嵌入列表
        
    Returns:
        所有搜索结果的合并列表
    """
    # 创建并发任务
    tasks = [
        search_single_embedding(graph_id, emb)
        for emb in embeddings
    ]
    
    # 并发执行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 过滤异常结果
    valid_results = [
        r for r in results 
        if not isinstance(r, Exception)
    ]
    
    # 合并结果
    return merge_search_results(valid_results)
```

### 缓存策略
```python
from functools import lru_cache
from typing import Optional

# 缓存向量大小（不会改变）
@lru_cache(maxsize=1)
def get_embedding_vector_size(model_name: str) -> int:
    """获取嵌入向量大小（带缓存）"""
    return Config.EMBEDDING_MODEL.get_vector_size()

# 缓存数据库描述（短期缓存）
_db_description_cache: Dict[str, Tuple[str, float]] = {}
CACHE_TTL = 300  # 5 分钟

async def get_cached_db_description(graph_id: str) -> str:
    """
    获取数据库描述（带缓存）
    
    Args:
        graph_id: 图数据库标识
        
    Returns:
        数据库描述
    """
    now = time.time()
    
    # 检查缓存
    if graph_id in _db_description_cache:
        description, timestamp = _db_description_cache[graph_id]
        if now - timestamp < CACHE_TTL:
            return description
    
    # 从数据库获取
    description, _ = await get_db_description(graph_id)
    
    # 更新缓存
    _db_description_cache[graph_id] = (description, now)
    
    return description
```

## 错误处理和日志

### 结构化日志
```python
import logging
import json

logger = logging.getLogger(__name__)

def log_query_execution(
    user_id: str,
    query: str,
    sql: str,
    success: bool,
    execution_time: float,
    error: Optional[str] = None
):
    """
    记录查询执行日志
    
    Args:
        user_id: 用户标识
        query: 用户查询
        sql: 生成的 SQL
        success: 是否成功
        execution_time: 执行时间
        error: 错误信息（如果有）
    """
    log_data = {
        "event": "query_execution",
        "user_id": user_id,
        "query": query,
        "sql": sql,
        "success": success,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(json.dumps(log_data))
    else:
        logger.error(json.dumps(log_data))
```
