import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { DatabaseProvider } from "@/contexts/DatabaseContext";
import { ChatProvider } from "@/contexts/ChatContext";
import { useFirstLoginGuide } from "@/hooks/useFirstLoginGuide";
import { AIConfigModal } from "@/components/modals/AIConfigModal";
import { useToast } from "@/components/ui/use-toast";
import Index from "./pages/Index";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

/**
 * 应用内容组件
 * 
 * 包含路由和首次登录引导逻辑
 */
const AppContent = () => {
  const { showConfigGuide, setShowConfigGuide } = useFirstLoginGuide();
  const { toast } = useToast();

  /**
   * 处理配置保存
   * 
   * 调用 /api/config/llm POST 接口保存用户配置
   * 
   * @param config - LLM 配置对象
   */
  const handleSaveConfig = async (config: any) => {
    try {
      const response = await fetch("/api/config/llm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || "保存配置失败");
      }

      // 保存成功，关闭模态框
      setShowConfigGuide(false);

      // 显示成功提示
      toast({
        title: "配置保存成功",
        description: "AI 模型配置已更新，您现在可以开始使用 QueryWeaver",
      });
    } catch (error) {
      console.error("保存配置失败:", error);
      
      // 显示错误提示
      toast({
        title: "保存失败",
        description: error instanceof Error ? error.message : "无法保存配置，请重试",
        variant: "destructive",
      });
      
      // 重新抛出错误，让 AIConfigModal 处理
      throw error;
    }
  };

  return (
    <>
      <TooltipProvider>
        <Toaster />
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/settings" element={<Settings />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>

      {/* 首次登录配置引导模态框 */}
      <AIConfigModal
        open={showConfigGuide}
        onClose={() => setShowConfigGuide(false)}
        onSave={handleSaveConfig}
        allowSkip={true}
      />
    </>
  );
};

/**
 * 主应用组件
 * 
 * 提供全局上下文和状态管理
 */
const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <DatabaseProvider>
        <ChatProvider>
          <AppContent />
        </ChatProvider>
      </DatabaseProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
