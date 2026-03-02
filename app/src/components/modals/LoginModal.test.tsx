/**
 * LoginModal 组件集成测试
 * 
 * 测试微信和企业微信登录按钮的显示逻辑和重定向行为
 * 
 * 注意：此测试文件需要配置测试框架（如 Vitest + React Testing Library）才能运行
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginModal from './LoginModal';

// Mock fetch API
global.fetch = vi.fn();

describe('LoginModal - 微信和企业微信登录集成测试', () => {
  beforeEach(() => {
    // 重置所有 mock
    vi.clearAllMocks();
    
    // Mock window.location.href
    delete (window as any).location;
    window.location = { href: '' } as any;
  });

  describe('登录按钮显示逻辑', () => {
    it('当微信登录启用时，应该显示微信登录按钮', async () => {
      // 模拟 auth-status API 返回微信登录已启用
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: true,
            wecom: false,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByText('使用微信登录')).toBeInTheDocument();
      });

      // 验证微信登录按钮存在
      const wechatButton = screen.getByTestId('wechat-login-btn');
      expect(wechatButton).toBeInTheDocument();
      expect(wechatButton).toHaveTextContent('使用微信登录');
    });

    it('当企业微信登录启用时，应该显示企业微信登录按钮', async () => {
      // 模拟 auth-status API 返回企业微信登录已启用
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: false,
            wecom: true,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByText('使用企业微信登录')).toBeInTheDocument();
      });

      // 验证企业微信登录按钮存在
      const wecomButton = screen.getByTestId('wecom-login-btn');
      expect(wecomButton).toBeInTheDocument();
      expect(wecomButton).toHaveTextContent('使用企业微信登录');
    });

    it('当微信和企业微信都启用时，应该同时显示两个按钮', async () => {
      // 模拟 auth-status API 返回两者都已启用
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: true,
            github: true,
            wechat: true,
            wecom: true,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByText('使用微信登录')).toBeInTheDocument();
      });

      // 验证所有登录按钮都存在
      expect(screen.getByTestId('google-login-btn')).toBeInTheDocument();
      expect(screen.getByTestId('github-login-btn')).toBeInTheDocument();
      expect(screen.getByTestId('wechat-login-btn')).toBeInTheDocument();
      expect(screen.getByTestId('wecom-login-btn')).toBeInTheDocument();
    });

    it('当微信登录未启用时，不应该显示微信登录按钮', async () => {
      // 模拟 auth-status API 返回微信登录未启用
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: true,
            github: true,
            wechat: false,
            wecom: false,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByText('使用 Google 登录')).toBeInTheDocument();
      });

      // 验证微信登录按钮不存在
      expect(screen.queryByTestId('wechat-login-btn')).not.toBeInTheDocument();
      expect(screen.queryByTestId('wecom-login-btn')).not.toBeInTheDocument();
    });
  });

  describe('登录按钮点击重定向行为', () => {
    it('点击微信登录按钮应该重定向到微信登录端点', async () => {
      // 模拟 auth-status API
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: true,
            wecom: false,
            email: false,
          },
        }),
      });

      const user = userEvent.setup();
      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待微信登录按钮出现
      await waitFor(() => {
        expect(screen.getByTestId('wechat-login-btn')).toBeInTheDocument();
      });

      // 点击微信登录按钮
      const wechatButton = screen.getByTestId('wechat-login-btn');
      await user.click(wechatButton);

      // 验证重定向到正确的 URL
      expect(window.location.href).toContain('/login/wechat');
    });

    it('点击企业微信登录按钮应该重定向到企业微信登录端点', async () => {
      // 模拟 auth-status API
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: false,
            wecom: true,
            email: false,
          },
        }),
      });

      const user = userEvent.setup();
      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待企业微信登录按钮出现
      await waitFor(() => {
        expect(screen.getByTestId('wecom-login-btn')).toBeInTheDocument();
      });

      // 点击企业微信登录按钮
      const wecomButton = screen.getByTestId('wecom-login-btn');
      await user.click(wecomButton);

      // 验证重定向到正确的 URL
      expect(window.location.href).toContain('/login/wecom');
    });
  });

  describe('加载状态', () => {
    it('在获取认证配置时应该显示加载指示器', async () => {
      // 模拟一个延迟的 API 响应
      (global.fetch as any).mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({
                    authenticated: false,
                    auth_methods: {
                      google: true,
                      github: true,
                      wechat: true,
                      wecom: true,
                      email: false,
                    },
                  }),
                }),
              100
            )
          )
      );

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 验证加载指示器存在
      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toBeInTheDocument();

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByRole('status', { hidden: true })).not.toBeInTheDocument();
      });
    });
  });

  describe('错误处理', () => {
    it('当 API 请求失败时应该显示默认配置', async () => {
      // 模拟 API 请求失败
      (global.fetch as any).mockRejectedValueOnce(new Error('网络错误'));

      // Mock console.error 以避免测试输出中的错误信息
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 等待加载完成
      await waitFor(() => {
        expect(screen.queryByRole('status', { hidden: true })).not.toBeInTheDocument();
      });

      // 验证显示了默认的 Google 和 GitHub 登录按钮
      expect(screen.getByTestId('google-login-btn')).toBeInTheDocument();
      expect(screen.getByTestId('github-login-btn')).toBeInTheDocument();

      // 验证 console.error 被调用
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '获取认证配置失败:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('UI 文本和样式', () => {
    it('应该显示中文的对话框标题和描述', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: true,
            github: true,
            wechat: true,
            wecom: true,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      // 验证中文标题和描述
      expect(screen.getByText('欢迎使用 QueryWeaver')).toBeInTheDocument();
      expect(screen.getByText('登录以访问您的数据库并开始查询')).toBeInTheDocument();
    });

    it('微信登录按钮应该使用微信品牌色', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: true,
            wecom: false,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      await waitFor(() => {
        expect(screen.getByTestId('wechat-login-btn')).toBeInTheDocument();
      });

      const wechatButton = screen.getByTestId('wechat-login-btn');
      
      // 验证按钮包含微信品牌色相关的类名
      expect(wechatButton.className).toContain('from-[#07c160]');
      expect(wechatButton.className).toContain('to-[#06ad56]');
    });

    it('企业微信登录按钮应该使用企业微信品牌色', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authenticated: false,
          auth_methods: {
            google: false,
            github: false,
            wechat: false,
            wecom: true,
            email: false,
          },
        }),
      });

      render(<LoginModal open={true} onOpenChange={() => {}} />);

      await waitFor(() => {
        expect(screen.getByTestId('wecom-login-btn')).toBeInTheDocument();
      });

      const wecomButton = screen.getByTestId('wecom-login-btn');
      
      // 验证按钮包含企业微信品牌色相关的类名
      expect(wecomButton.className).toContain('from-[#2e7cf6]');
      expect(wecomButton.className).toContain('to-[#2567d9]');
    });
  });
});
