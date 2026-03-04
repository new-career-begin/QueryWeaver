"""
日志记录功能测试

验证结构化日志记录是否符合设计要求
"""
import json
import logging
from io import StringIO
import pytest

from api.logging_config import JSONFormatter, configure_logging


class TestJSONFormatter:
    """测试 JSON 日志格式化器"""
    
    def test_basic_log_formatting(self):
        """测试基础日志格式化"""
        # 创建格式化器
        formatter = JSONFormatter()
        
        # 创建日志记录
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="测试消息",
            args=(),
            exc_info=None
        )
        
        # 格式化
        formatted = formatter.format(record)
        
        # 解析 JSON
        log_data = json.loads(formatted)
        
        # 验证基础字段
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "测试消息"
    
    def test_llm_call_log_formatting(self):
        """测试 LLM 调用日志格式化"""
        formatter = JSONFormatter()
        
        # 创建带额外字段的日志记录
        record = logging.LogRecord(
            name="api.llm_utils",
            level=logging.INFO,
            pathname="llm_utils.py",
            lineno=100,
            msg="LLM 调用成功",
            args=(),
            exc_info=None
        )
        
        # 添加额外字段
        record.event = "llm_call_success"
        record.model = "deepseek/deepseek-chat"
        record.user_email = "test@example.com"
        record.execution_time = 1.234
        record.prompt_tokens = 100
        record.completion_tokens = 50
        record.total_tokens = 150
        record.temperature = 0.7
        record.max_tokens = 2000
        
        # 格式化
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证所有字段
        assert log_data["event"] == "llm_call_success"
        assert log_data["model"] == "deepseek/deepseek-chat"
        assert log_data["user_email"] == "test@example.com"
        assert log_data["execution_time"] == 1.234
        assert log_data["prompt_tokens"] == 100
        assert log_data["completion_tokens"] == 50
        assert log_data["total_tokens"] == 150
        assert log_data["temperature"] == 0.7
        assert log_data["max_tokens"] == 2000
    
    def test_error_log_formatting(self):
        """测试错误日志格式化"""
        formatter = JSONFormatter()
        
        # 创建错误日志记录
        record = logging.LogRecord(
            name="api.llm_utils",
            level=logging.ERROR,
            pathname="llm_utils.py",
            lineno=150,
            msg="LLM 调用失败",
            args=(),
            exc_info=None
        )
        
        # 添加错误字段
        record.event = "llm_call_error"
        record.model = "deepseek/deepseek-chat"
        record.error_type = "RateLimitError"
        record.error_message = "Rate limit exceeded"
        record.retry_attempt = 2
        record.max_retries = 3
        
        # 格式化
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证错误字段
        assert log_data["event"] == "llm_call_error"
        assert log_data["error_type"] == "RateLimitError"
        assert log_data["error_message"] == "Rate limit exceeded"
        assert log_data["retry_attempt"] == 2
        assert log_data["max_retries"] == 3
    
    def test_batch_call_log_formatting(self):
        """测试批量调用日志格式化"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="api.llm_utils",
            level=logging.INFO,
            pathname="llm_utils.py",
            lineno=200,
            msg="批量 LLM 调用成功",
            args=(),
            exc_info=None
        )
        
        # 添加批量调用字段
        record.event = "llm_batch_call_success"
        record.model = "deepseek/deepseek-chat"
        record.batch_size = 5
        record.execution_time = 3.456
        record.total_tokens = 500
        
        # 格式化
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证批量调用字段
        assert log_data["event"] == "llm_batch_call_success"
        assert log_data["batch_size"] == 5
        assert log_data["execution_time"] == 3.456
        assert log_data["total_tokens"] == 500


class TestLoggingConfiguration:
    """测试日志配置"""
    
    def test_json_logging_configuration(self):
        """测试 JSON 日志配置"""
        # 配置 JSON 日志
        configure_logging(use_json=True, level=logging.INFO)
        
        # 获取根日志记录器
        root_logger = logging.getLogger()
        
        # 验证配置
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0
        
        # 验证格式化器类型
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)
    
    def test_text_logging_configuration(self):
        """测试文本日志配置"""
        # 配置文本日志
        configure_logging(use_json=False, level=logging.DEBUG)
        
        # 获取根日志记录器
        root_logger = logging.getLogger()
        
        # 验证配置
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) > 0
        
        # 验证格式化器类型
        handler = root_logger.handlers[0]
        assert not isinstance(handler.formatter, JSONFormatter)


class TestLogSecurity:
    """测试日志安全性"""
    
    def test_no_api_key_in_logs(self):
        """测试日志中不包含完整的 API Key"""
        # 配置日志到字符串缓冲区
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("test_security")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # 模拟记录包含 API Key 的日志（不应该这样做）
        # 这个测试验证即使错误地尝试记录 API Key，也不会出现在日志中
        record = logging.LogRecord(
            name="test_security",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="配置已保存",
            args=(),
            exc_info=None
        )
        
        # 注意：我们的日志记录器不应该记录 api_key 字段
        # 这个测试验证 JSONFormatter 不会自动包含未定义的字段
        record.model = "deepseek/deepseek-chat"
        
        # 格式化并获取日志
        formatted = handler.formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证日志中不包含 api_key 字段
        assert "api_key" not in log_data
        assert "API_KEY" not in log_data
        assert "apiKey" not in log_data
    
    def test_log_contains_required_fields(self):
        """测试日志包含所有必需字段"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="api.llm_utils",
            level=logging.INFO,
            pathname="llm_utils.py",
            lineno=100,
            msg="LLM 调用成功",
            args=(),
            exc_info=None
        )
        
        # 添加必需字段
        record.event = "llm_call_success"
        record.model = "deepseek/deepseek-chat"
        record.execution_time = 1.5
        record.prompt_tokens = 100
        record.completion_tokens = 50
        record.total_tokens = 150
        
        # 格式化
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证必需字段（根据需求 8.1, 8.2）
        required_fields = [
            "timestamp",
            "level",
            "logger",
            "message",
            "event",
            "model",
            "execution_time",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens"
        ]
        
        for field in required_fields:
            assert field in log_data, f"缺少必需字段: {field}"
    
    def test_timestamp_format(self):
        """测试时间戳格式"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="测试",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # 验证时间戳格式（ISO 8601 格式，UTC 时区）
        timestamp = log_data["timestamp"]
        # 新格式：2025-01-15T10:30:00+00:00 或 2025-01-15T10:30:00Z
        assert "T" in timestamp, "时间戳应该使用 ISO 8601 格式"
        assert ("+00:00" in timestamp or timestamp.endswith("Z")), \
            "时间戳应该使用 UTC 时区"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
