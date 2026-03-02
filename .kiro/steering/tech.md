---
inclusion: auto
description: "QueryWeaver 技术栈详解，包含后端（FastAPI、LiteLLM、FalkorDB）、前端（React、TypeScript、Tailwind CSS）、数据库、开发工具等完整技术选型说明"
---

# QueryWeaver 技术栈详解

## 概述

QueryWeaver 采用现代化的全栈技术架构，使用 Python FastAPI 构建后端服务，React + TypeScript 构建前端应用，FalkorDB 图数据库存储模式关系，LiteLLM 统一管理多种 AI 模型。

---

## 后端技术栈

### 核心框架

#### FastAPI 0.131.0
**用途**: Web 框架和 API 服务器

**特性**:
- 基于 Python 3.12+ 类型提示
- 自动生成 OpenAPI (Swagger) 文档
- 原生支持异步 (async/await)
- 高性能 (基于 Starlette 和 Pydantic)
- 内置数据验证

**使用场景**:
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(title="QueryWeaver")

class QueryRequest(BaseModel):
    """查询请求模型"""
    chat: list[str]
    result: list[dict] = []

@app.post("/graphs/{graph_id}")
async def query_database(
    graph_id: str,
    request: QueryRequest
):
    """执行数据库查询"""
    return await process_query(graph_id, request)
```

#### Uvicorn 0.40.0
**用途**: ASGI 服务器

**特性**:
- 高性能异步 HTTP 服务器
- 支持 HTTP/1.1 和 WebSocket
- 热重载 (开发模式)
- 生产级稳定性

**配置示例**:
```bash
uvicorn api.index:app --host 0.0.0.0 --port 5000 --reload
```

### AI 和机器学习

#### LiteLLM 1.80.9
**用途**: 统一的 LLM API 接口

**支持的模型**:
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Anthropic Claude
- Google PaLM
- Cohere
- 其他 100+ 模型

**使用示例**:
```python
from litellm import completion, embedding

# 文本生成
response = completion(
    model="azure/gpt-4.1",
    messages=[{"role": "user", "content": "生成 SQL"}],
    temperature=0
)

# 文本嵌入
embeddings = embedding(
    model="azure/text-embedding-ada-002",
    input=["表描述文本"]
)
```

**配置**:
```python
# 自动切换 OpenAI/Azure
if os.getenv("OPENAI_API_KEY"):
    model = "openai/gpt-4.1"
else:
    model = "azure/gpt-4.1"
```

#### Graphiti Core (staging)
**用途**: 对话记忆和上下文管理

**特性**:
- 基于图的记忆存储
- 时间感知的上下文检索
- 自动记忆摘要
- 支持长期和短期记忆

**集成方式**:
```python
from graphiti_core import Graphiti

# 初始化记忆系统
memory = Graphiti(graph_id=f"memory_{user_id}")

# 添加记忆
await memory.add_episode(
    content="用户查询了销售数据",
    timestamp=datetime.now()
)

# 检索相关记忆
relevant = await memory.search(
    query="销售",
    limit=5
)
```

### 数据库

#### FalkorDB 1.6.0
**用途**: 图数据库，存储数据库模式关系

**特性**:
- 基于 Redis 的图数据库
- 支持 Cypher 查询语言
- 向量索引和相似度搜索
- 高性能图遍历

**使用场景**:
```python
from falkordb import FalkorDB

# 连接数据库
db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("my_database")

# 创建节点和关系
await graph.query("""
    CREATE (t:Table {name: 'users', description: '用户表'})
    CREATE (c:Column {name: 'id', type: 'INTEGER'})
    CREATE (c)-[:BELONGS_TO]->(t)
""")

# 向量搜索
result = await graph.query("""
    CALL db.idx.vector.queryNodes(
        'Table', 'embedding', 3, vecf32($embedding)
    ) YIELD node, score
    RETURN node.name, score
""", {"embedding": embedding_vector})
```

#### PostgreSQL (psycopg2-binary 2.9.11)
**用途**: 连接和查询 PostgreSQL 数据库

**特性**:
- 完整的 PostgreSQL 协议支持
- 连接池管理
- 异步查询支持
- 类型转换

**使用示例**:
```python
import psycopg2

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)

# 查询模式信息
cursor = conn.cursor()
cursor.execute("""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
""")
schema = cursor.fetchall()
```

#### MySQL (PyMySQL 1.1.0)
**用途**: 连接和查询 MySQL 数据库

**特性**:
- 纯 Python 实现
- 兼容 MySQL 5.5+
- 支持 SSL 连接
- 游标类型支持

**使用示例**:
```python
import pymysql

# 连接数据库
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="password",
    database="mydb"
)

# 查询表结构
with conn.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
```

### 认证和安全

#### Authlib 1.6.4
**用途**: OAuth 2.0 客户端和服务器

**支持的提供商**:
- Google OAuth 2.0
- GitHub OAuth 2.0
- 自定义 OAuth 提供商

**使用示例**:
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

# 注册 Google OAuth
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# 登录流程
@app.route('/login/google')
async def login_google(request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)
```

#### itsdangerous 2.2.0
**用途**: 数据签名和会话管理

**特性**:
- 加密签名
- 时间戳验证
- URL 安全编码
- 会话 Cookie 管理

**使用示例**:
```python
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(SECRET_KEY)

# 生成 Token
token = serializer.dumps({"user_id": 123})

# 验证 Token
try:
    data = serializer.loads(token, max_age=3600)
    user_id = data["user_id"]
except SignatureExpired:
    # Token 过期
    pass
```

### 数据验证

#### Pydantic (FastAPI 内置)
**用途**: 数据验证和序列化

**特性**:
- 基于 Python 类型提示
- 自动数据验证
- JSON Schema 生成
- 性能优化

**使用示例**:
```python
from pydantic import BaseModel, Field, validator

class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    host: str = Field(..., description="数据库主机")
    port: int = Field(5432, ge=1, le=65535)
    database: str
    user: str
    password: str = Field(..., min_length=8)
    
    @validator('host')
    def validate_host(cls, v):
        """验证主机地址"""
        if not v or v.isspace():
            raise ValueError('主机地址不能为空')
        return v
```

#### jsonschema 4.26.0
**用途**: JSON Schema 验证

**使用场景**:
- 验证上传的 JSON 文件
- API 请求验证
- 配置文件验证

### 工具库

#### tqdm 4.67.3
**用途**: 进度条显示

**使用示例**:
```python
from tqdm import tqdm

# 显示加载进度
for table in tqdm(tables, desc="加载表结构"):
    load_table_schema(table)
```

#### python-multipart 0.0.10
**用途**: 文件上传处理

**使用场景**:
```python
from fastapi import UploadFile

@app.post("/upload")
async def upload_schema(file: UploadFile):
    """上传数据库模式文件"""
    content = await file.read()
    schema = json.loads(content)
    return {"status": "success"}
```

#### Jinja2 3.1.4
**用途**: 模板引擎

**使用场景**:
- 生成 SQL 模板
- 邮件模板
- 报告生成

### MCP 协议

#### FastMCP 2.13.1+
**用途**: Model Context Protocol 实现

**特性**:
- HTTP 传输支持
- 工具注册和调用
- 资源管理
- 提示模板

**使用示例**:
```python
from fastmcp import FastMCP

mcp = FastMCP.from_fastapi(
    app=app,
    name="queryweaver"
)

# 注册工具
@mcp.tool()
async def query_database(
    database: str,
    question: str
) -> dict:
    """查询数据库"""
    return await execute_query(database, question)
```

---

## 前端技术栈

### 核心框架

#### React 18.3.1
**用途**: UI 框架

**特性**:
- 并发渲染
- 自动批处理
- Suspense 数据获取
- Server Components (未来)

**使用示例**:
```tsx
import { useState, useEffect } from 'react';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  
  return (
    <div className="chat-container">
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
    </div>
  );
};
```

#### TypeScript 5.8.3
**用途**: 类型安全的 JavaScript

**配置**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "moduleResolution": "bundler"
  }
}
```

**使用示例**:
```typescript
// 类型定义
interface QueryRequest {
  chat: string[];
  result?: QueryResult[];
  instructions?: string;
}

// 类型安全的函数
async function executeQuery(
  graphId: string,
  request: QueryRequest
): Promise<QueryResult> {
  // 实现
}
```


### 路由

#### React Router DOM 6.30.1
**用途**: 客户端路由

**特性**:
- 声明式路由
- 嵌套路由
- 懒加载
- 数据加载器

**使用示例**:
```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### 状态管理

#### TanStack Query 5.83.0
**用途**: 服务器状态管理

**特性**:
- 自动缓存
- 后台重新获取
- 乐观更新
- 无限滚动

**使用示例**:
```tsx
import { useQuery, useMutation } from '@tanstack/react-query';

// 查询数据
const { data, isLoading } = useQuery({
  queryKey: ['graphs'],
  queryFn: () => fetch('/graphs').then(r => r.json())
});

// 修改数据
const mutation = useMutation({
  mutationFn: (newGraph) => 
    fetch('/graphs', {
      method: 'POST',
      body: JSON.stringify(newGraph)
    }),
  onSuccess: () => {
    queryClient.invalidateQueries(['graphs']);
  }
});
```

#### React Context API
**用途**: 全局状态管理

**使用示例**:
```tsx
// AuthContext.tsx
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: ReactNode}> = ({children}) => {
  const [user, setUser] = useState<User | null>(null);
  
  return (
    <AuthContext.Provider value={{user, setUser}}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用
const { user } = useAuth();
```

### UI 组件库

#### Radix UI
**用途**: 无样式的可访问组件

**组件**:
- Dialog (对话框)
- Dropdown Menu (下拉菜单)
- Select (选择器)
- Toast (通知)
- Tooltip (提示)
- Switch (开关)
- 等 30+ 组件

**使用示例**:
```tsx
import * as Dialog from '@radix-ui/react-dialog';

<Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
  <Dialog.Trigger asChild>
    <button>打开设置</button>
  </Dialog.Trigger>
  <Dialog.Portal>
    <Dialog.Overlay className="dialog-overlay" />
    <Dialog.Content className="dialog-content">
      <Dialog.Title>设置</Dialog.Title>
      {/* 内容 */}
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```


#### shadcn/ui
**用途**: 可复用的 UI 组件

**特点**:
- 基于 Radix UI
- 使用 Tailwind CSS
- 可定制化
- 复制粘贴使用

**组件示例**:
```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>数据库连接</CardTitle>
  </CardHeader>
  <CardContent>
    <Button variant="default">连接</Button>
  </CardContent>
</Card>
```

### 样式

#### Tailwind CSS 3.4.17
**用途**: 实用优先的 CSS 框架

**配置**:
```typescript
// tailwind.config.ts
export default {
  darkMode: ["selector", "[data-theme='dark']"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "var(--primary)",
        background: "var(--background)"
      }
    }
  }
}
```

**使用示例**:
```tsx
<div className="
  flex items-center justify-between
  p-4 rounded-lg
  bg-card text-card-foreground
  shadow-sm hover:shadow-md
  transition-shadow
">
  内容
</div>
```

#### tailwindcss-animate 1.0.7
**用途**: Tailwind 动画插件

**使用示例**:
```tsx
<div className="animate-in fade-in slide-in-from-bottom duration-300">
  淡入并从底部滑入
</div>
```

#### class-variance-authority 0.7.1
**用途**: 组件变体管理

**使用示例**:
```tsx
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        destructive: "bg-destructive text-destructive-foreground"
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 px-3"
      }
    }
  }
);
```

### 数据可视化

#### @falkordb/canvas 0.0.29
**用途**: 图数据库可视化

**特性**:
- 节点和边渲染
- 交互式图探索
- 力导向布局
- 缩放和平移

**使用示例**:
```tsx
import { Canvas } from '@falkordb/canvas';

<Canvas
  nodes={nodes}
  edges={edges}
  onNodeClick={handleNodeClick}
  layout="force"
/>
```

#### D3.js 7.9.0
**用途**: 数据驱动的可视化

**使用场景**:
- 自定义图表
- 复杂数据可视化
- 动画效果

### 表单处理

#### React Hook Form 7.61.1
**用途**: 高性能表单管理

**特性**:
- 最小重渲染
- 易于集成验证
- TypeScript 支持
- 小体积

**使用示例**:
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  host: z.string().min(1, '主机不能为空'),
  port: z.number().min(1).max(65535)
});

function DatabaseForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema)
  });
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('host')} />
      {errors.host && <span>{errors.host.message}</span>}
    </form>
  );
}
```


#### Zod 3.25.76
**用途**: TypeScript 优先的模式验证

**特性**:
- 类型推断
- 组合验证
- 错误消息定制
- 与 React Hook Form 集成

**使用示例**:
```typescript
import { z } from 'zod';

// 定义模式
const DatabaseSchema = z.object({
  host: z.string().min(1, '主机不能为空'),
  port: z.number().int().min(1).max(65535),
  database: z.string().min(1),
  user: z.string().min(1),
  password: z.string().min(8, '密码至少8位')
});

// 类型推断
type Database = z.infer<typeof DatabaseSchema>;

// 验证数据
const result = DatabaseSchema.safeParse(data);
if (!result.success) {
  console.error(result.error.errors);
}
```

### 工具库

#### clsx 2.1.1 + tailwind-merge 2.6.0
**用途**: 条件类名和 Tailwind 类名合并

**使用示例**:
```typescript
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// cn 工具函数
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 使用
<div className={cn(
  'base-class',
  isActive && 'active-class',
  className
)}>
```

#### date-fns 3.6.0
**用途**: 日期处理库

**使用示例**:
```typescript
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// 格式化日期
const formatted = format(new Date(), 'yyyy-MM-dd HH:mm:ss', {
  locale: zhCN
});

// 相对时间
const relative = formatDistanceToNow(new Date(), {
  addSuffix: true,
  locale: zhCN
}); // "3 分钟前"
```

### 构建工具

#### Vite 7.3.0
**用途**: 下一代前端构建工具

**特性**:
- 极速冷启动
- 即时热模块替换 (HMR)
- 按需编译
- 优化的生产构建

**配置示例**:
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
});
```

#### @vitejs/plugin-react-swc 3.11.0
**用途**: 使用 SWC 编译 React

**特性**:
- 比 Babel 快 20 倍
- 支持 JSX 和 TypeScript
- 自动 Fast Refresh

### 代码质量

#### ESLint 9.32.0
**用途**: JavaScript/TypeScript 代码检查

**配置示例**:
```javascript
// eslint.config.cjs
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended'
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'warn',
    'react-hooks/exhaustive-deps': 'warn'
  }
};
```

---

## 开发工具

### Python 开发工具

#### pipenv
**用途**: Python 依赖管理和虚拟环境

**常用命令**:
```bash
# 安装依赖
pipenv sync

# 安装开发依赖
pipenv sync --dev

# 运行命令
pipenv run python script.py

# 进入虚拟环境
pipenv shell
```

#### pytest 8.4.2
**用途**: Python 测试框架

**使用示例**:
```python
import pytest

@pytest.mark.asyncio
async def test_find_tables():
    """测试表查找功能"""
    result = await find_tables("test_db", ["查询用户"])
    assert len(result) > 0
    assert result[0][0] == "users"

@pytest.fixture
def mock_graph():
    """模拟图数据库"""
    return MockGraph()
```

#### pylint 4.0.3
**用途**: Python 代码质量检查

**配置**:
```ini
# .pylintrc
[MESSAGES CONTROL]
disable=C0111,C0103

[FORMAT]
max-line-length=100
```

### 前端开发工具

#### TypeScript 5.8.3
**用途**: 类型检查和编译

**配置**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 测试工具

#### Playwright 1.57.0
**用途**: 端到端测试

**使用示例**:
```python
from playwright.async_api import async_playwright

async def test_login_flow():
    """测试登录流程"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:5000")
        await page.click("text=登录")
        await page.fill("input[name=email]", "test@example.com")
        await page.click("button[type=submit]")
        
        await expect(page.locator(".user-menu")).to_be_visible()
        await browser.close()
```

---

## 部署技术

### 容器化

#### Docker
**用途**: 应用容器化

**Dockerfile 示例**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv sync --system

# 复制应用代码
COPY api/ ./api/
COPY app/dist/ ./app/dist/

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "5000"]
```

**docker-compose.yml 示例**:
```yaml
version: '3.8'

services:
  queryweaver:
    image: falkordb/queryweaver:latest
    ports:
      - "5000:5000"
    environment:
      - FALKORDB_HOST=falkordb
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - falkordb
  
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb-data:/data

volumes:
  falkordb-data:
```

### CI/CD

#### GitHub Actions
**用途**: 持续集成和部署

**工作流示例**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv sync --dev
      
      - name: Run tests
        run: pipenv run pytest
      
      - name: Run E2E tests
        run: |
          pipenv run playwright install
          pipenv run pytest tests/e2e/
```

---

## 性能优化技术

### 后端优化

#### 异步编程
```python
import asyncio

# 并发执行多个任务
async def process_queries(queries):
    """并发处理多个查询"""
    tasks = [process_single_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

#### 缓存策略
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_embedding_size(model_name: str) -> int:
    """缓存嵌入向量大小"""
    return calculate_size(model_name)
```

### 前端优化

#### 代码分割
```tsx
import { lazy, Suspense } from 'react';

// 懒加载组件
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Settings />
    </Suspense>
  );
}
```

#### React.memo
```tsx
import { memo } from 'react';

// 避免不必要的重渲染
export const ChatMessage = memo<ChatMessageProps>(({ message }) => {
  return <div>{message.content}</div>;
});
```

---

## 监控和日志

### 日志系统

#### Python logging
```python
import logging
import json

# 结构化日志
logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "event": "query_execution",
    "user_id": user_id,
    "query": query,
    "execution_time": 1.23,
    "success": True
}))
```

### 错误追踪

#### 前端错误边界
```tsx
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 发送错误到监控服务
    console.error('Error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

---

## 安全技术

### 认证和授权

#### OAuth 2.0 流程
```
1. 用户点击"使用 Google 登录"
2. 重定向到 Google 授权页面
3. 用户授权后回调到应用
4. 应用获取 access_token
5. 使用 token 获取用户信息
6. 创建会话 Cookie
```

#### API Token 认证
```python
from itsdangerous import URLSafeTimedSerializer

def generate_api_token(user_id: str) -> str:
    """生成 API Token"""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps({"user_id": user_id})

def verify_api_token(token: str) -> str:
    """验证 API Token"""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    data = serializer.loads(token, max_age=86400 * 365)
    return data["user_id"]
```

### SQL 注入防护

#### 参数化查询
```python
# 安全的查询方式
cursor.execute(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)
)

# 危险的查询方式 (避免)
# cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

#### SQL 清理
```python
from api.sql_utils.sql_sanitizer import sanitize_sql

def execute_user_query(query: str):
    """执行用户查询（带清理）"""
    # 清理 SQL
    clean_query = sanitize_sql(query)
    
    # 检查危险操作
    if is_destructive(clean_query):
        raise ValueError("不允许修改数据")
    
    return execute_query(clean_query)
```

---

## 技术选型原则

### 后端技术选型

1. **性能优先**: FastAPI 提供高性能异步支持
2. **类型安全**: Python 3.12+ 类型提示 + Pydantic
3. **生态成熟**: 丰富的 Python 生态系统
4. **易于维护**: 清晰的代码结构和文档

### 前端技术选型

1. **开发体验**: Vite 快速开发，TypeScript 类型安全
2. **用户体验**: React 18 并发特性，流畅交互
3. **可访问性**: Radix UI 提供无障碍支持
4. **可定制性**: Tailwind CSS 灵活的样式系统

### 数据库选型

1. **图数据库**: FalkorDB 适合存储关系网络
2. **向量搜索**: 支持语义相似度搜索
3. **高性能**: 基于 Redis 的内存数据库
4. **易于扩展**: 支持水平扩展

---

## 技术债务管理

### 已知技术债务

1. **前端状态管理**: 考虑引入 Zustand 或 Jotai
2. **缓存策略**: 需要更完善的缓存失效机制
3. **错误处理**: 统一的错误处理和重试机制
4. **测试覆盖率**: 提高单元测试和集成测试覆盖率

### 技术升级计划

1. **Q2 2025**: 升级到 React 19
2. **Q2 2025**: 引入 Server Components
3. **Q3 2025**: 迁移到 Tailwind CSS v4
4. **Q4 2025**: 评估 Rust 重写性能关键模块

---

## 学习资源

### 官方文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [FalkorDB 文档](https://docs.falkordb.com/)

### 推荐教程
- [Python 异步编程指南](https://realpython.com/async-io-python/)
- [React 性能优化](https://react.dev/learn/render-and-commit)
- [TypeScript 深入理解](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Tailwind CSS 最佳实践](https://tailwindcss.com/docs/utility-first)

### 社区资源
- [FastAPI Discord](https://discord.gg/fastapi)
- [React Discord](https://discord.gg/react)
- [FalkorDB Discord](https://discord.gg/falkordb)
- [QueryWeaver Discord](https://discord.gg/b32KEzMzce)

---

## 技术支持

### 常见问题

#### 后端问题
- **FalkorDB 连接失败**: 检查 FALKORDB_HOST 和 FALKORDB_PORT
- **LiteLLM 错误**: 确认 API Key 配置正确
- **OAuth 失败**: 检查回调 URL 和环境变量

#### 前端问题
- **构建失败**: 清除 node_modules 重新安装
- **类型错误**: 运行 `npm run type-check`
- **样式问题**: 检查 Tailwind 配置和 CSS 导入

### 获取帮助
- GitHub Issues: 报告 Bug 和功能请求
- Discord: 实时技术支持
- 文档: 查看完整的使用文档
- 邮件: support@queryweaver.ai
