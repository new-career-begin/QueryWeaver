# QueryWeaver 前端测试指南

## 快速开始

### 1. 安装测试依赖

```bash
cd app
npm install
```

这将安装以下测试相关的依赖：

- `vitest` - 快速的单元测试框架
- `@testing-library/react` - React 组件测试工具
- `@testing-library/user-event` - 用户交互模拟
- `@testing-library/jest-dom` - DOM 断言匹配器
- `jsdom` - 浏览器环境模拟
- `@vitest/ui` - 测试 UI 界面

### 2. 运行测试

```bash
# 运行所有测试
npm test

# 运行测试并查看 UI 界面
npm run test:ui

# 运行测试并生成覆盖率报告
npm run test:coverage

# 监听模式（开发时推荐）
npm test -- --watch
```

## 测试文件结构

```
app/
├── src/
│   ├── components/
│   │   └── modals/
│   │       ├── AIConfigModal.tsx          # 组件源码
│   │       ├── AIConfigModal.test.tsx     # 组件测试
│   │       └── README.test.md             # 测试说明
│   └── test/
│       └── setup.ts                       # 测试环境配置
├── vitest.config.ts                       # Vitest 配置
└── TESTING.md                             # 本文档
```

## 当前测试覆盖

### AIConfigModal 组件测试

位置：`app/src/components/modals/AIConfigModal.test.tsx`

**测试场景**：
- ✅ 组件渲染（8 个测试用例）
- ✅ 提供商切换（3 个测试用例）
- ✅ 连接测试按钮状态（2 个测试用例）
- ✅ 连接测试功能（5 个测试用例）
- ✅ 保存按钮状态（2 个测试用例）
- ✅ 保存功能（4 个测试用例）
- ✅ 跳过配置（1 个测试用例）
- ✅ 表单字段交互（3 个测试用例）

**总计**：28 个测试用例

**需求覆盖**：需求 2.1-2.11

详细说明请查看：[AIConfigModal 测试文档](./src/components/modals/README.test.md)

## 编写新测试

### 测试文件命名规范

- 组件测试：`ComponentName.test.tsx`
- Hook 测试：`useHookName.test.ts`
- 工具函数测试：`utilityName.test.ts`

### 测试模板

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { YourComponent } from './YourComponent';

describe('YourComponent', () => {
  const mockProps = {
    // 定义 mock props
  };

  beforeEach(() => {
    // 每个测试前的清理工作
    vi.clearAllMocks();
  });

  describe('功能描述', () => {
    it('应该执行预期行为', async () => {
      // 1. 准备
      const user = userEvent.setup();
      render(<YourComponent {...mockProps} />);

      // 2. 执行
      const button = screen.getByRole('button', { name: /按钮文本/i });
      await user.click(button);

      // 3. 断言
      await waitFor(() => {
        expect(screen.getByText(/预期结果/i)).toBeInTheDocument();
      });
    });
  });
});
```

### 测试最佳实践

#### 1. 使用语义化查询

优先级顺序：

1. `getByRole` - 最推荐，符合可访问性
2. `getByLabelText` - 表单元素
3. `getByPlaceholderText` - 输入框
4. `getByText` - 文本内容
5. `getByTestId` - 最后选择

```typescript
// ✅ 推荐
screen.getByRole('button', { name: /提交/i });
screen.getByLabelText('用户名');

// ⚠️ 避免
screen.getByTestId('submit-button');
```

#### 2. 等待异步操作

```typescript
// ✅ 使用 waitFor
await waitFor(() => {
  expect(screen.getByText('加载完成')).toBeInTheDocument();
});

// ✅ 使用 findBy（内置等待）
const element = await screen.findByText('加载完成');
expect(element).toBeInTheDocument();

// ❌ 不要直接断言异步结果
expect(screen.getByText('加载完成')).toBeInTheDocument();
```

#### 3. Mock 外部依赖

```typescript
// Mock fetch API
global.fetch = vi.fn();

beforeEach(() => {
  (global.fetch as any).mockClear();
});

it('应该调用 API', async () => {
  (global.fetch as any).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ data: 'test' }),
  });

  // 测试代码...

  expect(global.fetch).toHaveBeenCalledWith(
    '/api/endpoint',
    expect.objectContaining({
      method: 'POST',
    })
  );
});
```

#### 4. 测试用户行为而非实现

```typescript
// ✅ 测试用户看到和做的事情
const input = screen.getByLabelText('邮箱');
await user.type(input, 'test@example.com');
expect(input).toHaveValue('test@example.com');

// ❌ 测试实现细节
expect(component.state.email).toBe('test@example.com');
```

## 测试配置

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,              // 启用全局 API
    environment: 'jsdom',       // 使用 jsdom 模拟浏览器
    setupFiles: ['./src/test/setup.ts'],  // 测试设置文件
    css: true,                  // 支持 CSS
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),  // 路径别名
    },
  },
});
```

### src/test/setup.ts

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// 扩展 expect 断言
expect.extend(matchers);

// 每个测试后清理
afterEach(() => {
  cleanup();
});
```

## 调试测试

### 1. 查看当前 DOM

```typescript
import { screen } from '@testing-library/react';

// 打印整个 DOM
screen.debug();

// 打印特定元素
const element = screen.getByRole('button');
screen.debug(element);
```

### 2. 使用 Vitest UI

```bash
npm run test:ui
```

在浏览器中打开 `http://localhost:51204/__vitest__/` 查看测试结果和覆盖率。

### 3. 查看测试覆盖率

```bash
npm run test:coverage
```

覆盖率报告将生成在 `app/coverage/` 目录。

## 常见问题

### Q: 测试超时怎么办？

**A**: 确保正确等待异步操作：

```typescript
// ❌ 错误
expect(screen.getByText('加载完成')).toBeInTheDocument();

// ✅ 正确
await waitFor(() => {
  expect(screen.getByText('加载完成')).toBeInTheDocument();
});
```

### Q: 找不到元素怎么办？

**A**: 使用 `screen.debug()` 查看当前 DOM，检查：
1. 元素是否已渲染
2. 查询方式是否正确
3. 是否需要等待异步操作

### Q: Mock 不生效怎么办？

**A**: 确保：
1. Mock 在组件渲染前设置
2. 在 `beforeEach` 中清理 mock
3. Mock 的函数签名正确

### Q: 如何测试 Radix UI 组件？

**A**: Radix UI 组件使用 Portal，需要特殊处理：

```typescript
// 使用 getByRole 查询
const dialog = screen.getByRole('dialog');

// 或者查询 Portal 容器
const portal = document.querySelector('[data-radix-portal]');
```

## 持续集成

建议在 CI/CD 中运行测试：

```yaml
# .github/workflows/test.yml
name: Frontend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: app/package-lock.json
      
      - name: Install dependencies
        run: cd app && npm ci
      
      - name: Run tests
        run: cd app && npm test
      
      - name: Generate coverage
        run: cd app && npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./app/coverage
```

## 测试目标

- **单元测试覆盖率**: ≥ 80%
- **关键路径覆盖**: 100%
- **测试执行时间**: < 30 秒

## 参考资源

- [Vitest 官方文档](https://vitest.dev/)
- [React Testing Library 文档](https://testing-library.com/react)
- [Testing Library 最佳实践](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Vitest UI](https://vitest.dev/guide/ui.html)
- [用户事件 API](https://testing-library.com/docs/user-event/intro)

## 贡献指南

在提交 PR 前，请确保：

1. ✅ 所有测试通过
2. ✅ 新功能有对应的测试
3. ✅ 测试覆盖率不降低
4. ✅ 遵循测试最佳实践
5. ✅ 测试文档已更新
