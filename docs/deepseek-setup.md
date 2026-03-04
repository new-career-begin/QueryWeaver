# DeepSeek 配置指南

## 概述

DeepSeek 是一个高性能、高性价比的国产大语言模型服务提供商，提供与 OpenAI 兼容的 API 接口。本指南将帮助您在 QueryWeaver 中配置和使用 DeepSeek 模型。

### 为什么选择 DeepSeek？

- **成本优势**：比 OpenAI 便宜约 90%，大幅降低使用成本
- **高性能**：在中英文任务上表现优异，特别适合 Text2SQL 场景
- **国产化支持**：支持国产化部署需求，数据安全可控
- **兼容性好**：提供 OpenAI 兼容的 API，无需修改代码即可切换
- **响应快速**：国内访问速度快，延迟低

### 支持的模型

#### 对话模型（Completion Models）

1. **deepseek-chat**（推荐）
   - 用途：通用对话和文本生成
   - 特点：平衡性能和成本，适合大多数场景
   - 上下文长度：32K tokens
   - 定价：约 ¥0.001/1K tokens（输入）

2. **deepseek-coder**
   - 用途：代码生成和技术问答
   - 特点：针对代码任务优化，SQL 生成效果更好
   - 上下文长度：32K tokens
   - 定价：约 ¥0.001/1K tokens（输入）

#### 嵌入模型（Embedding Models）

目前 DeepSeek 的嵌入模型尚未公开发布，QueryWeaver 暂时使用 OpenAI 的 `text-embedding-ada-002` 作为嵌入模型。

## 快速开始

### 步骤 1：获取 DeepSeek API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 点击右上角"注册/登录"
3. 支持以下注册方式：
   - 手机号注册（支持中国大陆手机号）
   - 邮箱注册
4. 完成注册后，进入控制台
5. 在左侧菜单中选择"API Keys"
6. 点击"创建新密钥"按钮
7. 为密钥设置一个名称（如 "QueryWeaver"）
8. 复制生成的 API Key（格式：`sk-xxxxxxxxxxxxxxxx`）
9. **重要**：妥善保管 API Key，不要泄露给他人

### 步骤 2：配置 QueryWeaver

QueryWeaver 提供两种配置方式：

#### 方式 1：通过 Web 界面配置（推荐）

这是最简单的配置方式，无需修改配置文件或重启服务。

1. 启动 QueryWeaver 并登录
2. 点击右上角的用户头像，选择"设置"
3. 在设置页面中找到"AI 模型配置"部分
4. 点击"配置 AI 模型"或"修改配置"按钮
5. 在弹出的配置对话框中：
   - **模型提供商**：选择"DeepSeek（推荐，高性价比）"
   - **API Key**：粘贴您的 DeepSeek API Key
   - **API 端点**：保持默认值 `https://api.deepseek.com`
   - **对话模型**：选择 `deepseek-chat` 或 `deepseek-coder`
   - **嵌入模型**：保持默认值 `text-embedding-ada-002`
6. 点击"测试连接"按钮验证配置
7. 如果测试成功，点击"保存配置"

配置保存后立即生效，无需重启服务。

#### 方式 2：通过环境变量配置

适合系统管理员或需要批量部署的场景。

1. 复制环境变量示例文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，添加以下配置：
   ```bash
   # DeepSeek API 配置
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   DEEPSEEK_COMPLETION_MODEL=deepseek-chat
   DEEPSEEK_EMBEDDING_MODEL=text-embedding-ada-002
   
   # 加密密钥（用于 Web 界面配置的安全存储）
   LLM_CONFIG_ENCRYPTION_KEY=your-32-byte-base64-encoded-key
   ```

3. 生成加密密钥（可选，但推荐）：
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. 重启 QueryWeaver 服务：
   ```bash
   # Docker 方式
   docker restart queryweaver
   
   # 源码方式
   make run-dev
   ```

### 步骤 3：验证配置

1. 在 QueryWeaver 中连接一个数据库
2. 在聊天框中输入一个简单的查询，例如：
   - "显示所有表"
   - "查询用户表的前 10 条记录"
3. 观察系统是否正常生成 SQL 并返回结果
4. 检查日志中是否有 DeepSeek API 调用记录

## 配置优先级

QueryWeaver 按以下优先级加载 LLM 配置：

1. **用户配置**（最高优先级）
   - 通过 Web 界面设置的配置
   - 存储在 FalkorDB 中，加密保存
   - 每个用户可以有独立的配置

2. **环境变量**
   - 在 `.env` 文件或系统环境中设置
   - 作为系统默认配置
   - 所有用户共享

3. **系统默认值**（最低优先级）
   - 在 `api/config.py` 中定义
   - 当没有其他配置时使用
   - 默认使用 Azure OpenAI

### 配置示例场景

#### 场景 1：所有用户使用 DeepSeek
设置环境变量：
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

#### 场景 2：部分用户使用 DeepSeek，部分用户使用 OpenAI
1. 不设置环境变量（或设置默认提供商）
2. 让用户通过 Web 界面自行配置

#### 场景 3：测试环境使用 DeepSeek，生产环境使用 Azure
使用不同的 `.env` 文件：
```bash
# .env.test
DEEPSEEK_API_KEY=sk-test-key

# .env.prod
AZURE_API_KEY=your-azure-key
```

## 模型参数调优

### 推荐参数配置

对于 Text2SQL 任务，推荐以下参数配置：

```python
{
    "temperature": 0.7,      # 控制生成的随机性，0.7 平衡创造性和准确性
    "max_tokens": 2000,      # 最大生成长度，足够生成复杂 SQL
    "top_p": 0.9,            # 核采样参数，保持多样性
    "frequency_penalty": 0.0, # 频率惩罚，0 表示不惩罚重复
    "presence_penalty": 0.0   # 存在惩罚，0 表示不鼓励新话题
}
```

### 参数说明

#### temperature（温度）
- **范围**：0.0 - 2.0
- **默认值**：0.7
- **说明**：
  - 较低值（0.0-0.5）：生成更确定、保守的结果，适合需要精确答案的场景
  - 中等值（0.5-1.0）：平衡创造性和准确性，推荐用于 Text2SQL
  - 较高值（1.0-2.0）：生成更有创造性、多样化的结果，可能不够准确

#### max_tokens（最大令牌数）
- **范围**：1 - 32768
- **默认值**：2000
- **说明**：
  - 限制生成的最大长度
  - Text2SQL 通常不需要很长的输出，2000 已足够
  - 设置过大会增加成本和延迟

#### top_p（核采样）
- **范围**：0.0 - 1.0
- **默认值**：0.9
- **说明**：
  - 控制采样的多样性
  - 0.9 表示从累积概率达到 90% 的词中采样
  - 与 temperature 配合使用

#### frequency_penalty（频率惩罚）
- **范围**：-2.0 - 2.0
- **默认值**：0.0
- **说明**：
  - 正值会减少重复内容
  - Text2SQL 场景建议保持 0.0，因为 SQL 语法本身就有重复

#### presence_penalty（存在惩罚）
- **范围**：-2.0 - 2.0
- **默认值**：0.0
- **说明**：
  - 正值会鼓励模型谈论新话题
  - Text2SQL 场景建议保持 0.0

### 针对不同场景的调优建议

#### 场景 1：简单查询（单表查询）
```python
{
    "temperature": 0.3,      # 降低随机性，提高准确性
    "max_tokens": 1000,      # 简单查询不需要太长
    "top_p": 0.8
}
```

#### 场景 2：复杂查询（多表 JOIN）
```python
{
    "temperature": 0.7,      # 保持一定创造性
    "max_tokens": 3000,      # 复杂查询可能需要更长
    "top_p": 0.9
}
```

#### 场景 3：探索性查询（不确定需求）
```python
{
    "temperature": 0.9,      # 提高创造性
    "max_tokens": 2000,
    "top_p": 0.95
}
```

## 故障排查

### 问题 1：API Key 无效

**症状**：
- 错误消息："Authentication failed" 或 "Invalid API key"
- HTTP 状态码：401

**解决方案**：
1. 检查 API Key 是否正确复制（注意前后空格）
2. 确认 API Key 格式正确（以 `sk-` 开头）
3. 登录 DeepSeek 平台确认 API Key 是否有效
4. 检查 API Key 是否已过期或被删除
5. 尝试重新生成一个新的 API Key

### 问题 2：速率限制错误

**症状**：
- 错误消息："Rate limit exceeded"
- HTTP 状态码：429

**解决方案**：
1. 检查您的 API 配额是否已用完
2. 等待一段时间后重试（系统会自动重试）
3. 升级您的 DeepSeek 账户以获得更高的配额
4. 优化查询频率，避免短时间内大量请求

### 问题 3：连接超时

**症状**：
- 错误消息："Connection timeout" 或 "Request timeout"
- 请求长时间无响应

**解决方案**：
1. 检查网络连接是否正常
2. 确认防火墙没有阻止对 `api.deepseek.com` 的访问
3. 尝试使用代理服务器
4. 检查 DeepSeek 服务状态：https://status.deepseek.com
5. 增加超时时间配置（默认 30 秒）

### 问题 4：生成的 SQL 不正确

**症状**：
- SQL 语法错误
- 查询结果不符合预期
- 选择了错误的表或列

**解决方案**：
1. 检查数据库模式是否正确加载
2. 尝试更详细地描述查询需求
3. 调整 temperature 参数（降低到 0.3-0.5）
4. 切换到 `deepseek-coder` 模型（更适合 SQL 生成）
5. 检查表和列的描述是否准确
6. 使用更具体的查询语句，避免歧义

### 问题 5：嵌入向量生成失败

**症状**：
- 错误消息："Embedding generation failed"
- 模式加载失败

**解决方案**：
1. 确认已配置 OpenAI API Key（用于嵌入）
2. 检查 OpenAI API Key 是否有效
3. 检查网络连接到 OpenAI API
4. 查看日志中的详细错误信息

### 问题 6：配置保存失败

**症状**：
- Web 界面提示"配置保存失败"
- 配置无法持久化

**解决方案**：
1. 检查 FalkorDB 连接是否正常
2. 确认用户已登录且有权限
3. 检查加密密钥是否正确配置
4. 查看后端日志中的错误信息
5. 尝试使用环境变量配置作为替代方案

### 问题 7：Web 界面配置不生效

**症状**：
- 保存配置后仍使用旧的提供商
- 配置显示正确但实际未使用

**解决方案**：
1. 刷新浏览器页面
2. 清除浏览器缓存
3. 检查是否有环境变量覆盖了用户配置
4. 查看后端日志确认配置加载情况
5. 尝试删除配置后重新设置

## 性能优化建议

### 1. 使用批量请求

对于需要生成多个嵌入向量的场景，使用批量 API 可以显著提高性能：

```python
# 不推荐：多次单独调用
for text in texts:
    embedding = generate_embedding(text)

# 推荐：批量调用
embeddings = generate_embeddings_batch(texts)
```

### 2. 启用缓存

QueryWeaver 会自动缓存以下内容：
- 表和列的嵌入向量
- 常用的 Prompt 模板
- 数据库模式信息

确保 FalkorDB 有足够的内存用于缓存。

### 3. 优化 Prompt

- 使用清晰、具体的查询描述
- 提供必要的上下文信息
- 避免过长的 Prompt（超过 1000 tokens）

### 4. 调整超时设置

根据您的网络环境调整超时时间：

```python
# 在 api/config.py 中
API_TIMEOUT = 30  # 秒，根据实际情况调整
```

### 5. 监控 API 使用量

定期检查 API 使用情况：
1. 登录 DeepSeek 平台
2. 查看"使用统计"页面
3. 分析调用频率和成本
4. 根据需要调整配额或优化使用

## 成本估算

### DeepSeek 定价（参考）

- **deepseek-chat**：
  - 输入：¥0.001/1K tokens
  - 输出：¥0.002/1K tokens

- **deepseek-coder**：
  - 输入：¥0.001/1K tokens
  - 输出：¥0.002/1K tokens

### 使用场景成本估算

#### 场景 1：简单查询
- Prompt 长度：约 500 tokens
- 生成长度：约 100 tokens
- 单次成本：约 ¥0.0007
- 1000 次查询：约 ¥0.70

#### 场景 2：复杂查询
- Prompt 长度：约 1500 tokens
- 生成长度：约 300 tokens
- 单次成本：约 ¥0.0021
- 1000 次查询：约 ¥2.10

#### 场景 3：模式加载（嵌入生成）
- 使用 OpenAI API（text-embedding-ada-002）
- 100 个表，每个表 5 列，每列描述 50 tokens
- 总计：约 25,000 tokens
- 成本：约 ¥0.025（一次性）

### 成本优化建议

1. **启用缓存**：避免重复生成相同的嵌入向量
2. **优化 Prompt**：减少不必要的上下文信息
3. **批量处理**：使用批量 API 减少请求次数
4. **设置限额**：为用户设置 token 使用限额
5. **监控使用**：定期检查 API 使用情况，及时发现异常

## 安全最佳实践

### 1. API Key 管理

- ✅ **推荐做法**：
  - 使用环境变量存储 API Key
  - 通过 Web 界面配置（自动加密）
  - 定期轮换 API Key
  - 为不同环境使用不同的 API Key

- ❌ **避免做法**：
  - 将 API Key 硬编码在代码中
  - 将 API Key 提交到版本控制系统
  - 在日志中记录完整的 API Key
  - 与他人共享 API Key

### 2. 加密存储

确保配置了加密密钥：

```bash
# 生成安全的加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 在 .env 中配置
LLM_CONFIG_ENCRYPTION_KEY=生成的密钥
```

### 3. 访问控制

- 使用 OAuth 认证确保只有授权用户可以访问
- 为不同用户设置不同的权限级别
- 记录所有 API 调用的审计日志

### 4. 网络安全

- 使用 HTTPS 传输所有数据
- 配置防火墙规则限制访问
- 使用 VPN 或专线连接（企业部署）

### 5. 数据隐私

- 不要在 Prompt 中包含敏感数据
- 定期清理查询历史和日志
- 遵守数据保护法规（如 GDPR）

## 高级配置

### 自定义 API 端点

如果您使用的是 DeepSeek 的私有部署或代理服务，可以自定义 API 端点：

```bash
# 在 .env 中配置
DEEPSEEK_BASE_URL=https://your-custom-endpoint.com
```

或通过 Web 界面在"API 端点"字段中输入自定义 URL。

### 配置代理

如果需要通过代理访问 DeepSeek API：

```bash
# 在 .env 中配置
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```

### 多租户配置

对于多租户部署，可以为不同的租户配置不同的 API Key：

1. 每个租户使用独立的用户账号
2. 通过 Web 界面为每个用户配置独立的 API Key
3. 系统会自动隔离不同用户的配置

### 日志配置

调整 DeepSeek 相关的日志级别：

```python
# 在 api/config.py 中
DEEPSEEK_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 迁移指南

### 从 OpenAI 迁移到 DeepSeek

1. 获取 DeepSeek API Key
2. 通过 Web 界面或环境变量配置 DeepSeek
3. 测试几个查询确保正常工作
4. 逐步切换用户到 DeepSeek
5. 监控查询质量和成本

### 从 Azure OpenAI 迁移到 DeepSeek

1. 备份现有配置
2. 配置 DeepSeek API Key
3. 对比测试查询结果
4. 评估成本节省
5. 决定是否完全切换或混合使用

### 回滚到之前的提供商

如果需要回滚：

1. 通过 Web 界面切换回之前的提供商
2. 或删除 DeepSeek 环境变量
3. 重启服务（如果使用环境变量）
4. 验证功能正常

## 常见问题（FAQ）

### Q1：DeepSeek 支持哪些语言？
A：DeepSeek 支持中文和英文，在两种语言上都有优秀的表现。对于 Text2SQL 任务，中英文查询都能很好地处理。

### Q2：DeepSeek 的响应速度如何？
A：DeepSeek 的响应速度通常在 1-3 秒之间，具体取决于查询复杂度和网络状况。国内访问速度通常优于 OpenAI。

### Q3：可以同时配置多个 LLM 提供商吗？
A：可以。系统支持配置多个提供商，用户可以通过 Web 界面选择使用哪个提供商。

### Q4：DeepSeek 的 API 配额如何计算？
A：DeepSeek 按 token 数量计费，包括输入和输出 tokens。具体配额和定价请查看 DeepSeek 官方文档。

### Q5：如何监控 DeepSeek API 的使用情况？
A：可以通过以下方式监控：
1. DeepSeek 平台的使用统计页面
2. QueryWeaver 的日志文件
3. FalkorDB 中的使用记录

### Q6：DeepSeek 支持流式响应吗？
A：是的，DeepSeek 支持流式响应（Server-Sent Events），QueryWeaver 已经集成了这个功能。

### Q7：如何处理 API 调用失败？
A：QueryWeaver 内置了重试机制，会自动使用指数退避策略重试失败的请求。如果多次重试仍然失败，会返回错误信息给用户。

### Q8：DeepSeek 的模型会定期更新吗？
A：是的，DeepSeek 会定期更新模型。更新后的模型会自动生效，无需修改配置。

### Q9：可以使用 DeepSeek 的微调模型吗？
A：目前 QueryWeaver 支持 DeepSeek 的标准模型。如果您有微调模型，可以通过自定义 API 端点使用。

### Q10：DeepSeek 的数据安全性如何？
A：DeepSeek 承诺不会使用用户数据训练模型。具体的数据安全政策请参考 DeepSeek 官方文档。

## 获取帮助

如果您在配置或使用 DeepSeek 时遇到问题，可以通过以下渠道获取帮助：

1. **查看文档**：
   - QueryWeaver 文档：https://github.com/FalkorDB/QueryWeaver
   - DeepSeek 文档：https://platform.deepseek.com/docs

2. **社区支持**：
   - Discord 社区：https://discord.gg/b32KEzMzce
   - GitHub Issues：https://github.com/FalkorDB/QueryWeaver/issues

3. **技术支持**：
   - DeepSeek 技术支持：support@deepseek.com
   - QueryWeaver 技术支持：通过 GitHub Issues

## 更新日志

### 2025-01-15
- 初始版本发布
- 支持 DeepSeek API 集成
- 支持 Web 界面配置
- 支持环境变量配置

---

**文档版本**：1.0.0  
**最后更新**：2025-01-15  
**维护者**：QueryWeaver 团队
