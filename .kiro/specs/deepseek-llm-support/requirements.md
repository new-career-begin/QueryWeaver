# 需求文档：DeepSeek 大模型支持

## 引言

本需求文档描述了为 QueryWeaver 项目添加 DeepSeek 大语言模型支持的功能需求。DeepSeek 是一个国产高性价比的大语言模型，提供与 OpenAI 兼容的 API 接口。通过集成 DeepSeek，QueryWeaver 将为用户提供更多的模型选择，降低使用成本，并支持国产化部署需求。

## 术语表

- **DeepSeek**: 国产大语言模型服务提供商，提供高性价比的 API 服务
- **LiteLLM**: QueryWeaver 使用的多模型统一接口库，支持多种 LLM 提供商
- **Completion_Model**: 用于文本生成和对话的语言模型
- **Embedding_Model**: 用于生成文本向量嵌入的模型
- **API_Key**: 用于认证 DeepSeek API 访问的密钥
- **Model_Provider**: 模型提供商标识符，如 "deepseek", "openai", "azure"
- **Fallback_Mechanism**: 当主模型不可用时自动切换到备用模型的机制
- **Rate_Limiting**: API 调用频率限制，防止超出配额
- **Token_Usage**: 模型调用消耗的 token 数量统计
- **Organizations_Graph**: FalkorDB 中存储用户、身份和配置信息的图数据库

## 需求

### 需求 1：DeepSeek API 配置

**用户故事**: 作为系统管理员，我希望能够配置 DeepSeek API 密钥和模型参数，以便系统可以使用 DeepSeek 服务

#### 验收标准

1. WHEN 系统启动时 THEN System SHALL 从环境变量中读取 DeepSeek API 配置
2. WHEN 环境变量中设置了 DEEPSEEK_API_KEY THEN System SHALL 将 DeepSeek 作为可用的模型提供商
3. WHEN 环境变量中设置了 DEEPSEEK_BASE_URL THEN System SHALL 使用自定义的 API 端点
4. WHERE 用户配置了 DEEPSEEK_COMPLETION_MODEL THEN System SHALL 使用指定的对话模型
5. WHERE 用户配置了 DEEPSEEK_EMBEDDING_MODEL THEN System SHALL 使用指定的嵌入模型
6. WHEN API 密钥为空或无效 THEN System SHALL 记录警告日志并禁用 DeepSeek 提供商
7. THE System SHALL 支持通过 .env 文件配置 DeepSeek 参数

### 需求 2：用户配置界面

**用户故事**: 作为用户，我希望在登录后能够通过可视化界面配置 AI 模型参数，以便无需修改配置文件即可使用 DeepSeek

#### 验收标准

1. WHEN 用户完成 OAuth 登录后 THEN System SHALL 显示 AI 模型配置页面
2. THE System SHALL 在配置页面提供模型提供商选择下拉框（OpenAI、Azure、DeepSeek）
3. WHEN 用户选择 DeepSeek 作为提供商 THEN System SHALL 显示 DeepSeek 特定的配置字段
4. THE System SHALL 提供 API Key 输入框，支持密码遮蔽显示
5. THE System SHALL 提供 API Base URL 输入框，预填充 DeepSeek 默认端点
6. THE System SHALL 提供对话模型选择下拉框，列出可用的 DeepSeek 模型
7. THE System SHALL 提供嵌入模型选择下拉框，列出可用的 DeepSeek 嵌入模型
8. WHEN 用户点击"测试连接"按钮 THEN System SHALL 验证 API Key 有效性并显示测试结果
9. WHEN 用户点击"保存"按钮 THEN System SHALL 将配置保存到 FalkorDB Organizations 图中的用户节点
10. THE System SHALL 在 User 节点上创建或更新 llm_config 属性存储配置信息
11. WHEN 配置保存成功后 THEN System SHALL 关闭配置页面并应用新配置
12. THE System SHALL 提供"跳过配置"选项，使用环境变量或系统默认配置
13. WHEN 用户已有配置时 THEN System SHALL 在设置菜单中提供"AI 模型配置"入口
14. THE System SHALL 加密存储敏感信息（如 API Key）在图数据库中

### 需求 3：模型选择和切换

**用户故事**: 作为用户，我希望能够灵活选择和切换使用 DeepSeek 模型，以便降低使用成本并支持国产化需求

#### 验收标准

1. WHEN 用户创建新的数据库连接时 THEN System SHALL 使用用户配置的 LLM 提供商
2. WHEN 用户选择 DeepSeek 作为提供商 THEN System SHALL 使用 DeepSeek 的对话模型和嵌入模型
3. WHEN 系统配置了多个模型提供商 THEN System SHALL 按照用户配置优先级选择提供商
4. WHERE 用户未配置提供商 THEN System SHALL 使用环境变量或系统默认配置
5. WHEN 用户在设置中切换模型提供商 THEN System SHALL 保持现有的对话上下文和数据库连接
6. THE System SHALL 在用户界面中显示当前使用的模型提供商和模型名称
7. THE System SHALL 支持为不同的数据库连接配置不同的模型提供商

### 需求 4：LiteLLM 集成

**用户故事**: 作为开发者，我希望通过 LiteLLM 统一接口调用 DeepSeek API，以便保持代码的一致性和可维护性

#### 验收标准

1. WHEN 调用 completion 函数时 THEN System SHALL 使用 LiteLLM 的统一接口调用 DeepSeek API
2. WHEN 调用 embedding 函数时 THEN System SHALL 使用 LiteLLM 的统一接口生成向量嵌入
3. WHEN DeepSeek API 返回响应时 THEN System SHALL 将响应转换为 LiteLLM 标准格式
4. THE System SHALL 支持 DeepSeek 的流式响应模式
5. THE System SHALL 支持 DeepSeek 的批量请求功能
6. WHEN LiteLLM 版本更新时 THEN System SHALL 确保与 DeepSeek 集成的兼容性

### 需求 5：错误处理和重试

**用户故事**: 作为用户，我希望系统能够优雅地处理 DeepSeek API 错误，以便在出现问题时获得清晰的反馈

#### 验收标准

1. WHEN DeepSeek API 返回认证错误 THEN System SHALL 记录错误日志并返回用户友好的错误消息
2. WHEN DeepSeek API 返回速率限制错误 THEN System SHALL 使用指数退避策略自动重试
3. WHEN DeepSeek API 返回服务不可用错误 THEN System SHALL 尝试重试最多 3 次
4. IF 所有重试都失败 THEN System SHALL 记录详细错误信息并通知用户
5. WHERE 配置了备用模型提供商 THEN System SHALL 在 DeepSeek 不可用时自动切换到备用提供商
6. WHEN API 调用超时 THEN System SHALL 在 30 秒后取消请求并返回超时错误
7. THE System SHALL 记录所有 API 错误的详细信息用于故障排查

### 需求 6：成本监控和优化

**用户故事**: 作为系统管理员，我希望能够监控 DeepSeek API 的使用情况和成本，以便优化资源使用

#### 验收标准

1. WHEN 调用 DeepSeek API 时 THEN System SHALL 记录请求的 token 使用量
2. WHEN API 调用完成时 THEN System SHALL 记录响应的 token 使用量
3. THE System SHALL 在日志中记录每次 API 调用的 token 统计信息
4. THE System SHALL 支持配置每个用户的 token 使用限额
5. WHEN 用户达到 token 限额 THEN System SHALL 拒绝新的请求并返回限额错误
6. THE System SHALL 提供 API 使用情况的统计报告功能
7. WHERE 可能时 THEN System SHALL 使用缓存减少重复的 API 调用

### 需求 7：模型参数配置

**用户故事**: 作为开发者，我希望能够配置 DeepSeek 模型的参数，以便优化生成质量和性能

#### 验收标准

1. THE System SHALL 支持配置 temperature 参数控制生成的随机性
2. THE System SHALL 支持配置 max_tokens 参数限制生成的长度
3. THE System SHALL 支持配置 top_p 参数控制采样策略
4. THE System SHALL 支持配置 frequency_penalty 参数减少重复内容
5. THE System SHALL 支持配置 presence_penalty 参数鼓励话题多样性
6. WHERE 用户未指定参数 THEN System SHALL 使用针对 Text2SQL 任务优化的默认值
7. THE System SHALL 允许为不同的任务类型配置不同的模型参数

### 需求 8：向量嵌入支持

**用户故事**: 作为系统，我需要使用 DeepSeek 的嵌入模型生成表和列的向量表示，以便支持语义搜索

#### 验收标准

1. WHEN 加载数据库模式时 THEN System SHALL 使用 DeepSeek 嵌入模型生成表描述的向量
2. WHEN 加载数据库模式时 THEN System SHALL 使用 DeepSeek 嵌入模型生成列描述的向量
3. THE System SHALL 确保生成的向量维度与 FalkorDB 向量索引配置一致
4. WHEN 批量生成嵌入时 THEN System SHALL 使用批量 API 提高效率
5. THE System SHALL 缓存已生成的嵌入向量避免重复计算
6. WHEN 嵌入生成失败时 THEN System SHALL 记录错误并使用默认向量或跳过该项
7. THE System SHALL 支持配置嵌入模型的维度大小

### 需求 9：日志和监控

**用户故事**: 作为运维人员，我希望能够监控 DeepSeek API 的调用情况，以便及时发现和解决问题

#### 验收标准

1. WHEN 调用 DeepSeek API 时 THEN System SHALL 记录包含模型名称、请求参数的结构化日志
2. WHEN API 调用完成时 THEN System SHALL 记录响应时间和 token 使用量
3. WHEN API 调用失败时 THEN System SHALL 记录详细的错误信息和堆栈跟踪
4. THE System SHALL 使用 JSON 格式记录所有 DeepSeek 相关的日志
5. THE System SHALL 为 DeepSeek 日志添加特定的事件类型标识
6. THE System SHALL 支持配置日志级别控制日志详细程度
7. THE System SHALL 确保日志中不包含敏感信息（如完整的 API 密钥）

### 需求 10：文档和示例

**用户故事**: 作为用户，我希望有清晰的文档说明如何配置和使用 DeepSeek 模型，以便快速上手

#### 验收标准

1. THE System SHALL 在 README 文件中提供 DeepSeek 配置说明
2. THE System SHALL 在 .env.example 文件中包含 DeepSeek 配置示例
3. THE System SHALL 提供 DeepSeek API 密钥获取指南
4. THE System SHALL 提供 DeepSeek 与其他提供商的对比说明
5. THE System SHALL 提供常见问题和故障排查指南
6. THE System SHALL 提供 DeepSeek 模型参数调优建议
7. THE System SHALL 在 API 文档中说明如何通过 API 指定使用 DeepSeek

### 需求 11：兼容性和迁移

**用户故事**: 作为现有用户，我希望能够无缝切换到 DeepSeek 模型，而不影响现有功能

#### 验收标准

1. WHEN 添加 DeepSeek 支持后 THEN System SHALL 保持与现有 OpenAI 和 Azure 配置的兼容性
2. WHEN 用户从其他提供商切换到 DeepSeek THEN System SHALL 保持现有的数据库连接和图数据
3. THE System SHALL 支持在同一部署中同时配置多个模型提供商
4. WHEN 用户未配置 DeepSeek THEN System SHALL 继续使用原有的默认提供商
5. THE System SHALL 提供配置迁移脚本帮助用户从其他提供商迁移到 DeepSeek
6. THE System SHALL 确保 DeepSeek 生成的 SQL 查询与其他提供商的质量一致
7. THE System SHALL 在版本更新说明中明确标注 DeepSeek 支持的变更

### 需求 12：安全性

**用户故事**: 作为安全管理员，我希望 DeepSeek API 密钥得到安全保护，以防止泄露和滥用

#### 验收标准

1. THE System SHALL 从环境变量而非代码中读取 DeepSeek API 密钥
2. THE System SHALL 确保 API 密钥不出现在日志输出中
3. THE System SHALL 确保 API 密钥不出现在错误消息中
4. THE System SHALL 确保 API 密钥不出现在前端代码或响应中
5. WHERE 可能时 THEN System SHALL 使用加密存储 API 密钥
6. THE System SHALL 支持定期轮换 API 密钥
7. THE System SHALL 在 API 密钥泄露时提供撤销和更新机制

### 需求 13：性能优化

**用户故事**: 作为用户，我希望使用 DeepSeek 时系统响应速度快，以便获得良好的使用体验

#### 验收标准

1. WHEN 使用 DeepSeek 生成 SQL 时 THEN System SHALL 在 5 秒内返回结果（P95）
2. WHEN 使用 DeepSeek 生成嵌入时 THEN System SHALL 使用批量 API 减少请求次数
3. THE System SHALL 缓存常用的 prompt 模板避免重复构建
4. THE System SHALL 使用连接池管理 HTTP 连接提高效率
5. WHERE 可能时 THEN System SHALL 使用流式响应提供即时反馈
6. THE System SHALL 并发处理多个独立的 API 请求
7. THE System SHALL 监控 API 响应时间并在性能下降时发出告警
