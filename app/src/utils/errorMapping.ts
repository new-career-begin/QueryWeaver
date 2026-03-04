import i18n from '@/i18n';

/**
 * 后端错误消息映射
 * 
 * 将后端返回的英文错误消息映射为中文
 */

/**
 * 错误代码到翻译键的映射
 * 
 * 用于将后端返回的标准错误代码映射到 i18n 翻译键
 */
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

/**
 * 错误消息模式定义
 * 
 * 用于匹配后端返回的英文错误消息并转换为中文
 */
interface ErrorPattern {
  /** 匹配模式的正则表达式 */
  pattern: RegExp;
  /** 处理函数，接收原始消息并返回中文消息 */
  handler: (message: string) => string;
}

/**
 * 错误消息模式匹配列表
 * 
 * 按优先级顺序匹配，第一个匹配的模式将被使用
 */
const errorPatterns: ErrorPattern[] = [
  {
    // 匹配唯一约束冲突错误
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
    // 匹配外键约束冲突错误
    pattern: /violates foreign key constraint/i,
    handler: () => '由于其他表中存在相关记录，无法执行此操作',
  },
  {
    // 匹配非空约束冲突错误
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
    // 匹配 PostgreSQL 查询执行错误
    pattern: /(PostgreSQL|MySQL) query execution error:/i,
    handler: (message: string) => {
      // 移除技术前缀，只保留实际错误信息
      return message.replace(/^(PostgreSQL|MySQL) query execution error:\s*/i, '').split('\n')[0];
    },
  },
  {
    // 匹配表不存在错误
    pattern: /relation "(\w+)" does not exist/i,
    handler: (message: string) => {
      const match = message.match(/relation "(\w+)" does not exist/i);
      if (match) {
        return `表 "${match[1]}" 不存在`;
      }
      return i18n.t('errors.database.tableNotFound');
    },
  },
  {
    // 匹配列不存在错误
    pattern: /column "(\w+)" does not exist/i,
    handler: (message: string) => {
      const match = message.match(/column "(\w+)" does not exist/i);
      if (match) {
        return `列 "${match[1]}" 不存在`;
      }
      return i18n.t('errors.database.columnNotFound');
    },
  },
  {
    // 匹配语法错误
    pattern: /syntax error at or near/i,
    handler: () => i18n.t('errors.database.syntaxError'),
  },
  {
    // 匹配权限错误
    pattern: /permission denied/i,
    handler: () => i18n.t('errors.database.permissionDenied'),
  },
  {
    // 匹配连接超时错误
    pattern: /connection timeout|timed out/i,
    handler: () => i18n.t('errors.database.connectionTimeout'),
  },
  {
    // 匹配网络错误
    pattern: /network error|failed to fetch/i,
    handler: () => i18n.t('errors.network.offline'),
  },
];

/**
 * 翻译错误消息
 * 
 * 将后端返回的错误消息转换为用户友好的中文消息
 * 
 * @param error - 错误对象或错误消息字符串
 * @returns 翻译后的中文错误消息
 * 
 * @example
 * ```typescript
 * // 使用错误代码
 * const error = { code: 'AUTH_REQUIRED', message: 'Authentication required' };
 * translateError(error); // "未认证。请登录以连接数据库。"
 * 
 * // 使用错误消息模式匹配
 * translateError('duplicate key value violates unique constraint');
 * // "该记录已存在于数据库中"
 * 
 * // 已经是中文的错误消息
 * translateError('连接失败'); // "连接失败"
 * ```
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
