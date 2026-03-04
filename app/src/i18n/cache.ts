/**
 * i18n 翻译缓存管理
 * 
 * 提供翻译结果的内存缓存，减少重复翻译计算
 * 
 * 功能:
 * - 内存缓存翻译结果
 * - LRU 缓存策略
 * - 缓存统计和监控
 */

/**
 * 缓存项接口
 */
interface CacheEntry<T> {
  /** 缓存的值 */
  value: T;
  /** 创建时间戳 */
  timestamp: number;
  /** 访问次数 */
  hits: number;
}

/**
 * 缓存统计信息
 */
interface CacheStats {
  /** 缓存命中次数 */
  hits: number;
  /** 缓存未命中次数 */
  misses: number;
  /** 缓存大小 */
  size: number;
  /** 命中率 */
  hitRate: number;
}

/**
 * LRU 缓存类
 * 
 * 使用最近最少使用 (Least Recently Used) 策略管理缓存
 */
export class TranslationCache<T = string> {
  private cache: Map<string, CacheEntry<T>>;
  private maxSize: number;
  private ttl: number;
  private stats: { hits: number; misses: number };

  /**
   * 创建翻译缓存实例
   * 
   * @param maxSize - 最大缓存条目数 (默认 1000)
   * @param ttl - 缓存过期时间，毫秒 (默认 1小时)
   */
  constructor(maxSize: number = 1000, ttl: number = 60 * 60 * 1000) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttl;
    this.stats = { hits: 0, misses: 0 };
  }

  /**
   * 生成缓存键
   * 
   * @param key - 翻译键
   * @param options - 翻译选项 (如插值变量)
   * @returns 缓存键字符串
   */
  private generateKey(key: string, options?: Record<string, any>): string {
    if (!options || Object.keys(options).length === 0) {
      return key;
    }
    // 将选项序列化为稳定的字符串
    const sortedOptions = Object.keys(options)
      .sort()
      .map((k) => `${k}:${JSON.stringify(options[k])}`)
      .join('|');
    return `${key}::${sortedOptions}`;
  }

  /**
   * 检查缓存项是否过期
   * 
   * @param entry - 缓存项
   * @returns 是否过期
   */
  private isExpired(entry: CacheEntry<T>): boolean {
    return Date.now() - entry.timestamp > this.ttl;
  }

  /**
   * 获取缓存值
   * 
   * @param key - 翻译键
   * @param options - 翻译选项
   * @returns 缓存的值，如果不存在或已过期则返回 undefined
   */
  get(key: string, options?: Record<string, any>): T | undefined {
    const cacheKey = this.generateKey(key, options);
    const entry = this.cache.get(cacheKey);

    if (!entry) {
      this.stats.misses++;
      return undefined;
    }

    // 检查是否过期
    if (this.isExpired(entry)) {
      this.cache.delete(cacheKey);
      this.stats.misses++;
      return undefined;
    }

    // 更新访问统计
    entry.hits++;
    this.stats.hits++;

    // LRU: 将访问的项移到最后
    this.cache.delete(cacheKey);
    this.cache.set(cacheKey, entry);

    return entry.value;
  }

  /**
   * 设置缓存值
   * 
   * @param key - 翻译键
   * @param value - 翻译值
   * @param options - 翻译选项
   */
  set(key: string, value: T, options?: Record<string, any>): void {
    const cacheKey = this.generateKey(key, options);

    // 如果缓存已满，删除最旧的项 (Map 的第一个项)
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    // 添加新的缓存项
    this.cache.set(cacheKey, {
      value,
      timestamp: Date.now(),
      hits: 0,
    });
  }

  /**
   * 检查缓存中是否存在某个键
   * 
   * @param key - 翻译键
   * @param options - 翻译选项
   * @returns 是否存在且未过期
   */
  has(key: string, options?: Record<string, any>): boolean {
    const cacheKey = this.generateKey(key, options);
    const entry = this.cache.get(cacheKey);
    
    if (!entry) {
      return false;
    }

    if (this.isExpired(entry)) {
      this.cache.delete(cacheKey);
      return false;
    }

    return true;
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0 };
  }

  /**
   * 删除特定的缓存项
   * 
   * @param key - 翻译键
   * @param options - 翻译选项
   */
  delete(key: string, options?: Record<string, any>): void {
    const cacheKey = this.generateKey(key, options);
    this.cache.delete(cacheKey);
  }

  /**
   * 获取缓存统计信息
   * 
   * @returns 缓存统计
   */
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses;
    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      size: this.cache.size,
      hitRate: total > 0 ? this.stats.hits / total : 0,
    };
  }

  /**
   * 重置统计信息
   */
  resetStats(): void {
    this.stats = { hits: 0, misses: 0 };
  }

  /**
   * 清理过期的缓存项
   * 
   * @returns 清理的项数
   */
  cleanup(): number {
    let cleaned = 0;
    const now = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttl) {
        this.cache.delete(key);
        cleaned++;
      }
    }

    return cleaned;
  }
}

/**
 * 全局翻译缓存实例
 * 
 * 用于缓存翻译结果，提高性能
 */
export const translationCache = new TranslationCache<string>(
  1000, // 最大缓存 1000 条翻译
  60 * 60 * 1000 // 缓存 1 小时
);

/**
 * 定期清理过期缓存
 * 
 * 每 5 分钟清理一次过期的缓存项
 */
if (typeof window !== 'undefined') {
  setInterval(() => {
    const cleaned = translationCache.cleanup();
    if (cleaned > 0 && import.meta.env.DEV) {
      console.log(`[i18n Cache] 清理了 ${cleaned} 个过期缓存项`);
    }
  }, 5 * 60 * 1000);
}
