---
inclusion: fileMatch
fileMatchPattern: "api/**/*.py"
---

# Python 后端开发规范

## 代码风格

### 基本规范
- 遵循 PEP 8 代码风格指南
- 使用 4 个空格缩进（不使用 Tab）
- 每行最大长度 100 字符
- 使用 pylint 进行代码检查

### 命名约定
```python
# 模块名：小写字母，下划线分隔
# user_management.py

# 类名：大驼峰命名法
class UserAuthentication:
    pass

# 函数名：小写字母，下划线分隔
def get_user_by_id(user_id: int) -> dict:
    """根据用户ID获取用户信息"""
    pass

# 常量：全大写，下划线分隔
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 私有方法：单下划线前缀
def _internal_helper():
    """内部辅助方法"""
    pass
```

## 类型注解

### 必须使用类型注解
```python
from typing import List, Dict, Optional, Union, Any

# 函数参数和返回值必须有类型注解
async def find_tables(
    graph_id: str,
    queries_history: List[str],
    db_description: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查找与用户查询相关的表和列
    
    Args:
        graph_id: 图数据库标识符
        queries_history: 历史查询列表，最后一个为当前查询
        db_description: 可选的数据库描述
        
    Returns:
        相关表的列表
    """
    pass
```

## 异步编程规范

### FastAPI 异步处理
```python
# 使用 async/await 处理异步操作
@router.post("/graphs/{graph_id}/query")
async def query_database(
    graph_id: str,
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    执行数据库查询
    
    Args:
        graph_id: 数据库图ID
        request: 查询请求对象
        current_user: 当前认证用户
        
    Returns:
        流式响应对象
    """
    # 使用 asyncio.gather 并发执行多个异步任务
    results = await asyncio.gather(
        task1(),
        task2(),
        return_exceptions=True
    )
    return results
```

## 错误处理

### 异常处理最佳实践
```python
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def process_query(query: str) -> dict:
    """
    处理查询请求
    
    Args:
        query: SQL查询字符串
        
    Returns:
        查询结果字典
        
    Raises:
        HTTPException: 当查询处理失败时
    """
    try:
        # 业务逻辑
        result = await execute_query(query)
        return result
    except ValueError as e:
        # 记录详细错误信息
        logger.error(f"查询参数错误: {query}, 错误: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"查询参数不合法: {str(e)}"
        )
    except Exception as e:
        # 捕获未预期的错误
        logger.exception(f"查询处理失败: {query}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )
```

## 文档字符串规范

### Docstring 格式
```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    函数的简短描述（一行）
    
    更详细的函数说明，可以多行。解释函数的用途、
    工作原理和注意事项。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        param3: 可选参数3的描述，默认为 None
        
    Returns:
        返回值的描述，说明返回的数据结构
        
    Raises:
        ValueError: 当参数不合法时抛出
        RuntimeError: 当执行失败时抛出
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success', 'data': [...]}
    """
    pass
```

## 配置管理

### 环境变量和配置
```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    
    # AI 模型配置
    openai_api_key: Optional[str] = None
    azure_api_key: Optional[str] = None
    
    # 应用配置
    app_env: str = "development"
    debug_mode: bool = False
    
    class Config:
        # 从 .env 文件加载配置
        env_file = ".env"
        env_file_encoding = "utf-8"

# 全局配置实例
settings = Settings()
```

## 数据验证

### 使用 Pydantic 模型
```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    """查询请求模型"""
    
    chat: List[str] = Field(
        ...,
        description="聊天消息列表",
        min_items=1
    )
    result: List[dict] = Field(
        default_factory=list,
        description="历史查询结果"
    )
    instructions: Optional[str] = Field(
        None,
        description="额外的查询指令"
    )
    
    @validator('chat')
    def validate_chat_messages(cls, v):
        """验证聊天消息不为空"""
        if not v or all(not msg.strip() for msg in v):
            raise ValueError('聊天消息不能为空')
        return v
```

## 日志记录

### 日志最佳实践
```python
import logging

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def process_data(data: dict):
    """处理数据"""
    logger.info(f"开始处理数据: {data.get('id')}")
    
    try:
        result = await heavy_operation(data)
        logger.info(f"数据处理成功: {data.get('id')}")
        return result
    except Exception as e:
        logger.error(f"数据处理失败: {data.get('id')}, 错误: {str(e)}")
        raise
```

## 测试规范

### 单元测试
```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_find_tables():
    """测试表查找功能"""
    # Arrange - 准备测试数据
    graph_id = "test_db"
    queries = ["查询用户信息"]
    
    # Act - 执行测试
    result = await find_tables(graph_id, queries)
    
    # Assert - 验证结果
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'name' in result[0]

@pytest.fixture
def mock_database():
    """模拟数据库连接"""
    with patch('api.extensions.db') as mock_db:
        mock_db.select_graph.return_value = Mock()
        yield mock_db
```

## 性能优化

### 数据库查询优化
```python
# 使用批量操作减少数据库往返
async def batch_query(queries: List[str]) -> List[Any]:
    """批量执行查询"""
    tasks = [execute_single_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results

# 使用缓存减少重复计算
from functools import lru_cache

@lru_cache(maxsize=128)
def get_embedding_size(model_name: str) -> int:
    """获取嵌入向量大小（带缓存）"""
    return calculate_embedding_size(model_name)
```

## 安全规范

### 输入验证和清理
```python
from api.sql_utils.sql_sanitizer import sanitize_sql

async def execute_user_query(query: str, user_id: str):
    """
    执行用户查询（带安全检查）
    
    Args:
        query: 用户输入的查询
        user_id: 用户标识
    """
    # 清理和验证 SQL 查询
    sanitized_query = sanitize_sql(query)
    
    # 检查是否包含危险操作
    if is_destructive_query(sanitized_query):
        logger.warning(f"用户 {user_id} 尝试执行危险查询: {query}")
        raise ValueError("不允许执行修改数据的操作")
    
    # 执行查询
    return await execute_query(sanitized_query)
```
