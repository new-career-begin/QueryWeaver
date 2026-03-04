"""
重试机制单元测试

测试指数退避策略、最大重试次数和不同错误类型的处理
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from api.retry_handler import (
    call_with_retry,
    retry_on_error,
    RateLimitError,
    ServiceUnavailableError,
    AuthenticationError,
    map_litellm_exception
)


@pytest.mark.asyncio
async def test_successful_call_no_retry():
    """测试成功调用不需要重试"""
    async def successful_func():
        return "success"
    
    result = await call_with_retry(successful_func)
    assert result == "success"


@pytest.mark.asyncio
async def test_rate_limit_retry_success():
    """测试速率限制错误重试成功"""
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    result = await call_with_retry(failing_func, max_retries=3, initial_delay=0.1)
    
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_service_unavailable_retry_success():
    """测试服务不可用错误重试成功"""
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ServiceUnavailableError("Service unavailable")
        return "success"
    
    result = await call_with_retry(failing_func, max_retries=3, initial_delay=0.1)
    
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    """测试达到最大重试次数"""
    call_count = 0
    
    async def always_failing_func():
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limit exceeded")
    
    with pytest.raises(RateLimitError):
        await call_with_retry(always_failing_func, max_retries=3, initial_delay=0.1)
    
    # 应该调用 4 次（初始调用 + 3 次重试）
    assert call_count == 4


@pytest.mark.asyncio
async def test_authentication_error_no_retry():
    """测试认证错误不重试"""
    call_count = 0
    
    async def auth_failing_func():
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("Invalid API key")
    
    with pytest.raises(AuthenticationError):
        await call_with_retry(auth_failing_func, max_retries=3, initial_delay=0.1)
    
    # 认证错误不应该重试，只调用 1 次
    assert call_count == 1


@pytest.mark.asyncio
async def test_exponential_backoff():
    """测试指数退避策略"""
    delays = []
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    # 记录实际延迟时间
    original_sleep = asyncio.sleep
    
    async def mock_sleep(delay):
        delays.append(delay)
        await original_sleep(0.01)  # 实际测试时使用很短的延迟
    
    # 临时替换 asyncio.sleep
    asyncio.sleep = mock_sleep
    
    try:
        result = await call_with_retry(
            failing_func,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0
        )
        
        assert result == "success"
        assert call_count == 4
        
        # 验证指数退避：1.0, 2.0, 4.0
        assert len(delays) == 3
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        
    finally:
        # 恢复原始的 asyncio.sleep
        asyncio.sleep = original_sleep


@pytest.mark.asyncio
async def test_retry_decorator():
    """测试重试装饰器"""
    call_count = 0
    
    @retry_on_error(max_retries=2, initial_delay=0.1)
    async def decorated_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    result = await decorated_func()
    
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_sync_function_call():
    """测试同步函数调用"""
    call_count = 0
    
    def sync_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    result = await call_with_retry(sync_func, max_retries=3, initial_delay=0.1)
    
    assert result == "success"
    assert call_count == 2


def test_map_litellm_exception_rate_limit():
    """测试 LiteLLM 异常映射 - 速率限制"""
    exception = Exception("Rate limit exceeded (429)")
    mapped = map_litellm_exception(exception)
    
    assert isinstance(mapped, RateLimitError)


def test_map_litellm_exception_service_unavailable():
    """测试 LiteLLM 异常映射 - 服务不可用"""
    exception = Exception("Service unavailable (503)")
    mapped = map_litellm_exception(exception)
    
    assert isinstance(mapped, ServiceUnavailableError)


def test_map_litellm_exception_authentication():
    """测试 LiteLLM 异常映射 - 认证错误"""
    exception = Exception("Invalid API key (401)")
    mapped = map_litellm_exception(exception)
    
    assert isinstance(mapped, AuthenticationError)


def test_map_litellm_exception_other():
    """测试 LiteLLM 异常映射 - 其他错误"""
    exception = Exception("Some other error")
    mapped = map_litellm_exception(exception)
    
    # 其他错误保持原样
    assert mapped == exception
    assert not isinstance(mapped, (RateLimitError, ServiceUnavailableError, AuthenticationError))


@pytest.mark.asyncio
async def test_retry_with_args_and_kwargs():
    """测试带参数的重试调用"""
    call_count = 0
    
    async def func_with_args(a, b, c=None):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError("Rate limit exceeded")
        return f"{a}-{b}-{c}"
    
    result = await call_with_retry(
        func_with_args,
        max_retries=3,
        initial_delay=0.1,
        "arg1",
        "arg2",
        c="kwarg1"
    )
    
    assert result == "arg1-arg2-kwarg1"
    assert call_count == 2
