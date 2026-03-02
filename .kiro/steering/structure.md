---
inclusion: auto
---

# QueryWeaver 项目结构说明

## 项目概览

QueryWeaver 是一个开源的 Text2SQL 工具，采用前后端分离架构，使用图数据库驱动的模式理解技术将自然语言转换为 SQL 查询。

```
QueryWeaver/
├── api/                    # 后端 FastAPI 应用
├── app/                    # 前端 React 应用
├── tests/                  # 测试文件
├── e2e/                    # 端到端测试
├── docs/                   # 项目文档
├── .kiro/                  # Kiro 配置和规范
├── .github/                # GitHub Actions 配置
├── Dockerfile              # Docker 镜像构建
├── Pipfile                 # Python 依赖管理
├── Makefile                # 构建和运行脚本
└── README.md               # 项目说明
```

---

## 后端结构 (api/)

### 目录组织

```
api/
├── agents/                 # AI Agent 模块
│   ├── analysis_agent.py       # 查询分析 Agent
│   ├── follow_up_agent.py      # 后续问题 Agent
│   ├── healer_agent.py         # SQL 修复 Agent
│   ├── relevancy_agent.py      # 相关性判断 Agent
│   ├── response_formatter_agent.py  # 响应格式化 Agent
│   └── utils.py                # Agent 工具函数
│
├── auth/                   # 认证授权模块
│   ├── oauth_handlers.py       # OAuth 处理器 (Google/GitHub)
│   ├── user_management.py      # 用户管理和会话
│   └── __init__.py
│
├── core/                   # 核心业务逻辑
│   ├── errors.py               # 错误定义
│   ├── schema_loader.py        # 数据库模式加载器
│   ├── text2sql.py             # Text2SQL 核心引擎
│   └── __init__.py
│
├── loaders/                # 数据库加载器
│   ├── base_loader.py          # 加载器基类
│   ├── graph_loader.py         # 图数据库加载器
│   ├── mysql_loader.py         # MySQL 加载器
│   ├── postgres_loader.py      # PostgreSQL 加载器
│   └── __init__.py
│
├── memory/                 # 对话记忆模块
│   ├── graphiti_tool.py        # Graphiti 记忆工具
│   └── __init__.py
│
├── routes/                 # API 路由
│   ├── auth.py                 # 认证路由
│   ├── database.py             # 数据库连接路由
│   ├── graphs.py               # 图管理路由
│   └── tokens.py               # API Token 路由
│
├── sql_utils/              # SQL 工具
│   ├── sql_sanitizer.py        # SQL 清理和验证
│   └── __init__.py
│
├── app_factory.py          # FastAPI 应用工厂
├── config.py               # 配置管理
├── extensions.py           # 扩展和数据库连接
├── graph.py                # 图数据库操作
├── index.py                # 应用入口
└── utils.py                # 通用工具函数
```

### 核心模块说明

#### 1. agents/ - AI Agent 系统
多个专门的 AI Agent 协同工作，处理不同的查询阶段：

- **analysis_agent.py**: 分析用户查询意图，提取关键信息
- **relevancy_agent.py**: 判断查询是否与数据库相关
- **follow_up_agent.py**: 生成澄清问题，处理模糊查询
- **healer_agent.py**: 修复 SQL 语法错误
- **response_formatter_agent.py**: 格式化最终响应

#### 2. auth/ - 认证授权
处理用户认证和会话管理：

- OAuth 2.0 集成 (Google, GitHub)
- 会话管理和 Cookie 处理
- API Token 生成和验证
- 用户权限控制

#### 3. core/ - 核心引擎
Text2SQL 的核心业务逻辑：

- **text2sql.py**: 主要的 Text2SQL 转换引擎
- **schema_loader.py**: 从数据库加载和解析模式
- **errors.py**: 自定义异常类型

#### 4. loaders/ - 数据库加载器
支持多种数据库的模式加载：

- **base_loader.py**: 定义加载器接口
- **postgres_loader.py**: PostgreSQL 模式加载
- **mysql_loader.py**: MySQL 模式加载
- **graph_loader.py**: 将模式加载到 FalkorDB 图数据库

#### 5. routes/ - API 路由
RESTful API 端点定义：

- **auth.py**: `/login/*`, `/logout` - 认证端点
- **graphs.py**: `/graphs/*` - 图管理和查询
- **database.py**: `/database/*` - 数据库连接
- **tokens.py**: `/tokens/*` - API Token 管理

#### 6. memory/ - 对话记忆
使用 Graphiti 实现对话上下文记忆：

- 短期记忆：会话内的查询历史
- 长期记忆：跨会话的用户偏好和模式

---

## 前端结构 (app/)

### 目录组织

```
app/
├── public/                 # 静态资源
│   ├── icons/                  # 图标文件
│   ├── img/                    # 图片资源
│   ├── favicon.ico             # 网站图标
│   └── robots.txt              # 搜索引擎配置
│
├── src/                    # 源代码
│   ├── components/             # React 组件
│   │   ├── chat/                   # 聊天相关组件
│   │   │   ├── ChatInterface.tsx       # 聊天界面主组件
│   │   │   ├── ChatMessage.tsx         # 消息组件
│   │   │   └── QueryInput.tsx          # 查询输入框
│   │   │
│   │   ├── layout/                 # 布局组件
│   │   │   ├── Header.tsx              # 页头
│   │   │   ├── Sidebar.tsx             # 侧边栏
│   │   │   └── Footer.tsx              # 页脚
│   │   │
│   │   ├── modals/                 # 模态框组件
│   │   │   ├── AuthModal.tsx           # 认证模态框
│   │   │   ├── DatabaseModal.tsx       # 数据库连接模态框
│   │   │   ├── DeleteDatabaseModal.tsx # 删除确认模态框
│   │   │   ├── LoginModal.tsx          # 登录模态框
│   │   │   ├── SettingsModal.tsx       # 设置模态框
│   │   │   └── TokensModal.tsx         # Token 管理模态框
│   │   │
│   │   ├── schema/                 # 模式可视化组件
│   │   │   ├── SchemaViewer.tsx        # 模式查看器
│   │   │   └── index.ts
│   │   │
│   │   ├── ui/                     # shadcn/ui 基础组件
│   │   │   ├── button.tsx              # 按钮组件
│   │   │   ├── card.tsx                # 卡片组件
│   │   │   ├── input.tsx               # 输入框组件
│   │   │   ├── dialog.tsx              # 对话框组件
│   │   │   ├── alert.tsx               # 警告组件
│   │   │   └── ...                     # 其他 UI 组件
│   │   │
│   │   └── SuggestionCards.tsx     # 查询建议卡片
│   │
│   ├── contexts/               # React Context
│   │   ├── AuthContext.tsx         # 认证上下文
│   │   ├── ChatContext.tsx         # 聊天上下文
│   │   └── DatabaseContext.tsx     # 数据库上下文
│   │
│   ├── hooks/                  # 自定义 Hooks
│   │   ├── use-mobile.tsx          # 移动端检测
│   │   └── use-toast.ts            # Toast 通知
│   │
│   ├── lib/                    # 工具库
│   │   └── utils.ts                # 工具函数 (cn 等)
│   │
│   ├── pages/                  # 页面组件
│   │   ├── Index.tsx               # 首页
│   │   ├── Settings.tsx            # 设置页
│   │   └── NotFound.tsx            # 404 页面
│   │
│   ├── services/               # API 服务
│   │   ├── auth.ts                 # 认证服务
│   │   ├── chat.ts                 # 聊天服务
│   │   ├── database.ts             # 数据库服务
│   │   └── tokens.ts               # Token 服务
│   │
│   ├── types/                  # TypeScript 类型定义
│   │   └── api.ts                  # API 类型
│   │
│   ├── App.tsx                 # 应用根组件
│   ├── main.tsx                # 应用入口
│   └── index.css               # 全局样式
│
├── components.json         # shadcn/ui 配置
├── eslint.config.cjs       # ESLint 配置
├── index.html              # HTML 模板
├── package.json            # 依赖管理
├── postcss.config.js       # PostCSS 配置
├── tailwind.config.ts      # Tailwind CSS 配置
├── tsconfig.json           # TypeScript 配置
└── vite.config.ts          # Vite 构建配置
```

### 核心模块说明

#### 1. components/ - 组件库

##### chat/ - 聊天组件
- **ChatInterface.tsx**: 主聊天界面，管理消息流和查询状态
- **ChatMessage.tsx**: 单条消息展示，支持 SQL 高亮和结果表格
- **QueryInput.tsx**: 查询输入框，支持多行输入和快捷键

##### modals/ - 模态框
- **DatabaseModal.tsx**: 数据库连接配置
- **AuthModal.tsx**: 用户认证流程
- **SettingsModal.tsx**: 应用设置（记忆、主题等）
- **TokensModal.tsx**: API Token 管理

##### schema/ - 模式可视化
- **SchemaViewer.tsx**: 使用 @falkordb/canvas 可视化数据库模式图

##### ui/ - 基础 UI 组件
基于 shadcn/ui 的可复用组件库，包括按钮、输入框、卡片、对话框等

#### 2. contexts/ - 状态管理
使用 React Context API 管理全局状态：

- **AuthContext**: 用户认证状态、登录/登出
- **ChatContext**: 聊天历史、当前查询状态
- **DatabaseContext**: 数据库列表、选中的数据库

#### 3. services/ - API 服务层
封装所有后端 API 调用：

```typescript
// services/chat.ts
export const ChatService = {
  async query(graphId: string, request: QueryRequest): Promise<Response> {
    return fetch(`/graphs/${graphId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      credentials: 'include'
    });
  }
};
```

#### 4. hooks/ - 自定义 Hooks
可复用的 React Hooks：

- **use-mobile.tsx**: 检测移动端设备
- **use-toast.ts**: Toast 通知管理

---

## 测试结构 (tests/ 和 e2e/)

### 单元测试 (tests/)
```
tests/
├── test_agents.py          # Agent 测试
├── test_auth.py            # 认证测试
├── test_graph.py           # 图操作测试
├── test_loaders.py         # 加载器测试
└── test_text2sql.py        # Text2SQL 测试
```

### E2E 测试 (e2e/)
```
e2e/
├── config/                 # 测试配置
│   └── urls.ts
├── infra/                  # 测试基础设施
│   ├── api/                    # API 测试工具
│   └── ui/                     # UI 测试工具
├── logic/                  # 测试逻辑
│   ├── api/                    # API 测试用例
│   └── pom/                    # 页面对象模型
└── tests/                  # 测试文件
    ├── api/                    # API 测试
    └── ui/                     # UI 测试
```

---

## 配置文件说明

### 后端配置

#### Pipfile
Python 依赖管理，使用 pipenv：
- **packages**: 生产依赖（FastAPI, LiteLLM, FalkorDB 等）
- **dev-packages**: 开发依赖（pytest, pylint, playwright 等）

#### .env.example
环境变量模板：
```bash
# 应用配置
APP_ENV=development
FASTAPI_SECRET_KEY=your_secret_key

# AI 模型配置
OPENAI_API_KEY=your_openai_key
# 或使用 Azure OpenAI
AZURE_API_KEY=your_azure_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-12-01-preview

# OAuth 配置
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# FalkorDB 配置
FALKORDB_HOST=localhost
FALKORDB_PORT=6379

# 记忆配置
MEMORY_TTL_SECONDS=604800  # 7 天

# MCP 配置
DISABLE_MCP=false
```

### 前端配置

#### package.json
Node.js 依赖管理：
- **dependencies**: 生产依赖（React, Radix UI, Tailwind 等）
- **devDependencies**: 开发依赖（Vite, TypeScript, ESLint 等）

#### tailwind.config.ts
Tailwind CSS 配置：
- 颜色系统（基于 CSS 变量）
- 字体系统（Inter, Merriweather, JetBrains Mono）
- 响应式断点
- 插件配置

#### vite.config.ts
Vite 构建配置：
- React 插件
- 路径别名 (@/ -> src/)
- 代理配置（开发环境）
- 构建优化

---

## 数据流架构

### 查询处理流程

```
用户输入
    ↓
前端 ChatInterface
    ↓
POST /graphs/{graph_id}
    ↓
后端 API Router
    ↓
relevancy_agent (判断相关性)
    ↓
analysis_agent (分析查询)
    ↓
graph.find() (查找相关表)
    ├── 向量搜索表描述
    ├── 向量搜索列描述
    ├── 查找关联表
    └── 查找连接路径
    ↓
text2sql (生成 SQL)
    ↓
healer_agent (修复 SQL)
    ↓
执行 SQL 查询
    ↓
response_formatter_agent (格式化响应)
    ↓
流式返回结果
    ↓
前端展示结果
```

### 数据库模式加载流程

```
用户上传数据库连接信息
    ↓
database_router.connect_database()
    ↓
选择对应的 Loader (PostgresLoader/MySQLLoader)
    ↓
loader.load_schema()
    ├── 连接数据库
    ├── 查询表结构
    ├── 查询外键关系
    └── 查询列信息
    ↓
graph_loader.load_to_graph()
    ├── 创建 Database 节点
    ├── 创建 Table 节点
    ├── 创建 Column 节点
    ├── 创建 REFERENCES 关系
    └── 生成向量嵌入
    ↓
保存到 FalkorDB
    ↓
返回 graph_id
```

---

## 部署架构

### Docker 部署
```
Docker Container
├── FastAPI 应用 (端口 5000)
├── React 静态文件 (app/dist)
└── 连接外部 FalkorDB
```

### 开发环境
```
本地开发
├── 后端: uvicorn (端口 5000)
├── 前端: vite dev server (端口 5173)
└── FalkorDB: Docker (端口 6379)
```

### 生产环境
```
生产部署
├── 负载均衡器
├── FastAPI 应用集群
├── FalkorDB 集群
└── CDN (静态资源)
```

---

## 关键设计模式

### 1. Agent 模式
多个专门的 AI Agent 协同工作，每个 Agent 负责特定任务

### 2. 工厂模式
- `app_factory.py`: 创建 FastAPI 应用实例
- Loader 工厂: 根据数据库类型选择加载器

### 3. 策略模式
- 不同的数据库加载器实现相同接口
- 不同的 AI 模型配置策略

### 4. 观察者模式
- React Context 状态管理
- 流式响应处理

### 5. 装饰器模式
- FastAPI 路由装饰器
- 认证装饰器 (`@token_required`)

---

## 扩展指南

### 添加新的数据库支持

1. 在 `api/loaders/` 创建新的加载器
2. 继承 `BaseLoader` 类
3. 实现 `load_schema()` 方法
4. 在 `database_router` 中注册

### 添加新的 Agent

1. 在 `api/agents/` 创建新的 Agent 文件
2. 定义 Agent 的 Prompt 和逻辑
3. 在 `text2sql.py` 中集成

### 添加新的 UI 组件

1. 在 `app/src/components/` 创建组件
2. 遵循 shadcn/ui 设计规范
3. 使用 TypeScript 类型定义
4. 添加必要的测试

---

## 文件命名约定

### 后端 (Python)
- 模块文件: `snake_case.py`
- 类名: `PascalCase`
- 函数名: `snake_case`
- 常量: `UPPER_SNAKE_CASE`

### 前端 (TypeScript/React)
- 组件文件: `PascalCase.tsx`
- 工具文件: `kebab-case.ts`
- 类型文件: `kebab-case.ts`
- 样式文件: `kebab-case.css`

---

## 开发工作流

### 后端开发
```bash
# 安装依赖
pipenv sync --dev

# 运行开发服务器
make run-dev

# 运行测试
make test

# 代码检查
pipenv run pylint api/
```

### 前端开发
```bash
# 安装依赖
cd app && npm ci

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

---

## 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [FalkorDB 文档](https://docs.falkordb.com/)
- [shadcn/ui 文档](https://ui.shadcn.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
