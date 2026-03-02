# 需求文档：达梦和人大金仓数据库支持

## 引言

本文档描述了为 QueryWeaver 项目添加达梦数据库(DM Database)和人大金仓数据库(KingbaseES)支持的功能需求。QueryWeaver 是一个开源的 Text2SQL 工具，通过图驱动的模式理解技术，将自然语言问题转换为精确的 SQL 查询。当前系统已支持 PostgreSQL 和 MySQL 数据库，本需求旨在扩展对国产数据库的支持。

## 术语表

- **QueryWeaver**: 开源的 Text2SQL 工具系统
- **DM_Database**: 达梦数据库，国产关系型数据库管理系统
- **KingbaseES**: 人大金仓数据库，基于 PostgreSQL 的国产数据库
- **Loader**: 数据库加载器，负责连接数据库并提取模式信息
- **Schema**: 数据库模式，包括表、列、关系等结构信息
- **Graph_Database**: FalkorDB 图数据库，用于存储和查询数据库模式
- **Vector_Embedding**: 向量嵌入，用于语义相似度搜索
- **Foreign_Key**: 外键，表示表之间的引用关系
- **Connection_URL**: 数据库连接字符串，格式为 protocol://username:password@host:port/database

## 需求

### 需求 1：达梦数据库连接支持

**用户故事：** 作为用户，我希望能够连接到达梦数据库，以便使用 QueryWeaver 对达梦数据库进行自然语言查询。

#### 验收标准

1. WHEN 用户提供达梦数据库连接 URL，THE System SHALL 识别 URL 格式并选择达梦数据库加载器
2. WHEN 达梦数据库加载器建立连接，THE System SHALL 验证连接参数并成功连接到数据库
3. WHEN 连接失败，THE System SHALL 返回清晰的错误信息说明失败原因
4. THE System SHALL 支持标准的达梦数据库连接 URL 格式：dm://username:password@host:port/database
5. WHEN 连接成功，THE System SHALL 记录连接日志包含用户 ID、数据库名称和连接时间

### 需求 2：达梦数据库模式提取

**用户故事：** 作为用户，我希望系统能够自动提取达梦数据库的表结构信息，以便系统理解数据库模式并生成准确的 SQL 查询。

#### 验收标准

1. WHEN 连接到达梦数据库，THE System SHALL 提取所有用户表的名称和注释
2. WHEN 提取表信息，THE System SHALL 获取每个表的所有列信息包括列名、数据类型、是否可空、默认值和注释
3. WHEN 提取列信息，THE System SHALL 识别主键列并标记为 PRIMARY KEY
4. WHEN 提取列信息，THE System SHALL 识别外键列并标记为 FOREIGN KEY
5. WHEN 提取外键信息，THE System SHALL 记录外键约束名称、源列、引用表和引用列
6. WHEN 提取索引信息，THE System SHALL 获取表的所有索引包括索引名称、索引列和索引类型
7. THE System SHALL 为每个列提取最多 3 个示例值用于增强列描述
8. WHEN 提取过程中发生错误，THE System SHALL 记录详细错误日志并继续处理其他表

### 需求 3：达梦数据库查询执行

**用户故事：** 作为用户，我希望系统能够在达梦数据库上执行生成的 SQL 查询，以便获取查询结果。

#### 验收标准

1. WHEN 系统生成 SQL 查询，THE System SHALL 使用达梦数据库驱动执行查询
2. WHEN 执行 SELECT 查询，THE System SHALL 返回查询结果包括列名和数据行
3. WHEN 查询结果包含日期时间类型，THE System SHALL 将其序列化为 ISO 8601 格式字符串
4. WHEN 查询结果包含 DECIMAL 类型，THE System SHALL 将其转换为浮点数
5. WHEN 查询执行超时，THE System SHALL 取消查询并返回超时错误
6. WHEN 查询执行失败，THE System SHALL 返回数据库错误信息
7. THE System SHALL 记录查询执行时间和返回行数

### 需求 4：人大金仓数据库连接支持

**用户故事：** 作为用户，我希望能够连接到人大金仓数据库，以便使用 QueryWeaver 对人大金仓数据库进行自然语言查询。

#### 验收标准

1. WHEN 用户提供人大金仓数据库连接 URL，THE System SHALL 识别 URL 格式并选择人大金仓数据库加载器
2. WHEN 人大金仓数据库加载器建立连接，THE System SHALL 验证连接参数并成功连接到数据库
3. WHEN 连接失败，THE System SHALL 返回清晰的错误信息说明失败原因
4. THE System SHALL 支持标准的人大金仓数据库连接 URL 格式：kingbase://username:password@host:port/database
5. THE System SHALL 支持 PostgreSQL 兼容的连接 URL 格式：postgresql://username:password@host:port/database（当检测到人大金仓特征时）
6. WHEN 连接成功，THE System SHALL 记录连接日志包含用户 ID、数据库名称和连接时间

### 需求 5：人大金仓数据库模式提取

**用户故事：** 作为用户，我希望系统能够自动提取人大金仓数据库的表结构信息，以便系统理解数据库模式并生成准确的 SQL 查询。

#### 验收标准

1. WHEN 连接到人大金仓数据库，THE System SHALL 提取所有用户表的名称和注释
2. WHEN 提取表信息，THE System SHALL 获取每个表的所有列信息包括列名、数据类型、是否可空、默认值和注释
3. WHEN 提取列信息，THE System SHALL 识别主键列并标记为 PRIMARY KEY
4. WHEN 提取列信息，THE System SHALL 识别外键列并标记为 FOREIGN KEY
5. WHEN 提取外键信息，THE System SHALL 记录外键约束名称、源列、引用表和引用列
6. WHEN 提取索引信息，THE System SHALL 获取表的所有索引包括索引名称、索引列和索引类型
7. THE System SHALL 为每个列提取最多 3 个示例值用于增强列描述
8. WHEN 提取过程中发生错误，THE System SHALL 记录详细错误日志并继续处理其他表

### 需求 6：人大金仓数据库查询执行

**用户故事：** 作为用户，我希望系统能够在人大金仓数据库上执行生成的 SQL 查询，以便获取查询结果。

#### 验收标准

1. WHEN 系统生成 SQL 查询，THE System SHALL 使用人大金仓数据库驱动执行查询
2. WHEN 执行 SELECT 查询，THE System SHALL 返回查询结果包括列名和数据行
3. WHEN 查询结果包含日期时间类型，THE System SHALL 将其序列化为 ISO 8601 格式字符串
4. WHEN 查询结果包含 DECIMAL 类型，THE System SHALL 将其转换为浮点数
5. WHEN 查询执行超时，THE System SHALL 取消查询并返回超时错误
6. WHEN 查询执行失败，THE System SHALL 返回数据库错误信息
7. THE System SHALL 记录查询执行时间和返回行数

### 需求 7：图数据库模式加载

**用户故事：** 作为系统，我希望将提取的数据库模式加载到 FalkorDB 图数据库中，以便支持基于向量嵌入的语义搜索和关系推理。

#### 验收标准

1. WHEN 模式提取完成，THE System SHALL 为每个表创建 Table 节点包含表名、描述和向量嵌入
2. WHEN 创建表节点，THE System SHALL 为每个列创建 Column 节点包含列名、数据类型、描述和向量嵌入
3. WHEN 创建列节点，THE System SHALL 创建 BELONGS_TO 关系连接列到表
4. WHEN 存在外键关系，THE System SHALL 创建 REFERENCES 关系连接源列到目标列
5. THE System SHALL 使用 LLM 生成表和列的自然语言描述
6. THE System SHALL 使用嵌入模型将描述转换为向量嵌入
7. WHEN 加载过程显示进度，THE System SHALL 流式返回进度消息包括当前步骤和完成百分比

### 需求 8：模式修改检测和刷新

**用户故事：** 作为用户，我希望当数据库模式发生变化时，系统能够检测并刷新图数据库中的模式信息，以便查询始终基于最新的数据库结构。

#### 验收标准

1. WHEN 执行 SQL 查询，THE System SHALL 检测查询是否包含模式修改操作（CREATE、ALTER、DROP、TRUNCATE）
2. WHEN 检测到模式修改操作，THE System SHALL 在执行后自动触发模式刷新
3. WHEN 用户手动请求刷新，THE System SHALL 清除现有图数据并重新加载模式
4. WHEN 刷新过程中，THE System SHALL 流式返回进度消息
5. WHEN 刷新完成，THE System SHALL 返回成功消息包含表数量统计
6. WHEN 刷新失败，THE System SHALL 返回错误信息并保留原有图数据

### 需求 9：SQL 标识符引用处理

**用户故事：** 作为系统，我希望正确处理不同数据库的 SQL 标识符引用规则，以便生成的 SQL 查询在目标数据库上能够正确执行。

#### 验收标准

1. WHEN 生成达梦数据库 SQL 查询，THE System SHALL 使用双引号引用标识符
2. WHEN 生成人大金仓数据库 SQL 查询，THE System SHALL 使用双引号引用标识符
3. WHEN 标识符包含特殊字符或空格，THE System SHALL 强制使用引号
4. WHEN 标识符是 SQL 保留字，THE System SHALL 使用引号
5. THE System SHALL 正确转义标识符中的引号字符

### 需求 10：错误处理和日志记录

**用户故事：** 作为开发者，我希望系统提供详细的错误信息和日志记录，以便快速诊断和解决问题。

#### 验收标准

1. WHEN 发生连接错误，THE System SHALL 记录错误日志包含数据库类型、主机地址和错误详情
2. WHEN 发生查询错误，THE System SHALL 记录错误日志包含 SQL 语句和数据库错误消息
3. WHEN 发生模式提取错误，THE System SHALL 记录错误日志包含表名和错误详情
4. THE System SHALL 使用结构化日志格式包含时间戳、日志级别、事件类型和详细信息
5. WHEN 向用户返回错误，THE System SHALL 提供用户友好的错误消息不暴露敏感信息
6. THE System SHALL 记录所有数据库操作的性能指标包括连接时间、查询执行时间和数据传输量

### 需求 11：数据库驱动依赖管理

**用户故事：** 作为开发者，我希望系统能够正确管理数据库驱动依赖，以便项目能够顺利安装和运行。

#### 验收标准

1. THE System SHALL 在 Pipfile 中声明达梦数据库 Python 驱动依赖
2. THE System SHALL 在 Pipfile 中声明人大金仓数据库 Python 驱动依赖
3. WHEN 安装依赖，THE System SHALL 验证驱动版本兼容性
4. THE System SHALL 在文档中说明如何安装和配置数据库驱动
5. WHEN 驱动不可用，THE System SHALL 返回清晰的错误消息指导用户安装

### 需求 12：单元测试和集成测试

**用户故事：** 作为开发者，我希望有完整的测试覆盖，以便确保新功能的正确性和稳定性。

#### 验收标准

1. THE System SHALL 提供达梦数据库加载器的单元测试覆盖所有公共方法
2. THE System SHALL 提供人大金仓数据库加载器的单元测试覆盖所有公共方法
3. THE System SHALL 提供集成测试验证端到端的数据库连接和查询流程
4. WHEN 运行测试，THE System SHALL 使用模拟数据库或测试容器
5. THE System SHALL 测试错误处理路径包括连接失败、查询失败和超时场景
6. THE System SHALL 测试边界条件包括空表、大表和特殊字符

### 需求 13：文档更新

**用户故事：** 作为用户和开发者，我希望有完整的文档说明如何使用新支持的数据库，以便快速上手。

#### 验收标准

1. THE System SHALL 在 README 文档中列出达梦数据库和人大金仓数据库为支持的数据库类型
2. THE System SHALL 提供达梦数据库连接示例包括 URL 格式和配置说明
3. THE System SHALL 提供人大金仓数据库连接示例包括 URL 格式和配置说明
4. THE System SHALL 说明数据库驱动的安装步骤
5. THE System SHALL 提供故障排查指南包括常见错误和解决方案
6. THE System SHALL 更新 API 文档说明新增的数据库类型参数
