---
inclusion: fileMatch
fileMatchPattern: "app/src/**/*.{tsx,ts,jsx,js}"
---

# React 前端开发规范

## 组件设计原则

### 组件命名和结构
```typescript
// 组件文件名使用 PascalCase
// ChatInterface.tsx

import { useState, useEffect } from "react";

/**
 * 聊天界面组件
 * 
 * 提供用户与 AI 进行自然语言查询的交互界面
 * 
 * @param disabled - 是否禁用输入
 * @param onProcessingChange - 处理状态变化回调
 * @param useMemory - 是否使用对话记忆
 */
interface ChatInterfaceProps {
  disabled?: boolean;
  onProcessingChange?: (processing: boolean) => void;
  useMemory?: boolean;
  useRulesFromDatabase?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  disabled = false,
  onProcessingChange,
  useMemory = true,
  useRulesFromDatabase = false,
}) => {
  // 组件实现
  return <div>...</div>;
};
```

### 自定义 Hooks
```typescript
// hooks/useDatabase.ts

import { useState, useEffect } from "react";

/**
 * 数据库连接管理 Hook
 * 
 * 提供数据库列表、选择、上传等功能
 * 
 * @returns 数据库管理相关的状态和方法
 */
export const useDatabase = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载数据库列表
  const loadGraphs = async () => {
    setLoading(true);
    try {
      const data = await DatabaseService.getGraphs();
      setGraphs(data);
    } catch (error) {
      console.error("加载数据库列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphs();
  }, []);

  return {
    graphs,
    selectedGraph,
    loading,
    selectGraph: setSelectedGraph,
    refreshGraphs: loadGraphs,
  };
};
```

## TypeScript 类型定义

### 接口和类型
```typescript
// types/api.ts

/**
 * 数据库图信息
 */
export interface Graph {
  /** 图数据库唯一标识 */
  id: string;
  /** 显示名称 */
  name: string;
  /** 数据库类型 (postgres, mysql) */
  type?: "postgres" | "mysql";
  /** 创建时间 */
  createdAt?: string;
}

/**
 * 查询请求参数
 */
export interface QueryRequest {
  /** 聊天消息列表 */
  chat: string[];
  /** 历史查询结果 */
  result?: QueryResult[];
  /** 额外的查询指令 */
  instructions?: string;
  /** 是否使用对话记忆 */
  useMemory?: boolean;
}

/**
 * 查询结果
 */
export interface QueryResult {
  /** SQL 查询语句 */
  sql: string;
  /** 查询返回的数据 */
  data: Record<string, any>[];
  /** 执行时间(毫秒) */
  executionTime?: number;
}

/**
 * API 响应包装类型
 */
export type ApiResponse<T> = {
  success: true;
  data: T;
} | {
  success: false;
  error: {
    code: string;
    message: string;
  };
};
```

## 状态管理

### Context 使用规范
```typescript
// contexts/DatabaseContext.tsx

import { createContext, useContext, useState, ReactNode } from "react";

/**
 * 数据库上下文类型定义
 */
interface DatabaseContextType {
  graphs: Graph[];
  selectedGraph: Graph | null;
  selectGraph: (graphId: string) => void;
  uploadSchema: (file: File, name: string) => Promise<void>;
}

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

/**
 * 数据库上下文提供者
 */
export const DatabaseProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);

  const selectGraph = (graphId: string) => {
    const graph = graphs.find(g => g.id === graphId);
    if (graph) {
      setSelectedGraph(graph);
      // 保存到 localStorage
      localStorage.setItem("selectedGraphId", graphId);
    }
  };

  const uploadSchema = async (file: File, name: string) => {
    // 上传逻辑
  };

  return (
    <DatabaseContext.Provider
      value={{
        graphs,
        selectedGraph,
        selectGraph,
        uploadSchema,
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
};

/**
 * 使用数据库上下文的 Hook
 */
export const useDatabase = () => {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error("useDatabase 必须在 DatabaseProvider 内部使用");
  }
  return context;
};
```

## 组件优化

### React.memo 和 useCallback
```typescript
import { memo, useCallback, useMemo } from "react";

/**
 * 聊天消息组件（已优化）
 */
interface ChatMessageProps {
  message: string;
  sender: "user" | "assistant";
  timestamp: Date;
  onDelete?: (id: string) => void;
}

export const ChatMessage = memo<ChatMessageProps>(({
  message,
  sender,
  timestamp,
  onDelete,
}) => {
  // 使用 useCallback 避免函数重新创建
  const handleDelete = useCallback(() => {
    onDelete?.(message);
  }, [message, onDelete]);

  // 使用 useMemo 缓存计算结果
  const formattedTime = useMemo(() => {
    return timestamp.toLocaleTimeString("zh-CN");
  }, [timestamp]);

  return (
    <div className={`message ${sender}`}>
      <p>{message}</p>
      <span>{formattedTime}</span>
      {onDelete && (
        <button onClick={handleDelete}>删除</button>
      )}
    </div>
  );
});

ChatMessage.displayName = "ChatMessage";
```

## 错误处理

### 错误边界组件
```typescript
// components/ErrorBoundary.tsx

import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * 错误边界组件
 * 
 * 捕获子组件树中的 JavaScript 错误，记录错误并显示备用 UI
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("组件错误:", error, errorInfo);
    // 可以将错误发送到错误追踪服务
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-container">
          <h2>出错了</h2>
          <p>抱歉，页面遇到了问题。请刷新页面重试。</p>
          <details>
            <summary>错误详情</summary>
            <pre>{this.state.error?.message}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 异步错误处理
```typescript
// services/database.ts

import { toast } from "@/components/ui/use-toast";

/**
 * 数据库服务类
 */
export class DatabaseService {
  /**
   * 获取数据库列表
   */
  static async getGraphs(): Promise<Graph[]> {
    try {
      const response = await fetch("/api/graphs", {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("获取数据库列表失败:", error);
      
      // 显示用户友好的错误提示
      toast({
        title: "加载失败",
        description: error instanceof Error 
          ? error.message 
          : "无法加载数据库列表，请检查网络连接",
        variant: "destructive",
      });
      
      throw error;
    }
  }

  /**
   * 删除数据库
   */
  static async deleteGraph(graphId: string): Promise<void> {
    try {
      const response = await fetch(`/api/graphs/${graphId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || "删除失败");
      }
    } catch (error) {
      console.error(`删除数据库 ${graphId} 失败:`, error);
      throw error;
    }
  }
}
```

## 性能优化

### 懒加载和代码分割
```typescript
// App.tsx

import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LoadingSpinner from "@/components/ui/loading-spinner";

// 使用 lazy 进行代码分割
const Index = lazy(() => import("./pages/Index"));
const Settings = lazy(() => import("./pages/Settings"));
const NotFound = lazy(() => import("./pages/NotFound"));

const App = () => (
  <BrowserRouter>
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  </BrowserRouter>
);

export default App;
```

### 虚拟滚动
```typescript
// 对于长列表使用虚拟滚动
import { useVirtualizer } from "@tanstack/react-virtual";

/**
 * 虚拟化消息列表组件
 */
export const VirtualMessageList: React.FC<{ messages: Message[] }> = ({ messages }) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // 估计每项高度
    overscan: 5, // 预渲染项数
  });

  return (
    <div ref={parentRef} className="message-list">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: "relative",
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <ChatMessage message={messages[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 可访问性 (a11y)

### 语义化 HTML 和 ARIA
```typescript
/**
 * 可访问的模态框组件
 */
export const AccessibleModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}> = ({ isOpen, onClose, title, children }) => {
  useEffect(() => {
    if (isOpen) {
      // 禁用背景滚动
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = "";
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="modal-overlay"
      onClick={onClose}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="modal-title">{title}</h2>
        <button
          onClick={onClose}
          aria-label="关闭对话框"
          className="close-button"
        >
          ×
        </button>
        {children}
      </div>
    </div>
  );
};
```

## 测试规范

### 组件测试
```typescript
// ChatInterface.test.tsx

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatInterface } from "./ChatInterface";

describe("ChatInterface", () => {
  it("应该渲染输入框和发送按钮", () => {
    render(<ChatInterface />);
    
    expect(screen.getByPlaceholderText(/输入您的问题/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /发送/i })).toBeInTheDocument();
  });

  it("当禁用时应该禁用输入", () => {
    render(<ChatInterface disabled />);
    
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    expect(input).toBeDisabled();
  });

  it("应该在发送消息时调用回调", async () => {
    const onProcessingChange = jest.fn();
    render(<ChatInterface onProcessingChange={onProcessingChange} />);
    
    const input = screen.getByPlaceholderText(/输入您的问题/i);
    const sendButton = screen.getByRole("button", { name: /发送/i });
    
    fireEvent.change(input, { target: { value: "测试查询" } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(onProcessingChange).toHaveBeenCalledWith(true);
    });
  });
});
```

## 样式规范

### Tailwind CSS 使用
```typescript
// 使用 clsx 或 cn 工具函数组合类名
import { cn } from "@/lib/utils";

export const Button: React.FC<{
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  children: ReactNode;
}> = ({ variant = "primary", size = "md", disabled, children }) => {
  return (
    <button
      className={cn(
        // 基础样式
        "rounded-lg font-medium transition-colors",
        // 尺寸变体
        {
          "px-3 py-1.5 text-sm": size === "sm",
          "px-4 py-2 text-base": size === "md",
          "px-6 py-3 text-lg": size === "lg",
        },
        // 颜色变体
        {
          "bg-purple-600 text-white hover:bg-purple-700": variant === "primary",
          "bg-gray-200 text-gray-800 hover:bg-gray-300": variant === "secondary",
          "bg-red-600 text-white hover:bg-red-700": variant === "danger",
        },
        // 禁用状态
        disabled && "opacity-50 cursor-not-allowed"
      )}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```
