"""
LLM API 调用重试机制

提供指数退避重试策略，处理速率限制、服务不可用等错误
"""
import asyncio
import logging
from typing import Callable, Any, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimitError(Exception):
    """速率限制错误"""
    pass


class ServiceUnavailableError(Exception):
    """服务不可用错误"""
    pass


class AuthenticationError(Exception):
    """认证错误"""
    pass


async def call_with_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> T:
    """
    带重试的异步函数调用，使用指数退避策略
    
    Args:
        func: 要调用的异步函数
        max_retries: 最大重试次数（默认 3 次）
        initial_delay: 初始延迟秒数（默认 1.0 秒）
        backoff_factor: 退避因子（默认 2.0，每次延迟翻倍）
        *args: 传递给函数的位置参数
        **kwargs: 传递给函数的关键字参数
        
    Returns:
        函数执行结果
        
    Raises:
        最后一次尝试的异常
        
    Example:
        >>> async def api_call():
        ...     return await some_api()
        >>> result = await call_with_retry(api_call, max_retries=3)
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # 调用函数
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        except RateLimitError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"速率限制错误，{delay:.1f}秒后重试 "
                    f"(尝试 {attempt + 1}/{max_retries})",
                    extra={
                        "event": "rate_limit_retry",
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "delay": delay
                    }
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "达到最大重试次数，速率限制错误",
                    extra={
                        "event": "rate_limit_max_retries",
                        "max_retries": max_retries
                    }
                )
                
        except ServiceUnavailableError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"服务不可用，{delay:.1f}秒后重试 "
                    f"(尝试 {attempt + 1}/{max_retries})",
                    extra={
                        "event": "service_unavailable_retry",
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "delay": delay
                    }
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "服务持续不可用，放弃请求",
                    extra={
                        "event": "service_unavailable_max_retries",
                        "max_retries": max_retries
                    }
                )
                
        except AuthenticationError as e:
            # 认证错误不重试
            logger.error(
                f"API 认证失败: {str(e)}",
                extra={
                    "event": "authentication_error",
                    "error": str(e)
                }
            )
            raise
            
        except Exception as e:
            logger.exception(
                f"API 调用失败: {str(e)}",
                extra={
                    "event": "api_call_error",
                    "error": str(e),
                    "attempt": attempt + 1
                }
            )
            raise
    
    # 如果所有重试都失败，抛出最后一个异常
    if last_exception:
        raise last_exception
    
    # 理论上不应该到达这里
    raise RuntimeError("重试逻辑异常")


def retry_on_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    装饰器：为异步函数添加重试机制
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟秒数
        backoff_factor: 退避因子
        
    Example:
        >>> @retry_on_error(max_retries=3)
        ... async def fetch_data():
        ...     return await api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await call_with_retry(
                func,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


def map_litellm_exception(exception: Exception) -> Exception:
    """
    将 LiteLLM 异常映射到自定义异常类型
    
    Args:
        exception: LiteLLM 抛出的异常
        
    Returns:
        映射后的自定义异常
    """
    error_message = str(exception).lower()
    
    # 速率限制错误
    if "rate limit" in error_message or "429" in error_message:
        return RateLimitError(str(exception))
    
    # 服务不可用错误
    if "service unavailable" in error_message or "503" in error_message:
        return ServiceUnavailableError(str(exception))
    
    # 认证错误
    if "authentication" in error_message or "401" in error_message or "invalid api key" in error_message:
        return AuthenticationError(str(exception))
    
    # 其他错误保持原样
    return exception
