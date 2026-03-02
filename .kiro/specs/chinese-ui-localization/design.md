# 设计文档

## 概述

本设计文档描述了 QueryWeaver 项目中文界面本地化的技术实现方案。该方案基于 react-i18next 国际化框架，提供完整的多语言支持，包括界面文本翻译、日期时间格式化、数字格式化以及语言切换功能。

### 设计目标

1. **完整的中文支持**: 所有用户可见的文本都能正确显示中文
2. **灵活的语言切换**: 用户可以在中文和英文之间自由切换
3. **性能优化**: 语言切换和翻译不影响应用性能
4. **易于维护**: 翻译资源结构清晰，便于添加和修改
5. **开发友好**: 提供类型安全的翻译 API 和开发工具

### 技术选型

- **国际化框架**: react-i18next (基于 i18next)
- **类型支持**: TypeScript 类型定义
- **存储方案**: localStorage 保存用户语言偏好
- **格式化库**: date-fns 用于日期时间格式化
- **构建工具**: Vite (已有)

## 架构

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    React Application                     │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │         i18n Provider (I18nextProvider)           │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │         Language Context                    │  │  │
│  │  │  - currentLanguage                          │  │  │
│  │  │  - changeLanguage()                         │  │  │
│  │  │  - t() translation function                 │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐  │
│  │  Components   │  │   Services    │  │   Utils    │  │
│  │  - useTransl  │  │  - API calls  │  │  - format  │  │
│  │  - Trans      │  │  - error map  │  │  - helpers │  │
│  └───────────────┘  └───────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Translation Resources                       │
│  ┌──────────────┐           ┌──────────────┐           │
│  │   zh-CN      │           │    en-US     │           │
│  │  (中文简体)   │           │   (English)  │           │
│  │              │           │              │           │
│  │  common.json │           │  common.json │           │
│  │  auth.json   │           │  auth.json   │           │
│  │  database.   │           │  database.   │           │
│  │  chat.json   │           │  chat.json   │           │
│  └──────────────┘           └──────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 目录结构

```
app/src/
├── i18n/
│   ├── index.ts                 # i18n 配置和初始化
│   ├── locales/
│   │   ├── zh-CN/              # 中文翻译资源
│   │   │   ├── common.json     # 通用文本
│   │   │   ├── auth.json       # 认证相关
│   │   │   ├── database.json   # 数据库相关
│   │   │   ├── chat.json       # 聊天相关
│   │   │   ├── schema.json     # 模式查看器
│   │   │   └── errors.json     # 错误消息
│   │   └── en-US/              # 英文翻译资源
│   │       ├── common.json
│   │       ├── auth.json
│   │       ├── database.json
│   │       ├── chat.json
│   │       ├── schema.json
│   │       └── errors.json
│   └── types.ts                # TypeScript 类型定义
├── contexts/
│   └── LanguageContext.tsx     # 语言上下文 (可选)
├── components/
│   └── LanguageSwitcher.tsx    # 语言切换组件
└── utils/
    ├── formatDate.ts           # 日期格式化工具
    └── formatNumber.ts         # 数字格式化工具
```


## 组件和接口

### 1. i18n 配置 (i18n/index.ts)

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 导入翻译资源
import zhCN from './locales/zh-CN';
import enUS from './locales/en-US';

/**
 * i18n 配置和初始化
 * 
 * 功能:
 * - 初始化 i18next 实例
 * - 配置语言检测
 * - 加载翻译资源
 * - 设置默认语言
 */
i18n
  .use(LanguageDetector) // 自动检测浏览器语言
  .use(initReactI18next) // 集成 React
  .init({
    resources: {
      'zh-CN': zhCN,
      'en-US': enUS,
    },
    fallbackLng: 'zh-CN', // 默认语言为中文
    lng: 'zh-CN', // 初始语言
    debug: import.meta.env.DEV, // 开发模式下启用调试
    interpolation: {
      escapeValue: false, // React 已经处理 XSS
    },
    detection: {
      // 语言检测顺序
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'queryweaver_language',
    },
  });

export default i18n;
```

### 2. 翻译资源结构

#### 中文资源示例 (locales/zh-CN/common.json)

```json
{
  "appName": "QueryWeaver",
  "tagline": "图驱动的 Text-to-SQL 工具",
  "buttons": {
    "connect": "连接数据库",
    "upload": "上传模式",
    "refresh": "刷新模式",
    "save": "保存",
    "cancel": "取消",
    "delete": "删除",
    "edit": "编辑",
    "close": "关闭",
    "confirm": "确认",
    "submit": "提交",
    "signIn": "登录",
    "signOut": "退出登录"
  },
  "status": {
    "connected": "已连接: {{name}}",
    "noDatabase": "未选择数据库",
    "loading": "加载中...",
    "processing": "处理中...",
    "success": "成功",
    "error": "错误",
    "refreshing": "刷新中..."
  },
  "placeholders": {
    "search": "搜索...",
    "query": "输入您的问题...",
    "selectDatabase": "选择数据库",
    "enterUrl": "输入连接 URL"
  }
}
```

#### 数据库模块 (locales/zh-CN/database.json)

```json
{
  "modal": {
    "title": "连接到数据库",
    "description": "使用连接 URL 或手动输入连接到 PostgreSQL 或 MySQL 数据库。",
    "privacyPolicy": "隐私政策"
  },
  "fields": {
    "databaseType": "数据库类型",
    "connectionUrl": "连接 URL",
    "host": "主机",
    "port": "端口",
    "database": "数据库名称",
    "username": "用户名",
    "password": "密码"
  },
  "types": {
    "postgresql": "PostgreSQL",
    "mysql": "MySQL"
  },
  "modes": {
    "url": "连接 URL",
    "manual": "手动输入"
  },
  "messages": {
    "connecting": "正在连接...",
    "connected": "连接成功",
    "connectionFailed": "连接失败",
    "deleteConfirm": "确定要删除数据库 \"{{name}}\" 吗？",
    "deleteSuccess": "成功删除 \"{{name}}\"",
    "deleteFailed": "删除失败",
    "refreshSuccess": "模式刷新成功",
    "refreshFailed": "模式刷新失败",
    "noDatabaseSelected": "请先选择数据库",
    "missingFields": "请填写所有必填字段"
  },
  "steps": {
    "validating": "正在验证连接信息...",
    "connecting": "正在连接到数据库...",
    "loadingSchema": "正在加载数据库模式...",
    "buildingGraph": "正在构建关系图...",
    "complete": "连接完成"
  }
}
```


#### 聊天模块 (locales/zh-CN/chat.json)

```json
{
  "interface": {
    "placeholder": "向我提问关于您数据库的任何问题...",
    "processing": "正在处理您的查询...",
    "poweredBy": "由 {{provider}} 提供支持"
  },
  "suggestions": {
    "showCustomers": "显示五个客户",
    "topCustomers": "显示收入最高的客户",
    "pendingOrders": "待处理的订单有哪些？"
  },
  "messages": {
    "queryComplete": "查询完成",
    "querySuccess": "成功处理您的数据库查询！",
    "queryFailed": "查询失败",
    "noDatabase": "没有可用的数据库",
    "noDatabaseDescription": "请先上传数据库模式，或启动 QueryWeaver 后端以使用真实数据库。",
    "operationCancelled": "操作已取消",
    "operationCancelledDescription": "破坏性 SQL 查询未执行。"
  },
  "steps": {
    "analyzing": "正在分析查询...",
    "findingTables": "正在查找相关表...",
    "generatingSql": "正在生成 SQL...",
    "executing": "正在执行查询...",
    "executingOperation": "正在执行已确认的操作..."
  },
  "results": {
    "title": "查询结果",
    "rows": "{{count}} 行",
    "executionTime": "执行时间: {{time}}ms"
  },
  "confirmation": {
    "title": "确认操作",
    "message": "此操作将修改数据库。是否继续？",
    "confirm": "确认执行",
    "cancel": "取消"
  }
}
```

#### 错误消息 (locales/zh-CN/errors.json)

```json
{
  "auth": {
    "notAuthenticated": "未认证。请登录以连接数据库。",
    "accessDenied": "访问被拒绝。您没有权限连接数据库。",
    "sessionExpired": "会话已过期。请重新登录。",
    "loginFailed": "登录失败",
    "logoutFailed": "退出登录失败"
  },
  "database": {
    "invalidUrl": "无效的数据库连接 URL。",
    "connectionFailed": "连接数据库失败",
    "connectionTimeout": "连接超时。请检查网络连接。",
    "queryFailed": "查询执行失败",
    "syntaxError": "SQL 语法错误，请检查您的查询",
    "permissionDenied": "权限不足",
    "tableNotFound": "表不存在",
    "columnNotFound": "列不存在"
  },
  "network": {
    "offline": "网络连接已断开",
    "timeout": "请求超时",
    "serverError": "服务器错误。请稍后重试。",
    "unknownError": "发生未知错误"
  },
  "validation": {
    "required": "此字段为必填项",
    "invalidEmail": "邮箱格式不正确",
    "invalidFormat": "格式不正确",
    "tooShort": "内容过短",
    "tooLong": "内容过长"
  }
}
```

### 3. 语言切换组件 (components/LanguageSwitcher.tsx)

```typescript
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

/**
 * 语言切换组件
 * 
 * 功能:
 * - 显示当前语言
 * - 提供语言选择下拉菜单
 * - 切换语言并保存到 localStorage
 */
export const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();
  const [isChanging, setIsChanging] = useState(false);

  const languages = [
    { code: 'zh-CN', name: '简体中文', nativeName: '简体中文' },
    { code: 'en-US', name: 'English', nativeName: 'English' },
  ];

  const currentLanguage = languages.find(
    (lang) => lang.code === i18n.language
  ) || languages[0];

  const handleLanguageChange = async (languageCode: string) => {
    setIsChanging(true);
    try {
      await i18n.changeLanguage(languageCode);
      // 保存到 localStorage (i18next 会自动处理)
    } catch (error) {
      console.error('语言切换失败:', error);
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          disabled={isChanging}
          title={t('common.changeLanguage')}
          aria-label={t('common.changeLanguage')}
        >
          <Globe className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.code}
            onClick={() => handleLanguageChange(language.code)}
            className={
              currentLanguage.code === language.code
                ? 'bg-accent'
                : ''
            }
          >
            {language.nativeName}
            {currentLanguage.code === language.code && (
              <span className="ml-2">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```


### 4. 日期时间格式化工具 (utils/formatDate.ts)

```typescript
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';

/**
 * 日期时间格式化工具
 * 
 * 根据当前语言设置格式化日期和时间
 */

// 获取当前语言的 date-fns locale
const getLocale = (language: string) => {
  switch (language) {
    case 'zh-CN':
      return zhCN;
    case 'en-US':
      return enUS;
    default:
      return zhCN;
  }
};

/**
 * 格式化日期
 * @param date - 日期对象或时间戳
 * @param formatStr - 格式字符串
 * @param language - 语言代码
 */
export const formatDate = (
  date: Date | number,
  formatStr: string = 'PPP',
  language: string = 'zh-CN'
): string => {
  const locale = getLocale(language);
  return format(date, formatStr, { locale });
};

/**
 * 格式化相对时间 (如 "5分钟前")
 * @param date - 日期对象或时间戳
 * @param language - 语言代码
 */
export const formatRelativeTime = (
  date: Date | number,
  language: string = 'zh-CN'
): string => {
  const locale = getLocale(language);
  return formatDistanceToNow(date, { addSuffix: true, locale });
};

/**
 * 格式化时间戳为中文格式
 * @param timestamp - 时间戳
 * @param language - 语言代码
 */
export const formatTimestamp = (
  timestamp: Date | number,
  language: string = 'zh-CN'
): string => {
  if (language === 'zh-CN') {
    return formatDate(timestamp, 'yyyy年MM月dd日 HH:mm:ss', language);
  }
  return formatDate(timestamp, 'PPpp', language);
};
```

### 5. 数字格式化工具 (utils/formatNumber.ts)

```typescript
/**
 * 数字格式化工具
 * 
 * 根据当前语言设置格式化数字、货币和百分比
 */

/**
 * 格式化数字 (添加千位分隔符)
 * @param num - 数字
 * @param language - 语言代码
 */
export const formatNumber = (
  num: number,
  language: string = 'zh-CN'
): string => {
  return new Intl.NumberFormat(language).format(num);
};

/**
 * 格式化货币
 * @param amount - 金额
 * @param currency - 货币代码
 * @param language - 语言代码
 */
export const formatCurrency = (
  amount: number,
  currency: string = 'CNY',
  language: string = 'zh-CN'
): string => {
  return new Intl.NumberFormat(language, {
    style: 'currency',
    currency,
  }).format(amount);
};

/**
 * 格式化百分比
 * @param value - 数值 (0-1)
 * @param language - 语言代码
 */
export const formatPercent = (
  value: number,
  language: string = 'zh-CN'
): string => {
  return new Intl.NumberFormat(language, {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * 格式化大数字 (使用中文单位)
 * @param num - 数字
 * @param language - 语言代码
 */
export const formatLargeNumber = (
  num: number,
  language: string = 'zh-CN'
): string => {
  if (language === 'zh-CN') {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(2)}亿`;
    }
    if (num >= 10000) {
      return `${(num / 10000).toFixed(2)}万`;
    }
    return formatNumber(num, language);
  }
  
  // 英文使用 K, M, B
  if (num >= 1000000000) {
    return `${(num / 1000000000).toFixed(2)}B`;
  }
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(2)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(2)}K`;
  }
  return formatNumber(num, language);
};
```

### 6. 后端错误消息映射 (utils/errorMapping.ts)

```typescript
import i18n from '@/i18n';

/**
 * 后端错误消息映射
 * 
 * 将后端返回的英文错误消息映射为中文
 */

// 错误代码到翻译键的映射
const errorCodeMap: Record<string, string> = {
  'AUTH_REQUIRED': 'errors.auth.notAuthenticated',
  'ACCESS_DENIED': 'errors.auth.accessDenied',
  'SESSION_EXPIRED': 'errors.auth.sessionExpired',
  'INVALID_URL': 'errors.database.invalidUrl',
  'CONNECTION_FAILED': 'errors.database.connectionFailed',
  'CONNECTION_TIMEOUT': 'errors.database.connectionTimeout',
  'QUERY_FAILED': 'errors.database.queryFailed',
  'SYNTAX_ERROR': 'errors.database.syntaxError',
  'PERMISSION_DENIED': 'errors.database.permissionDenied',
  'TABLE_NOT_FOUND': 'errors.database.tableNotFound',
  'COLUMN_NOT_FOUND': 'errors.database.columnNotFound',
  'NETWORK_ERROR': 'errors.network.offline',
  'TIMEOUT': 'errors.network.timeout',
  'SERVER_ERROR': 'errors.network.serverError',
};

// 错误消息模式匹配
const errorPatterns = [
  {
    pattern: /duplicate key value violates unique constraint/i,
    handler: (message: string) => {
      const match = message.match(/Key \((\w+)\)=\(([^)]+)\)/);
      if (match) {
        const [, field, value] = match;
        return `字段 ${field} 的值 "${value}" 已存在`;
      }
      return '该记录已存在于数据库中';
    },
  },
  {
    pattern: /violates foreign key constraint/i,
    handler: () => '由于其他表中存在相关记录，无法执行此操作',
  },
  {
    pattern: /violates not-null constraint/i,
    handler: (message: string) => {
      const match = message.match(/column "(\w+)"/);
      if (match) {
        return `字段 "${match[1]}" 不能为空`;
      }
      return '必填字段不能为空';
    },
  },
  {
    pattern: /(PostgreSQL|MySQL) query execution error:/i,
    handler: (message: string) => {
      // 移除技术前缀
      return message.replace(/^(PostgreSQL|MySQL) query execution error:\s*/i, '').split('\n')[0];
    },
  },
];

/**
 * 翻译错误消息
 * @param error - 错误对象或错误消息
 * @returns 翻译后的错误消息
 */
export const translateError = (error: Error | string): string => {
  const message = typeof error === 'string' ? error : error.message;
  
  // 1. 尝试通过错误代码匹配
  const errorCode = (error as any)?.code;
  if (errorCode && errorCodeMap[errorCode]) {
    return i18n.t(errorCodeMap[errorCode]);
  }
  
  // 2. 尝试通过消息模式匹配
  for (const { pattern, handler } of errorPatterns) {
    if (pattern.test(message)) {
      return handler(message);
    }
  }
  
  // 3. 返回原始消息 (如果已经是中文则直接返回)
  if (/[\u4e00-\u9fa5]/.test(message)) {
    return message;
  }
  
  // 4. 返回通用错误消息
  return i18n.t('errors.network.unknownError');
};
```


## 数据模型

### 翻译资源类型定义

```typescript
/**
 * 翻译资源类型定义
 * 
 * 提供类型安全的翻译键访问
 */

// 通用翻译
export interface CommonTranslations {
  appName: string;
  tagline: string;
  buttons: {
    connect: string;
    upload: string;
    refresh: string;
    save: string;
    cancel: string;
    delete: string;
    edit: string;
    close: string;
    confirm: string;
    submit: string;
    signIn: string;
    signOut: string;
  };
  status: {
    connected: string;
    noDatabase: string;
    loading: string;
    processing: string;
    success: string;
    error: string;
    refreshing: string;
  };
  placeholders: {
    search: string;
    query: string;
    selectDatabase: string;
    enterUrl: string;
  };
}

// 数据库翻译
export interface DatabaseTranslations {
  modal: {
    title: string;
    description: string;
    privacyPolicy: string;
  };
  fields: {
    databaseType: string;
    connectionUrl: string;
    host: string;
    port: string;
    database: string;
    username: string;
    password: string;
  };
  types: {
    postgresql: string;
    mysql: string;
  };
  modes: {
    url: string;
    manual: string;
  };
  messages: {
    connecting: string;
    connected: string;
    connectionFailed: string;
    deleteConfirm: string;
    deleteSuccess: string;
    deleteFailed: string;
    refreshSuccess: string;
    refreshFailed: string;
    noDatabaseSelected: string;
    missingFields: string;
  };
  steps: {
    validating: string;
    connecting: string;
    loadingSchema: string;
    buildingGraph: string;
    complete: string;
  };
}

// 聊天翻译
export interface ChatTranslations {
  interface: {
    placeholder: string;
    processing: string;
    poweredBy: string;
  };
  suggestions: {
    showCustomers: string;
    topCustomers: string;
    pendingOrders: string;
  };
  messages: {
    queryComplete: string;
    querySuccess: string;
    queryFailed: string;
    noDatabase: string;
    noDatabaseDescription: string;
    operationCancelled: string;
    operationCancelledDescription: string;
  };
  steps: {
    analyzing: string;
    findingTables: string;
    generatingSql: string;
    executing: string;
    executingOperation: string;
  };
  results: {
    title: string;
    rows: string;
    executionTime: string;
  };
  confirmation: {
    title: string;
    message: string;
    confirm: string;
    cancel: string;
  };
}

// 错误翻译
export interface ErrorTranslations {
  auth: {
    notAuthenticated: string;
    accessDenied: string;
    sessionExpired: string;
    loginFailed: string;
    logoutFailed: string;
  };
  database: {
    invalidUrl: string;
    connectionFailed: string;
    connectionTimeout: string;
    queryFailed: string;
    syntaxError: string;
    permissionDenied: string;
    tableNotFound: string;
    columnNotFound: string;
  };
  network: {
    offline: string;
    timeout: string;
    serverError: string;
    unknownError: string;
  };
  validation: {
    required: string;
    invalidEmail: string;
    invalidFormat: string;
    tooShort: string;
    tooLong: string;
  };
}

// 完整的翻译资源类型
export interface Translations {
  common: CommonTranslations;
  database: DatabaseTranslations;
  chat: ChatTranslations;
  errors: ErrorTranslations;
}
```

### 语言配置类型

```typescript
/**
 * 语言配置类型
 */
export interface LanguageConfig {
  code: string;        // 语言代码 (如 'zh-CN')
  name: string;        // 英文名称 (如 'Chinese')
  nativeName: string;  // 本地名称 (如 '简体中文')
  direction: 'ltr' | 'rtl'; // 文本方向
}

/**
 * i18n 配置选项
 */
export interface I18nConfig {
  defaultLanguage: string;
  fallbackLanguage: string;
  supportedLanguages: LanguageConfig[];
  debug: boolean;
  storageKey: string;
}
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 翻译键映射完整性

*对于任意*有效的翻译键，系统应该返回对应的翻译文本，而不是返回键本身或 undefined

**验证需求**: 需求 1.3

### 属性 2: 语言资源动态加载

*对于任意*支持的语言代码，当切换到该语言时，系统应该成功加载对应的语言资源文件

**验证需求**: 需求 1.4

### 属性 3: UI 元素中文翻译完整性

*对于任意*UI 元素（按钮、标签、占位符、导航、模态框、表单、徽章），当语言设置为中文时，该元素应该显示中文文本

**验证需求**: 需求 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8

### 属性 4: 错误消息中文化

*对于任意*错误类型（Toast、验证、成功、警告、确认、加载、空状态），当系统发生该类型错误时，应该显示中文错误消息

**验证需求**: 需求 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8

### 属性 5: 日期格式化中文化

*对于任意*日期对象，当使用中文语言设置格式化时，应该返回符合中文格式的字符串（包含 "年"、"月"、"日" 字符）

**验证需求**: 需求 4.1, 4.4

### 属性 6: 时间格式化 24 小时制

*对于任意*时间对象，当格式化时间时，应该使用 24 小时制（小时值在 0-23 之间）

**验证需求**: 需求 4.2

### 属性 7: 相对时间中文表达

*对于任意*时间差，当格式化为相对时间时，应该使用中文表达（如 "刚刚"、"分钟前"、"小时前"、"天前"）

**验证需求**: 需求 4.3

### 属性 8: 数字格式化中文化

*对于任意*数字，当使用中文语言设置格式化时，应该符合中文习惯（千位分隔符、正确的小数点、货币符号 ¥、百分比符号 %、大数字使用 "万" 和 "亿" 单位）

**验证需求**: 需求 5.1, 5.2, 5.3, 5.4, 5.5

### 属性 9: 语言切换即时性

*对于任意*支持的语言，当用户选择该语言时，界面应该立即切换到该语言，所有可见文本都应该更新

**验证需求**: 需求 6.3

### 属性 10: 语言偏好持久化往返

*对于任意*支持的语言，如果用户选择该语言，然后重新加载应用，应用应该恢复到该语言设置

**验证需求**: 需求 6.4, 6.5

### 属性 11: 当前语言显示一致性

*对于任意*时刻，语言切换器中显示的当前语言应该与实际使用的语言一致

**验证需求**: 需求 6.6

### 属性 12: 嵌套翻译键访问

*对于任意*嵌套的翻译键路径（如 "common.buttons.save"），系统应该能够正确访问并返回对应的翻译文本

**验证需求**: 需求 7.4

### 属性 13: 缺失翻译键降级

*对于任意*不存在的翻译键，系统应该返回默认文本或键名，而不是抛出错误或返回 undefined

**验证需求**: 需求 7.5

### 属性 14: 动态内容中文化

*对于任意*动态生成的内容（查询建议、SQL 步骤、连接状态、结果表头），当语言设置为中文时，应该显示中文文本

**验证需求**: 需求 8.1, 8.2, 8.3, 8.4

### 属性 15: 插值变量本地化

*对于任意*包含插值变量的翻译键（如 "已连接: {{name}}"），系统应该正确替换变量并返回完整的翻译文本

**验证需求**: 需求 8.5

### 属性 16: 可访问性属性中文化

*对于任意*具有可访问性属性（aria-label、aria-describedby、title、placeholder）的元素，当语言设置为中文时，这些属性应该包含中文文本

**验证需求**: 需求 9.1, 9.2, 9.3, 9.4

### 属性 17: 翻译资源缓存

*对于任意*已加载的语言资源，重复访问相同的翻译键应该使用缓存，而不是重新加载资源文件

**验证需求**: 需求 11.2

### 属性 18: 语言切换性能

*对于任意*语言切换操作，从用户点击到界面完全更新应该在 500ms 内完成

**验证需求**: 需求 11.3

### 属性 19: 后端错误消息翻译

*对于任意*后端返回的错误消息，系统应该将其映射或翻译为中文错误消息

**验证需求**: 需求 12.1, 12.2, 12.3

### 属性 20: 浏览器语言检测降级

*对于任意*浏览器语言设置，如果该语言不受支持，系统应该降级到默认语言（中文）

**验证需求**: 需求 14.4

### 属性 21: 用户语言覆盖

*对于任意*自动检测的语言，用户应该能够手动选择不同的语言，并且手动选择应该优先于自动检测

**验证需求**: 需求 14.5


## 错误处理

### 错误类型和处理策略

#### 1. 翻译键缺失错误

**场景**: 访问不存在的翻译键

**处理策略**:
- 开发模式: 在控制台显示警告，返回翻译键本身
- 生产模式: 返回翻译键本身或默认文本
- 不抛出异常，确保应用继续运行

```typescript
// 示例实现
const t = (key: string, defaultValue?: string) => {
  const translation = i18n.t(key);
  
  if (translation === key) {
    // 翻译键不存在
    if (import.meta.env.DEV) {
      console.warn(`翻译键缺失: ${key}`);
    }
    return defaultValue || key;
  }
  
  return translation;
};
```

#### 2. 语言资源加载失败

**场景**: 网络错误或资源文件不存在

**处理策略**:
- 降级到默认语言（中文）
- 显示用户友好的错误提示
- 记录错误日志用于监控

```typescript
// 示例实现
const loadLanguage = async (languageCode: string) => {
  try {
    await i18n.changeLanguage(languageCode);
  } catch (error) {
    console.error(`加载语言 ${languageCode} 失败:`, error);
    
    // 降级到默认语言
    await i18n.changeLanguage('zh-CN');
    
    toast({
      title: '语言切换失败',
      description: '已恢复到默认语言',
      variant: 'destructive',
    });
  }
};
```

#### 3. 插值变量错误

**场景**: 翻译文本中的变量未提供或类型错误

**处理策略**:
- 使用默认值或空字符串替换缺失的变量
- 在开发模式下显示警告
- 确保翻译文本仍然可读

```typescript
// 示例实现
const translateWithVariables = (
  key: string,
  variables: Record<string, any> = {}
) => {
  try {
    return i18n.t(key, variables);
  } catch (error) {
    if (import.meta.env.DEV) {
      console.warn(`翻译插值错误: ${key}`, error);
    }
    
    // 返回不带变量的翻译
    return i18n.t(key);
  }
};
```

#### 4. 格式化函数错误

**场景**: 日期或数字格式化失败

**处理策略**:
- 返回原始值的字符串表示
- 记录错误日志
- 不影响应用正常运行

```typescript
// 示例实现
const safeFormatDate = (date: Date | number, format: string) => {
  try {
    return formatDate(date, format);
  } catch (error) {
    console.error('日期格式化失败:', error);
    return String(date);
  }
};
```

### 错误监控和日志

```typescript
/**
 * i18n 错误监控
 */
i18n.on('missingKey', (lngs, namespace, key, res) => {
  // 记录缺失的翻译键
  if (import.meta.env.DEV) {
    console.warn(`缺失翻译键: [${lngs}] ${namespace}:${key}`);
  }
  
  // 发送到错误监控服务（生产环境）
  if (import.meta.env.PROD) {
    // 例如: Sentry.captureMessage(...)
  }
});

i18n.on('failedLoading', (lng, ns, msg) => {
  console.error(`加载翻译资源失败: [${lng}] ${ns}`, msg);
  
  // 发送到错误监控服务
  if (import.meta.env.PROD) {
    // 例如: Sentry.captureException(...)
  }
});
```

## 测试策略

### 双重测试方法

本地化功能需要同时使用单元测试和属性测试来确保完整的覆盖：

#### 单元测试

**用途**: 验证特定示例、边缘情况和错误条件

**测试内容**:
- i18n 配置正确初始化
- 特定翻译键返回正确的翻译
- 语言切换器组件正确渲染
- 格式化函数处理特定输入
- 错误情况的降级处理

**示例**:

```typescript
// i18n 初始化测试
describe('i18n 初始化', () => {
  it('应该默认使用中文', () => {
    expect(i18n.language).toBe('zh-CN');
  });
  
  it('应该加载中文翻译资源', () => {
    expect(i18n.hasResourceBundle('zh-CN', 'common')).toBe(true);
  });
});

// 翻译功能测试
describe('翻译功能', () => {
  it('应该返回正确的中文翻译', () => {
    expect(i18n.t('common.buttons.save')).toBe('保存');
  });
  
  it('应该处理插值变量', () => {
    expect(i18n.t('common.status.connected', { name: '测试数据库' }))
      .toBe('已连接: 测试数据库');
  });
  
  it('应该处理缺失的翻译键', () => {
    const result = i18n.t('nonexistent.key');
    expect(result).toBe('nonexistent.key');
  });
});

// 日期格式化测试
describe('日期格式化', () => {
  it('应该格式化为中文日期格式', () => {
    const date = new Date('2025-01-15');
    const formatted = formatDate(date, 'PPP', 'zh-CN');
    expect(formatted).toContain('2025年');
    expect(formatted).toContain('1月');
    expect(formatted).toContain('15日');
  });
  
  it('应该使用24小时制', () => {
    const date = new Date('2025-01-15 14:30:00');
    const formatted = formatDate(date, 'HH:mm', 'zh-CN');
    expect(formatted).toBe('14:30');
  });
});
```

#### 属性测试

**用途**: 验证跨所有输入的通用属性

**测试内容**:
- 所有翻译键都有对应的翻译
- 语言切换后所有文本都更新
- 日期格式化始终返回有效字符串
- 数字格式化始终返回有效字符串
- 缓存机制正确工作

**配置**: 每个属性测试至少运行 100 次迭代

**示例**:

```typescript
import fc from 'fast-check';

/**
 * 属性测试: 翻译键映射完整性
 * Feature: chinese-ui-localization, Property 1: 翻译键映射完整性
 */
describe('属性 1: 翻译键映射完整性', () => {
  it('对于任意有效的翻译键，应该返回翻译文本', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          'common.buttons.save',
          'common.buttons.cancel',
          'database.modal.title',
          'chat.interface.placeholder',
          // ... 更多翻译键
        ),
        (key) => {
          const translation = i18n.t(key);
          // 翻译不应该等于键本身（除非是缺失的键）
          // 翻译不应该是 undefined
          expect(translation).toBeDefined();
          expect(typeof translation).toBe('string');
          expect(translation.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * 属性测试: 日期格式化中文化
 * Feature: chinese-ui-localization, Property 5: 日期格式化中文化
 */
describe('属性 5: 日期格式化中文化', () => {
  it('对于任意日期，中文格式化应该包含中文字符', () => {
    fc.assert(
      fc.property(
        fc.date({ min: new Date('2000-01-01'), max: new Date('2030-12-31') }),
        (date) => {
          const formatted = formatDate(date, 'PPP', 'zh-CN');
          // 应该包含中文日期字符
          expect(formatted).toMatch(/[年月日]/);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * 属性测试: 数字格式化中文化
 * Feature: chinese-ui-localization, Property 8: 数字格式化中文化
 */
describe('属性 8: 数字格式化中文化', () => {
  it('对于任意数字，格式化应该返回有效字符串', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 1000000000 }),
        (num) => {
          const formatted = formatNumber(num, 'zh-CN');
          expect(formatted).toBeDefined();
          expect(typeof formatted).toBe('string');
          // 格式化后的字符串应该可以被解析回数字
          const parsed = parseFloat(formatted.replace(/,/g, ''));
          expect(parsed).toBe(num);
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('对于大数字，应该使用中文单位', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 10000, max: 1000000000 }),
        (num) => {
          const formatted = formatLargeNumber(num, 'zh-CN');
          if (num >= 100000000) {
            expect(formatted).toContain('亿');
          } else if (num >= 10000) {
            expect(formatted).toContain('万');
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * 属性测试: 语言偏好持久化往返
 * Feature: chinese-ui-localization, Property 10: 语言偏好持久化往返
 */
describe('属性 10: 语言偏好持久化往返', () => {
  it('选择语言后重新加载应该恢复该语言', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('zh-CN', 'en-US'),
        async (language) => {
          // 切换语言
          await i18n.changeLanguage(language);
          
          // 验证保存到 localStorage
          const saved = localStorage.getItem('queryweaver_language');
          expect(saved).toBe(language);
          
          // 模拟重新加载
          const newI18n = createI18nInstance();
          await newI18n.init();
          
          // 验证恢复的语言
          expect(newI18n.language).toBe(language);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### 端到端测试

使用 Playwright 进行端到端测试，验证完整的本地化流程：

```typescript
import { test, expect } from '@playwright/test';

test.describe('中文界面本地化', () => {
  test('应该默认显示中文界面', async ({ page }) => {
    await page.goto('/');
    
    // 验证关键元素显示中文
    await expect(page.getByRole('button', { name: '连接数据库' })).toBeVisible();
    await expect(page.getByPlaceholder('输入您的问题...')).toBeVisible();
  });
  
  test('应该能够切换到英文', async ({ page }) => {
    await page.goto('/');
    
    // 点击语言切换器
    await page.getByRole('button', { name: /语言/i }).click();
    await page.getByRole('menuitem', { name: 'English' }).click();
    
    // 验证界面切换到英文
    await expect(page.getByRole('button', { name: 'Connect Database' })).toBeVisible();
  });
  
  test('应该保持语言偏好', async ({ page, context }) => {
    await page.goto('/');
    
    // 切换到英文
    await page.getByRole('button', { name: /语言/i }).click();
    await page.getByRole('menuitem', { name: 'English' }).click();
    
    // 刷新页面
    await page.reload();
    
    // 验证仍然是英文
    await expect(page.getByRole('button', { name: 'Connect Database' })).toBeVisible();
  });
});
```

### 测试覆盖目标

- 单元测试覆盖率: ≥ 80%
- 属性测试: 每个属性至少 100 次迭代
- 端到端测试: 覆盖主要用户流程
- 翻译完整性: 100% 的翻译键都有对应的翻译


## 性能优化

### 1. 懒加载语言资源

**策略**: 只在需要时加载语言资源文件

**实现**:

```typescript
// 配置懒加载
i18n.init({
  // ... 其他配置
  backend: {
    loadPath: '/locales/{{lng}}/{{ns}}.json',
    // 按需加载
    lazy: true,
  },
});

// 动态导入语言资源
const loadLanguageAsync = async (language: string) => {
  const resources = await import(`./locales/${language}/index.ts`);
  i18n.addResourceBundle(language, 'translation', resources.default);
};
```

**收益**: 减少初始加载时间，提升首屏性能

### 2. 翻译缓存

**策略**: 缓存已翻译的文本，避免重复计算

**实现**:

```typescript
// i18next 内置缓存机制
i18n.init({
  // ... 其他配置
  cache: {
    enabled: true,
    expirationTime: 7 * 24 * 60 * 60 * 1000, // 7 天
  },
});

// 自定义缓存层（可选）
const translationCache = new Map<string, string>();

const cachedTranslate = (key: string, options?: any) => {
  const cacheKey = `${key}:${JSON.stringify(options)}`;
  
  if (translationCache.has(cacheKey)) {
    return translationCache.get(cacheKey)!;
  }
  
  const translation = i18n.t(key, options);
  translationCache.set(cacheKey, translation);
  
  return translation;
};
```

**收益**: 减少翻译函数调用开销，提升渲染性能

### 3. 组件优化

**策略**: 使用 React.memo 和 useMemo 避免不必要的重新渲染

**实现**:

```typescript
// 优化翻译组件
export const TranslatedText = memo<{ tKey: string; values?: any }>(
  ({ tKey, values }) => {
    const { t } = useTranslation();
    
    // 使用 useMemo 缓存翻译结果
    const text = useMemo(() => t(tKey, values), [t, tKey, values]);
    
    return <span>{text}</span>;
  }
);

TranslatedText.displayName = 'TranslatedText';

// 优化语言切换器
export const LanguageSwitcher = memo(() => {
  const { i18n } = useTranslation();
  
  // 使用 useCallback 缓存回调函数
  const handleChange = useCallback(
    (language: string) => {
      i18n.changeLanguage(language);
    },
    [i18n]
  );
  
  return (
    <DropdownMenu>
      {/* ... */}
    </DropdownMenu>
  );
});
```

**收益**: 减少组件重新渲染次数，提升交互性能

### 4. 语言切换性能

**目标**: 语言切换在 500ms 内完成

**优化措施**:

```typescript
// 预加载常用语言
const preloadLanguages = async () => {
  const languages = ['zh-CN', 'en-US'];
  
  await Promise.all(
    languages.map((lang) => i18n.loadLanguages(lang))
  );
};

// 在应用启动时预加载
useEffect(() => {
  preloadLanguages();
}, []);

// 优化语言切换
const changeLanguageOptimized = async (language: string) => {
  const startTime = performance.now();
  
  // 使用 startTransition 避免阻塞 UI
  startTransition(() => {
    i18n.changeLanguage(language);
  });
  
  const endTime = performance.now();
  const duration = endTime - startTime;
  
  // 监控性能
  if (duration > 500) {
    console.warn(`语言切换耗时 ${duration}ms，超过目标 500ms`);
  }
};
```

**收益**: 确保语言切换流畅，不阻塞用户交互

### 5. 代码分割

**策略**: 将翻译资源和相关代码分割到独立的 chunk

**实现**:

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'i18n': ['react-i18next', 'i18next'],
          'i18n-zh': ['./src/i18n/locales/zh-CN'],
          'i18n-en': ['./src/i18n/locales/en-US'],
        },
      },
    },
  },
});
```

**收益**: 减少主 bundle 大小，提升加载速度

### 性能监控

```typescript
/**
 * 性能监控工具
 */
export const i18nPerformanceMonitor = {
  // 监控翻译函数性能
  measureTranslation: (key: string, fn: () => string) => {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    if (duration > 10) {
      console.warn(`翻译键 ${key} 耗时 ${duration}ms`);
    }
    
    return result;
  },
  
  // 监控语言切换性能
  measureLanguageChange: async (
    language: string,
    fn: () => Promise<void>
  ) => {
    const start = performance.now();
    await fn();
    const duration = performance.now() - start;
    
    console.log(`切换到 ${language} 耗时 ${duration}ms`);
    
    // 发送到分析服务
    if (import.meta.env.PROD) {
      // 例如: analytics.track('language_change', { language, duration });
    }
  },
};
```

## 部署和维护

### 部署清单

在部署本地化功能之前，确保完成以下检查：

- [ ] 所有翻译键都有对应的中文和英文翻译
- [ ] 翻译文本经过审校，无语法错误
- [ ] 所有组件都使用翻译函数，没有硬编码文本
- [ ] 日期和数字格式化正确
- [ ] 语言切换功能正常工作
- [ ] 语言偏好正确保存和恢复
- [ ] 错误消息正确翻译
- [ ] 可访问性属性正确翻译
- [ ] 单元测试和属性测试全部通过
- [ ] 端到端测试覆盖主要流程
- [ ] 性能测试满足目标（语言切换 < 500ms）
- [ ] 文档已更新

### 维护指南

#### 添加新翻译

1. 在对应的翻译文件中添加新的键值对：

```json
// locales/zh-CN/common.json
{
  "newFeature": {
    "title": "新功能标题",
    "description": "新功能描述"
  }
}
```

2. 在所有支持的语言中添加相同的键：

```json
// locales/en-US/common.json
{
  "newFeature": {
    "title": "New Feature Title",
    "description": "New Feature Description"
  }
}
```

3. 在组件中使用新翻译：

```typescript
const { t } = useTranslation();
<h1>{t('common.newFeature.title')}</h1>
```

4. 添加测试验证新翻译：

```typescript
it('应该显示新功能标题', () => {
  expect(i18n.t('common.newFeature.title')).toBe('新功能标题');
});
```

#### 更新现有翻译

1. 修改翻译文件中的值
2. 确保所有语言都同步更新
3. 运行测试确保没有破坏现有功能
4. 在 UI 中验证更新后的文本

#### 添加新语言

1. 创建新的语言目录：

```bash
mkdir -p src/i18n/locales/ja-JP
```

2. 复制现有翻译文件并翻译：

```bash
cp -r src/i18n/locales/zh-CN/* src/i18n/locales/ja-JP/
# 然后翻译所有文件
```

3. 在 i18n 配置中注册新语言：

```typescript
i18n.init({
  resources: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP, // 新增
  },
});
```

4. 在语言切换器中添加新选项：

```typescript
const languages = [
  { code: 'zh-CN', name: '简体中文' },
  { code: 'en-US', name: 'English' },
  { code: 'ja-JP', name: '日本語' }, // 新增
];
```

### 翻译质量保证流程

1. **初稿翻译**: 开发者或翻译工具生成初稿
2. **专业审校**: 母语者审校翻译质量
3. **上下文验证**: 在实际 UI 中验证翻译是否合适
4. **用户测试**: 收集用户反馈
5. **持续改进**: 根据反馈优化翻译

### 监控和分析

```typescript
/**
 * 翻译使用情况分析
 */
export const trackTranslationUsage = () => {
  // 记录最常用的翻译键
  const usageStats = new Map<string, number>();
  
  const originalT = i18n.t.bind(i18n);
  i18n.t = (key: string, ...args: any[]) => {
    usageStats.set(key, (usageStats.get(key) || 0) + 1);
    return originalT(key, ...args);
  };
  
  // 定期上报统计数据
  setInterval(() => {
    const topKeys = Array.from(usageStats.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    
    console.log('最常用的翻译键:', topKeys);
    
    // 发送到分析服务
    if (import.meta.env.PROD) {
      // 例如: analytics.track('translation_usage', { topKeys });
    }
  }, 60000); // 每分钟
};
```

## 总结

本设计文档详细描述了 QueryWeaver 项目中文界面本地化的完整技术方案。通过集成 react-i18next 国际化框架，实现了：

1. **完整的多语言支持**: 支持中文和英文，易于扩展到其他语言
2. **灵活的语言切换**: 用户可以自由切换语言，偏好自动保存
3. **本地化格式化**: 日期、时间、数字都按照中文习惯格式化
4. **性能优化**: 懒加载、缓存、代码分割确保良好性能
5. **易于维护**: 结构化的翻译资源，清晰的维护流程
6. **完整的测试**: 单元测试和属性测试确保功能正确性

该方案遵循最佳实践，确保了可扩展性、可维护性和性能，为 QueryWeaver 提供了专业的国际化支持。
