# 需求文档

## 引言

QueryWeaver 是一个开源的 Text2SQL 工具，通过图驱动的模式理解技术将自然语言问题转换为精确的 SQL 查询。当前界面主要使用英文，为了更好地服务中文用户群体，需要将整个交互界面本地化为中文。本需求文档定义了中文界面本地化的完整功能需求。

## 术语表

- **System**: QueryWeaver 前端应用系统
- **User**: 使用 QueryWeaver 的最终用户
- **i18n**: 国际化 (Internationalization) 的缩写
- **Locale**: 语言区域设置
- **Translation_Key**: 翻译键，用于标识需要翻译的文本
- **Language_Switcher**: 语言切换器组件
- **Localization_Context**: 本地化上下文，管理当前语言状态
- **Format_Function**: 格式化函数，用于处理日期、数字等本地化格式

## 需求

### 需求 1: 国际化框架集成

**用户故事**: 作为开发者，我希望集成一个成熟的国际化框架，以便系统能够支持多语言切换和文本翻译。

#### 验收标准

1. THE System SHALL 集成 react-i18next 或 react-intl 国际化库
2. THE System SHALL 创建 Localization_Context 用于管理当前语言状态
3. THE System SHALL 提供 Translation_Key 到翻译文本的映射机制
4. THE System SHALL 支持动态加载语言资源文件
5. THE System SHALL 在应用启动时初始化默认语言为中文

### 需求 2: 界面文本中文化

**用户故事**: 作为用户，我希望看到所有界面文本都是中文，以便我能够更容易地理解和使用系统。

#### 验收标准

1. WHEN User 访问任何页面 THEN THE System SHALL 显示中文界面文本
2. THE System SHALL 翻译所有按钮文本为中文
3. THE System SHALL 翻译所有标签和提示文本为中文
4. THE System SHALL 翻译所有占位符文本为中文
5. THE System SHALL 翻译所有导航菜单项为中文
6. THE System SHALL 翻译所有模态框标题和描述为中文
7. THE System SHALL 翻译所有表单字段标签为中文
8. THE System SHALL 翻译所有状态徽章文本为中文

### 需求 3: 错误消息和提示信息中文化

**用户故事**: 作为用户，我希望所有错误消息和提示信息都是中文，以便我能够快速理解问题并采取行动。

#### 验收标准

1. WHEN 系统发生错误 THEN THE System SHALL 显示中文错误消息
2. THE System SHALL 翻译所有 Toast 通知消息为中文
3. THE System SHALL 翻译所有验证错误消息为中文
4. THE System SHALL 翻译所有成功提示消息为中文
5. THE System SHALL 翻译所有警告消息为中文
6. THE System SHALL 翻译所有确认对话框消息为中文
7. THE System SHALL 翻译所有加载状态文本为中文
8. THE System SHALL 翻译所有空状态提示文本为中文

### 需求 4: 日期时间格式本地化

**用户故事**: 作为用户，我希望日期和时间以中文习惯的格式显示，以便我能够更自然地阅读时间信息。

#### 验收标准

1. THE System SHALL 使用中文日期格式 (YYYY年MM月DD日)
2. THE System SHALL 使用 24 小时制时间格式
3. WHEN 显示相对时间 THEN THE System SHALL 使用中文表达 (如 "刚刚"、"5分钟前"、"昨天")
4. THE System SHALL 使用中文星期表示 (如 "星期一"、"星期二")
5. THE System SHALL 在时间戳中包含中文时区信息

### 需求 5: 数字格式本地化

**用户故事**: 作为用户，我希望数字以中文习惯的格式显示，以便我能够更容易地阅读数值信息。

#### 验收标准

1. THE System SHALL 使用中文千位分隔符格式化大数字
2. THE System SHALL 使用中文小数点格式 (使用 "." 作为小数点)
3. WHEN 显示货币 THEN THE System SHALL 使用人民币符号 (¥)
4. WHEN 显示百分比 THEN THE System SHALL 在数字后添加 "%" 符号
5. THE System SHALL 支持中文数字单位 (如 "万"、"亿")

### 需求 6: 语言切换功能

**用户故事**: 作为用户，我希望能够在中文和英文之间切换，以便根据我的偏好选择界面语言。

#### 验收标准

1. THE System SHALL 提供 Language_Switcher 组件
2. WHEN User 点击 Language_Switcher THEN THE System SHALL 显示可用语言列表
3. WHEN User 选择语言 THEN THE System SHALL 立即切换界面语言
4. THE System SHALL 将用户的语言偏好保存到 localStorage
5. WHEN User 重新访问应用 THEN THE System SHALL 加载用户上次选择的语言
6. THE System SHALL 在 Language_Switcher 中显示当前选中的语言
7. THE System SHALL 支持至少中文和英文两种语言

### 需求 7: 翻译资源管理

**用户故事**: 作为开发者，我希望翻译资源以结构化的方式组织，以便易于维护和扩展。

#### 验收标准

1. THE System SHALL 将翻译资源存储在独立的 JSON 文件中
2. THE System SHALL 按功能模块组织翻译键 (如 common、auth、database、chat)
3. THE System SHALL 为每种语言创建独立的翻译文件
4. THE System SHALL 支持嵌套的翻译键结构
5. THE System SHALL 提供默认翻译文本以处理缺失的翻译键
6. THE System SHALL 在开发模式下显示缺失翻译键的警告

### 需求 8: 动态内容本地化

**用户故事**: 作为用户，我希望动态生成的内容也能正确本地化，以便获得一致的用户体验。

#### 验收标准

1. WHEN 显示查询建议 THEN THE System SHALL 使用中文建议文本
2. WHEN 显示 SQL 查询步骤 THEN THE System SHALL 使用中文描述
3. WHEN 显示数据库连接状态 THEN THE System SHALL 使用中文状态文本
4. WHEN 显示查询结果表头 THEN THE System SHALL 使用中文列名 (如果可能)
5. THE System SHALL 支持插值变量的本地化 (如 "已连接: {databaseName}")

### 需求 9: 可访问性支持

**用户故事**: 作为使用辅助技术的用户，我希望本地化后的界面仍然保持良好的可访问性，以便我能够正常使用系统。

#### 验收标准

1. THE System SHALL 翻译所有 aria-label 属性为中文
2. THE System SHALL 翻译所有 aria-describedby 引用的文本为中文
3. THE System SHALL 翻译所有 title 属性为中文
4. THE System SHALL 翻译所有 placeholder 属性为中文
5. THE System SHALL 确保屏幕阅读器能够正确读取中文文本

### 需求 10: 文档更新

**用户故事**: 作为开发者或用户，我希望文档能够反映中文界面的变化，以便了解如何使用和维护本地化功能。

#### 验收标准

1. THE System SHALL 更新 README 文档说明中文界面支持
2. THE System SHALL 创建本地化开发指南文档
3. THE System SHALL 记录翻译键命名规范
4. THE System SHALL 提供添加新翻译的步骤说明
5. THE System SHALL 记录语言切换功能的使用方法
6. THE System SHALL 提供翻译贡献指南

### 需求 11: 性能优化

**用户故事**: 作为用户，我希望语言切换和本地化不会影响应用性能，以便获得流畅的使用体验。

#### 验收标准

1. THE System SHALL 懒加载语言资源文件
2. THE System SHALL 缓存已加载的翻译资源
3. WHEN User 切换语言 THEN THE System SHALL 在 500ms 内完成切换
4. THE System SHALL 避免不必要的组件重新渲染
5. THE System SHALL 使用 React.memo 优化翻译组件性能

### 需求 12: 后端 API 响应本地化

**用户故事**: 作为用户，我希望后端返回的消息也能以中文显示，以便获得一致的用户体验。

#### 验收标准

1. WHEN 后端返回错误消息 THEN THE System SHALL 将其翻译为中文
2. THE System SHALL 映射常见的后端错误代码到中文消息
3. THE System SHALL 处理后端返回的英文消息并翻译为中文
4. THE System SHALL 保留技术错误详情的原始英文文本 (在开发者模式下)
5. THE System SHALL 为数据库连接错误提供友好的中文提示

### 需求 13: 测试覆盖

**用户故事**: 作为开发者，我希望本地化功能有完整的测试覆盖，以便确保翻译的正确性和功能的稳定性。

#### 验收标准

1. THE System SHALL 为每个翻译键提供单元测试
2. THE System SHALL 测试语言切换功能
3. THE System SHALL 测试日期时间格式化函数
4. THE System SHALL 测试数字格式化函数
5. THE System SHALL 测试缺失翻译键的降级处理
6. THE System SHALL 进行端到端测试验证完整的本地化流程

### 需求 14: 浏览器语言检测

**用户故事**: 作为用户，我希望系统能够自动检测我的浏览器语言设置，以便默认显示我偏好的语言。

#### 验收标准

1. WHEN User 首次访问应用 THEN THE System SHALL 检测浏览器语言设置
2. IF 浏览器语言为中文 THEN THE System SHALL 默认使用中文界面
3. IF 浏览器语言为英文 THEN THE System SHALL 默认使用英文界面
4. IF 浏览器语言不受支持 THEN THE System SHALL 默认使用中文界面
5. THE System SHALL 允许用户手动覆盖自动检测的语言

### 需求 15: 翻译质量保证

**用户故事**: 作为用户，我希望翻译准确且符合中文表达习惯，以便获得自然流畅的使用体验。

#### 验收标准

1. THE System SHALL 使用专业的技术术语翻译
2. THE System SHALL 保持翻译的一致性 (相同概念使用相同翻译)
3. THE System SHALL 使用简洁明了的中文表达
4. THE System SHALL 避免直译导致的生硬表达
5. THE System SHALL 遵循中文标点符号规范 (使用中文标点)
6. THE System SHALL 为专业术语提供中英文对照 (首次出现时)
