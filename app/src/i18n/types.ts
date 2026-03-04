/**
 * 翻译资源类型定义
 * 
 * 提供类型安全的翻译键访问
 */

// 通用翻译
export interface CommonTranslations {
  appName: string;
  tagline: string;
  changeLanguage: string;
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

// 认证翻译
export interface AuthTranslations {
  login: {
    title: string;
    description: string;
    email: string;
    password: string;
    rememberMe: string;
    forgotPassword: string;
    submit: string;
    noAccount: string;
    signUp: string;
  };
  register: {
    title: string;
    description: string;
    email: string;
    password: string;
    confirmPassword: string;
    submit: string;
    hasAccount: string;
    signIn: string;
  };
  oauth: {
    continueWith: string;
    google: string;
    github: string;
    microsoft: string;
  };
  messages: {
    loginSuccess: string;
    logoutSuccess: string;
    registerSuccess: string;
    passwordMismatch: string;
    weakPassword: string;
    emailInUse: string;
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

// 模式查看器翻译
export interface SchemaTranslations {
  title: string;
  noSchema: string;
  tables: string;
  columns: string;
  relationships: string;
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
  auth: AuthTranslations;
  database: DatabaseTranslations;
  chat: ChatTranslations;
  schema: SchemaTranslations;
  errors: ErrorTranslations;
}

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
