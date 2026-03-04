"""
指数退避重试属性测试

Feature: deepseek-llm-support
Property 9: 指数退避重试
验证需求: 4.2

属性：对于任意速率限制错误，系统应该使用指数退避策略进行重试，
每次重试延迟应该是前一次的倍数
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from api.retry_handler import call_with_retry, RateLimitError, ServiceUnavailableError


@given(
    max_retries=st.integers(min_value=1, max_value=5),
    initial_delay=st.floats(min_value=0.1, max_value=2.0),
    backoff_factor=st.floats(min_value=1.5, max_value=3.0)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_exponential_backoff_property(max_retries, initial_delay, backoff_factor):
    """
    属性测试：指数退避重试
    
    验证：需求 4.2
    
    属性：对于任意的重试参数配置，延迟时间应该按照指数增长
    """
    delays = []
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        # 总是失败，触发所有重试
        raise RateLimitError("Rate limit exceeded")
    
    # 记录实际延迟时间
    original_sleep = asyncio.sleep
    
    async def mock_sleep(delay):
        delays.append(delay)
        await original_sleep(0.001)  # 实际测试时使用很短的延迟
    
    # 临时替换 asyncio.sleep
    asyncio.sleep = mock_sleep
    
    try:
        with pytest.raises(RateLimitError):
            await call_with_retry(
                failing_func,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor
            )
        
        # 验证调用次数 = 初始调用 + 重试次数
        assert call_count == max_retries + 1
        
        # 验证延迟次数 = 重试次数
        assert len(delays) == max_retries
        
        # 验证指数退避：每次延迟应该是前一次的 backoff_factor 倍
        expected_delay = initial_delay
        for i, actual_delay in enumerate(delays):
            # 允许浮点数误差
            assert abs(actual_delay - expected_delay) < 0.001, \
                f"第 {i+1} 次重试延迟不符合指数退避：期望 {expected_delay}，实际 {actual_delay}"
            expected_delay *= backoff_factor
        
    finally:
        # 恢复原始的 asyncio.sleep
        asyncio.sleep = original_sleep


@given(
    failure_count=st.integers(min_value=1, max_value=4),
    max_retries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_retry_until_success_property(failure_count, max_retries):
    """
    属性测试：重试直到成功
    
    验证：需求 4.2, 4.3
    
    属性：如果在最大重试次数内成功，应该停止重试
    """
    call_count = 0
    delays = []
    
    async def eventually_succeeding_func():
        nonlocal call_count
        call_count += 1
        if call_count <= failure_count:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    # 记录延迟
    original_sleep = asyncio.sleep
    
    async def mock_sleep(delay):
        delays.append(delay)
        await original_sleep(0.001)
    
    asyncio.sleep = mock_sleep
    
    try:
        if failure_count <= max_retries:
            # 应该成功
            result = await call_with_retry(
                eventually_succeeding_func,
                max_retries=max_retries,
                initial_delay=0.1,
                backoff_factor=2.0
            )
            assert result == "success"
            assert call_count == failure_count + 1
            assert len(delays) == failure_count
        else:
            # 应该失败（超过最大重试次数）
            with pytest.raises(RateLimitError):
                await call_with_retry(
                    eventually_succeeding_func,
                    max_retries=max_retries,
                    initial_delay=0.1,
                    backoff_factor=2.0
                )
            assert call_count == max_retries + 1
            assert len(delays) == max_retries
    
    finally:
        asyncio.sleep = original_sleep


@given(
    initial_delay=st.floats(min_value=0.1, max_value=1.0),
    backoff_factor=st.floats(min_value=2.0, max_value=4.0),
    retry_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_total_delay_increases_exponentially(initial_delay, backoff_factor, retry_count):
    """
    属性测试：总延迟时间指数增长
    
    验证：需求 4.2
    
    属性：总延迟时间应该随着重试次数指数增长
    """
    delays = []
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limit exceeded")
    
    original_sleep = asyncio.sleep
    
    async def mock_sleep(delay):
        delays.append(delay)
        await original_sleep(0.001)
    
    asyncio.sleep = mock_sleep
    
    try:
        with pytest.raises(RateLimitError):
            await call_with_retry(
                failing_func,
                max_retries=retry_count,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor
            )
        
        # 计算总延迟时间
        total_delay = sum(delays)
        
        # 计算期望的总延迟时间（等比数列求和）
        # S = a * (1 - r^n) / (1 - r)，其中 a = initial_delay, r = backoff_factor, n = retry_count
        if backoff_factor == 1.0:
            expected_total = initial_delay * retry_count
        else:
            expected_total = initial_delay * (1 - backoff_factor ** retry_count) / (1 - backoff_factor)
        
        # 验证总延迟时间（允许浮点数误差）
        assert abs(total_delay - expected_total) < 0.01, \
            f"总延迟时间不符合预期：期望 {expected_total}，实际 {total_delay}"
        
        # 验证总延迟时间随重试次数增长
        if retry_count > 1:
            # 最后一次延迟应该大于第一次延迟
            assert delays[-1] > delays[0]
    
    finally:
        asyncio.sleep = original_sleep


@given(
    max_retries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_retry_count_never_exceeds_max(max_retries):
    """
    属性测试：重试次数不超过最大值
    
    验证：需求 4.3
    
    属性：无论如何，实际重试次数不应该超过配置的最大重试次数
    """
    call_count = 0
    
    async def always_failing_func():
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limit exceeded")
    
    with pytest.raises(RateLimitError):
        await call_with_retry(
            always_failing_func,
            max_retries=max_retries,
            initial_delay=0.01,
            backoff_factor=2.0
        )
    
    # 验证调用次数 = 初始调用 + 最大重试次数
    assert call_count == max_retries + 1
    # 确保没有超过最大重试次数
    assert call_count <= max_retries + 1


@given(
    service_errors=st.lists(
        st.sampled_from([RateLimitError, ServiceUnavailableError]),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_retry_on_different_error_types(service_errors):
    """
    属性测试：不同错误类型的重试
    
    验证：需求 4.2, 4.3
    
    属性：对于速率限制和服务不可用错误，都应该进行重试
    """
    from api.retry_handler import ServiceUnavailableError
    
    call_count = 0
    error_index = 0
    
    async def multi_error_func():
        nonlocal call_count, error_index
        call_count += 1
        if error_index < len(service_errors):
            error_class = service_errors[error_index]
            error_index += 1
            raise error_class("Service error")
        return "success"
    
    max_retries = len(service_errors)
    
    result = await call_with_retry(
        multi_error_func,
        max_retries=max_retries,
        initial_delay=0.01,
        backoff_factor=2.0
    )
    
    # 应该在所有错误后成功
    assert result == "success"
    assert call_count == len(service_errors) + 1
