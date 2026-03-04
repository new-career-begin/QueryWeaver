import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useFirstLoginGuide } from "./useFirstLoginGuide";

// Mock fetch
global.fetch = vi.fn();

describe("useFirstLoginGuide", () => {
  beforeEach(() => {
    // 清除所有 mock
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("应该初始化时 showConfigGuide 为 false", () => {
    // Mock API 返回已配置
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        config: {
          provider: "deepseek",
          completion_model: "deepseek-chat",
        },
      }),
    });

    const { result } = renderHook(() => useFirstLoginGuide());

    expect(result.current.showConfigGuide).toBe(false);
    expect(result.current.isChecking).toBe(true);
  });

  it("当用户未配置 LLM 时应该设置 showConfigGuide 为 true", async () => {
    // Mock API 返回未配置
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        config: null,
      }),
    });

    const { result } = renderHook(() => useFirstLoginGuide());

    // 等待异步操作完成
    await waitFor(() => {
      expect(result.current.isChecking).toBe(false);
    });

    expect(result.current.showConfigGuide).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith("/api/config/llm", {
      credentials: "include",
    });
  });

  it("当用户已配置 LLM 时应该保持 showConfigGuide 为 false", async () => {
    // Mock API 返回已配置
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        config: {
          provider: "deepseek",
          completion_model: "deepseek-chat",
          embedding_model: "text-embedding-ada-002",
        },
      }),
    });

    const { result } = renderHook(() => useFirstLoginGuide());

    await waitFor(() => {
      expect(result.current.isChecking).toBe(false);
    });

    expect(result.current.showConfigGuide).toBe(false);
  });

  it("当 API 请求失败时应该保持 showConfigGuide 为 false", async () => {
    // Mock API 返回错误
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      statusText: "Unauthorized",
    });

    const { result } = renderHook(() => useFirstLoginGuide());

    await waitFor(() => {
      expect(result.current.isChecking).toBe(false);
    });

    expect(result.current.showConfigGuide).toBe(false);
  });

  it("当网络错误时应该保持 showConfigGuide 为 false", async () => {
    // Mock 网络错误
    (global.fetch as any).mockRejectedValueOnce(
      new Error("Network error")
    );

    const { result } = renderHook(() => useFirstLoginGuide());

    await waitFor(() => {
      expect(result.current.isChecking).toBe(false);
    });

    expect(result.current.showConfigGuide).toBe(false);
  });

  it("应该允许手动设置 showConfigGuide", async () => {
    // Mock API 返回未配置
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        config: null,
      }),
    });

    const { result } = renderHook(() => useFirstLoginGuide());

    await waitFor(() => {
      expect(result.current.showConfigGuide).toBe(true);
    });

    // 手动关闭引导
    result.current.setShowConfigGuide(false);

    await waitFor(() => {
      expect(result.current.showConfigGuide).toBe(false);
    });
  });

  it("应该在组件挂载时自动检查配置状态", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        config: null,
      }),
    });

    renderHook(() => useFirstLoginGuide());

    // 验证 fetch 被调用
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith("/api/config/llm", {
        credentials: "include",
      });
    });
  });
});
