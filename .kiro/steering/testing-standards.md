---
inclusion: fileMatch
fileMatchPattern: "{tests,e2e}/**/*.{py,ts}"
---

# 测试开发规范

## 测试金字塔原则

```
        /\
       /  \      E2E 测试 (10%)
      /____\     - 完整用户流程
     /      \    - 浏览器自动化
    /________\   
   /          \  集成测试 (20%)
  /____________\ - API 端点测试
 /              \- 数据库集成
/________________\
                  单元测试 (70%)
                  - 函数级测试
                  - 模块隔离
```

## Python 单元测试

### Pytest 基础规范
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# 测试文件命名：test_*.py
# 测试函数命名：test_*

class TestGraphFunctions:
    """图数据库功能测试套件"""
    
    @pytest.fixture
    def mock_graph(self):
        """
        模拟图数据库连接
        
        使用 fixture 提供可重用的测试数据
        """
        mock = Mock()
        mock.query = AsyncMock(return_value=Mock(result_set=[]))
        return mock
    
    @pytest.fixture
    def sample_tables(self) -> List[Dict[str, Any]]:
        """示例表数据"""
        return [
            {
                "name": "users",
                "description": "用户信息表",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "email", "type": "varchar"}
                ]
            },
            {
                "name": "orders",
                "description": "订单表",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "user_id", "type": "integer"}
                ]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_find_tables_returns_list(self, mock_graph):
        """
        测试：find_tables 应该返回列表
        
        使用 AAA 模式：
        - Arrange: 准备测试数据
        - Act: 执行被测试的函数
        - Assert: 验证结果
        """
        # Arrange - 准备
        graph_id = "test_db"
        queries = ["查询用户信息"]
        
        with patch('api.extensions.db.select_graph', return_value=mock_graph):
            # Act - 执行
            result = await find_tables(graph_id, queries)
            
            # Assert - 验证
            assert isinstance(result, list)
            assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_find_tables_with_empty_query(self, mock_graph):
        """测试：空查询应该返回空列表"""
        graph_id = "test_db"
        queries = []
        
        with patch('api.extensions.db.select_graph', return_value=mock_graph):
            result = await find_tables(graph_id, queries)
            assert result == []
    
    @pytest.mark.parametrize("query,expected_count", [
        ("查询用户", 1),
        ("查询订单", 1),
        ("查询用户和订单", 2),
    ])
    @pytest.mark.asyncio
    async def test_find_tables_parametrized(
        self, 
        mock_graph, 
        query, 
        expected_count
    ):
        """
        参数化测试：测试不同查询返回不同数量的表
        
        使用 @pytest.mark.parametrize 减少重复代码
        """
        graph_id = "test_db"
        
        with patch('api.extensions.db.select_graph', return_value=mock_graph):
            result = await find_tables(graph_id, [query])
            assert len(result) >= expected_count
```

### Mock 和 Patch 使用
```python
from unittest.mock import Mock, patch, MagicMock, call

class TestDatabaseLoader:
    """数据库加载器测试"""
    
    @pytest.mark.asyncio
    async def test_postgres_loader_connect(self):
        """测试 PostgreSQL 连接"""
        # Mock asyncpg.connect
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            loader = PostgresLoader({
                'host': 'localhost',
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_pass'
            })
            
            await loader.connect()
            
            # 验证 connect 被正确调用
            mock_connect.assert_called_once_with(
                host='localhost',
                port=5432,
                database='test_db',
                user='test_user',
                password='test_pass',
                timeout=30
            )
            
            # 验证连接被保存
            assert loader.connection == mock_conn
    
    @pytest.mark.asyncio
    async def test_get_tables_returns_table_names(self):
        """测试获取表名列表"""
        loader = PostgresLoader({})
        
        # Mock 数据库查询结果
        mock_rows = [
            {'table_name': 'users'},
            {'table_name': 'orders'},
            {'table_name': 'products'}
        ]
        
        loader.connection = AsyncMock()
        loader.connection.fetch = AsyncMock(return_value=mock_rows)
        
        result = await loader.get_tables()
        
        assert result == ['users', 'orders', 'products']
        loader.connection.fetch.assert_called_once()
```

### 异常测试
```python
class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_connection_failure_raises_error(self):
        """测试：连接失败应该抛出 ConnectionError"""
        with patch('asyncpg.connect', side_effect=Exception("连接失败")):
            loader = PostgresLoader({
                'host': 'invalid_host',
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_pass'
            })
            
            with pytest.raises(ConnectionError) as exc_info:
                await loader.connect()
            
            assert "无法连接到数据库" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_sql_raises_value_error(self):
        """测试：无效 SQL 应该抛出 ValueError"""
        sql = "DROP TABLE users;"
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_sanitize_sql(sql, "user_123")
        
        assert "不允许执行 DROP 操作" in str(exc_info.value)
```

## TypeScript/React 测试

### React Testing Library
```typescript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ChatInterface } from "./ChatInterface";

describe("ChatInterface", () => {
  /**
   * 测试：组件应该正确渲染
   */
  it("应该渲染输入框和发送按钮", () => {
    render(<ChatInterface />);
    
    // 使用语义化查询
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    const button = screen.getByRole("button", { name: /发送/i });
    
    expect(input).toBeInTheDocument();
    expect(button).toBeInTheDocument();
  });
  
  /**
   * 测试：禁用状态
   */
  it("当 disabled 为 true 时应该禁用输入", () => {
    render(<ChatInterface disabled />);
    
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    expect(input).toBeDisabled();
  });
  
  /**
   * 测试：用户交互
   */
  it("应该在用户输入时更新状态", async () => {
    render(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    
    // 模拟用户输入
    fireEvent.change(input, { target: { value: "测试查询" } });
    
    expect(input).toHaveValue("测试查询");
  });
  
  /**
   * 测试：异步操作
   */
  it("应该在发送消息时调用回调", async () => {
    const onProcessingChange = vi.fn();
    render(<ChatInterface onProcessingChange={onProcessingChange} />);
    
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    const button = screen.getByRole("button", { name: /发送/i });
    
    fireEvent.change(input, { target: { value: "测试查询" } });
    fireEvent.click(button);
    
    // 等待异步操作完成
    await waitFor(() => {
      expect(onProcessingChange).toHaveBeenCalledWith(true);
    });
  });
});
```

### Hook 测试
```typescript
import { renderHook, act, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { useDatabase } from "./useDatabase";

describe("useDatabase", () => {
  /**
   * 测试：Hook 初始化
   */
  it("应该初始化为空状态", () => {
    const { result } = renderHook(() => useDatabase());
    
    expect(result.current.graphs).toEqual([]);
    expect(result.current.selectedGraph).toBeNull();
    expect(result.current.loading).toBe(false);
  });
  
  /**
   * 测试：加载数据
   */
  it("应该加载数据库列表", async () => {
    // Mock API 调用
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        { id: "db1", name: "Database 1" },
        { id: "db2", name: "Database 2" }
      ]
    });
    
    const { result } = renderHook(() => useDatabase());
    
    // 等待数据加载
    await waitFor(() => {
      expect(result.current.graphs).toHaveLength(2);
    });
    
    expect(result.current.graphs[0].name).toBe("Database 1");
  });
  
  /**
   * 测试：选择数据库
   */
  it("应该能够选择数据库", async () => {
    const { result } = renderHook(() => useDatabase());
    
    // 先加载数据
    await waitFor(() => {
      expect(result.current.graphs).toHaveLength(2);
    });
    
    // 选择数据库
    act(() => {
      result.current.selectGraph("db1");
    });
    
    expect(result.current.selectedGraph?.id).toBe("db1");
  });
});
```

### Mock API 请求
```typescript
import { vi } from "vitest";
import { DatabaseService } from "./database";

describe("DatabaseService", () => {
  /**
   * 测试：成功获取数据库列表
   */
  it("应该成功获取数据库列表", async () => {
    const mockGraphs = [
      { id: "db1", name: "Database 1" },
      { id: "db2", name: "Database 2" }
    ];
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockGraphs
    });
    
    const result = await DatabaseService.getGraphs();
    
    expect(result).toEqual(mockGraphs);
    expect(fetch).toHaveBeenCalledWith("/api/graphs", {
      credentials: "include"
    });
  });
  
  /**
   * 测试：处理 API 错误
   */
  it("应该处理 API 错误", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error"
    });
    
    await expect(DatabaseService.getGraphs()).rejects.toThrow(
      "HTTP 500: Internal Server Error"
    );
  });
  
  /**
   * 测试：处理网络错误
   */
  it("应该处理网络错误", async () => {
    global.fetch = vi.fn().mockRejectedValue(
      new Error("Network error")
    );
    
    await expect(DatabaseService.getGraphs()).rejects.toThrow(
      "Network error"
    );
  });
});
```

## E2E 测试 (Playwright)

### 页面对象模型 (POM)
```typescript
// e2e/logic/pom/homePage.ts

import { Page, Locator } from "@playwright/test";

/**
 * 首页页面对象
 * 
 * 封装页面元素和操作，提高测试可维护性
 */
export class HomePage {
  readonly page: Page;
  readonly databaseSelector: Locator;
  readonly connectButton: Locator;
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly messageList: Locator;
  
  constructor(page: Page) {
    this.page = page;
    this.databaseSelector = page.getByTestId("database-selector-trigger");
    this.connectButton = page.getByTestId("connect-database-btn");
    this.chatInput = page.getByPlaceholderText(/输入您的问题/i);
    this.sendButton = page.getByRole("button", { name: /发送/i });
    this.messageList = page.getByTestId("message-list");
  }
  
  /**
   * 导航到首页
   */
  async goto() {
    await this.page.goto("/");
  }
  
  /**
   * 选择数据库
   */
  async selectDatabase(databaseName: string) {
    await this.databaseSelector.click();
    await this.page.getByText(databaseName).click();
  }
  
  /**
   * 发送查询
   */
  async sendQuery(query: string) {
    await this.chatInput.fill(query);
    await this.sendButton.click();
  }
  
  /**
   * 等待响应
   */
  async waitForResponse() {
    await this.page.waitForSelector(
      "[data-testid='chat-message']",
      { timeout: 10000 }
    );
  }
  
  /**
   * 获取最后一条消息
   */
  async getLastMessage(): Promise<string> {
    const messages = await this.page
      .getByTestId("chat-message")
      .allTextContents();
    return messages[messages.length - 1];
  }
}
```

### E2E 测试用例
```typescript
// e2e/tests/chat.spec.ts

import { test, expect } from "@playwright/test";
import { HomePage } from "../logic/pom/homePage";

test.describe("聊天功能", () => {
  let homePage: HomePage;
  
  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    await homePage.goto();
  });
  
  /**
   * 测试：完整的查询流程
   */
  test("应该能够发送查询并获得响应", async () => {
    // 选择数据库
    await homePage.selectDatabase("DEMO_CRM");
    
    // 发送查询
    await homePage.sendQuery("显示所有用户");
    
    // 等待响应
    await homePage.waitForResponse();
    
    // 验证响应
    const lastMessage = await homePage.getLastMessage();
    expect(lastMessage).toContain("SELECT");
  });
  
  /**
   * 测试：错误处理
   */
  test("应该显示错误消息当查询失败时", async () => {
    await homePage.selectDatabase("DEMO_CRM");
    await homePage.sendQuery("无效的查询");
    
    await homePage.page.waitForSelector(
      "[data-testid='error-message']",
      { timeout: 5000 }
    );
    
    const errorMessage = await homePage.page
      .getByTestId("error-message")
      .textContent();
    
    expect(errorMessage).toBeTruthy();
  });
  
  /**
   * 测试：多轮对话
   */
  test("应该支持多轮对话", async () => {
    await homePage.selectDatabase("DEMO_CRM");
    
    // 第一轮
    await homePage.sendQuery("有多少用户？");
    await homePage.waitForResponse();
    
    // 第二轮
    await homePage.sendQuery("显示前 10 个用户");
    await homePage.waitForResponse();
    
    // 验证有两条响应
    const messages = await homePage.page
      .getByTestId("chat-message")
      .count();
    
    expect(messages).toBeGreaterThanOrEqual(2);
  });
});
```

### API 测试
```typescript
// e2e/tests/api.spec.ts

import { test, expect } from "@playwright/test";

test.describe("API 端点", () => {
  /**
   * 测试：获取数据库列表
   */
  test("GET /graphs 应该返回数据库列表", async ({ request }) => {
    const response = await request.get("/api/graphs");
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });
  
  /**
   * 测试：查询数据库
   */
  test("POST /graphs/:id 应该执行查询", async ({ request }) => {
    const response = await request.post("/api/graphs/demo_crm", {
      data: {
        chat: ["显示所有用户"],
        result: []
      }
    });
    
    expect(response.ok()).toBeTruthy();
  });
  
  /**
   * 测试：认证
   */
  test("未认证请求应该返回 401", async ({ request }) => {
    const response = await request.delete("/api/graphs/test_db");
    
    expect(response.status()).toBe(401);
  });
});
```

## 测试覆盖率

### 配置覆盖率报告
```python
# pytest.ini 或 pyproject.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = """
    --cov=api
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
"""
```

### 覆盖率目标
- 单元测试覆盖率：≥ 80%
- 关键路径覆盖率：100%
- 分支覆盖率：≥ 70%

## 测试最佳实践

### 1. 测试命名
```python
# ✅ 好的命名
def test_find_tables_returns_empty_list_when_no_tables_exist():
    """清晰描述测试场景和预期结果"""
    pass

# ❌ 不好的命名
def test_1():
    """不清楚测试什么"""
    pass
```

### 2. 测试隔离
```python
# ✅ 每个测试独立
@pytest.fixture
def clean_database():
    """每个测试前清理数据库"""
    db.clear()
    yield
    db.clear()

# ❌ 测试之间有依赖
def test_create_user():
    user = create_user("test")
    # 不清理，影响下一个测试

def test_get_user():
    user = get_user("test")  # 依赖上一个测试
```

### 3. 使用 Fixture
```python
# ✅ 使用 fixture 共享设置
@pytest.fixture
def sample_data():
    return {"id": 1, "name": "test"}

def test_with_fixture(sample_data):
    assert sample_data["id"] == 1

# ❌ 重复设置代码
def test_without_fixture():
    data = {"id": 1, "name": "test"}
    assert data["id"] == 1
```

### 4. 测试边界条件
```python
def test_get_sample_data():
    """测试各种边界条件"""
    # 正常情况
    result = get_sample_data("users", limit=10)
    assert len(result) <= 10
    
    # 边界：limit = 0
    result = get_sample_data("users", limit=0)
    assert len(result) == 0
    
    # 边界：limit = 负数
    with pytest.raises(ValueError):
        get_sample_data("users", limit=-1)
    
    # 边界：表不存在
    with pytest.raises(TableNotFoundError):
        get_sample_data("nonexistent_table", limit=10)
```
