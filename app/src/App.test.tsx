import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App";

// Mock 所有依赖
vi.mock("@/hooks/useFirstLoginGuide", () => ({
  useFirstLoginGuide: vi.fn(() => ({
    showConfigGuide: false,
    setShowConfigGuide: vi.fn(),
    isChecking: false,
  })),
}));

vi.mock("@/components/modals/AIConfigModal", () => ({
  AIConfigModal: ({ open }: { open: boolean }) => (
    <div data-testid="ai-config-modal">{open ? "Modal Open" : "Modal Closed"}</div>
  ),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Routes: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Route: () => <div>Route</div>,
  };
});

vi.mock("@/contexts/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/contexts/DatabaseContext", () => ({
  DatabaseProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/contexts/ChatContext", () => ({
  ChatProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe("App 组件", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("应该渲染应用", () => {
    render(<App />);
    expect(screen.getByTestId("ai-config-modal")).toBeInTheDocument();
  });

  it("当 showConfigGuide 为 false 时，模态框应该关闭", () => {
    const { useFirstLoginGuide } = require("@/hooks/useFirstLoginGuide");
    useFirstLoginGuide.mockReturnValue({
      showConfigGuide: false,
      setShowConfigGuide: vi.fn(),
      isChecking: false,
    });

    render(<App />);
    expect(screen.getByText("Modal Closed")).toBeInTheDocument();
  });

  it("当 showConfigGuide 为 true 时，模态框应该打开", () => {
    const { useFirstLoginGuide } = require("@/hooks/useFirstLoginGuide");
    useFirstLoginGuide.mockReturnValue({
      showConfigGuide: true,
      setShowConfigGuide: vi.fn(),
      isChecking: false,
    });

    render(<App />);
    expect(screen.getByText("Modal Open")).toBeInTheDocument();
  });
});
