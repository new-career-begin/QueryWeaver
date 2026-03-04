import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

/**
 * i18n 配置和初始化
 * 
 * 功能:
 * - 初始化 i18next 实例
 * - 配置语言检测
 * - 懒加载翻译资源
 * - 设置默认语言
 * 
 * 性能优化:
 * - 使用 i18next-http-backend 实现懒加载
 * - 按需加载语言资源，减少初始加载时间
 * - 自动缓存已加载的资源
 */
i18n
  .use(Backend) // 使用后端加载器实现懒加载
  .use(LanguageDetector) // 自动检测浏览器语言
  .use(initReactI18next) // 集成 React
  .init({
    // 懒加载配置
    backend: {
      // 翻译文件路径模板
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      // 允许跨域加载
      crossDomain: false,
      // 请求超时时间 (毫秒)
      requestOptions: {
        cache: 'default',
      },
    },
    // 默认命名空间
    ns: ['common', 'auth', 'database', 'chat', 'schema', 'errors'],
    defaultNS: 'common',
    // 语言配置
    fallbackLng: 'zh-CN', // 默认语言为中文
    lng: 'zh-CN', // 初始语言
    // 开发配置
    debug: import.meta.env.DEV, // 开发模式下启用调试
    // 插值配置
    interpolation: {
      escapeValue: false, // React 已经处理 XSS
    },
    // 语言检测配置
    detection: {
      // 语言检测顺序
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'queryweaver_language',
    },
    // 性能优化配置
    react: {
      // 使用 Suspense 模式
      useSuspense: true,
      // 绑定 i18n 实例到组件
      bindI18n: 'languageChanged loaded',
      // 绑定 i18n store 到组件
      bindI18nStore: 'added removed',
      // 事务更新
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p'],
    },
    // 加载策略
    load: 'currentOnly', // 只加载当前语言，不加载区域变体
    // 预加载语言
    preload: ['zh-CN'], // 预加载中文
    // 命名空间分离
    partialBundledLanguages: true, // 允许部分加载命名空间
    // 缓存配置
    cache: {
      enabled: true, // 启用缓存
      prefix: 'i18next_res_', // 缓存键前缀
      expirationTime: 7 * 24 * 60 * 60 * 1000, // 缓存过期时间 (7天)
      versions: {
        'zh-CN': 'v1.0',
        'en-US': 'v1.0',
      },
    },
  });

export default i18n;
