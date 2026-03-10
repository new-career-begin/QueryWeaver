"""
日志配置模块

提供 JSON 格式的结构化日志配置，用于生产环境的日志收集和分析
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    JSON 格式日志格式化器
    
    将日志记录转换为 JSON 格式，便于日志收集系统（如 ELK）处理
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON 字符串
        
        Args:
            record: 日志记录对象
            
        Returns:
            JSON 格式的日志字符串
        """
        # 基础日志字段
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加额外字段（通过 extra 参数传递）
        if hasattr(record, 'event'):
            log_data['event'] = record.event
        
        if hasattr(record, 'model'):
            log_data['model'] = record.model
        
        if hasattr(record, 'user_email'):
            log_data['user_email'] = record.user_email
        
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        
        if hasattr(record, 'prompt_tokens'):
            log_data['prompt_tokens'] = record.prompt_tokens
        
        if hasattr(record, 'completion_tokens'):
            log_data['completion_tokens'] = record.completion_tokens
        
        if hasattr(record, 'total_tokens'):
            log_data['total_tokens'] = record.total_tokens
        
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        
        if hasattr(record, 'error_message'):
            log_data['error_message'] = record.error_message
        
        if hasattr(record, 'retry_attempt'):
            log_data['retry_attempt'] = record.retry_attempt
        
        if hasattr(record, 'max_retries'):
            log_data['max_retries'] = record.max_retries
        
        if hasattr(record, 'batch_size'):
            log_data['batch_size'] = record.batch_size
        
        if hasattr(record, 'message_count'):
            log_data['message_count'] = record.message_count
        
        if hasattr(record, 'temperature'):
            log_data['temperature'] = record.temperature
        
        if hasattr(record, 'max_tokens'):
            log_data['max_tokens'] = record.max_tokens
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加堆栈信息（如果有）
        if record.stack_info:
            log_data['stack_info'] = self.formatStack(record.stack_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def configure_logging(use_json: bool = True, level: int = logging.INFO) -> None:
    """
    配置应用日志
    
    Args:
        use_json: 是否使用 JSON 格式（生产环境推荐）
        level: 日志级别
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 设置格式化器
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
