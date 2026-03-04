"""
LLM 调用工具函数

提供统一的 LLM 调用接口，支持：
- 用户配置优先级（用户配置 > 环境变量 > 默认值）
- 自动重试机制
- 错误处理和日志记录
- Token 使用量统计
"""
import logging
import time
from typing import Any, Dict, List, Optional, Union

from litellm import completion, batch_completion

from api.config import Config
from api.retry_handler import (
    call_with_retry,
    map_litellm_exception,
    RateLimitError,
    ServiceUnavailableError,
    AuthenticationError
)
from api.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


async def call_completion(
    messages: List[Dict[str, str]],
    user_email: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    调用 LLM completion API，支持用户配置和重试机制
    
    优先级：用户配置 > 环境变量 > 默认值
    
    Args:
        messages: 消息列表
        user_email: 可选的用户邮箱，用于加载用户配置
        model: 可选的模型名称，覆盖配置
        temperature: 温度参数
        max_tokens: 最大 token 数
        response_format: 响应格式（用于结构化输出）
        **kwargs: 其他 LiteLLM 参数
        
    Returns:
        LiteLLM 响应对象
        
    Raises:
        AuthenticationError: 认证失败
        RateLimitError: 速率限制（重试后仍失败）
        ServiceUnavailableError: 服务不可用（重试后仍失败）
        
    Example:
        >>> response = await call_completion(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     user_email="user@example.com",
        ...     temperature=0.7
        ... )
    """
    # 获取模型配置
    if model is None:
        model = await Config.get_completion_model(user_email)
    
    # 构建调用参数
    params = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        **kwargs
    }
    
    if max_tokens is not None:
        params['max_tokens'] = max_tokens
    
    if response_format is not None:
        params['response_format'] = response_format
    
    # 如果有用户配置，添加用户特定参数
    if user_email:
        try:
            user_config = await Config.load_user_config(user_email)
            if user_config:
                user_params = user_config.to_litellm_params()
                # 合并参数，但不覆盖已设置的参数
                for key, value in user_params.items():
                    if key not in params:
                        params[key] = value
        except Exception as e:
            logger.warning(f"加载用户配置失败: {user_email}, 错误: {str(e)}")
    
    # 记录调用开始
    start_time = time.time()
    logger.info(
        "LLM 调用开始",
        extra={
            "event": "llm_call_start",
            "model": model,
            "user_email": user_email,
            "message_count": len(messages),
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    )
    
    # 定义调用函数
    async def _call():
        try:
            return completion(**params)
        except Exception as e:
            # 映射异常类型
            mapped_exception = map_litellm_exception(e)
            raise mapped_exception
    
    try:
        # 使用重试机制调用
        response = await call_with_retry(
            _call,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0
        )
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 记录性能指标
        performance_monitor.record_call(
            model=model,
            response_time=execution_time,
            success=True,
            user_email=user_email
        )
        
        # 记录 token 使用量
        usage = getattr(response, 'usage', None)
        if usage:
            prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            completion_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = getattr(usage, 'total_tokens', 0)
            
            logger.info(
                "LLM 调用成功",
                extra={
                    "event": "llm_call_success",
                    "model": model,
                    "user_email": user_email,
                    "execution_time": execution_time,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            )
        else:
            logger.info(
                "LLM 调用成功",
                extra={
                    "event": "llm_call_success",
                    "model": model,
                    "user_email": user_email,
                    "execution_time": execution_time
                }
            )
        
        return response
        
    except (RateLimitError, ServiceUnavailableError, AuthenticationError) as e:
        # 记录错误
        execution_time = time.time() - start_time
        logger.error(
            f"LLM 调用失败: {type(e).__name__}",
            extra={
                "event": "llm_call_error",
                "model": model,
                "user_email": user_email,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }
        )
        raise
    except Exception as e:
        # 记录未预期的错误
        execution_time = time.time() - start_time
        logger.exception(
            f"LLM 调用失败: {str(e)}",
            extra={
                "event": "llm_call_error",
                "model": model,
                "user_email": user_email,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }
        )
        raise


async def call_batch_completion(
    messages_list: List[List[Dict[str, str]]],
    user_email: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> List[Any]:
    """
    批量调用 LLM completion API
    
    Args:
        messages_list: 消息列表的列表
        user_email: 可选的用户邮箱
        model: 可选的模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数
        **kwargs: 其他 LiteLLM 参数
        
    Returns:
        响应列表
        
    Example:
        >>> responses = await call_batch_completion(
        ...     messages_list=[
        ...         [{"role": "user", "content": "Hello"}],
        ...         [{"role": "user", "content": "Hi"}]
        ...     ],
        ...     user_email="user@example.com"
        ... )
    """
    # 获取模型配置
    if model is None:
        model = await Config.get_completion_model(user_email)
    
    # 构建调用参数
    params = {
        'model': model,
        'messages': messages_list,
        'temperature': temperature,
        **kwargs
    }
    
    if max_tokens is not None:
        params['max_tokens'] = max_tokens
    
    # 如果有用户配置，添加用户特定参数
    if user_email:
        try:
            user_config = await Config.load_user_config(user_email)
            if user_config:
                user_params = user_config.to_litellm_params()
                for key, value in user_params.items():
                    if key not in params and key != 'model':
                        params[key] = value
        except Exception as e:
            logger.warning(f"加载用户配置失败: {user_email}, 错误: {str(e)}")
    
    # 记录调用开始
    start_time = time.time()
    logger.info(
        "批量 LLM 调用开始",
        extra={
            "event": "llm_batch_call_start",
            "model": model,
            "user_email": user_email,
            "batch_size": len(messages_list)
        }
    )
    
    # 定义调用函数
    async def _call():
        try:
            return batch_completion(**params)
        except Exception as e:
            mapped_exception = map_litellm_exception(e)
            raise mapped_exception
    
    try:
        # 使用重试机制调用
        responses = await call_with_retry(
            _call,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0
        )
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 统计总 token 使用量
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        
        for response in responses:
            if not isinstance(response, Exception):
                usage = getattr(response, 'usage', None)
                if usage:
                    total_prompt_tokens += getattr(usage, 'prompt_tokens', 0)
                    total_completion_tokens += getattr(usage, 'completion_tokens', 0)
                    total_tokens += getattr(usage, 'total_tokens', 0)
        
        logger.info(
            "批量 LLM 调用成功",
            extra={
                "event": "llm_batch_call_success",
                "model": model,
                "user_email": user_email,
                "batch_size": len(messages_list),
                "execution_time": execution_time,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens
            }
        )
        
        return responses
        
    except (RateLimitError, ServiceUnavailableError, AuthenticationError) as e:
        execution_time = time.time() - start_time
        logger.error(
            f"批量 LLM 调用失败: {type(e).__name__}",
            extra={
                "event": "llm_batch_call_error",
                "model": model,
                "user_email": user_email,
                "batch_size": len(messages_list),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }
        )
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.exception(
            f"批量 LLM 调用失败: {str(e)}",
            extra={
                "event": "llm_batch_call_error",
                "model": model,
                "user_email": user_email,
                "batch_size": len(messages_list),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }
        )
        raise


def call_completion_sync(
    messages: List[Dict[str, str]],
    user_email: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    同步调用 LLM completion API（用于非异步上下文）
    
    注意：此函数不支持重试机制，建议使用异步版本
    
    Args:
        messages: 消息列表
        user_email: 可选的用户邮箱
        model: 可选的模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数
        response_format: 响应格式
        **kwargs: 其他 LiteLLM 参数
        
    Returns:
        LiteLLM 响应对象
    """
    # 获取模型配置
    if model is None:
        model = Config.get_completion_model(user_email)
    
    # 构建调用参数
    params = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        **kwargs
    }
    
    if max_tokens is not None:
        params['max_tokens'] = max_tokens
    
    if response_format is not None:
        params['response_format'] = response_format
    
    # 如果有用户配置，添加用户特定参数
    if user_email:
        try:
            user_config = Config.load_user_config(user_email)
            if user_config:
                user_params = user_config.to_litellm_params()
                for key, value in user_params.items():
                    if key not in params:
                        params[key] = value
        except Exception as e:
            logger.warning(f"加载用户配置失败: {user_email}, 错误: {str(e)}")
    
    # 记录调用
    start_time = time.time()
    logger.info(
        "同步 LLM 调用开始",
        extra={
            "event": "llm_sync_call_start",
            "model": model,
            "user_email": user_email
        }
    )
    
    try:
        response = completion(**params)
        
        execution_time = time.time() - start_time
        
        # 记录 token 使用量
        usage = getattr(response, 'usage', None)
        if usage:
            logger.info(
                "同步 LLM 调用成功",
                extra={
                    "event": "llm_sync_call_success",
                    "model": model,
                    "user_email": user_email,
                    "execution_time": execution_time,
                    "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(usage, 'completion_tokens', 0),
                    "total_tokens": getattr(usage, 'total_tokens', 0)
                }
            )
        
        return response
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"同步 LLM 调用失败: {str(e)}",
            extra={
                "event": "llm_sync_call_error",
                "model": model,
                "user_email": user_email,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time
            }
        )
        raise
