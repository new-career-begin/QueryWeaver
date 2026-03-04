# i18n 性能优化指南

## 概述

本文档描述了 QueryWeaver 项目中 i18n 国际化功能的性能优化实现，包括懒加载、缓存和组件渲染优化。

## 优化策略

### 1. 懒加载 (Lazy Loading)

**实现方式**: 使用 `i18next-http-backend` 实现翻译资源的按需加载

**配置位置**: `app/src/i18n/index.ts`

**优化效果**:
- 减少初始加载时间
- 只加载当前语言的资源
- 按命名空间分离，支持部分加载

**配置示例**:
```typescript
i18n
  .use(Backend) // 使用后端加载器
  .init({
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
    ns: ['common', 'auth', 'database', 'chat', 'schema', 'errors'],
    defaultNS: 'common',
    load: 'currentOnly', // 只加载当前语言
    preload: ['zh-CN'], // 预加载中文
  });
```

**资源文件位置**:
- 开发环境: `app/public/locales/{language}/{namespace}.json`
- 生产环境: 通过 HTTP 请求动态加载

### 2. 翻译缓存 (Translation Cache)

**实现方式**: 自定义 LRU 缓存层，缓存翻译结果

**实现位置**: `app/src/i18n/cache.ts`

**缓存策略**:
- **LRU (Least Recently Used)**: 最近最少使用算法
- **最大容量**: 1000 条翻译
- **过期时间**: 1 小时
- **自动清理**: 每 5 分钟清理过期项

**使用示例**:
```typescript
import { translationCache } from '@/i18n/cache';

// 获取缓存
const cached = translationCache.get('common.buttons.save');

// 设置缓存
translationCache.set('common.buttons.save', '保存');

// 获取统计信息
const stats = translationCache.getStats();
console.log(`缓存命中率: ${(stats.hitRate * 100).toFixed(2)}%`);
```

**缓存统计**:
- `hits`: 缓存命中次数
- `misses`: 缓存未命中次数
- `size`: 当前缓存大小
- `hitRate`: 缓存命中率

### 3. 组件渲染优化

#### 3.1 LanguageSwitcher 组件优化

**优化位置**: `app/src/components/LanguageSwitcher.tsx`

**优化技术**:
- `React.memo`: 避免不必要的重新渲染
- `useMemo`: 缓存当前语言配置和翻译文本
- `useCallback`: 缓存事件处理函数

**优化前后对比**:
```typescript
// 优化前
const languages = [
  { code: 'zh-CN', name: 'Chinese', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
]; // 每次渲染都创建新数组

// 优化后
const SUPPORTED_LANGUAGES = [
  { code: 'zh-CN', name: 'Chinese', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
] as const; // 常量，只创建一次
```

#### 3.2 TranslatedText 组件

**实现位置**: `app/src/components/TranslatedText.tsx`

**功能**: 优化的翻译文本组件，使用 `React.memo` 和 `useMemo`

**使用示例**:
```tsx
// 简单翻译
<TranslatedText tKey="common.buttons.save" />

// 带插值变量
<TranslatedText 
  tKey="common.status.connected" 
  values={{ name: '数据库' }}
/>

// 自定义标签
<TranslatedText 
  tKey="common.title" 
  as="h1"
  className="text-2xl font-bold"
/>
```

#### 3.3 useCachedTranslation Hook

**实现位置**: `app/src/hooks/useCachedTranslation.ts`

**功能**: 带缓存和性能监控的翻译 Hook

**使用示例**:
```typescript
import { useCachedTranslation } from '@/hooks/useCachedTranslation';

const MyComponent = () => {
  const { t, cacheStats, clearCache } = useCachedTranslation();

  // 使用翻译
  const title = t('common.buttons.save');

  // 查看缓存统计 (仅开发模式)
  console.log('缓存统计:', cacheStats);

  // 清空缓存
  const handleClearCache = () => {
    clearCache();
  };

  return <div>{title}</div>;
};
```

### 4. 性能监控

**实现位置**: `app/src/utils/i18nPerformance.ts`

**功能**: 监控翻译性能，识别性能瓶颈

**监控指标**:
- 翻译调用次数
- 总翻译时间
- 平均翻译时间
- 最慢的翻译

**使用方式**:
```typescript
import { i18nPerformanceMonitor } from '@/utils/i18nPerformance';

// 获取性能指标
const metrics = i18nPerformanceMonitor.getMetrics();

// 打印性能报告
i18nPerformanceMonitor.printReport();

// 重置统计
i18nPerformanceMonitor.reset();
```

**自动报告**: 开发模式下每 30 秒自动打印性能报告

## 性能优化效果

### 预期性能提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 初始加载时间 | ~200ms | ~50ms | 75% ↓ |
| 语言切换时间 | ~500ms | ~100ms | 80% ↓ |
| 翻译调用时间 | ~1ms | ~0.1ms | 90% ↓ |
| 内存占用 | ~5MB | ~2MB | 60% ↓ |

### 缓存命中率

- **目标命中率**: ≥ 90%
- **实际命中率**: 监控中

## 最佳实践

### 1. 使用缓存的翻译 Hook

```typescript
// ✅ 推荐: 使用 useCachedTranslation
import { useCachedTranslation } from '@/hooks/useCachedTranslation';

const MyComponent = () => {
  const { t } = useCachedTranslation();
  return <div>{t('common.title')}</div>;
};

// ❌ 不推荐: 直接使用 useTranslation (无缓存)
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  return <div>{t('common.title')}</div>;
};
```

### 2. 使用 TranslatedText 组件

```typescript
// ✅ 推荐: 使用 TranslatedText 组件
<TranslatedText tKey="common.buttons.save" />

// ❌ 不推荐: 在 JSX 中直接调用 t 函数
<span>{t('common.buttons.save')}</span>
```

### 3. 缓存翻译结果

```typescript
// ✅ 推荐: 使用 useMemo 缓存翻译结果
const title = useMemo(() => t('common.title'), [t]);

// ❌ 不推荐: 每次渲染都调用 t 函数
const title = t('common.title');
```

### 4. 避免在循环中调用翻译

```typescript
// ✅ 推荐: 在循环外翻译
const labels = useMemo(() => ({
  save: t('common.buttons.save'),
  cancel: t('common.buttons.cancel'),
}), [t]);

items.map(item => (
  <Button>{labels.save}</Button>
));

// ❌ 不推荐: 在循环中调用翻译
items.map(item => (
  <Button>{t('common.buttons.save')}</Button>
));
```

## 调试和监控

### 开发模式

在开发模式下，性能监控自动启用：

1. **控制台输出**: 每 30 秒打印性能报告
2. **缓存统计**: 通过 `useCachedTranslation` 获取
3. **性能指标**: 通过 `i18nPerformanceMonitor` 获取

### 生产模式

在生产模式下，性能监控自动禁用，避免影响性能。

### 手动监控

```typescript
// 获取缓存统计
const cacheStats = translationCache.getStats();
console.log('缓存命中率:', cacheStats.hitRate);

// 获取性能指标
const perfMetrics = i18nPerformanceMonitor.getMetrics();
console.log('平均翻译时间:', perfMetrics.averageTime);
```

## 故障排查

### 问题 1: 翻译资源加载失败

**症状**: 控制台显示 404 错误

**原因**: 翻译文件路径不正确

**解决方案**:
1. 检查 `public/locales` 目录是否存在
2. 确认翻译文件已正确复制
3. 检查 `i18n/index.ts` 中的 `loadPath` 配置

### 问题 2: 缓存命中率低

**症状**: 缓存命中率 < 50%

**原因**: 翻译键或参数频繁变化

**解决方案**:
1. 检查是否在循环中调用翻译
2. 确保插值变量稳定
3. 使用 `useMemo` 缓存翻译结果

### 问题 3: 语言切换慢

**症状**: 切换语言需要 > 500ms

**原因**: 翻译资源未预加载

**解决方案**:
1. 在 `i18n/index.ts` 中配置 `preload`
2. 减少翻译资源文件大小
3. 启用 HTTP 缓存

## 未来优化方向

### 1. Service Worker 缓存

使用 Service Worker 缓存翻译资源，实现离线支持。

### 2. 增量加载

只加载当前页面需要的翻译，进一步减少加载时间。

### 3. 翻译预编译

在构建时预编译翻译，减少运行时开销。

### 4. CDN 加速

将翻译资源部署到 CDN，加快全球访问速度。

## 参考资源

- [i18next 文档](https://www.i18next.com/)
- [React i18next 文档](https://react.i18next.com/)
- [i18next-http-backend](https://github.com/i18next/i18next-http-backend)
- [React 性能优化](https://react.dev/learn/render-and-commit)

---

**最后更新**: 2026-03-04
**维护者**: QueryWeaver 团队
