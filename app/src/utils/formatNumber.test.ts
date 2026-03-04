import { describe, it, expect } from 'vitest';
import { formatNumber, formatCurrency, formatPercent, formatLargeNumber } from './formatNumber';

/**
 * 数字格式化工具单元测试
 */
describe('formatNumber', () => {
  it('应该格式化数字并添加千位分隔符', () => {
    expect(formatNumber(1234567, 'zh-CN')).toBe('1,234,567');
    expect(formatNumber(1000, 'zh-CN')).toBe('1,000');
    expect(formatNumber(999, 'zh-CN')).toBe('999');
  });

  it('应该处理小数', () => {
    expect(formatNumber(1234.56, 'zh-CN')).toBe('1,234.56');
  });

  it('应该处理零和负数', () => {
    expect(formatNumber(0, 'zh-CN')).toBe('0');
    expect(formatNumber(-1234, 'zh-CN')).toBe('-1,234');
  });

  it('应该支持英文格式', () => {
    expect(formatNumber(1234567, 'en-US')).toBe('1,234,567');
  });
});

describe('formatCurrency', () => {
  it('应该格式化为人民币', () => {
    const formatted = formatCurrency(1234.56, 'CNY', 'zh-CN');
    expect(formatted).toContain('1,234.56');
    expect(formatted).toMatch(/¥|CN¥/);
  });

  it('应该格式化为美元', () => {
    const formatted = formatCurrency(1234.56, 'USD', 'en-US');
    expect(formatted).toContain('1,234.56');
    expect(formatted).toContain('$');
  });

  it('应该处理零金额', () => {
    const formatted = formatCurrency(0, 'CNY', 'zh-CN');
    expect(formatted).toMatch(/¥|CN¥/);
    expect(formatted).toContain('0');
  });

  it('应该处理负金额', () => {
    const formatted = formatCurrency(-100, 'CNY', 'zh-CN');
    expect(formatted).toContain('-');
    expect(formatted).toContain('100');
  });
});

describe('formatPercent', () => {
  it('应该格式化百分比', () => {
    expect(formatPercent(0.1234, 'zh-CN')).toBe('12.34%');
    expect(formatPercent(0.5, 'zh-CN')).toBe('50%');
    expect(formatPercent(1, 'zh-CN')).toBe('100%');
  });

  it('应该处理零百分比', () => {
    expect(formatPercent(0, 'zh-CN')).toBe('0%');
  });

  it('应该处理大于1的值', () => {
    expect(formatPercent(1.5, 'zh-CN')).toBe('150%');
  });

  it('应该支持英文格式', () => {
    expect(formatPercent(0.1234, 'en-US')).toBe('12.34%');
  });
});

describe('formatLargeNumber', () => {
  it('应该使用"万"单位格式化中文大数字', () => {
    expect(formatLargeNumber(10000, 'zh-CN')).toBe('1.00万');
    expect(formatLargeNumber(50000, 'zh-CN')).toBe('5.00万');
    expect(formatLargeNumber(123456, 'zh-CN')).toBe('12.35万');
  });

  it('应该使用"亿"单位格式化中文超大数字', () => {
    expect(formatLargeNumber(100000000, 'zh-CN')).toBe('1.00亿');
    expect(formatLargeNumber(500000000, 'zh-CN')).toBe('5.00亿');
    expect(formatLargeNumber(1234567890, 'zh-CN')).toBe('12.35亿');
  });

  it('应该直接格式化小于1万的数字', () => {
    expect(formatLargeNumber(9999, 'zh-CN')).toBe('9,999');
    expect(formatLargeNumber(1000, 'zh-CN')).toBe('1,000');
  });

  it('应该使用K/M/B单位格式化英文大数字', () => {
    expect(formatLargeNumber(1000, 'en-US')).toBe('1.00K');
    expect(formatLargeNumber(1000000, 'en-US')).toBe('1.00M');
    expect(formatLargeNumber(1000000000, 'en-US')).toBe('1.00B');
  });

  it('应该直接格式化小于1000的英文数字', () => {
    expect(formatLargeNumber(999, 'en-US')).toBe('999');
  });

  it('应该处理零', () => {
    expect(formatLargeNumber(0, 'zh-CN')).toBe('0');
    expect(formatLargeNumber(0, 'en-US')).toBe('0');
  });
});
