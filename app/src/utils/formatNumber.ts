/**
 * 数字格式化工具
 * 
 * 根据当前语言设置格式化数字、货币和百分比
 */

/**
 * 格式化数字 (添加千位分隔符)
 * @param num - 数字
 * @param language - 语言代码
 * @returns 格式化后的数字字符串
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
 * @returns 格式化后的货币字符串
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
 * @returns 格式化后的百分比字符串
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
 * @returns 格式化后的大数字字符串
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
