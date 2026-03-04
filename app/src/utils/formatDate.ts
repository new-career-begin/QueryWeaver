import { format, formatDistanceToNow } from 'date-fns';
import { zhCN, enUS } from 'date-fns/locale';

/**
 * 日期时间格式化工具
 * 
 * 根据当前语言设置格式化日期和时间
 */

/**
 * 获取当前语言的 date-fns locale
 * @param language - 语言代码
 * @returns date-fns locale 对象
 */
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
 * @returns 格式化后的日期字符串
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
 * @returns 相对时间字符串
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
 * @returns 格式化后的时间戳字符串
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
