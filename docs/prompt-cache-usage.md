# Prompt 模板缓存使用指南

## 概述

Prompt 模板缓存是一个性能优化功能，通过缓存常用的 Prompt 模板来减少重复构建开销，提高系统响应速度。

## 功能特性

- **LRU 缓存策略**：自动移除最少使用的缓存条目
- **TTL 过期机制**：支持设置缓存过期时间
- **缓存统计**：提供命中率、缓存大小等统计信息
- **线程安全**：支持并发访问
- **灵活的缓存键生成**：基于参数自动生成唯一缓存键

## 基本使用

### 1. 获取全局缓存实例

```python
from api.prompt_cache import get_prompt_cache

# 获取全局缓存实例
cache = get_prompt_cache()
```

### 2. 生成缓存键

```python
from api.prompt_cache import PromptCache

# 基于参数生成缓存键
cache_key = PromptCache.generate_cache_key(
    template_type='analysis',
    database_type='postgresql',
    has_memory=True,
    has_instructions=False
)
```

### 3. 设置和获取缓存

```python
# 设置缓存
prompt_template = "Your prompt template here..."
cache.set(cache_key, prompt_template)

# 获取缓存
cached_template = cache.get(cache_key)
if cached_template:
    # 使用缓存的模板
    prompt = cached_template.format(user_input=user_query, ...)
else:
    # 构建新模板
    prompt = build_prompt_template(...)
    cache.set(cache_key, prompt)
```

## 在 Agent 中使用

### Analysis Agent 示例

```python
from api.prompt_cache import get_prompt_cache, PromptCache

class AnalysisAgent:
    def _build_prompt(self, user_input, formatted_schema, db_description, 
                     instructions=None, memory_context=None, database_type=None):
        """构建 Prompt（带缓存）"""
        
        # 生成缓存键
        cache = get_prompt_cache()
        cache_key = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type=database_type or 'unknown',
            has_instructions=bool(instructions),
            has_memory=bool(memory_context)
        )
        
        # 尝试从缓存获取模板
        cached_template = cache.get(cache_key)
        if cached_template:
            # 使用缓存的模板，只需替换动态内容
            return cached_template.format(
                user_input=user_input,
                formatted_schema=formatted_schema,
                db_description=db_description,
                instructions=instructions or "",
                memory_context=memory_context or ""
            )
        
        # 构建新模板
        template = self._construct_prompt_template(
            database_type, 
            bool(instructions), 
            bool(memory_context)
        )
        
        # 存入缓存
        cache.set(cache_key, template)
        
        # 替换动态内容
        return template.format(
            user_input=user_input,
            formatted_schema=formatted_schema,
            db_description=db_description,
            instructions=instructions or "",
            memory_context=memory_context or ""
        )
```

## 缓存配置

### 自定义缓存参数

```python
from api.prompt_cache import PromptCache

# 创建自定义缓存实例
custom_cache = PromptCache(
    max_size=256,      # 最大缓存条目数
    ttl_seconds=7200   # 缓存过期时间（2小时）
)
```

### 环境变量配置（可选）

```bash
# .env 文件
PROMPT_CACHE_MAX_SIZE=128
PROMPT_CACHE_TTL_SECONDS=3600
```

## 缓存统计

### 获取统计信息

```python
cache = get_prompt_cache()

# 获取详细统计
stats = cache.get_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
print(f"缓存大小: {stats['cache_size']}/{stats['max_size']}")
print(f"总请求数: {stats['total_requests']}")
print(f"命中次数: {stats['hits']}")
print(f"未命中次数: {stats['misses']}")
print(f"移除次数: {stats['evictions']}")
```

### 监控缓存性能

```python
import logging

logger = logging.getLogger(__name__)

# 定期记录缓存统计
def log_cache_stats():
    cache = get_prompt_cache()
    stats = cache.get_stats()
    
    logger.info(
        f"Prompt 缓存统计 - "
        f"命中率: {stats['hit_rate']:.2%}, "
        f"大小: {stats['cache_size']}/{stats['max_size']}, "
        f"命中: {stats['hits']}, "
        f"未命中: {stats['misses']}"
    )
```

## 最佳实践

### 1. 缓存键设计

```python
# ✅ 好的做法：包含所有影响模板结构的参数
cache_key = PromptCache.generate_cache_key(
    template_type='analysis',
    database_type='postgresql',
    has_instructions=True,
    has_user_rules=False,
    has_memory=True
)

# ❌ 不好的做法：包含动态内容
cache_key = PromptCache.generate_cache_key(
    template_type='analysis',
    user_input=user_query,  # 动态内容不应该在缓存键中
    schema=formatted_schema  # 动态内容不应该在缓存键中
)
```

### 2. 模板与内容分离

```python
# ✅ 好的做法：缓存模板，动态替换内容
template = """
You are a SQL expert.

Database: {database_type}
Schema: {schema}
Query: {user_query}
"""

cache.set(cache_key, template)
prompt = template.format(
    database_type=db_type,
    schema=schema,
    user_query=query
)

# ❌ 不好的做法：缓存完整的 Prompt
prompt = f"""
You are a SQL expert.

Database: {db_type}
Schema: {schema}
Query: {query}
"""
cache.set(cache_key, prompt)  # 包含动态内容，缓存效果差
```

### 3. 缓存清理

```python
from api.prompt_cache import clear_prompt_cache

# 在需要时清空缓存（如配置更新后）
def on_config_update():
    clear_prompt_cache()
    logger.info("Prompt 缓存已清空")
```

## 性能影响

### 预期性能提升

- **首次请求**：无缓存，正常构建时间
- **后续请求**：从缓存获取，减少 90%+ 的构建时间
- **内存占用**：每个缓存条目约 5-50KB（取决于模板大小）

### 性能测试示例

```python
import time

def benchmark_cache_performance():
    cache = get_prompt_cache()
    cache_key = "benchmark_key"
    
    # 模拟构建 Prompt
    def build_prompt():
        time.sleep(0.01)  # 模拟 10ms 构建时间
        return "Complex prompt template"
    
    # 测试无缓存
    start = time.time()
    prompt = build_prompt()
    no_cache_time = time.time() - start
    
    # 测试有缓存
    cache.set(cache_key, prompt)
    start = time.time()
    cached_prompt = cache.get(cache_key)
    cache_time = time.time() - start
    
    print(f"无缓存: {no_cache_time*1000:.2f}ms")
    print(f"有缓存: {cache_time*1000:.2f}ms")
    print(f"性能提升: {no_cache_time/cache_time:.1f}x")
```

## 故障排查

### 缓存未命中

```python
# 检查缓存键是否一致
key1 = PromptCache.generate_cache_key(template_type='analysis', db='postgresql')
key2 = PromptCache.generate_cache_key(template_type='analysis', db='mysql')
print(f"键是否相同: {key1 == key2}")  # False

# 检查缓存是否过期
stats = cache.get_stats()
print(f"移除次数: {stats['evictions']}")  # 如果很高，可能是 TTL 太短
```

### 内存占用过高

```python
# 减小缓存大小
cache = PromptCache(max_size=64)  # 默认 128

# 或减少 TTL
cache = PromptCache(ttl_seconds=1800)  # 30 分钟而不是 1 小时
```

## 相关需求

- **需求 12.3**：缓存常用的 Prompt 模板，减少重复构建开销

## 参考资料

- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [缓存策略最佳实践](https://en.wikipedia.org/wiki/Cache_replacement_policies)
