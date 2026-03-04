"""
Prompt 缓存功能测试

测试 Prompt 模板缓存的基本功能和性能
"""

import pytest
import time
from api.prompt_cache import PromptCache, get_prompt_cache, clear_prompt_cache


class TestPromptCache:
    """Prompt 缓存测试类"""
    
    def setup_method(self):
        """每个测试方法前清空缓存"""
        clear_prompt_cache()
    
    def test_cache_basic_operations(self):
        """测试缓存的基本操作：设置和获取"""
        cache = PromptCache(max_size=10, ttl_seconds=60)
        
        # 生成缓存键
        cache_key = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type='postgresql'
        )
        
        # 设置缓存
        prompt = "这是一个测试 Prompt 模板"
        cache.set(cache_key, prompt)
        
        # 获取缓存
        cached_prompt = cache.get(cache_key)
        
        assert cached_prompt == prompt
        assert cache.get_stats()['hits'] == 1
        assert cache.get_stats()['misses'] == 0
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = PromptCache()
        
        # 尝试获取不存在的缓存
        result = cache.get("nonexistent_key")
        
        assert result is None
        assert cache.get_stats()['misses'] == 1
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = PromptCache(max_size=10, ttl_seconds=1)  # 1秒过期
        
        cache_key = "test_key"
        cache.set(cache_key, "test_prompt")
        
        # 立即获取应该成功
        assert cache.get(cache_key) == "test_prompt"
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后应该返回 None
        assert cache.get(cache_key) is None
        assert cache.get_stats()['evictions'] == 1
    
    def test_cache_max_size(self):
        """测试缓存大小限制"""
        cache = PromptCache(max_size=3, ttl_seconds=60)
        
        # 添加 4 个条目，应该移除最旧的
        for i in range(4):
            cache.set(f"key_{i}", f"prompt_{i}")
        
        # 第一个条目应该被移除
        assert cache.get("key_0") is None
        assert cache.get("key_1") == "prompt_1"
        assert cache.get("key_2") == "prompt_2"
        assert cache.get("key_3") == "prompt_3"
        
        assert cache.get_stats()['evictions'] == 1
    
    def test_cache_key_generation(self):
        """测试缓存键生成的一致性"""
        # 相同参数应该生成相同的键
        key1 = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type='postgresql',
            has_memory=True
        )
        
        key2 = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type='postgresql',
            has_memory=True
        )
        
        assert key1 == key2
        
        # 不同参数应该生成不同的键
        key3 = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type='mysql',
            has_memory=True
        )
        
        assert key1 != key3
    
    def test_cache_hit_rate(self):
        """测试缓存命中率计算"""
        cache = PromptCache()
        
        cache_key = "test_key"
        cache.set(cache_key, "test_prompt")
        
        # 3 次命中，2 次未命中
        cache.get(cache_key)  # 命中
        cache.get(cache_key)  # 命中
        cache.get(cache_key)  # 命中
        cache.get("nonexistent_1")  # 未命中
        cache.get("nonexistent_2")  # 未命中
        
        stats = cache.get_stats()
        assert stats['hits'] == 3
        assert stats['misses'] == 2
        assert stats['total_requests'] == 5
        assert stats['hit_rate'] == 0.6  # 3/5 = 0.6
    
    def test_cache_clear(self):
        """测试清空缓存"""
        cache = PromptCache()
        
        # 添加多个条目
        for i in range(5):
            cache.set(f"key_{i}", f"prompt_{i}")
        
        assert cache.get_stats()['cache_size'] == 5
        
        # 清空缓存
        cache.clear()
        
        assert cache.get_stats()['cache_size'] == 0
        assert cache.get("key_0") is None
    
    def test_global_cache_instance(self):
        """测试全局缓存实例"""
        cache1 = get_prompt_cache()
        cache2 = get_prompt_cache()
        
        # 应该返回同一个实例
        assert cache1 is cache2
        
        # 在一个实例中设置，在另一个实例中应该能获取
        cache1.set("test_key", "test_prompt")
        assert cache2.get("test_key") == "test_prompt"
    
    def test_cache_with_large_prompt(self):
        """测试缓存大型 Prompt"""
        cache = PromptCache()
        
        # 生成一个大型 Prompt（模拟实际的 Analysis Prompt）
        large_prompt = "You are a professional Text-to-SQL system. " * 1000
        
        cache_key = "large_prompt_key"
        cache.set(cache_key, large_prompt)
        
        cached_prompt = cache.get(cache_key)
        assert cached_prompt == large_prompt
        assert len(cached_prompt) > 10000
    
    def test_cache_performance(self):
        """测试缓存性能提升"""
        cache = PromptCache()
        
        # 模拟构建 Prompt 的开销
        def build_prompt():
            time.sleep(0.01)  # 模拟 10ms 的构建时间
            return "Complex prompt template"
        
        cache_key = "perf_test_key"
        
        # 第一次：构建并缓存
        start = time.time()
        prompt = build_prompt()
        cache.set(cache_key, prompt)
        first_time = time.time() - start
        
        # 第二次：从缓存获取
        start = time.time()
        cached_prompt = cache.get(cache_key)
        second_time = time.time() - start
        
        assert cached_prompt == prompt
        # 从缓存获取应该快得多
        assert second_time < first_time / 10


@pytest.mark.parametrize("template_type,database_type,expected_different", [
    ('analysis', 'postgresql', False),
    ('analysis', 'mysql', True),
    ('healer', 'postgresql', True),
])
def test_cache_key_uniqueness(template_type, database_type, expected_different):
    """测试不同参数组合的缓存键唯一性"""
    base_key = PromptCache.generate_cache_key(
        template_type='analysis',
        database_type='postgresql'
    )
    
    test_key = PromptCache.generate_cache_key(
        template_type=template_type,
        database_type=database_type
    )
    
    if expected_different:
        assert base_key != test_key
    else:
        assert base_key == test_key


def test_cache_statistics_accuracy():
    """测试缓存统计信息的准确性"""
    cache = PromptCache(max_size=5)
    
    # 添加 3 个条目
    for i in range(3):
        cache.set(f"key_{i}", f"prompt_{i}")
    
    # 执行一些操作
    cache.get("key_0")  # 命中
    cache.get("key_1")  # 命中
    cache.get("nonexistent")  # 未命中
    
    stats = cache.get_stats()
    
    assert stats['cache_size'] == 3
    assert stats['max_size'] == 5
    assert stats['hits'] == 2
    assert stats['misses'] == 1
    assert stats['total_requests'] == 3
    assert abs(stats['hit_rate'] - 2/3) < 0.01
