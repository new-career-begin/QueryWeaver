import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AIConfigModal } from './AIConfigModal';

/**
 * AIConfigModal 组件单元测试
 * 
 * 测试覆盖：
 * 1. 组件渲染 - 验证所有表单字段正确显示
 * 2. 提供商切换 - 验证切换时自动更新模型和 Base URL
 * 3. 连接测试 - 验证测试按钮的启用/禁用状态和 API 调用
 * 4. 保存功能 - 验证保存按钮的启用/禁用状态和 API 调用
 * 
 * 需求引用：2.1-2.11
 */

// Mock fetch API
global.fetch = vi.fn();

describe('AIConfigModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
  });

  /**
   * 测试 1: 组件正确渲染所有表单字段
   * 
   * 验收标准：
   * - 显示模态框标题
   * - 显示提供商选择下拉框
   * - 显示 API Key 输入框
   * - 显示 API 端点输入框
   * - 显示对话模型选择
   * - 显示嵌入模型选择
   * - 显示测试连接按钮
   * - 显示保存配置按钮
   * 
   * 需求：2.2, 2.3, 2.4, 2.5, 2.6, 2.7
   */
  describe('组件渲染', () => {
    it('应该渲染所有必需的表单字段', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 验证标题
      expect(screen.getByText('配置 AI 模型')).toBeInTheDocument();

      // 验证提供商选择
      expect(screen.getByText('模型提供商')).toBeInTheDocument();

      // 验证 API Key 输入框
      expect(screen.getByLabelText('API Key')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('输入您的 API Key')).toBeInTheDocument();

      // 验证 API 端点输入框
      expect(screen.getByLabelText('API 端点')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('API 基础 URL')).toBeInTheDocument();

      // 验证对话模型选择
      expect(screen.getByText('对话模型')).toBeInTheDocument();

      // 验证嵌入模型选择
      expect(screen.getByText('嵌入模型')).toBeInTheDocument();

      // 验证按钮
      expect(screen.getByRole('button', { name: /测试连接/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /保存配置/i })).toBeInTheDocument();
    });

    it('当 allowSkip 为 true 时应该显示跳过按钮', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          allowSkip={true}
        />
      );

      expect(screen.getByRole('button', { name: /跳过配置/i })).toBeInTheDocument();
    });

    it('当 allowSkip 为 false 时不应该显示跳过按钮', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          allowSkip={false}
        />
      );

      expect(screen.queryByRole('button', { name: /跳过配置/i })).not.toBeInTheDocument();
    });

    it('当 open 为 false 时不应该渲染模态框', () => {
      render(
        <AIConfigModal
          open={false}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      expect(screen.queryByText('配置 AI 模型')).not.toBeInTheDocument();
    });
  });

  /**
   * 测试 2: 提供商切换时自动更新模型和 Base URL
   * 
   * 验收标准：
   * - 切换到 DeepSeek 时，更新为 deepseek-chat 和 https://api.deepseek.com
   * - 切换到 OpenAI 时，更新为 gpt-4 和 https://api.openai.com/v1
   * - 切换到 Azure 时，更新为 gpt-4 和空 Base URL
   * 
   * 需求：2.3, 2.5, 2.6
   */
  describe('提供商切换', () => {
    it('默认应该选择 DeepSeek 提供商', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 验证默认 Base URL
      const baseUrlInput = screen.getByPlaceholderText('API 基础 URL') as HTMLInputElement;
      expect(baseUrlInput.value).toBe('https://api.deepseek.com');
    });

    it('切换到 OpenAI 时应该更新 Base URL', async () => {
      const user = userEvent.setup();
      
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 点击提供商选择器
      const providerTrigger = screen.getByRole('combobox', { name: /模型提供商/i });
      await user.click(providerTrigger);

      // 选择 OpenAI
      const openaiOption = screen.getByText('OpenAI');
      await user.click(openaiOption);

      // 验证 Base URL 已更新
      await waitFor(() => {
        const baseUrlInput = screen.getByPlaceholderText('API 基础 URL') as HTMLInputElement;
        expect(baseUrlInput.value).toBe('https://api.openai.com/v1');
      });
    });

    it('切换到 Azure 时应该清空 Base URL', async () => {
      const user = userEvent.setup();
      
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 点击提供商选择器
      const providerTrigger = screen.getByRole('combobox', { name: /模型提供商/i });
      await user.click(providerTrigger);

      // 选择 Azure
      const azureOption = screen.getByText('Azure OpenAI');
      await user.click(azureOption);

      // 验证 Base URL 已清空
      await waitFor(() => {
        const baseUrlInput = screen.getByPlaceholderText('API 基础 URL') as HTMLInputElement;
        expect(baseUrlInput.value).toBe('');
      });
    });
  });

  /**
   * 测试 3: 连接测试按钮的启用/禁用状态
   * 
   * 验收标准：
   * - 当 API Key 为空时，测试按钮应该被禁用
   * - 当 API Key 不为空时，测试按钮应该被启用
   * - 测试进行中时，按钮应该显示"测试中..."
   * 
   * 需求：2.8
   */
  describe('连接测试按钮状态', () => {
    it('当 API Key 为空时应该禁用测试按钮', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      const testButton = screen.getByRole('button', { name: /测试连接/i });
      expect(testButton).toBeDisabled();
    });

    it('当 API Key 不为空时应该启用测试按钮', async () => {
      const user = userEvent.setup();
      
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 验证测试按钮已启用
      const testButton = screen.getByRole('button', { name: /测试连接/i });
      expect(testButton).not.toBeDisabled();
    });
  });

  /**
   * 测试 4: 连接测试功能的 API 调用
   * 
   * 验收标准：
   * - 点击测试按钮时应该调用 /api/config/llm/test 端点
   * - 应该发送正确的请求参数（provider, api_key, base_url）
   * - 测试成功时应该显示成功消息
   * - 测试失败时应该显示错误消息
   * 
   * 需求：2.8, 4.1
   */
  describe('连接测试功能', () => {
    it('应该调用测试连接 API 并显示成功结果', async () => {
      const user = userEvent.setup();
      
      // Mock 成功响应
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: '连接成功',
          latency: 234.5,
        }),
      });

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击测试按钮
      const testButton = screen.getByRole('button', { name: /测试连接/i });
      await user.click(testButton);

      // 验证 API 调用
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/config/llm/test',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: expect.stringContaining('sk-test-key-123'),
          })
        );
      });

      // 验证成功消息显示
      await waitFor(() => {
        expect(screen.getByText(/连接成功/i)).toBeInTheDocument();
        expect(screen.getByText(/延迟: 234ms/i)).toBeInTheDocument();
      });
    });

    it('应该显示测试失败的错误消息', async () => {
      const user = userEvent.setup();
      
      // Mock 失败响应
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: false,
          message: 'API Key 无效',
        }),
      });

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-invalid-key');

      // 点击测试按钮
      const testButton = screen.getByRole('button', { name: /测试连接/i });
      await user.click(testButton);

      // 验证错误消息显示
      await waitFor(() => {
        expect(screen.getByText(/API Key 无效/i)).toBeInTheDocument();
      });
    });

    it('应该处理网络错误', async () => {
      const user = userEvent.setup();
      
      // Mock 网络错误
      (global.fetch as any).mockRejectedValueOnce(new Error('网络连接失败'));

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击测试按钮
      const testButton = screen.getByRole('button', { name: /测试连接/i });
      await user.click(testButton);

      // 验证错误消息显示
      await waitFor(() => {
        expect(screen.getByText(/连接测试失败.*网络连接失败/i)).toBeInTheDocument();
      });
    });

    it('测试进行中时应该显示加载状态', async () => {
      const user = userEvent.setup();
      
      // Mock 延迟响应
      (global.fetch as any).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ success: true, message: '连接成功' }),
        }), 100))
      );

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击测试按钮
      const testButton = screen.getByRole('button', { name: /测试连接/i });
      await user.click(testButton);

      // 验证加载状态
      expect(screen.getByText(/测试中.../i)).toBeInTheDocument();
      expect(testButton).toBeDisabled();

      // 等待完成
      await waitFor(() => {
        expect(screen.getByText(/连接成功/i)).toBeInTheDocument();
      });
    });
  });

  /**
   * 测试 5: 保存按钮的启用/禁用状态
   * 
   * 验收标准：
   * - 当 API Key 为空时，保存按钮应该被禁用
   * - 当 API Key 不为空时，保存按钮应该被启用
   * - 保存进行中时，按钮应该显示"保存中..."
   * 
   * 需求：2.9
   */
  describe('保存按钮状态', () => {
    it('当 API Key 为空时应该禁用保存按钮', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      expect(saveButton).toBeDisabled();
    });

    it('当 API Key 不为空时应该启用保存按钮', async () => {
      const user = userEvent.setup();
      
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 验证保存按钮已启用
      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      expect(saveButton).not.toBeDisabled();
    });
  });

  /**
   * 测试 6: 保存功能的 API 调用和模态框关闭
   * 
   * 验收标准：
   * - 点击保存按钮时应该调用 onSave 回调
   * - 应该传递正确的配置对象
   * - 保存成功后应该关闭模态框
   * - 保存失败时应该显示错误消息
   * 
   * 需求：2.9, 2.11
   */
  describe('保存功能', () => {
    it('应该调用 onSave 回调并传递正确的配置', async () => {
      const user = userEvent.setup();
      mockOnSave.mockResolvedValueOnce(undefined);

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击保存按钮
      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      await user.click(saveButton);

      // 验证 onSave 被调用
      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            provider: 'deepseek',
            completion_model: 'deepseek-chat',
            embedding_model: 'text-embedding-ada-002',
            api_key: 'sk-test-key-123',
            base_url: 'https://api.deepseek.com',
          })
        );
      });
    });

    it('保存成功后应该关闭模态框', async () => {
      const user = userEvent.setup();
      mockOnSave.mockResolvedValueOnce(undefined);

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击保存按钮
      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      await user.click(saveButton);

      // 验证模态框关闭
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('保存失败时应该显示错误消息', async () => {
      const user = userEvent.setup();
      mockOnSave.mockRejectedValueOnce(new Error('保存失败：数据库连接错误'));

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击保存按钮
      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      await user.click(saveButton);

      // 验证错误消息显示
      await waitFor(() => {
        expect(screen.getByText(/保存失败.*数据库连接错误/i)).toBeInTheDocument();
      });

      // 验证模态框未关闭
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('保存进行中时应该显示加载状态', async () => {
      const user = userEvent.setup();
      
      // Mock 延迟保存
      mockOnSave.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // 输入 API Key
      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      await user.type(apiKeyInput, 'sk-test-key-123');

      // 点击保存按钮
      const saveButton = screen.getByRole('button', { name: /保存配置/i });
      await user.click(saveButton);

      // 验证加载状态
      expect(screen.getByText(/保存中.../i)).toBeInTheDocument();
      expect(saveButton).toBeDisabled();

      // 等待完成
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  /**
   * 测试 7: 跳过配置功能
   * 
   * 验收标准：
   * - 点击跳过按钮应该关闭模态框
   * - 不应该调用 onSave 回调
   * 
   * 需求：2.12
   */
  describe('跳过配置', () => {
    it('点击跳过按钮应该关闭模态框', async () => {
      const user = userEvent.setup();

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          allowSkip={true}
        />
      );

      // 点击跳过按钮
      const skipButton = screen.getByRole('button', { name: /跳过配置/i });
      await user.click(skipButton);

      // 验证模态框关闭
      expect(mockOnClose).toHaveBeenCalled();
      // 验证未调用保存
      expect(mockOnSave).not.toHaveBeenCalled();
    });
  });

  /**
   * 测试 8: 表单字段交互
   * 
   * 验收标准：
   * - 用户可以输入和修改所有字段
   * - API Key 输入框应该是密码类型
   * 
   * 需求：2.4, 2.5, 2.6, 2.7
   */
  describe('表单字段交互', () => {
    it('应该允许用户输入 API Key', async () => {
      const user = userEvent.setup();

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key') as HTMLInputElement;
      await user.type(apiKeyInput, 'sk-test-key-123');

      expect(apiKeyInput.value).toBe('sk-test-key-123');
    });

    it('API Key 输入框应该是密码类型', () => {
      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      const apiKeyInput = screen.getByPlaceholderText('输入您的 API Key');
      expect(apiKeyInput).toHaveAttribute('type', 'password');
    });

    it('应该允许用户修改 Base URL', async () => {
      const user = userEvent.setup();

      render(
        <AIConfigModal
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      const baseUrlInput = screen.getByPlaceholderText('API 基础 URL') as HTMLInputElement;
      await user.clear(baseUrlInput);
      await user.type(baseUrlInput, 'https://custom.api.com');

      expect(baseUrlInput.value).toBe('https://custom.api.com');
    });
  });
});
