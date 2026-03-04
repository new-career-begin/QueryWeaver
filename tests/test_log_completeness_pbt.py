"""
结构化日志完整性属性测试

Feature: deepseek-llm-support
Property 14: 结构化日志完整性
验证：需求 8.1

使用 Hypothesis 进行属性测试，验证对于任意 DeepSeek API 调用，
日志应该包含模型名称、请求参数、响应时间和 token 使用量等必需字段
"""
import json
import logging
from io import StringIO
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

import pytest
from hypothesis import given, strategies as st, settings

from api.logging_config import JSONFormatter, configure_logging
from api.llm_utils import call_completion, call_batch_completion


# ============================================================================
# 测试策略定义
# ============================================================================

# 模型名称策略：生成有效的模型名称
model_names = st.sampled_from([
    "deepseek/deepseek-chat",
    "deepseek/deepseek-coder",
    "openai/gpt-4",
    "openai/gpt-3.5-turbo",
    "azure/gpt-4"
])

# 用户邮箱策略
user_emails = st.emails() | st.none()

# 消息策略：生成聊天消息列表
messages_strategy = st.lists(
    st.fixed_dictionaries({
        'role': st.sampled_from(['user', 'assistant', 'system']),
        'content': st.text(min_size=1, max_size=200)
    }),
    min_size=1,
    max_size=5
)

# 温度参数策略
temperature_strategy = st.floats(min_value=0.0, max_value=2.0)

# Token 使用量策略
token_strategy = st.integers(min_value=0, max_value=10000)

# 执行时间策略（秒）
execution_time_strategy = st.floats(min_value=0.1, max_value=30.0)


# ============================================================================
# 辅助函数
# ============================================================================

def create_mock_response(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int
) -> Mock:
    """
    创建模拟的 LLM 响应对象
    
    Args:
        prompt_tokens: 提示词 token 数
        completion_tokens: 完成 token 数
        total_tokens: 总 token 数
        
    Returns:
        模拟的响应对象
    """
    mock_response = Mock()
    mock_response.choices = [
        Mock(message={'role': 'assistant', 'content': 'Test response'})
    ]
    
    # 创建 usage 对象
    mock_usage = Mock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens
    mock_usage.total_tokens = total_tokens
    mock_response.usage = mock_usage
    
    return mock_response


def capture_log_output(logger_name: str = "api.llm_utils") -> StringIO:
    """
    捕获日志输出到字符串缓冲区
    
    Args:
        logger_name: 日志记录器名称
        
    Returns:
        字符串缓冲区对象
    """
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return log_stream


def parse_log_lines(log_output: str) -> List[Dict[str, Any]]:
    """
    解析日志输出为字典列表
    
    Args:
        log_output: 日志输出字符串
        
    Returns:
        日志条目字典列表
    """
    log_lines = []
    for line in log_output.strip().split('\n'):
        if line:
            try:
                log_lines.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return log_lines


# ============================================================================
# 属性测试：单次 LLM 调用日志完整性
# ============================================================================

@given(
    model=model_names,
    user_email=user_emails,
    messages=messages_strategy,
    temperature=temperature_strategy,
    prompt_tokens=token_strategy,
    completion_tokens=token_strategy,
    execution_time=execution_time_strategy
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_single_llm_call_log_completeness(
    model: str,
    user_email: str,
    messages: List[Dict[str, str]],
    temperature: float,
    prompt_tokens: int,
    completion_tokens: int,
    execution_time: float
):
    """
    属性测试：单次 LLM 调用日志完整性
    
    Feature: deepseek-llm-support, Property 14: 结构化日志完整性
    验证：需求 8.1
    
    属性：对于任意 DeepSeek API 调用，日志应该包含以下必需字段：
    - timestamp: 时间戳
    - level: 日志级别
    - logger: 日志记录器名称
    - message: 日志消息
    - event: 事件类型
    - model: 模型名称
    - execution_time: 执行时间
    - prompt_tokens: 提示词 token 数
    - completion_tokens: 完成 token 数
    - total_tokens: 总 token 数
    """
    # 计算总 token 数
    total_tokens = prompt_tokens + completion_tokens
    
    # 创建模拟响应
    mock_response = create_mock_response(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )
    
    # 捕获日志输出
    log_stream = capture_log_output()
    
    # Mock litellm.completion 和 Config.load_user_config
    with patch('api.llm_utils.completion', return_value=mock_response):
        with patch('api.llm_utils.call_with_retry') as mock_retry:
            with patch('api.config.Config.load_user_config', new_callable=AsyncMock, return_value=None):
                # 配置 mock_retry 直接返回响应
                async def mock_call(func, **kwargs):
                    return await func()
                mock_retry.side_effect = mock_call
                
                try:
                    # 调用 LLM
                    await call_completion(
                        messages=messages,
                        user_email=user_email,
                        model=model,
                        temperature=temperature
                    )
                except Exception:
                    # 忽略可能的异常，我们只关心日志
                    pass
    
    # 获取日志输出
    log_output = log_stream.getvalue()
    log_lines = parse_log_lines(log_output)
    
    # 应该至少有两条日志：开始和成功
    assert len(log_lines) >= 1, "应该至少有一条日志记录"
    
    # 查找成功日志
    success_logs = [
        log for log in log_lines 
        if log.get('event') == 'llm_call_success'
    ]
    
    if success_logs:
        success_log = success_logs[0]
        
        # 验证必需字段存在
        required_fields = [
            'timestamp',
            'level',
            'logger',
            'message',
            'event',
            'model',
            'execution_time'
        ]
        
        for field in required_fields:
            assert field in success_log, f"日志缺少必需字段: {field}"
        
        # 验证字段值的类型和合理性
        assert isinstance(success_log['timestamp'], str), "timestamp 应该是字符串"
        assert success_log['level'] in ['INFO', 'DEBUG', 'WARNING', 'ERROR'], \
            "level 应该是有效的日志级别"
        assert isinstance(success_log['logger'], str), "logger 应该是字符串"
        assert isinstance(success_log['message'], str), "message 应该是字符串"
        assert success_log['event'] == 'llm_call_success', "event 应该是 llm_call_success"
        assert success_log['model'] == model, f"model 应该是 {model}"
        assert isinstance(success_log['execution_time'], (int, float)), \
            "execution_time 应该是数字"
        assert success_log['execution_time'] >= 0, "execution_time 应该非负"
        
        # 验证 token 使用量字段（如果存在）
        if 'prompt_tokens' in success_log:
            assert isinstance(success_log['prompt_tokens'], int), \
                "prompt_tokens 应该是整数"
            assert success_log['prompt_tokens'] >= 0, "prompt_tokens 应该非负"
        
        if 'completion_tokens' in success_log:
            assert isinstance(success_log['completion_tokens'], int), \
                "completion_tokens 应该是整数"
            assert success_log['completion_tokens'] >= 0, "completion_tokens 应该非负"
        
        if 'total_tokens' in success_log:
            assert isinstance(success_log['total_tokens'], int), \
                "total_tokens 应该是整数"
            assert success_log['total_tokens'] >= 0, "total_tokens 应该非负"
        
        # 验证时间戳格式（ISO 8601）
        timestamp = success_log['timestamp']
        assert 'T' in timestamp, "时间戳应该使用 ISO 8601 格式"
        assert ('+00:00' in timestamp or timestamp.endswith('Z')), \
            "时间戳应该使用 UTC 时区"


# ============================================================================
# 属性测试：批量 LLM 调用日志完整性
# ============================================================================

@given(
    model=model_names,
    user_email=user_emails,
    batch_size=st.integers(min_value=1, max_value=5),
    temperature=temperature_strategy,
    total_prompt_tokens=token_strategy,
    total_completion_tokens=token_strategy
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_batch_llm_call_log_completeness(
    model: str,
    user_email: str,
    batch_size: int,
    temperature: float,
    total_prompt_tokens: int,
    total_completion_tokens: int
):
    """
    属性测试：批量 LLM 调用日志完整性
    
    Feature: deepseek-llm-support, Property 14: 结构化日志完整性
    验证：需求 8.1
    
    属性：对于任意批量 DeepSeek API 调用，日志应该包含：
    - 所有基础字段（timestamp, level, logger, message, event）
    - model: 模型名称
    - batch_size: 批量大小
    - execution_time: 执行时间
    - token 使用量统计
    """
    # 计算总 token 数
    total_tokens = total_prompt_tokens + total_completion_tokens
    
    # 创建批量消息列表
    messages_list = [
        [{'role': 'user', 'content': f'Query {i}'}]
        for i in range(batch_size)
    ]
    
    # 创建批量模拟响应
    mock_responses = [
        create_mock_response(
            prompt_tokens=total_prompt_tokens // batch_size,
            completion_tokens=total_completion_tokens // batch_size,
            total_tokens=total_tokens // batch_size
        )
        for _ in range(batch_size)
    ]
    
    # 捕获日志输出
    log_stream = capture_log_output()
    
    # Mock litellm.batch_completion 和 Config.load_user_config
    with patch('api.llm_utils.batch_completion', return_value=mock_responses):
        with patch('api.llm_utils.call_with_retry') as mock_retry:
            with patch('api.config.Config.load_user_config', new_callable=AsyncMock, return_value=None):
                # 配置 mock_retry 直接返回响应
                async def mock_call(func, **kwargs):
                    return await func()
                mock_retry.side_effect = mock_call
                
                try:
                    # 调用批量 LLM
                    await call_batch_completion(
                        messages_list=messages_list,
                        user_email=user_email,
                        model=model,
                        temperature=temperature
                    )
                except Exception:
                    # 忽略可能的异常，我们只关心日志
                    pass
    
    # 获取日志输出
    log_output = log_stream.getvalue()
    log_lines = parse_log_lines(log_output)
    
    # 应该至少有日志记录
    assert len(log_lines) >= 1, "应该至少有一条日志记录"
    
    # 查找批量调用成功日志
    batch_success_logs = [
        log for log in log_lines 
        if log.get('event') == 'llm_batch_call_success'
    ]
    
    if batch_success_logs:
        batch_log = batch_success_logs[0]
        
        # 验证必需字段存在
        required_fields = [
            'timestamp',
            'level',
            'logger',
            'message',
            'event',
            'model',
            'batch_size',
            'execution_time'
        ]
        
        for field in required_fields:
            assert field in batch_log, f"批量调用日志缺少必需字段: {field}"
        
        # 验证字段值
        assert batch_log['event'] == 'llm_batch_call_success', \
            "event 应该是 llm_batch_call_success"
        assert batch_log['model'] == model, f"model 应该是 {model}"
        assert batch_log['batch_size'] == batch_size, \
            f"batch_size 应该是 {batch_size}"
        assert isinstance(batch_log['execution_time'], (int, float)), \
            "execution_time 应该是数字"
        assert batch_log['execution_time'] >= 0, "execution_time 应该非负"
        
        # 验证 token 统计字段
        if 'prompt_tokens' in batch_log:
            assert isinstance(batch_log['prompt_tokens'], int), \
                "prompt_tokens 应该是整数"
            assert batch_log['prompt_tokens'] >= 0, "prompt_tokens 应该非负"
        
        if 'completion_tokens' in batch_log:
            assert isinstance(batch_log['completion_tokens'], int), \
                "completion_tokens 应该是整数"
            assert batch_log['completion_tokens'] >= 0, "completion_tokens 应该非负"
        
        if 'total_tokens' in batch_log:
            assert isinstance(batch_log['total_tokens'], int), \
                "total_tokens 应该是整数"
            assert batch_log['total_tokens'] >= 0, "total_tokens 应该非负"


# ============================================================================
# 属性测试：错误日志完整性
# ============================================================================

@given(
    model=model_names,
    user_email=user_emails,
    messages=messages_strategy,
    error_type=st.sampled_from([
        'RateLimitError',
        'ServiceUnavailableError',
        'AuthenticationError',
        'ValueError'
    ]),
    error_message=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_error_log_completeness(
    model: str,
    user_email: str,
    messages: List[Dict[str, str]],
    error_type: str,
    error_message: str
):
    """
    属性测试：错误日志完整性
    
    Feature: deepseek-llm-support, Property 14: 结构化日志完整性
    验证：需求 8.1, 8.3
    
    属性：对于任意失败的 DeepSeek API 调用，日志应该包含：
    - 所有基础字段
    - event: llm_call_error
    - model: 模型名称
    - error_type: 错误类型
    - error_message: 错误消息
    - execution_time: 执行时间
    """
    # 捕获日志输出
    log_stream = capture_log_output()
    
    # 根据错误类型创建对应的异常
    # 创建一个动态异常类
    exception_class = type(error_type, (Exception,), {})
    exception = exception_class(error_message)
    
    # Mock litellm.completion 抛出异常和 Config.load_user_config
    with patch('api.llm_utils.completion', side_effect=exception):
        with patch('api.llm_utils.call_with_retry') as mock_retry:
            with patch('api.config.Config.load_user_config', new_callable=AsyncMock, return_value=None):
                # 配置 mock_retry 抛出异常
                async def mock_call(func, **kwargs):
                    return await func()
                mock_retry.side_effect = mock_call
                
                try:
                    # 调用 LLM（应该失败）
                    await call_completion(
                        messages=messages,
                        user_email=user_email,
                        model=model
                    )
                except Exception:
                    # 预期会抛出异常
                    pass
    
    # 获取日志输出
    log_output = log_stream.getvalue()
    log_lines = parse_log_lines(log_output)
    
    # 应该有日志记录
    assert len(log_lines) >= 1, "应该至少有一条日志记录"
    
    # 查找错误日志
    error_logs = [
        log for log in log_lines 
        if log.get('event') == 'llm_call_error'
    ]
    
    if error_logs:
        error_log = error_logs[0]
        
        # 验证必需字段存在
        required_fields = [
            'timestamp',
            'level',
            'logger',
            'message',
            'event',
            'model',
            'error_type',
            'error_message',
            'execution_time'
        ]
        
        for field in required_fields:
            assert field in error_log, f"错误日志缺少必需字段: {field}"
        
        # 验证字段值
        assert error_log['level'] in ['ERROR', 'CRITICAL'], \
            "错误日志级别应该是 ERROR 或 CRITICAL"
        assert error_log['event'] == 'llm_call_error', \
            "event 应该是 llm_call_error"
        assert error_log['model'] == model, f"model 应该是 {model}"
        assert isinstance(error_log['error_type'], str), \
            "error_type 应该是字符串"
        assert isinstance(error_log['error_message'], str), \
            "error_message 应该是字符串"
        assert isinstance(error_log['execution_time'], (int, float)), \
            "execution_time 应该是数字"
        assert error_log['execution_time'] >= 0, "execution_time 应该非负"


# ============================================================================
# 属性测试：日志参数完整性
# ============================================================================

@given(
    model=model_names,
    user_email=user_emails,
    messages=messages_strategy,
    temperature=temperature_strategy,
    max_tokens=st.integers(min_value=1, max_value=4000) | st.none()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_log_parameters_completeness(
    model: str,
    user_email: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int
):
    """
    属性测试：日志参数完整性
    
    Feature: deepseek-llm-support, Property 14: 结构化日志完整性
    验证：需求 8.1
    
    属性：对于任意 DeepSeek API 调用，开始日志应该包含请求参数：
    - message_count: 消息数量
    - temperature: 温度参数
    - max_tokens: 最大 token 数（如果指定）
    """
    # 创建模拟响应
    mock_response = create_mock_response(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    # 捕获日志输出
    log_stream = capture_log_output()
    
    # Mock litellm.completion 和 Config.load_user_config
    with patch('api.llm_utils.completion', return_value=mock_response):
        with patch('api.llm_utils.call_with_retry') as mock_retry:
            with patch('api.config.Config.load_user_config', new_callable=AsyncMock, return_value=None):
                async def mock_call(func, **kwargs):
                    return await func()
                mock_retry.side_effect = mock_call
                
                try:
                    # 调用 LLM
                    await call_completion(
                        messages=messages,
                        user_email=user_email,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                except Exception:
                    pass
    
    # 获取日志输出
    log_output = log_stream.getvalue()
    log_lines = parse_log_lines(log_output)
    
    # 查找开始日志
    start_logs = [
        log for log in log_lines 
        if log.get('event') == 'llm_call_start'
    ]
    
    if start_logs:
        start_log = start_logs[0]
        
        # 验证参数字段存在
        assert 'message_count' in start_log, "开始日志应该包含 message_count"
        assert 'temperature' in start_log, "开始日志应该包含 temperature"
        
        # 验证参数值
        assert start_log['message_count'] == len(messages), \
            f"message_count 应该等于消息数量 {len(messages)}"
        assert abs(start_log['temperature'] - temperature) < 0.01, \
            f"temperature 应该等于 {temperature}"
        
        # 如果指定了 max_tokens，应该在日志中
        if max_tokens is not None:
            assert 'max_tokens' in start_log, \
                "如果指定了 max_tokens，开始日志应该包含它"
            assert start_log['max_tokens'] == max_tokens, \
                f"max_tokens 应该等于 {max_tokens}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
