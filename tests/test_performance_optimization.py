"""性能优化测试模块

测试 Token 缓存机制和数据库查询优化的性能表现。
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from api.auth.token_cache import TokenCache, token_cache
from api.auth.db_optimization import (
    create_identity_indexes,
    create_token_indexes,
    create_user_indexes,
    initialize_all_indexes,
    optimize_user_query,
    cleanup_expired_tokens
)


class TestTokenCache:
    """Token 缓存机制测试"""
    
    def setup_method(self):
        """每个测试方法前清空缓存"""
        self.cache = TokenCache()
    
    def test_cache_set_and_get(self):
        """测试基本的缓存设置和获取"""
        # 设置缓存
        self.cache.set("wechat:test_app_id", "test_token_123", expires_in=3600)
        
        # 获取缓存
        token = self.cache.get("wechat:test_app_id")
        
        assert token == "test_token_123"
    
    def test_cache_expiration(self):
        """测试缓存过期机制"""
        # 设置一个很短的过期时间（1秒）
        self.cache.set("wechat:test_app_id", "test_token_123", expires_in=1, buffer_seconds=0)
        
        # 立即获取应该成功
        token = self.cache.get("wechat:test_app_id")
        assert token == "test_token_123"
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后应该返回 None
        token = self.cache.get("wechat:test_app_id")
        assert token is None
    
    def test_cache_buffer_time(self):
        """测试缓存提前过期的缓冲时间"""
        # 设置 10 秒过期，5 秒缓冲
        self.cache.set("wechat:test_app_id", "test_token_123", expires_in=10, buffer_seconds=5)
        
        # 检查实际过期时间应该是 5 秒（10 - 5）
        cache_entry = self.cache._cache.get("wechat:test_app_id")
        assert cache_entry is not None
        
        # 过期时间应该在 4-6 秒之间（允许一些误差）
        time_diff = (cache_entry["expire_time"] - datetime.now()).total_seconds()
        assert 4 <= time_diff <= 6
    
    def test_cache_delete(self):
        """测试缓存删除"""
        # 设置缓存
        self.cache.set("wechat:test_app_id", "test_token_123", expires_in=3600)
        
        # 删除缓存
        result = self.cache.delete("wechat:test_app_id")
        assert result is True
        
        # 获取应该返回 None
        token = self.cache.get("wechat:test_app_id")
        assert token is None
        
        # 删除不存在的键应该返回 False
        result = self.cache.delete("wechat:non_existent")
        assert result is False
    
    def test_cache_clear(self):
        """测试清空所有缓存"""
        # 设置多个缓存
        self.cache.set("wechat:app1", "token1", expires_in=3600)
        self.cache.set("wechat:app2", "token2", expires_in=3600)
        self.cache.set("wecom:corp1", "token3", expires_in=3600)
        
        # 清空缓存
        self.cache.clear()
        
        # 所有缓存都应该被清空
        assert self.cache.get("wechat:app1") is None
        assert self.cache.get("wechat:app2") is None
        assert self.cache.get("wecom:corp1") is None
    
    def test_cache_stats(self):
        """测试缓存统计信息"""
        # 设置一些缓存
        self.cache.set("wechat:app1", "token1", expires_in=3600)
        self.cache.set("wechat:app2", "token2", expires_in=1, buffer_seconds=0)
        
        # 等待一个过期
        time.sleep(1.1)
        
        # 获取统计信息
        stats = self.cache.get_stats()
        
        assert stats["total_count"] == 2
        assert stats["valid_count"] == 1
        assert stats["expired_count"] == 1
    
    def test_cache_cleanup_expired(self):
        """测试清理过期缓存"""
        # 设置一些缓存，其中一些会过期
        self.cache.set("wechat:app1", "token1", expires_in=3600)
        self.cache.set("wechat:app2", "token2", expires_in=1, buffer_seconds=0)
        self.cache.set("wechat:app3", "token3", expires_in=1, buffer_seconds=0)
        
        # 等待过期
        time.sleep(1.1)
        
        # 清理过期缓存
        cleaned_count = self.cache.cleanup_expired()
        
        assert cleaned_count == 2
        assert self.cache.get("wechat:app1") == "token1"
        assert self.cache.get("wechat:app2") is None
        assert self.cache.get("wechat:app3") is None
    
    def test_cache_thread_safety(self):
        """测试缓存的线程安全性"""
        import threading
        
        results = []
        
        def set_cache(key, value):
            self.cache.set(key, value, expires_in=3600)
            results.append(f"set_{key}")
        
        def get_cache(key):
            token = self.cache.get(key)
            results.append(f"get_{key}_{token}")
        
        # 创建多个线程同时操作缓存
        threads = []
        for i in range(10):
            t1 = threading.Thread(target=set_cache, args=(f"key_{i}", f"value_{i}"))
            t2 = threading.Thread(target=get_cache, args=(f"key_{i}",))
            threads.extend([t1, t2])
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有操作都完成了
        assert len(results) == 20


class TestTokenCachePerformance:
    """Token 缓存性能测试"""
    
    def setup_method(self):
        """每个测试方法前清空缓存"""
        self.cache = TokenCache()
    
    def test_cache_hit_performance(self):
        """测试缓存命中的性能"""
        # 设置缓存
        self.cache.set("wechat:test_app", "test_token", expires_in=3600)
        
        # 测试 1000 次缓存命中的时间
        start_time = time.time()
        for _ in range(1000):
            self.cache.get("wechat:test_app")
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # 1000 次缓存命中应该在 0.1 秒内完成
        assert elapsed_time < 0.1, f"缓存命中性能不佳: {elapsed_time}秒"
    
    def test_cache_miss_performance(self):
        """测试缓存未命中的性能"""
        # 测试 1000 次缓存未命中的时间
        start_time = time.time()
        for i in range(1000):
            self.cache.get(f"wechat:non_existent_{i}")
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # 1000 次缓存未命中应该在 0.1 秒内完成
        assert elapsed_time < 0.1, f"缓存未命中性能不佳: {elapsed_time}秒"
    
    def test_cache_set_performance(self):
        """测试缓存设置的性能"""
        # 测试 1000 次缓存设置的时间
        start_time = time.time()
        for i in range(1000):
            self.cache.set(f"wechat:app_{i}", f"token_{i}", expires_in=3600)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # 1000 次缓存设置应该在 0.5 秒内完成
        assert elapsed_time < 0.5, f"缓存设置性能不佳: {elapsed_time}秒"


@pytest.mark.asyncio
class TestDatabaseOptimization:
    """数据库查询优化测试"""
    
    @patch('api.auth.db_optimization.db')
    async def test_create_identity_indexes(self, mock_db):
        """测试创建 Identity 索引"""
        # Mock 图数据库
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # 执行索引创建
        results = await create_identity_indexes()
        
        # 验证调用了正确的查询
        assert mock_graph.query.call_count == 3
        
        # 验证返回结果
        assert "provider_composite_index" in results
        assert "email_index" in results
        assert "last_login_index" in results
    
    @patch('api.auth.db_optimization.db')
    async def test_create_token_indexes(self, mock_db):
        """测试创建 Token 索引"""
        # Mock 图数据库
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # 执行索引创建
        results = await create_token_indexes()
        
        # 验证调用了正确的查询
        assert mock_graph.query.call_count == 2
        
        # 验证返回结果
        assert "token_id_index" in results
        assert "expires_at_index" in results
    
    @patch('api.auth.db_optimization.db')
    async def test_create_user_indexes(self, mock_db):
        """测试创建 User 索引"""
        # Mock 图数据库
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # 执行索引创建
        results = await create_user_indexes()
        
        # 验证调用了正确的查询
        assert mock_graph.query.call_count == 1
        
        # 验证返回结果
        assert "user_email_index" in results
    
    @patch('api.auth.db_optimization.db')
    async def test_initialize_all_indexes(self, mock_db):
        """测试初始化所有索引"""
        # Mock 图数据库
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # 执行索引初始化
        results = await initialize_all_indexes()
        
        # 验证返回结果包含所有类别
        assert "identity_indexes" in results
        assert "token_indexes" in results
        assert "user_indexes" in results
    
    @patch('api.auth.db_optimization.db')
    async def test_optimize_user_query(self, mock_db):
        """测试优化的用户查询"""
        # Mock 图数据库和查询结果
        mock_graph = AsyncMock()
        mock_result = Mock()
        mock_result.result_set = [
            [
                {"provider": "wechat", "provider_user_id": "test_openid"},
                {"email": "test@example.com", "name": "测试用户"}
            ]
        ]
        mock_graph.query.return_value = mock_result
        mock_db.select_graph.return_value = mock_graph
        
        # 执行优化查询
        result = await optimize_user_query("wechat", "test_openid")
        
        # 验证返回结果
        assert result is not None
        assert "identity" in result
        assert "user" in result
        assert result["identity"]["provider"] == "wechat"
    
    @patch('api.auth.db_optimization.db')
    async def test_cleanup_expired_tokens(self, mock_db):
        """测试清理过期 Token"""
        # Mock 图数据库和查询结果
        mock_graph = AsyncMock()
        mock_result = Mock()
        mock_result.result_set = [[5]]  # 删除了 5 个 Token
        mock_graph.query.return_value = mock_result
        mock_db.select_graph.return_value = mock_graph
        
        # 执行清理
        deleted_count = await cleanup_expired_tokens()
        
        # 验证返回结果
        assert deleted_count == 5


@pytest.mark.asyncio
class TestConcurrentLogin:
    """并发登录性能测试"""
    
    @patch('api.auth.oauth_handlers.token_cache')
    @patch('api.auth.oauth_handlers.httpx.AsyncClient')
    async def test_concurrent_wechat_token_requests(self, mock_client, mock_cache):
        """测试并发微信 Token 请求的性能"""
        from api.auth.oauth_handlers import WeChatOAuthHandler
        
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "openid": "test_openid",
            "expires_in": 7200
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # 创建处理器
        config = {
            "app_id": "test_app_id",
            "app_secret": "test_secret",
            "authorize_url": "https://test.com/authorize",
            "access_token_url": "https://test.com/token",
            "userinfo_url": "https://test.com/userinfo",
            "scope": "snsapi_userinfo"
        }
        handler = WeChatOAuthHandler(config)
        
        # 并发执行 10 个 Token 请求
        start_time = time.time()
        tasks = [
            handler.exchange_code_for_token(f"code_{i}")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # 验证所有请求都成功
        assert len(results) == 10
        for result in results:
            assert "access_token" in result
            assert "openid" in result
        
        # 并发请求应该在 2 秒内完成
        assert elapsed_time < 2.0, f"并发请求性能不佳: {elapsed_time}秒"
    
    @patch('api.auth.oauth_handlers.token_cache')
    @patch('api.auth.oauth_handlers.httpx.AsyncClient')
    async def test_wecom_token_cache_effectiveness(self, mock_client, mock_cache):
        """测试企业微信 Token 缓存的有效性"""
        from api.auth.oauth_handlers import WeComOAuthHandler
        
        # Mock 缓存行为
        cache_hits = 0
        cache_misses = 0
        
        def mock_get(key):
            nonlocal cache_hits, cache_misses
            if cache_hits < 5:
                cache_misses += 1
                return None
            cache_hits += 1
            return "cached_token"
        
        mock_cache.get.side_effect = mock_get
        
        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "test_token",
            "expires_in": 7200
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # 创建处理器
        config = {
            "corp_id": "test_corp_id",
            "agent_id": "test_agent_id",
            "corp_secret": "test_secret",
            "authorize_url": "https://test.com/authorize",
            "access_token_url": "https://test.com/token",
            "userinfo_url": "https://test.com/userinfo",
            "user_detail_url": "https://test.com/user",
            "scope": "snsapi_base"
        }
        handler = WeComOAuthHandler(config)
        
        # 执行 10 次 Token 获取
        for _ in range(10):
            await handler.get_access_token()
        
        # 验证缓存命中率
        # 前 5 次应该是缓存未命中，后 5 次应该是缓存命中
        assert cache_misses == 5
        assert cache_hits >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
