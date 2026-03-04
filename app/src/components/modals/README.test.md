# AIConfigModal 组件测试说明

## 测试概述

本测试文件 `AIConfigModal.test.tsx` 为 AIConfigModal 组件提供全面的单元测试覆盖。

## 测试覆盖范围

### 1. 组件渲染测试
- ✅ 验证所有表单字段正确显示（提供商、API Key、Base URL、模型选择）
- ✅ 验证按钮正确渲染（测试连接、保存配置、跳过配置）
- ✅ 验证 allowSkip 属性控制跳过按钮的显示
- ✅ 验证 open 属性控制模态框的显示/隐藏

### 2. 提供商切换测试
- ✅ 验证默认选择 DeepSeek 提供商
- ✅ 验证切换到 OpenAI 时自动更新 Base URL
- ✅ 验证切换到 Azure 时清空 Base URL
- ✅ 验证切换提供商时自动更新可用模型列表

### 3. 连接测试功能
- ✅ 验证 API Key 为空时禁用测试按钮
- ✅ 验证 API Key 不为空时启用测试按钮
- ✅ 验证测试连接时调用正确的 API 端点
- ✅ 验证测试成功时显示成功消息和延迟信息
- ✅ 验证测试失败时显示错误消息
- ✅ 验证网络错误时的错误处理
- ✅ 验证测试进行中时显示加载状态

### 4. 保存功能测试
- ✅ 验证 API Key 为空时禁用保存按钮
- ✅ 验证 API Key 不为空时启用保存按钮
- ✅ 验证保存时调用 onSave 回调并传递正确的配置
- ✅ 验证保存成功后关闭模态框
- ✅ 验证保存失败时显示错误消息且不关闭模态框
- ✅ 验证保存进行中时显示加载状态

### 5. 表单交互测试
- ✅ 验证用户可以输入 API Key
- ✅ 验证 API Key 输入框为密码类型
- ✅ 验证用户可以修改 Base URL

### 6. 跳过配置测试
- ✅ 验证点击跳过按钮关闭模态框
- ✅ 验证跳过时不调用 onSave 回调

## 需求覆盖

本测试覆盖以下需求：

- **需求 2.1**: 用户登录后显示配置页面
- **需求 2.2**: 提供模型提供商选择下拉框
- **需求 2.3**: 显示 DeepSeek 特定配置字段
- **需求 2.4**: 提供 API Key 输入框（密码遮蔽）
- **需求 2.5**: 提供 API Base URL 输入框
- **需求 2.6**: 提供对话模型选择下拉框
- **需求 2.7**: 提供嵌入模型选择下拉框
- **需求 2.8**: 测试连接功能
- **需求 2.9**: 保存配置到数据库
- **需求 2.11**: 保存成功后关闭配置页面
- **需求 2.12**: 提供跳过配置选项

## 运行测试

### 安装依赖

首先安装测试所需的依赖：

```bash
cd app
npm install
```

### 运行所有测试

```bash
npm test
```

### 运行测试并查看 UI

```bash
npm run test:ui
```

### 运行测试并生成覆盖率报告

```bash
npm run test:coverage
```

### 运行特定测试文件

```bash
npm test AIConfigModal.test.tsx
```

### 监听模式（开发时使用）

```bash
npm test -- --watch
```

## 测试技术栈

- **Vitest**: 快速的单元测试框架
- **React Testing Library**: React 组件测试工具
- **@testing-library/user-event**: 模拟用户交互
- **@testing-library/jest-dom**: 额外的 DOM 断言匹配器
- **jsdom**: 浏览器环境模拟

## 测试最佳实践

### 1. 测试用户行为而非实现细节

```typescript
// ✅ 好的做法：测试用户看到和做的事情
expect(screen.getByRole('button', { name: /保存配置/i })).toBeInTheDocument();

// ❌ 避免：测试实现细节
expect(wrapper.find('.save-button')).toHaveLength(1);
```

### 2. 使用语义化查询

```typescript
// ✅ 优先使用 getByRole
screen.getByRole('button', { name: /测试连接/i })

// ✅ 其次使用 getByLabelText
screen.getByLabelText('API Key')

// ⚠️ 最后才使用 getByTestId
screen.getByTestId('api-key-input')
```

### 3. 等待异步操作

```typescript
// ✅ 使用 waitFor 等待异步更新
await waitFor(() => {
  expect(screen.getByText(/连接成功/i)).toBeInTheDocument();
});
```

### 4. 清理和隔离测试

```typescript
// ✅ 每个测试前清理 mock
beforeEach(() => {
  vi.clearAllMocks();
});
```

## 故障排查

### 问题：测试超时

**原因**: 异步操作未正确等待

**解决方案**: 使用 `waitFor` 或 `findBy*` 查询

```typescript
// ❌ 错误
expect(screen.getByText('加载完成')).toBeInTheDocument();

// ✅ 正确
await waitFor(() => {
  expect(screen.getByText('加载完成')).toBeInTheDocument();
});
```

### 问题：找不到元素

**原因**: 查询方式不正确或元素未渲染

**解决方案**: 
1. 使用 `screen.debug()` 查看当前 DOM
2. 检查元素是否条件渲染
3. 使用更宽松的查询（如正则表达式）

```typescript
// 调试当前 DOM
screen.debug();

// 使用正则表达式匹配
screen.getByText(/保存/i);
```

### 问题：Mock 未生效

**原因**: Mock 设置时机不对或未正确清理

**解决方案**:
1. 在 `beforeEach` 中清理 mock
2. 确保 mock 在组件渲染前设置

```typescript
beforeEach(() => {
  vi.clearAllMocks();
  (global.fetch as any).mockClear();
});
```

## 扩展测试

如果需要添加新的测试用例，请遵循以下模式：

```typescript
describe('新功能测试', () => {
  it('应该执行预期行为', async () => {
    // 1. 准备：设置测试环境
    const user = userEvent.setup();
    render(<AIConfigModal {...props} />);
    
    // 2. 执行：触发用户操作
    const button = screen.getByRole('button', { name: /操作/i });
    await user.click(button);
    
    // 3. 断言：验证结果
    await waitFor(() => {
      expect(screen.getByText(/预期结果/i)).toBeInTheDocument();
    });
  });
});
```

## 持续集成

建议在 CI/CD 流程中运行测试：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd app && npm install
      - run: cd app && npm test
      - run: cd app && npm run test:coverage
```

## 参考资源

- [Vitest 文档](https://vitest.dev/)
- [React Testing Library 文档](https://testing-library.com/react)
- [Testing Library 最佳实践](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [用户事件 API](https://testing-library.com/docs/user-event/intro)
