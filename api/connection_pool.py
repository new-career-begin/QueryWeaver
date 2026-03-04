"""
HTTP 连接池管理模块

提供全局的 HTTP 连接池配置，用于复用连接、减少开销。
支持 LiteLLM 和其他 HTTP 客户端的连接池管理。
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    HTTP 连接池管理器
    
    负责配置和管理全局的 HTTP 连接池，包括：
    - 连接池大小配置
    - 连接超时设置
    - 连接复用策略
    - 代理配置
    """
    
    # 全局连接池实例
    _client: Optional[httpx.AsyncClient] = None
    _sync_client: Optional[httpx.Client] = None
    
    # 连接池配置常量
    DEFAULT_POOL_SIZE = 100  # 连接池大小
    DEFAULT_MAX_OVERFLOW = 10  # 超出连接池大小时的额外连接数
    DEFAULT_TIMEOUT = 30.0  # 连接超时时间（秒）
    DEFAULT_KEEPALIVE_TIMEOUT = 30.0  # Keep-Alive 超时时间（秒）
    
    @classmethod
    def initialize(cls) -> None:
        """
        初始化全局连接池
        
        从环境变量读取配置，创建全局的异步和同步 HTTP 客户端。
        应该在应用启动时调用。
        
        Example:
            >>> ConnectionPoolManager.initialize()
        """
        try:
            # 从环境变量读取配置
            pool_size = int(os.getenv('HTTP_POOL_SIZE', cls.DEFAULT_POOL_SIZE))
            max_overflow = int(os.getenv('HTTP_MAX_OVERFLOW', cls.DEFAULT_MAX_OVERFLOW))
            timeout = float(os.getenv('HTTP_TIMEOUT', cls.DEFAULT_TIMEOUT))
            keepalive_timeout = float(os.getenv('HTTP_KEEPALIVE_TIMEOUT', cls.DEFAULT_KEEPALIVE_TIMEOUT))
            
            logger.info(
                "初始化 HTTP 连接池",
                extra={
                    "event": "connection_pool_init",
                    "pool_size": pool_size,
                    "max_overflow": max_overflow,
                    "timeout": timeout,
                    "keepalive_timeout": keepalive_timeout
                }
            )
            
            # 创建连接池限制配置
            limits = httpx.Limits(
                max_connections=pool_size,  # 最大连接数
                max_keepalive_connections=pool_size,  # 最大 Keep-Alive 连接数
                keepalive_expiry=keepalive_timeout  # Keep-Alive 过期时间
            )
            
            # 创建异步客户端
            cls._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                http2=False,  # 禁用 HTTP/2 以避免依赖 h2 包
                verify=True  # 验证 SSL 证书
            )
            
            # 创建同步客户端
            cls._sync_client = httpx.Client(
                limits=limits,
                timeout=timeout,
                http2=False,
                verify=True
            )
            
            logger.info(
                "HTTP 连接池初始化成功",
                extra={
                    "event": "connection_pool_initialized",
                    "pool_size": pool_size
                }
            )
            
            # 配置代理（如果需要）
            cls._configure_proxy()
            
        except Exception as e:
            logger.error(
                f"连接池初始化失败: {str(e)}",
                extra={
                    "event": "connection_pool_init_error",
                    "error": str(e)
                }
            )
            raise
    
    @classmethod
    def _configure_proxy(cls) -> None:
        """
        配置代理设置
        
        如果环境变量中配置了代理，则记录代理信息。
        httpx 客户端会自动使用系统代理或环境变量中的代理。
        """
        http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        
        if http_proxy or https_proxy:
            logger.info(
                "代理配置已检测",
                extra={
                    "event": "proxy_configured",
                    "has_http_proxy": bool(http_proxy),
                    "has_https_proxy": bool(https_proxy)
                }
            )
    
    @classmethod
    def get_async_client(cls) -> httpx.AsyncClient:
        """
        获取全局异步 HTTP 客户端
        
        Returns:
            全局的 httpx.AsyncClient 实例
            
        Raises:
            RuntimeError: 如果连接池未初始化
            
        Example:
            >>> client = ConnectionPoolManager.get_async_client()
            >>> response = await client.get('https://api.example.com')
        """
        if cls._client is None:
            raise RuntimeError("连接池未初始化，请先调用 initialize()")
        return cls._client
    
    @classmethod
    def get_sync_client(cls) -> httpx.Client:
        """
        获取全局同步 HTTP 客户端
        
        Returns:
            全局的 httpx.Client 实例
            
        Raises:
            RuntimeError: 如果连接池未初始化
            
        Example:
            >>> client = ConnectionPoolManager.get_sync_client()
            >>> response = client.get('https://api.example.com')
        """
        if cls._sync_client is None:
            raise RuntimeError("连接池未初始化，请先调用 initialize()")
        return cls._sync_client
    
    @classmethod
    async def close_async_client(cls) -> None:
        """
        关闭异步客户端并释放连接池资源
        
        应该在应用关闭时调用。
        
        Example:
            >>> await ConnectionPoolManager.close_async_client()
        """
        if cls._client is not None:
            try:
                await cls._client.aclose()
                logger.info(
                    "异步 HTTP 客户端已关闭",
                    extra={"event": "async_client_closed"}
                )
            except Exception as e:
                logger.error(
                    f"关闭异步客户端失败: {str(e)}",
                    extra={
                        "event": "async_client_close_error",
                        "error": str(e)
                    }
                )
            finally:
                cls._client = None
    
    @classmethod
    def close_sync_client(cls) -> None:
        """
        关闭同步客户端并释放连接池资源
        
        应该在应用关闭时调用。
        
        Example:
            >>> ConnectionPoolManager.close_sync_client()
        """
        if cls._sync_client is not None:
            try:
                cls._sync_client.close()
                logger.info(
                    "同步 HTTP 客户端已关闭",
                    extra={"event": "sync_client_closed"}
                )
            except Exception as e:
                logger.error(
                    f"关闭同步客户端失败: {str(e)}",
                    extra={
                        "event": "sync_client_close_error",
                        "error": str(e)
                    }
                )
            finally:
                cls._sync_client = None
    
    @classmethod
    async def close_all(cls) -> None:
        """
        关闭所有客户端并释放所有资源
        
        应该在应用关闭时调用。
        
        Example:
            >>> await ConnectionPoolManager.close_all()
        """
        await cls.close_async_client()
        cls.close_sync_client()
        logger.info(
            "所有 HTTP 客户端已关闭",
            extra={"event": "all_clients_closed"}
        )
    
    @classmethod
    def get_pool_stats(cls) -> dict:
        """
        获取连接池统计信息
        
        Returns:
            包含连接池统计信息的字典
            
        Example:
            >>> stats = ConnectionPoolManager.get_pool_stats()
            >>> print(stats)
            {'async_client_initialized': True, 'sync_client_initialized': True}
        """
        return {
            'async_client_initialized': cls._client is not None,
            'sync_client_initialized': cls._sync_client is not None,
            'async_client_type': type(cls._client).__name__ if cls._client else None,
            'sync_client_type': type(cls._sync_client).__name__ if cls._sync_client else None
        }


# 便捷函数
async def get_async_client() -> httpx.AsyncClient:
    """
    获取全局异步 HTTP 客户端的便捷函数
    
    Returns:
        全局的 httpx.AsyncClient 实例
    """
    return ConnectionPoolManager.get_async_client()


def get_sync_client() -> httpx.Client:
    """
    获取全局同步 HTTP 客户端的便捷函数
    
    Returns:
        全局的 httpx.Client 实例
    """
    return ConnectionPoolManager.get_sync_client()
