import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Save, TestTube, AlertCircle, CheckCircle, Loader2 } from "lucide-react";

/**
 * 模型选项配置
 * 定义每个提供商支持的模型列表和默认端点
 */
const MODEL_OPTIONS = {
  deepseek: {
    completion: ["deepseek-chat", "deepseek-coder"],
    embedding: ["text-embedding-ada-002"], // 暂用 OpenAI
    baseUrl: "https://api.deepseek.com",
  },
  openai: {
    completion: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
    embedding: ["text-embedding-ada-002", "text-embedding-3-small"],
    baseUrl: "https://api.openai.com/v1",
  },
  azure: {
    completion: ["gpt-4", "gpt-35-turbo"],
    embedding: ["text-embedding-ada-002"],
    baseUrl: "", // 需要用户提供
  },
} as const;

/**
 * LLM 配置接口
 */
interface LLMConfig {
  /** 模型提供商 */
  provider: "deepseek" | "openai" | "azure";
  /** 对话模型名称 */
  completion_model: string;
  /** 嵌入模型名称 */
  embedding_model: string;
  /** API 密钥 */
  api_key: string;
  /** API 基础 URL */
  base_url?: string;
  /** 额外参数 */
  parameters?: Record<string, any>;
}

/**
 * AI 配置模态框组件属性
 */
interface AIConfigModalProps {
  /** 是否打开模态框 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 保存配置回调 */
  onSave: (config: LLMConfig) => Promise<void>;
  /** 是否允许跳过配置 */
  allowSkip?: boolean;
}

/**
 * AI 配置模态框组件
 * 
 * 提供用户配置 AI 模型的界面，支持 DeepSeek、OpenAI 和 Azure OpenAI
 * 
 * @param open - 是否打开模态框
 * @param onClose - 关闭回调
 * @param onSave - 保存配置回调
 * @param allowSkip - 是否允许跳过配置（默认 true）
 */
export const AIConfigModal: React.FC<AIConfigModalProps> = ({
  open,
  onClose,
  onSave,
  allowSkip = true,
}) => {
  // 配置状态
  const [config, setConfig] = useState<LLMConfig>({
    provider: "deepseek",
    completion_model: "deepseek-chat",
    embedding_model: "text-embedding-ada-002",
    api_key: "",
    base_url: "https://api.deepseek.com",
  });

  // UI 状态
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    latency?: number;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  /**
   * 当提供商改变时，自动更新默认值
   * 
   * 功能：
   * 1. 更新对话模型为该提供商的第一个可用模型
   * 2. 更新嵌入模型为该提供商的第一个可用模型
   * 3. 更新 Base URL 为该提供商的默认端点
   */
  useEffect(() => {
    const options = MODEL_OPTIONS[config.provider];
    setConfig((prev) => ({
      ...prev,
      completion_model: options.completion[0],
      embedding_model: options.embedding[0],
      base_url: options.baseUrl,
    }));
  }, [config.provider]);

  /**
   * 测试连接
   */
  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch("/api/config/llm/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          provider: config.provider,
          api_key: config.api_key,
          base_url: config.base_url,
        }),
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: "连接测试失败：" + (error instanceof Error ? error.message : "未知错误"),
      });
    } finally {
      setTesting(false);
    }
  };

  /**
   * 保存配置
   */
  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(config);
      onClose();
    } catch (error) {
      setTestResult({
        success: false,
        message: "保存失败：" + (error instanceof Error ? error.message : "未知错误"),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] bg-gray-900 text-white border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">配置 AI 模型</DialogTitle>
          <DialogDescription className="text-gray-400">
            配置用于 Text2SQL 的 AI 模型提供商和参数。选择适合您的模型以获得最佳体验。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 提供商选择 */}
          <div className="space-y-2">
            <Label htmlFor="provider" className="text-sm font-medium text-gray-200">
              模型提供商
            </Label>
            <Select
              value={config.provider}
              onValueChange={(value) =>
                setConfig({ ...config, provider: value as LLMConfig["provider"] })
              }
            >
              <SelectTrigger
                id="provider"
                className="bg-gray-800 border-gray-700 text-white focus:border-purple-500 focus:ring-purple-500"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="deepseek" className="text-white hover:bg-gray-700">
                  DeepSeek（推荐，高性价比）
                </SelectItem>
                <SelectItem value="openai" className="text-white hover:bg-gray-700">
                  OpenAI
                </SelectItem>
                <SelectItem value="azure" className="text-white hover:bg-gray-700">
                  Azure OpenAI
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <Label htmlFor="api-key" className="text-sm font-medium text-gray-200">
              API Key
            </Label>
            <Input
              id="api-key"
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
              placeholder="输入您的 API Key"
              className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>

          {/* API 端点 */}
          <div className="space-y-2">
            <Label htmlFor="base-url" className="text-sm font-medium text-gray-200">
              API 端点
            </Label>
            <Input
              id="base-url"
              type="text"
              value={config.base_url}
              onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
              placeholder="API 基础 URL"
              className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-purple-500 focus:ring-purple-500"
            />
          </div>

          {/* 对话模型 */}
          <div className="space-y-2">
            <Label htmlFor="completion-model" className="text-sm font-medium text-gray-200">
              对话模型
            </Label>
            <Select
              value={config.completion_model}
              onValueChange={(value) => setConfig({ ...config, completion_model: value })}
            >
              <SelectTrigger
                id="completion-model"
                className="bg-gray-800 border-gray-700 text-white focus:border-purple-500 focus:ring-purple-500"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {MODEL_OPTIONS[config.provider].completion.map((model) => (
                  <SelectItem
                    key={model}
                    value={model}
                    className="text-white hover:bg-gray-700"
                  >
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 嵌入模型 */}
          <div className="space-y-2">
            <Label htmlFor="embedding-model" className="text-sm font-medium text-gray-200">
              嵌入模型
            </Label>
            <Select
              value={config.embedding_model}
              onValueChange={(value) => setConfig({ ...config, embedding_model: value })}
            >
              <SelectTrigger
                id="embedding-model"
                className="bg-gray-800 border-gray-700 text-white focus:border-purple-500 focus:ring-purple-500"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {MODEL_OPTIONS[config.provider].embedding.map((model) => (
                  <SelectItem
                    key={model}
                    value={model}
                    className="text-white hover:bg-gray-700"
                  >
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 测试结果 */}
          {testResult && (
            <Alert
              className={
                testResult.success
                  ? "bg-green-900/20 border-green-800/30 text-green-300"
                  : "bg-red-900/20 border-red-800/30 text-red-300"
              }
            >
              {testResult.success ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>
                {testResult.message}
                {testResult.success && testResult.latency && (
                  <span className="ml-2 text-xs opacity-80">
                    (延迟: {testResult.latency.toFixed(0)}ms)
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* 提示信息 */}
          <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-3">
            <p className="text-xs text-blue-300">
              <strong>💡 提示：</strong> DeepSeek 提供高性价比的 AI 模型服务，价格比 OpenAI 便宜约
              90%。您可以在{" "}
              <a
                href="https://platform.deepseek.com"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-blue-200"
              >
                DeepSeek 平台
              </a>
              获取 API Key。
            </p>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-between pt-4 border-t border-gray-700">
          <div>
            {allowSkip && (
              <Button
                variant="outline"
                onClick={onClose}
                className="border-gray-700 hover:bg-gray-800 hover:text-white"
              >
                跳过配置
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={!config.api_key || testing}
              className="border-gray-700 hover:bg-gray-800 hover:text-white"
            >
              {testing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  测试中...
                </>
              ) : (
                <>
                  <TestTube className="w-4 h-4 mr-2" />
                  测试连接
                </>
              )}
            </Button>
            <Button
              onClick={handleSave}
              disabled={!config.api_key || saving}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  保存中...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  保存配置
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AIConfigModal;
