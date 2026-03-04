import { describe, it, expect } from 'vitest';
import { formatDate, formatRelativeTime, formatTimestamp } from './formatDate';

/**
 * 日期时间格式化工具单元测试
 */
describe('formatDate', () => {
  it('应该格式化为中文日期格式', () => {
    const date = new Date('2025-01-15T10:30:00');
    const formatted = formatDate(date, 'PPP', 'zh-CN');
    
    // 验证包含中文日期字符
    expect(formatted).toContain('2025年');
    expect(formatted).toContain('1月');
    expect(formatted).toContain('15日');
  });

  it('应该格式化为英文日期格式', () => {
    const date = new Date('2025-01-15T10:30:00');
    const formatted = formatDate(date, 'PPP', 'en-US');
    
    // 验证英文格式
    expect(formatted).toContain('January');
    expect(formatted).toContain('15');
    expect(formatted).toContain('2025');
  });

  it('应该使用24小时制格式化时间', () => {
    const date = new Date('2025-01-15T14:30:00');
    const formatted = formatDate(date, 'HH:mm', 'zh-CN');
    
    expect(formatted).toBe('14:30');
  });

  it('应该处理时间戳输入', () => {
    const timestamp = new Date('2025-01-15T10:30:00').getTime();
    const formatted = formatDate(timestamp, 'PPP', 'zh-CN');
    
    expect(formatted).toContain('2025年');
  });
});

describe('formatRelativeTime', () => {
  it('应该格式化相对时间为中文', () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    const formatted = formatRelativeTime(fiveMinutesAgo, 'zh-CN');
    
    // 验证包含中文相对时间表达
    expect(formatted).toMatch(/分钟前|秒前/);
  });

  it('应该格式化相对时间为英文', () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    const formatted = formatRelativeTime(fiveMinutesAgo, 'en-US');
    
    // 验证英文相对时间表达
    expect(formatted).toMatch(/ago/);
  });
});

describe('formatTimestamp', () => {
  it('应该格式化时间戳为中文格式', () => {
    const date = new Date('2025-01-15T14:30:45');
    const formatted = formatTimestamp(date, 'zh-CN');
    
    expect(formatted).toBe('2025年01月15日 14:30:45');
  });

  it('应该格式化时间戳为英文格式', () => {
    const date = new Date('2025-01-15T14:30:45');
    const formatted = formatTimestamp(date, 'en-US');
    
    // 验证英文格式包含日期和时间
    expect(formatted).toContain('Jan');
    expect(formatted).toContain('2025');
    expect(formatted).toContain('PM');
  });

  it('应该处理时间戳数字输入', () => {
    const timestamp = new Date('2025-01-15T14:30:45').getTime();
    const formatted = formatTimestamp(timestamp, 'zh-CN');
    
    expect(formatted).toContain('2025年');
    expect(formatted).toContain('14:30:45');
  });
});
