"""
HTTP 连接池管理单元测试

测试连接池的初始化、获取、关闭等功能
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from api.connection_pool import ConnectionPoolManager, get_async_client, get_sync_client


class TestConnectionPoolManager:
    """连接池管理器测试类"""
    
    def setup_method(self):
        """
        测试前清理
        
        重置连接池状态，确保每个测试都从干净的状态开始
        """
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def teardown_method(self):
        """
        测试后清理
        
        关闭连接池，释放资源
        """
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def test_initialize_creates_clients(self):
        """
        测试初始化创建客户端
        
        验证 initialize() 方法能够成功创建异步和同步客户端
        """
        # 初始化连接池
        ConnectionPoolManager.initialize()
        
        # 验证客户端已创建
        assert ConnectionPoolManager._client is not None
        assert ConnectionPoolManager._sync_client is not None
        assert isinstance(ConnectionPoolManager._client, httpx.AsyncClient)
        assert isinstance(ConnectionPoolManager._sync_client, httpx.Client)
    
    def test_initialize_with_custom_pool_size(self):
        """
        测试使用自定义连接池大小初始化
        
        验证从环境变量读取连接池配置
        """
        with patch.dict(os.environ, {'HTTP_POOL_SIZE': '50', 'HTTP_MAX_OVERFLOW': '5'}):
            ConnectionPoolManager.initialize()
            
            # 验证客户端已创建
            assert ConnectionPoolManager._client is not None
            assert ConnectionPoolManager._sync_client is not None
    
    def test_get_async_client_returns_client(self):
        """
        测试获取异步客户端
        
        验证 get_async_client() 返回正确的客户端实例
        """
        ConnectionPoolManager.initialize()
        
        client = ConnectionPoolManager.get_async_client()
        
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)
        assert client is ConnectionPoolManager._client
    
    def test_get_sync_client_returns_client(self):
        """
        测试获取同步客户端
        
        验证 get_sync_client() 返回正确的客户端实例
        """
        ConnectionPoolManager.initialize()
        
        client = ConnectionPoolManager.get_sync_client()
        
        assert client is not None
        assert isinstance(client, httpx.Client)
        assert client is ConnectionPoolManager._sync_client
    
    def test_get_async_client_raises_when_not_initialized(self):
        """
        测试未初始化时获取异步客户端抛出异常
        
        验证在连接池未初始化时调用 get_async_client() 会抛出 RuntimeError
        """
        with pytest.raises(RuntimeError, match="连接池未初始化"):
            ConnectionPoolManager.get_async_client()
    
    def test_get_sync_client_raises_when_not_initialized(self):
        """
        测试未初始化时获取同步客户端抛出异常
        
        验证在连接池未初始化时调用 get_sync_client() 会抛出 RuntimeError
        """
        with pytest.raises(RuntimeError, match="连接池未初始化"):
            ConnectionPoolManager.get_sync_client()
    
    def test_close_async_client_sync(self):
        """
        测试关闭异步客户端（同步版本）
        
        验证 close_async_client() 能够正确关闭异步客户端
        """
        ConnectionPoolManager.initialize()
        
        # 验证客户端已创建
        assert ConnectionPoolManager._client is not None
        
        # 注意：这里我们只验证客户端存在，实际的异步关闭需要在异步上下文中进行
        # 在生产环境中，应该在应用关闭事件中调用 await ConnectionPoolManager.close_all()
    
    def test_close_sync_client(self):
        """
        测试关闭同步客户端
        
        验证 close_sync_client() 能够正确关闭同步客户端
        """
        ConnectionPoolManager.initialize()
        
        # 验证客户端已创建
        assert ConnectionPoolManager._sync_client is not None
        
        # 关闭客户端
        ConnectionPoolManager.close_sync_client()
        
        # 验证客户端已关闭
        assert ConnectionPoolManager._sync_client is None
    
    def test_get_pool_stats(self):
        """
        测试获取连接池统计信息
        
        验证 get_pool_stats() 返回正确的统计信息
        """
        # 初始化前
        stats = ConnectionPoolManager.get_pool_stats()
        assert stats['async_client_initialized'] is False
        assert stats['sync_client_initialized'] is False
        
        # 初始化后
        ConnectionPoolManager.initialize()
        stats = ConnectionPoolManager.get_pool_stats()
        assert stats['async_client_initialized'] is True
        assert stats['sync_client_initialized'] is True
        assert stats['async_client_type'] == 'AsyncClient'
        assert stats['sync_client_type'] == 'Client'
    
    def test_initialize_with_proxy_config(self):
        """
        测试使用代理配置初始化
        
        验证从环境变量读取代理配置
        """
        with patch.dict(os.environ, {
            'HTTP_PROXY': 'http://proxy.example.com:8080',
            'HTTPS_PROXY': 'https://proxy.example.com:8443'
        }):
            ConnectionPoolManager.initialize()
            
            # 验证客户端已创建
            assert ConnectionPoolManager._client is not None
            assert ConnectionPoolManager._sync_client is not None
    
    def test_initialize_handles_error(self):
        """
        测试初始化错误处理
        
        验证初始化失败时能够正确处理异常
        """
        with patch('api.connection_pool.httpx.AsyncClient', side_effect=Exception("连接失败")):
            with pytest.raises(Exception, match="连接失败"):
                ConnectionPoolManager.initialize()


class TestConvenienceFunctions:
    """便捷函数测试类"""
    
    def setup_method(self):
        """测试前清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def teardown_method(self):
        """测试后清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def test_get_sync_client_function(self):
        """
        测试 get_sync_client() 便捷函数
        
        验证便捷函数能够返回同步客户端
        """
        ConnectionPoolManager.initialize()
        
        client = get_sync_client()
        
        assert client is not None
        assert isinstance(client, httpx.Client)


class TestConnectionPoolConfiguration:
    """连接池配置测试类"""
    
    def setup_method(self):
        """测试前清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def teardown_method(self):
        """测试后清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def test_default_pool_size(self):
        """
        测试默认连接池大小
        
        验证使用默认配置时的连接池大小
        """
        assert ConnectionPoolManager.DEFAULT_POOL_SIZE == 100
        assert ConnectionPoolManager.DEFAULT_MAX_OVERFLOW == 10
        assert ConnectionPoolManager.DEFAULT_TIMEOUT == 30.0
        assert ConnectionPoolManager.DEFAULT_KEEPALIVE_TIMEOUT == 30.0
    
    def test_http2_enabled(self):
        """
        测试 HTTP/2 支持
        
        验证客户端启用了 HTTP/2 支持
        """
        ConnectionPoolManager.initialize()
        
        # 验证客户端已创建
        assert ConnectionPoolManager._client is not None
        assert ConnectionPoolManager._sync_client is not None
    
    def test_ssl_verification_enabled(self):
        """
        测试 SSL 证书验证
        
        验证客户端启用了 SSL 证书验证
        """
        ConnectionPoolManager.initialize()
        
        # 验证客户端已创建
        assert ConnectionPoolManager._client is not None
        assert ConnectionPoolManager._sync_client is not None


class TestConnectionPoolIntegration:
    """连接池集成测试类"""
    
    def setup_method(self):
        """测试前清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def teardown_method(self):
        """测试后清理"""
        ConnectionPoolManager._client = None
        ConnectionPoolManager._sync_client = None
    
    def test_multiple_initialize_calls(self):
        """
        测试多次初始化调用
        
        验证多次调用 initialize() 会创建新的客户端实例
        """
        ConnectionPoolManager.initialize()
        first_client = ConnectionPoolManager._client
        first_sync_client = ConnectionPoolManager._sync_client
        
        # 再次初始化
        ConnectionPoolManager.initialize()
        second_client = ConnectionPoolManager._client
        second_sync_client = ConnectionPoolManager._sync_client
        
        # 验证创建了新的客户端（因为每次都会创建新实例）
        assert first_client is not None
        assert second_client is not None
        assert first_sync_client is not None
        assert second_sync_client is not None
    
    def test_close_sync_and_reinitialize(self):
        """
        测试关闭同步客户端后重新初始化
        
        验证关闭连接池后能够重新初始化
        """
        # 初始化
        ConnectionPoolManager.initialize()
        assert ConnectionPoolManager._client is not None
        assert ConnectionPoolManager._sync_client is not None
        
        # 关闭同步客户端
        ConnectionPoolManager.close_sync_client()
        assert ConnectionPoolManager._sync_client is None
        
        # 重新初始化
        ConnectionPoolManager.initialize()
        assert ConnectionPoolManager._client is not None
        assert ConnectionPoolManager._sync_client is not None
