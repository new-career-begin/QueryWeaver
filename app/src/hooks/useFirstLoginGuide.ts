import { useEffect, useState } from "react";

/**
 * 首次登录引导 Hook
 * 
 * 检查用户是否已配置 LLM，如果未配置则显示配置引导
 * 
 * @returns {Object} 引导状态和控制方法
 * @returns {boolean} showConfigGuide - 是否显示配置引导
 * @returns {Function} setShowConfigGuide - 设置引导显示状态
 * 
 * @example
 * ```tsx
 * const { showConfigGuide, setShowConfigGuide } = useFirstLoginGuide();
 * 
 * return (
 *   <AIConfigModal
 *     open={showConfigGuide}
 *     onClose={() => setShowConfigGuide(false)}
 *     onSave={handleSaveConfig}
 *   />
 * );
 * ```
 */
export const useFirstLoginGuide = () => {
  const [showConfigGuide, setShowConfigGuide] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkFirstLogin();
  }, []);

  /**
   * 检查用户是否首次登录（未配置 LLM）
   * 
   * 通过调用 /api/config/llm 接口检查用户配置状态
   * 如果用户未配置 LLM，则设置 showConfigGuide 为 true
   */
  const checkFirstLogin = async () => {
    try {
      setIsChecking(true);
      
      // 调用配置 API 检查用户是否已配置 LLM
      const response = await fetch("/api/config/llm", {
        credentials: "include", // 包含认证凭证
      });

      if (!response.ok) {
        // 如果请求失败（如未登录），不显示引导
        console.warn("无法检查 LLM 配置状态:", response.statusText);
        return;
      }

      const data = await response.json();

      // 如果用户未配置 LLM，显示配置引导
      if (data.success && !data.config) {
        setShowConfigGuide(true);
      }
    } catch (error) {
      // 网络错误或其他异常，不显示引导
      console.error("检查首次登录状态失败:", error);
    } finally {
      setIsChecking(false);
    }
  };

  return {
    showConfigGuide,
    setShowConfigGuide,
    isChecking,
  };
};
