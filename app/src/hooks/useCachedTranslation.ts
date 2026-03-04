import { useTranslation } from 'react-i18next';
import { useCallback, useMemo, useRef } from 'react';
import { translationCache } from '@/i18n/cache';
import { i18nPerformanceMonitor } from '@/utils/i18nPerformance';

/**
 * 使用缓存的翻译 Hook
 * 
 * 在 useTranslation 基础上添加内存缓存层和性能监控，提高翻译性能
 * 
 * 性能优化:
 * - 内存缓存翻译结果
 * - 性能监控和分析
 * - 使用 useCallback 避免函数重新创建
 * 
 * @param ns - 命名空间 (可选)
 * @returns 翻译函数和 i18n 实例
 * 
 * @example
 * ```tsx
 * const { t } = useCachedTranslation();
 * const title = t('common.buttons.save');
 * ```
 */
export const useCachedTranslation = (ns?: string | string[]) => {
  const { t: originalT, i18n, ready } = useTranslation(ns);
  
  // 使用 ref 避免在每次渲染时创建新的 Map
  const translationTimesRef = useRef(new Map<string, number>());

  /**
   * 带缓存和性能监控的翻译函数
   * 
   * 首先检查缓存，如果缓存未命中则调用原始翻译函数
   */
  const t = useCallback(
    (key: string, options?: Record<string, any>): string => {
      const startTime = performance.now();

      // 尝试从缓存获取
      const cached = translationCache.get(key, options);
      if (cached !== undefined) {
        // 记录缓存命中的性能
        i18nPerformanceMonitor.recordTranslation(key, startTime);
        return cached;
      }

      // 缓存未命中，调用原始翻译函数
      const result = originalT(key, options);

      // 将结果存入缓存
      if (typeof result === 'string') {
        translationCache.set(key, result, options);
      }

      // 记录翻译性能
      i18nPerformanceMonitor.recordTranslation(key, startTime);

      return result;
    },
    [originalT]
  );

  /**
   * 获取缓存统计信息 (仅开发模式)
   * 
   * 使用 useMemo 缓存统计结果
   */
  const cacheStats = useMemo(() => {
    if (import.meta.env.DEV) {
      return translationCache.getStats();
    }
    return null;
  }, []);

  /**
   * 清空缓存
   */
  const clearCache = useCallback(() => {
    translationCache.clear();
  }, []);

  return {
    t,
    i18n,
    ready,
    cacheStats,
    clearCache,
  };
};
