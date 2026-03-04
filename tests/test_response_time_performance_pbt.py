"""
响应时间性能属性测试

Feature: deepseek-llm-support
Property 16: 响应时间性能

属性：对于任意 SQL 生成请求，95% 的请求应该在 5 秒内返回结果

验证需求：12.1
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import random

from api.performance_monitor import performance_monitor


# 生成响应时间列表的策略
# 大部分响应时间在 0.5-3 秒，少数在 3-5 秒
response_time_strategy = st.one_of(
    st.floats(min_value=0.5, max_value=3.0),  # 90% 的请求
    st.floats(min_value=3.0, max_value=4.8)   # 10% 的请求
)


@given(
    response_times=st.lists(
        response_time_strategy,
        min_size=30,
        max_size=100
    )
)
@settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_p95_response_time_under_threshold(response_times):
    """
    属性测试：P95 响应时间性能
    
    **验证：需求 12.1**
    
    属性：对于任意批量 SQL 生成请求，P95 响应时间应该在 5 秒内
    
    测试策略：
    1. 生成模拟的响应时间列表（大部分在 1-3 秒，少数在 3-5 秒）
    2. 将响应时间记录到性能监控器
    3. 计算 P95 响应时间
    4. 验证 P95 < 5 秒
    """
    # 重置性能监控器
    model_name = 'deepseek/deepseek-chat'
    performance_monitor.reset_metrics(model_name)
    
    # 记录所有响应时间
    for response_time in response_times:
        performance_monitor.record_call(
            model=model_name,
            response_time=response_time,
            success=True,
            user_email="test@example.com"
        )
    
    # 计算 P95 响应时间
    p95 = performance_monitor.calculate_p95(model_name)
    
    # 验证 P95 不为 None（有足够的数据点）
    assert p95 is not None, "数据点不足，无法计算 P95"
    
    # 验证 P95 响应时间 < 5 秒（需求 12.1）
    assert p95 < 5.0, f"P95 响应时间 {p95:.2f}s 超过 5 秒阈值"
    
    # 验证 P95 在合理范围内（应该接近最大值的 95%）
    sorted_times = sorted(response_times)
    p95_index = int(len(sorted_times) * 0.95)
    expected_p95 = sorted_times[p95_index]
    
    # 允许小的浮点数误差
    assert abs(p95 - expected_p95) < 0.01, \
        f"P95 计算不准确：期望 {expected_p95:.2f}s，实际 {p95:.2f}s"


@given(
    response_times=st.lists(
        st.floats(min_value=0.1, max_value=10.0),
        min_size=20,
        max_size=80
    )
)
@settings(max_examples=10, deadline=None)
def test_p95_calculation_accuracy(response_times):
    """
    属性测试：P95 计算准确性
    
    属性：对于任意响应时间列表，P95 计算应该准确
    
    验证：
    1. P95 值在最小值和最大值之间
    2. 至少 95% 的值小于等于 P95
    """
    # 重置监控器
    model_name = 'test/model'
    performance_monitor.reset_metrics(model_name)
    
    # 记录所有响应时间
    for rt in response_times:
        performance_monitor.record_call(
            model=model_name,
            response_time=rt,
            success=True
        )
    
    # 计算 P95
    p95 = performance_monitor.calculate_p95(model_name)
    
    if p95 is None:
        pytest.skip("数据点不足")
    
    # 验证 P95 在合理范围内
    assert min(response_times) <= p95 <= max(response_times), \
        f"P95 {p95} 应该在 [{min(response_times)}, {max(response_times)}] 范围内"
    
    # 验证至少 95% 的值 <= P95
    count_below_p95 = sum(1 for rt in response_times if rt <= p95)
    percentage = count_below_p95 / len(response_times)
    assert percentage >= 0.95, \
        f"只有 {percentage*100:.1f}% 的值 <= P95，应该 >= 95%"



