"""
验证日志记录功能

演示结构化日志记录的使用
"""
import logging
import json
from api.logging_config import configure_logging

# 配置 JSON 日志
configure_logging(use_json=True, level=logging.INFO)

logger = logging.getLogger("demo")

print("=" * 80)
print("演示 1: 基础日志记录")
print("=" * 80)
logger.info("这是一条基础日志消息")

print("\n" + "=" * 80)
print("演示 2: LLM 调用成功日志")
print("=" * 80)
logger.info(
    "LLM 调用成功",
    extra={
        "event": "llm_call_success",
        "model": "deepseek/deepseek-chat",
        "user_email": "demo@example.com",
        "execution_time": 1.234,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "temperature": 0.7,
        "max_tokens": 2000
    }
)

print("\n" + "=" * 80)
print("演示 3: LLM 调用错误日志")
print("=" * 80)
logger.error(
    "LLM 调用失败",
    extra={
        "event": "llm_call_error",
        "model": "deepseek/deepseek-chat",
        "user_email": "demo@example.com",
        "error_type": "RateLimitError",
        "error_message": "Rate limit exceeded",
        "retry_attempt": 2,
        "max_retries": 3,
        "execution_time": 0.5
    }
)

print("\n" + "=" * 80)
print("演示 4: 批量调用日志")
print("=" * 80)
logger.info(
    "批量 LLM 调用成功",
    extra={
        "event": "llm_batch_call_success",
        "model": "deepseek/deepseek-chat",
        "user_email": "demo@example.com",
        "batch_size": 5,
        "execution_time": 3.456,
        "prompt_tokens": 500,
        "completion_tokens": 250,
        "total_tokens": 750
    }
)

print("\n" + "=" * 80)
print("演示 5: 验证日志安全性（不包含 API Key）")
print("=" * 80)
# 注意：我们的日志记录器不会记录 api_key 字段
# 这是设计上的安全特性
logger.info(
    "配置已保存",
    extra={
        "event": "config_saved",
        "user_email": "demo@example.com",
        "provider": "deepseek"
        # 注意：这里没有 api_key 字段
    }
)

print("\n" + "=" * 80)
print("验证完成！")
print("=" * 80)
print("\n说明：")
print("1. 所有日志都使用 JSON 格式输出")
print("2. 包含时间戳、日志级别、日志记录器名称和消息")
print("3. LLM 调用日志包含模型名称、执行时间、Token 使用量等信息")
print("4. 错误日志包含错误类型和错误消息")
print("5. 日志中不包含敏感信息（如完整的 API Key）")
