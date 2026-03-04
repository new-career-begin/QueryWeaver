"""
Prompt 模板缓存模块

提供 Prompt 模板的缓存功能，减少重复构建开销，提高性能。
"""

import hashlib
import logging
from typing import Dict, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PromptCache:
    """
    Prompt 模板缓存管理器
    
    使用 LRU 缓存策略缓存常用的 Prompt 模板，减少重复构建开销。
    支持基于参数的缓存键生成和缓存统计。
    """
    
    def __init__(self, max_size: int = 128, ttl_seconds: int = 3600):
        """
        初始化 Prompt 缓存
        
        Args:
            max_size: 缓存最大条目数（默认 128）
            ttl_seconds: 缓存过期时间（秒，默认 3600 = 1小时）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        logger.info(
            f"Prompt 缓存已初始化：max_size={max_size}, ttl={ttl_seconds}秒"
        )
    
    def get(self, cache_key: str) -> Optional[str]:
        """
        从缓存中获取 Prompt 模板
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的 Prompt 模板，如果不存在或已过期则返回 None
        """
        if cache_key not in self._cache:
            self._stats['misses'] += 1
            return None
        
        entry = self._cache[cache_key]
        
        # 检查是否过期
        if datetime.now() > entry['expires_at']:
            logger.debug(f"缓存条目已过期：{cache_key[:16]}...")
            del self._cache[cache_key]
            self._stats['misses'] += 1
            self._stats['evictions'] += 1
            return None
        
        # 缓存命中
        self._stats['hits'] += 1
        entry['last_accessed'] = datetime.now()
        
        logger.debug(
            f"缓存命中：{cache_key[:16]}... "
            f"(命中率: {self.get_hit_rate():.2%})"
        )
        
        return entry['prompt']
    
    def set(self, cache_key: str, prompt: str) -> None:
        """
        将 Prompt 模板存入缓存
        
        Args:
            cache_key: 缓存键
            prompt: Prompt 模板内容
        """
        # 如果缓存已满，移除最旧的条目
        if len(self._cache) >= self.max_size and cache_key not in self._cache:
            self._evict_oldest()
        
        now = datetime.now()
        self._cache[cache_key] = {
            'prompt': prompt,
            'created_at': now,
            'last_accessed': now,
            'expires_at': now + timedelta(seconds=self.ttl_seconds)
        }
        
        logger.debug(f"Prompt 已缓存：{cache_key[:16]}... (大小: {len(prompt)} 字符)")
    
    def _evict_oldest(self) -> None:
        """移除最旧的缓存条目（基于最后访问时间）"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['last_accessed']
        )
        
        del self._cache[oldest_key]
        self._stats['evictions'] += 1
        
        logger.debug(f"缓存条目已移除：{oldest_key[:16]}...")
    
    def clear(self) -> None:
        """清空所有缓存"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"缓存已清空：移除了 {count} 个条目")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含命中率、缓存大小等统计信息的字典
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'evictions': self._stats['evictions'],
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'cache_size': len(self._cache),
            'max_size': self.max_size
        }
    
    def get_hit_rate(self) -> float:
        """
        获取缓存命中率
        
        Returns:
            命中率（0.0 到 1.0）
        """
        total = self._stats['hits'] + self._stats['misses']
        return self._stats['hits'] / total if total > 0 else 0.0
    
    @staticmethod
    def generate_cache_key(**kwargs) -> str:
        """
        生成缓存键
        
        基于传入的参数生成唯一的缓存键。使用 SHA256 哈希确保键的唯一性。
        
        Args:
            **kwargs: 用于生成缓存键的参数
            
        Returns:
            缓存键（SHA256 哈希值）
            
        Example:
            >>> key = PromptCache.generate_cache_key(
            ...     template_type='analysis',
            ...     database_type='postgresql',
            ...     has_memory=True
            ... )
        """
        # 将参数排序并序列化
        sorted_items = sorted(kwargs.items())
        key_string = '|'.join(f"{k}={v}" for k, v in sorted_items)
        
        # 生成 SHA256 哈希
        hash_obj = hashlib.sha256(key_string.encode('utf-8'))
        cache_key = hash_obj.hexdigest()
        
        return cache_key


# 全局缓存实例
_global_prompt_cache: Optional[PromptCache] = None


def get_prompt_cache() -> PromptCache:
    """
    获取全局 Prompt 缓存实例
    
    Returns:
        全局 PromptCache 实例
    """
    global _global_prompt_cache
    
    if _global_prompt_cache is None:
        _global_prompt_cache = PromptCache()
    
    return _global_prompt_cache


def clear_prompt_cache() -> None:
    """清空全局 Prompt 缓存"""
    cache = get_prompt_cache()
    cache.clear()


@lru_cache(maxsize=32)
def get_static_prompt_template(template_name: str) -> str:
    """
    获取静态 Prompt 模板（使用 functools.lru_cache）
    
    用于缓存完全静态的模板，不需要任何参数替换。
    
    Args:
        template_name: 模板名称
        
    Returns:
        模板内容
        
    Raises:
        ValueError: 如果模板名称不存在
    """
    templates = {
        'response_formatter': """
You are an AI assistant that helps users understand database query results. Your task is to analyze the SQL query results and provide a clear, concise, and user-friendly explanation.

**Context:**
Database Description: {DB_DESCRIPTION}

**User's Original Question:**
{USER_QUERY}

**SQL Query Executed:**
{SQL_QUERY}

**Query Type:** {SQL_TYPE}

**Query Results:**
{FORMATTED_RESULTS}

**Instructions:**
1. Provide a clear, natural language answer to the user's question based on the query results
2. For SELECT queries: Focus on the key insights and findings from the data
3. For INSERT/UPDATE/DELETE queries: Confirm the operation was successful and mention how many records were affected
4. For other operations (CREATE, DROP, etc.): Confirm the operation was completed successfully
5. Use bullet points or numbered lists when presenting multiple items
6. Include relevant numbers, percentages, or trends if applicable
7. Be concise but comprehensive - avoid unnecessary technical jargon
8. If the results are empty, explain that no data was found matching the criteria
9. If there are many results, provide a summary with highlights
10. Do not mention the SQL query or technical database details unless specifically relevant to the user's understanding

**Response Format:**
Provide a direct answer to the user's question in a conversational tone, as if you were explaining the findings to a colleague.
""",
        'healer_base': """You are a SQL query debugging expert. Your task is to fix a SQL query that failed execution.

DATABASE TYPE: {DATABASE_TYPE}

FAILED SQL QUERY:
```sql
{FAILED_SQL}
```

EXECUTION ERROR:
{ERROR_MESSAGE}

{QUESTION_SECTION}

{DB_INFO_SECTION}

COMMON ERROR PATTERNS:
{ERROR_HINTS}

YOUR TASK:
1. Identify the exact cause of the error
2. Fix ONLY what's broken - don't rewrite the entire query
3. Ensure the fix is compatible with {DATABASE_TYPE}
4. Maintain the original query logic and intent

CRITICAL RULES FOR {DATABASE_TYPE}:
{DIALECT_RULES}

RESPONSE FORMAT (valid JSON only):
{
  "sql_query": "-- your fixed SQL query here",
  "confidence": 85,
  "explanation": "Brief explanation of what was fixed",
  "changes_made": ["Changed EXTRACT to strftime", "Fixed column casing"]
}

IMPORTANT:
- Return ONLY the JSON object, no other text
- Fix ONLY the specific error, preserve the rest
- Test your fix mentally before responding
- If error is about a column/table name, check spelling carefully
"""
    }
    
    if template_name not in templates:
        raise ValueError(f"未知的模板名称: {template_name}")
    
    return templates[template_name]
