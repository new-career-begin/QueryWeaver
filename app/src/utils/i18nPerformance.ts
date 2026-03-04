/**
 * i18n 性能监控工具
 * 
 * 用于监控翻译性能，帮助识别性能瓶颈
 */

/**
 * 性能指标接口
 */
interface PerformanceMetrics {
  /** 翻译调用次数 */
  translationCalls: number;
  /** 总翻译时间 (毫秒) */
  totalTime: number;
  /** 平均翻译时间 (毫秒) */
  averageTime: number;
  /** 最慢的翻译 */
  slowestTranslations: Array<{
    key: string;
    time: number;
  }>;
}

/**
 * 性能监控类
 */
class I18nPerformanceMonitor {
  private enabled: boolean;
  private metrics: {
    calls: number;
    totalTime: number;
    translations: Map<string, number[]>;
  };

  constructor() {
    // 只在开发模式下启用
    this.enabled = import.meta.env.DEV;
    this.metrics = {
      calls: 0,
      totalTime: 0,
      translations: new Map(),
    };
  }

  /**
   * 记录翻译性能
   * 
   * @param key - 翻译键
   * @param startTime - 开始时间
   */
  recordTranslation(key: string, startTime: number): void {
    if (!this.enabled) return;

    const duration = performance.now() - startTime;
    this.metrics.calls++;
    this.metrics.totalTime += duration;

    // 记录每个键的翻译时间
    const times = this.metrics.translations.get(key) || [];
    times.push(duration);
    this.metrics.translations.set(key, times);
  }

  /**
   * 获取性能指标
   * 
   * @returns 性能指标
   */
  getMetrics(): PerformanceMetrics {
    const averageTime = this.metrics.calls > 0
      ? this.metrics.totalTime / this.metrics.calls
      : 0;

    // 找出最慢的翻译
    const slowestTranslations = Array.from(this.metrics.translations.entries())
      .map(([key, times]) => ({
        key,
        time: Math.max(...times),
      }))
      .sort((a, b) => b.time - a.time)
      .slice(0, 10);

    return {
      translationCalls: this.metrics.calls,
      totalTime: this.metrics.totalTime,
      averageTime,
      slowestTranslations,
    };
  }

  /**
   * 重置指标
   */
  reset(): void {
    this.metrics = {
      calls: 0,
      totalTime: 0,
      translations: new Map(),
    };
  }

  /**
   * 打印性能报告
   */
  printReport(): void {
    if (!this.enabled) return;

    const metrics = this.getMetrics();
    
    console.group('📊 i18n 性能报告');
    console.log(`总翻译调用次数: ${metrics.translationCalls}`);
    console.log(`总翻译时间: ${metrics.totalTime.toFixed(2)}ms`);
    console.log(`平均翻译时间: ${metrics.averageTime.toFixed(2)}ms`);
    
    if (metrics.slowestTranslations.length > 0) {
      console.group('🐌 最慢的翻译:');
      metrics.slowestTranslations.forEach(({ key, time }, index) => {
        console.log(`${index + 1}. ${key}: ${time.toFixed(2)}ms`);
      });
      console.groupEnd();
    }
    
    console.groupEnd();
  }
}

/**
 * 全局性能监控实例
 */
export const i18nPerformanceMonitor = new I18nPerformanceMonitor();

/**
 * 性能监控装饰器
 * 
 * 用于包装翻译函数，自动记录性能
 * 
 * @param fn - 翻译函数
 * @returns 包装后的函数
 */
export function withPerformanceMonitoring<T extends (...args: any[]) => any>(
  fn: T
): T {
  return ((...args: Parameters<T>): ReturnType<T> => {
    const startTime = performance.now();
    const result = fn(...args);
    
    // 假设第一个参数是翻译键
    const key = args[0];
    if (typeof key === 'string') {
      i18nPerformanceMonitor.recordTranslation(key, startTime);
    }
    
    return result;
  }) as T;
}

/**
 * 在开发模式下定期打印性能报告
 */
if (import.meta.env.DEV && typeof window !== 'undefined') {
  // 每 30 秒打印一次报告
  setInterval(() => {
    const metrics = i18nPerformanceMonitor.getMetrics();
    if (metrics.translationCalls > 0) {
      i18nPerformanceMonitor.printReport();
      i18nPerformanceMonitor.reset();
    }
  }, 30000);
}
