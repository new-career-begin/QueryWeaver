"""Token 缓存管理模块

提供统一的 Token 缓存机制，用于缓存微信和企业微信的 access_token，
减少 API 调用次数，提高性能。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)


class TokenCache:
    """
    Token 缓存类
    
    使用内存缓存存储 access_token，支持自动过期管理。
    线程安全，支持并发访问。
    """
    
    def __init__(self):
        """初始化 Token 缓存"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("TokenCache 初始化完成")
    
    def get(self, key: str) -> Optional[str]:
        """
        获取缓存的 Token
        
        Args:
            key: 缓存键，格式为 "provider:identifier"
                例如: "wechat:wx1234567890", "wecom:ww1234567890"
        
        Returns:
            如果 Token 存在且未过期，返回 Token 字符串；否则返回 None
        """
        with self._lock:
            if key not in self._cache:
                logger.debug(f"Token 缓存未命中: {key}")
                return None
            
            cache_entry = self._cache[key]
            expire_time = cache_entry.get("expire_time")
            
            # 检查是否过期
            if expire_time and datetime.now() >= expire_time:
                logger.info(f"Token 已过期，从缓存中移除: {key}")
                del self._cache[key]
                return None
            
            token = cache_entry.get("token")
            logger.debug(f"Token 缓存命中: {key}")
            return token
    
    def set(
        self,
        key: str,
        token: str,
        expires_in: int,
        buffer_seconds: int = 300
    ) -> None:
        """
        设置 Token 缓存
        
        Args:
            key: 缓存键，格式为 "provider:identifier"
            token: Token 字符串
            expires_in: Token 有效期（秒）
            buffer_seconds: 提前过期的缓冲时间（秒），默认 5 分钟
                           实际过期时间 = expires_in - buffer_seconds
        """
        with self._lock:
            # 计算过期时间（提前 buffer_seconds 过期）
            actual_expires_in = max(expires_in - buffer_seconds, 60)
            expire_time = datetime.now() + timedelta(seconds=actual_expires_in)
            
            self._cache[key] = {
                "token": token,
                "expire_time": expire_time,
                "created_at": datetime.now()
            }
            
            logger.info(
                f"Token 已缓存: {key}, "
                f"有效期: {actual_expires_in}秒, "
                f"过期时间: {expire_time.isoformat()}"
            )
    
    def delete(self, key: str) -> bool:
        """
        删除缓存的 Token
        
        Args:
            key: 缓存键
        
        Returns:
            如果删除成功返回 True，如果键不存在返回 False
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Token 已从缓存中删除: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"已清空所有 Token 缓存，共 {count} 个")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计信息的字典
        """
        with self._lock:
            total_count = len(self._cache)
            valid_count = 0
            expired_count = 0
            
            now = datetime.now()
            for cache_entry in self._cache.values():
                expire_time = cache_entry.get("expire_time")
                if expire_time and now < expire_time:
                    valid_count += 1
                else:
                    expired_count += 1
            
            return {
                "total_count": total_count,
                "valid_count": valid_count,
                "expired_count": expired_count
            }
    
    def cleanup_expired(self) -> int:
        """
        清理所有过期的 Token
        
        Returns:
            清理的 Token 数量
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.get("expire_time") and now >= entry["expire_time"]
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"已清理 {len(expired_keys)} 个过期 Token")
            
            return len(expired_keys)


# 全局 Token 缓存实例
token_cache = TokenCache()
