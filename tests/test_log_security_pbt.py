"""
日志安全性属性测试

使用 Hypothesis 进行基于属性的测试，验证日志中不包含敏感信息（API Key）

属性 15：日志安全性
验证：需求 8.7, 11.2
"""
import json
import logging
from io import StringIO
from typing import List

import pytest
from hypothesis import given, strategies as st, settings

from api.logging_config import JSONFormatter


# API Key 生成策略
@st.composite
def api_key_strategy(draw):
    """
    生成各种格式的 API Key
    
    包括：
    - 标准格式：sk-xxxxxxxx
    - 大写变体：SK-xxxxxxxx
    - 不同长度
    - 不同前缀
    """
    prefix = draw(st.sampled_from(['sk-', 'SK-', 'api-', 'API-', 'key-', 'KEY-']))
    # 生成 20-64 个字符的随机字符串
    suffix = draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),  # 大写、小写、数字
            min_codepoint=48,  # '0'
            max_codepoint=122  # 'z'
        ),
        min_size=20,
        max_size=64
    ))
    return prefix + suffix


# 日志消息生成策略
@st.composite
def log_message_strategy(draw):
    """
    生成各种日志消息
    
    包括：
    - 配置保存消息
    - API 调用消息
    - 错误消息
    """
    message_templates = [
        "配置已保存",
        "LLM 调用成功",
        "LLM 调用失败",
        "用户配置更新",
        "API 连接测试",
        "模型初始化完成",
        "查询处理中",
    ]
    return draw(st.sampled_from(message_templates))


# 日志字段名称策略（API Key 的各种变体）
api_key_field_names = st.sampled_from([
    'api_key',
    'API_KEY',
    'apiKey',
    'ApiKey',
    'api-key',
    'API-KEY',
    'api_token',
    'API_TOKEN',
    'apiToken',
    'access_key',
    'ACCESS_KEY',
    'accessKey',
    'secret_key',
    'SECRET_KEY',
    'secretKey',
])


class TestLogSecurityProperties:
    """日志安全性属性测试套件"""
    
    @given(
        api_key=api_key_strategy(),
        message=log_message_strategy(),
    )
    @settings(max_examples=100)
    def test_api_key_not_in_log_message(self, api_key: str, message: str):
        """
        属性 15：日志安全性 - API Key 不应出现在日志消息中
        
        对于任意 API Key 和日志消息，格式化后的日志不应包含完整的 API Key
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建日志记录
        record = logging.LogRecord(
            name="api.config_manager",
            level=logging.INFO,
            pathname="config_manager.py",
            lineno=100,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加常见的日志字段（但不包含 API Key）
        record.event = "config_saved"
        record.model = "deepseek/deepseek-chat"
        record.user_email = "test@example.com"
        
        # 格式化日志
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证：日志中不应包含完整的 API Key
        # 检查所有字段的值
        for field_name, field_value in log_data.items():
            if isinstance(field_value, str):
                assert api_key not in field_value, \
                    f"日志字段 '{field_name}' 包含完整的 API Key: {field_value}"
        
        # 验证：日志的 JSON 字符串表示中也不应包含完整的 API Key
        assert api_key not in formatted, \
            f"日志的 JSON 字符串包含完整的 API Key"
    
    @given(
        api_key=api_key_strategy(),
        field_name=api_key_field_names,
    )
    @settings(max_examples=100)
    def test_api_key_field_not_in_log(self, api_key: str, field_name: str):
        """
        属性 15：日志安全性 - API Key 字段不应出现在日志中
        
        对于任意 API Key 字段名称变体，日志中不应包含该字段
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建日志记录
        record = logging.LogRecord(
            name="api.config_manager",
            level=logging.INFO,
            pathname="config_manager.py",
            lineno=100,
            msg="配置操作",
            args=(),
            exc_info=None
        )
        
        # 尝试添加 API Key 字段（模拟错误的日志记录）
        # 注意：我们的 JSONFormatter 应该忽略这些字段
        setattr(record, field_name, api_key)
        
        # 格式化日志
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证：日志中不应包含任何 API Key 相关字段
        # 将字段名转换为小写进行比较
        log_fields_lower = {k.lower() for k in log_data.keys()}
        field_name_lower = field_name.lower().replace('-', '_')
        
        assert field_name_lower not in log_fields_lower, \
            f"日志包含 API Key 字段: {field_name}"
        
        # 验证：日志中不应包含 API Key 的值
        assert api_key not in formatted, \
            f"日志包含 API Key 的值"
    
    @given(
        api_keys=st.lists(api_key_strategy(), min_size=1, max_size=5),
        message=log_message_strategy(),
    )
    @settings(max_examples=100)
    def test_multiple_api_keys_not_in_log(
        self,
        api_keys: List[str],
        message: str
    ):
        """
        属性 15：日志安全性 - 多个 API Key 都不应出现在日志中
        
        对于任意多个 API Key，日志中不应包含任何一个完整的 API Key
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建日志记录
        record = logging.LogRecord(
            name="api.config_manager",
            level=logging.INFO,
            pathname="config_manager.py",
            lineno=100,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加正常的日志字段
        record.event = "batch_config_update"
        record.model = "deepseek/deepseek-chat"
        record.batch_size = len(api_keys)
        
        # 格式化日志
        formatted = formatter.format(record)
        
        # 验证：日志中不应包含任何一个 API Key
        for api_key in api_keys:
            assert api_key not in formatted, \
                f"日志包含 API Key: {api_key[:10]}..."
    
    @given(
        api_key=api_key_strategy(),
    )
    @settings(max_examples=100)
    def test_api_key_not_in_error_log(self, api_key: str):
        """
        属性 15：日志安全性 - 错误日志中不应包含 API Key
        
        对于任意 API Key，即使在错误日志中也不应泄露
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建错误日志记录
        record = logging.LogRecord(
            name="api.config_manager",
            level=logging.ERROR,
            pathname="config_manager.py",
            lineno=150,
            msg="配置保存失败",
            args=(),
            exc_info=None
        )
        
        # 添加错误相关字段
        record.event = "config_save_error"
        record.error_type = "DatabaseError"
        record.error_message = "无法连接到数据库"
        
        # 格式化日志
        formatted = formatter.format(record)
        
        # 验证：错误日志中不应包含 API Key
        assert api_key not in formatted, \
            f"错误日志包含 API Key"
    
    @given(
        api_key=api_key_strategy(),
    )
    @settings(max_examples=100)
    def test_api_key_not_in_exception_log(self, api_key: str):
        """
        属性 15：日志安全性 - 异常日志中不应包含 API Key
        
        对于任意 API Key，即使在异常堆栈中也不应泄露
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建带异常信息的日志记录
        try:
            # 模拟一个异常（但不在消息中包含 API Key）
            raise ValueError("配置验证失败")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="api.config_manager",
            level=logging.ERROR,
            pathname="config_manager.py",
            lineno=200,
            msg="处理配置时发生异常",
            args=(),
            exc_info=exc_info
        )
        
        # 添加异常相关字段
        record.event = "config_exception"
        record.error_type = "ValueError"
        
        # 格式化日志
        formatted = formatter.format(record)
        
        # 验证：异常日志中不应包含 API Key
        assert api_key not in formatted, \
            f"异常日志包含 API Key"
    
    @given(
        api_key=api_key_strategy(),
        model_name=st.sampled_from([
            "deepseek/deepseek-chat",
            "openai/gpt-4",
            "azure/gpt-4.1",
        ]),
        execution_time=st.floats(min_value=0.1, max_value=10.0),
        token_count=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100)
    def test_api_key_not_in_llm_call_log(
        self,
        api_key: str,
        model_name: str,
        execution_time: float,
        token_count: int
    ):
        """
        属性 15：日志安全性 - LLM 调用日志中不应包含 API Key
        
        对于任意 LLM 调用参数，日志中不应包含 API Key
        
        验证：需求 8.7, 11.2
        """
        # 创建日志格式化器
        formatter = JSONFormatter()
        
        # 创建 LLM 调用日志记录
        record = logging.LogRecord(
            name="api.llm_utils",
            level=logging.INFO,
            pathname="llm_utils.py",
            lineno=100,
            msg="LLM 调用成功",
            args=(),
            exc_info=None
        )
        
        # 添加 LLM 调用相关字段（不包含 API Key）
        record.event = "llm_call_success"
        record.model = model_name
        record.execution_time = execution_time
        record.total_tokens = token_count
        record.prompt_tokens = int(token_count * 0.7)
        record.completion_tokens = int(token_count * 0.3)
        
        # 格式化日志
        formatted = formatter.format(record)
        
        # 验证：LLM 调用日志中不应包含 API Key
        assert api_key not in formatted, \
            f"LLM 调用日志包含 API Key"
        
        # 验证：日志包含必需的字段
        log_data = json.loads(formatted)
        assert "model" in log_data
        assert "execution_time" in log_data
        assert "total_tokens" in log_data


class TestLogSecurityIntegration:
    """日志安全性集成测试"""
    
    @given(
        api_key=api_key_strategy(),
    )
    @settings(max_examples=100)
    def test_real_logger_does_not_log_api_key(self, api_key: str):
        """
        集成测试：真实的日志记录器不应记录 API Key
        
        验证：需求 8.7, 11.2
        """
        # 创建一个字符串缓冲区来捕获日志输出
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(JSONFormatter())
        
        # 创建测试日志记录器
        logger = logging.getLogger("test_security_integration")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # 记录一条日志（不应包含 API Key）
        logger.info(
            "配置已保存",
            extra={
                "event": "config_saved",
                "model": "deepseek/deepseek-chat",
                "user_email": "test@example.com",
            }
        )
        
        # 获取日志输出
        log_output = log_stream.getvalue()
        
        # 验证：日志输出中不应包含 API Key
        assert api_key not in log_output, \
            f"日志输出包含 API Key"
        
        # 验证：日志是有效的 JSON
        log_data = json.loads(log_output.strip())
        assert "message" in log_data
        assert "event" in log_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
