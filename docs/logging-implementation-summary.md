# 结构化日志记录实现总结

## 任务概述

任务 7.1：为 DeepSeek LLM 支持实现结构化日志记录功能。

## 实现内容

### 1. JSON 日志格式化器（`api/logging_config.py`）

创建了 `JSONFormatter` 类，将日志记录转换为 JSON 格式：

**功能特性：**
- ✅ 使用 ISO 8601 格式的 UTC 时间戳
- ✅ 包含基础字段：timestamp, level, logger, message
- ✅ 支持扩展字段：event, model, user_email, execution_time 等
- ✅ 自动处理异常信息和堆栈跟踪
- ✅ 支持所有 LLM 调用相关的字段

**支持的日志字段：**
```json
{
  "timestamp": "2026-03-03T04:21:17.571616+00:00",
  "level": "INFO",
  "logger": "api.llm_utils",
  "message": "LLM 调用成功",
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
```

### 2. 日志配置函数（`api/logging_config.py`）

实现了 `configure_logging()` 函数：

**功能特性：**
- ✅ 支持 JSON 和文本两种格式
- ✅ 可配置日志级别
- ✅ 清除现有处理器避免重复日志
- ✅ 输出到标准输出（stdout）

**使用方式：**
```python
from api.logging_config import configure_logging

# 启用 JSON 日志（生产环境推荐）
configure_logging(use_json=True, level=logging.INFO)

# 使用文本日志（开发环境）
configure_logging(use_json=False, level=logging.DEBUG)
```

### 3. 应用启动配置（`api/app_factory.py`）

更新了应用工厂以使用新的日志配置：

**功能特性：**
- ✅ 通过环境变量 `USE_JSON_LOGS` 控制日志格式
- ✅ 默认启用 JSON 日志（生产环境友好）
- ✅ 在应用启动时自动配置日志

**环境变量：**
```bash
# 启用 JSON 日志（默认）
USE_JSON_LOGS=true

# 禁用 JSON 日志，使用文本格式
USE_JSON_LOGS=false
```

### 4. LLM 调用日志增强（`api/llm_utils.py`）

更新了 LLM 调用函数的日志记录：

**改进内容：**
- ✅ 记录请求参数（temperature, max_tokens）
- ✅ 记录模型名称
- ✅ 记录执行时间
- ✅ 记录 Token 使用量（prompt_tokens, completion_tokens, total_tokens）
- ✅ 记录错误类型和错误消息
- ✅ 支持批量调用的日志记录

**日志事件类型：**
- `llm_call_start` - LLM 调用开始
- `llm_call_success` - LLM 调用成功
- `llm_call_error` - LLM 调用失败
- `llm_batch_call_start` - 批量调用开始
- `llm_batch_call_success` - 批量调用成功
- `llm_batch_call_error` - 批量调用失败
- `llm_sync_call_start` - 同步调用开始
- `llm_sync_call_success` - 同步调用成功
- `llm_sync_call_error` - 同步调用失败

### 5. 安全性保障

**已实现的安全措施：**
- ✅ 日志中不记录完整的 API Key
- ✅ 日志中不记录敏感的用户数据
- ✅ 使用 `mask_api_key()` 函数遮蔽 API Key（在其他模块中）
- ✅ JSONFormatter 只记录预定义的字段，不会泄露额外信息

### 6. 测试覆盖（`tests/test_logging.py`）

创建了全面的测试套件：

**测试类别：**

1. **TestJSONFormatter** - JSON 格式化器测试
   - ✅ 基础日志格式化
   - ✅ LLM 调用日志格式化
   - ✅ 错误日志格式化
   - ✅ 批量调用日志格式化

2. **TestLoggingConfiguration** - 日志配置测试
   - ✅ JSON 日志配置
   - ✅ 文本日志配置

3. **TestLogSecurity** - 日志安全性测试
   - ✅ 验证日志中不包含 API Key
   - ✅ 验证日志包含所有必需字段
   - ✅ 验证时间戳格式

**测试结果：**
```
9 passed in 0.35s
```

### 7. 验证脚本（`verify_logging.py`）

创建了演示脚本，展示各种日志场景：

**演示内容：**
- ✅ 基础日志记录
- ✅ LLM 调用成功日志
- ✅ LLM 调用错误日志
- ✅ 批量调用日志
- ✅ 日志安全性验证

## 需求验证

### 需求 8.1 - 记录模型名称和请求参数
✅ **已实现** - 日志中包含 `model`, `temperature`, `max_tokens` 等字段

### 需求 8.2 - 记录响应时间
✅ **已实现** - 日志中包含 `execution_time` 字段（单位：秒）

### 需求 8.3 - 记录 Token 使用量
✅ **已实现** - 日志中包含 `prompt_tokens`, `completion_tokens`, `total_tokens` 字段

### 需求 8.4 - 使用 JSON 格式
✅ **已实现** - 实现了 `JSONFormatter` 类，所有日志都以 JSON 格式输出

### 需求 8.5 - 添加事件类型标识
✅ **已实现** - 日志中包含 `event` 字段，标识不同的事件类型

### 需求 8.7 - 不记录完整的 API Key
✅ **已实现** - 日志记录器不包含 `api_key` 字段，确保安全性

## 使用示例

### 在代码中使用

```python
import logging
from api.llm_utils import call_completion

logger = logging.getLogger(__name__)

# LLM 调用会自动记录日志
response = await call_completion(
    messages=[{"role": "user", "content": "查询用户"}],
    user_email="user@example.com",
    temperature=0.7,
    max_tokens=2000
)

# 日志输出示例：
# {
#   "timestamp": "2026-03-03T04:21:17+00:00",
#   "level": "INFO",
#   "logger": "api.llm_utils",
#   "message": "LLM 调用成功",
#   "event": "llm_call_success",
#   "model": "deepseek/deepseek-chat",
#   "user_email": "user@example.com",
#   "execution_time": 1.234,
#   "prompt_tokens": 100,
#   "completion_tokens": 50,
#   "total_tokens": 150,
#   "temperature": 0.7,
#   "max_tokens": 2000
# }
```

### 配置日志格式

通过环境变量控制：

```bash
# .env 文件
USE_JSON_LOGS=true  # 启用 JSON 日志（生产环境）
# USE_JSON_LOGS=false  # 使用文本日志（开发环境）
```

## 日志收集和分析

### 与日志收集系统集成

JSON 格式的日志可以轻松集成到各种日志收集系统：

**ELK Stack（Elasticsearch + Logstash + Kibana）：**
```bash
# Logstash 配置示例
input {
  file {
    path => "/var/log/queryweaver/*.log"
    codec => json
  }
}

filter {
  # JSON 已经解析，无需额外处理
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "queryweaver-logs-%{+YYYY.MM.dd}"
  }
}
```

**Grafana Loki：**
```yaml
# Promtail 配置示例
scrape_configs:
  - job_name: queryweaver
    static_configs:
      - targets:
          - localhost
        labels:
          job: queryweaver
          __path__: /var/log/queryweaver/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            event: event
            model: model
```

### 常用查询示例

**查询所有 LLM 调用错误：**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event": "llm_call_error" } }
      ]
    }
  }
}
```

**统计 Token 使用量：**
```json
{
  "aggs": {
    "total_tokens": {
      "sum": { "field": "total_tokens" }
    },
    "by_model": {
      "terms": { "field": "model" },
      "aggs": {
        "tokens": { "sum": { "field": "total_tokens" } }
      }
    }
  }
}
```

**分析响应时间：**
```json
{
  "aggs": {
    "response_time_stats": {
      "stats": { "field": "execution_time" }
    },
    "response_time_percentiles": {
      "percentiles": {
        "field": "execution_time",
        "percents": [50, 95, 99]
      }
    }
  }
}
```

## 性能影响

### JSON 序列化开销

- JSON 格式化比文本格式略慢（约 10-20%）
- 对于高频日志场景，建议使用异步日志处理
- 生产环境的可观测性收益远大于性能开销

### 优化建议

1. **使用合适的日志级别**
   ```python
   # 生产环境使用 INFO 或 WARNING
   configure_logging(use_json=True, level=logging.INFO)
   
   # 开发环境可以使用 DEBUG
   configure_logging(use_json=False, level=logging.DEBUG)
   ```

2. **避免记录大量数据**
   ```python
   # ❌ 不好：记录完整的消息内容
   logger.info("处理消息", extra={"messages": messages})
   
   # ✅ 好：只记录消息数量
   logger.info("处理消息", extra={"message_count": len(messages)})
   ```

3. **使用异步日志处理器**（未来优化）
   ```python
   # 可以考虑使用 QueueHandler 进行异步日志处理
   from logging.handlers import QueueHandler
   ```

## 后续改进建议

### 短期改进（P1）

1. **添加日志采样**
   - 对于高频日志，实现采样机制
   - 例如：每 100 次调用只记录 1 次详细日志

2. **添加日志轮转**
   - 实现日志文件轮转（按大小或时间）
   - 避免日志文件过大

3. **添加结构化错误追踪**
   - 集成 Sentry 或类似服务
   - 自动捕获和报告异常

### 长期改进（P2）

1. **实现分布式追踪**
   - 添加 trace_id 和 span_id
   - 集成 OpenTelemetry

2. **添加日志聚合**
   - 实现日志聚合和去重
   - 减少重复日志的存储

3. **添加日志告警**
   - 基于日志模式的自动告警
   - 集成 PagerDuty 或类似服务

## 总结

任务 7.1 已成功完成，实现了符合设计文档要求的结构化日志记录功能：

✅ **功能完整性**
- 实现了 JSON 格式的日志输出
- 记录了所有必需的字段（模型名称、请求参数、响应时间、Token 使用量）
- 支持多种日志事件类型

✅ **安全性**
- 日志中不包含敏感信息（API Key）
- 实现了字段白名单机制

✅ **可测试性**
- 创建了全面的测试套件
- 所有测试都通过

✅ **可维护性**
- 代码结构清晰，易于扩展
- 提供了详细的文档和示例

✅ **生产就绪**
- 支持环境变量配置
- 兼容主流日志收集系统
- 性能影响可控

该实现为 QueryWeaver 项目提供了强大的可观测性基础，有助于监控系统运行状况、诊断问题和优化性能。
