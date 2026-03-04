/**
 * i18n 配置测试
 * 
 * 验证 i18n 初始化和基本功能
 */

import { describe, it, expect, beforeEach } from 'vitest';
import i18n from './index';

describe('i18n 配置', () => {
  beforeEach(async () => {
    // 重置语言为默认中文
    await i18n.changeLanguage('zh-CN');
  });

  it('应该默认使用中文', () => {
    expect(i18n.language).toBe('zh-CN');
  });

  it('应该加载中文翻译资源', () => {
    expect(i18n.hasResourceBundle('zh-CN', 'common')).toBe(true);
    expect(i18n.hasResourceBundle('zh-CN', 'database')).toBe(true);
    expect(i18n.hasResourceBundle('zh-CN', 'chat')).toBe(true);
    expect(i18n.hasResourceBundle('zh-CN', 'schema')).toBe(true);
    expect(i18n.hasResourceBundle('zh-CN', 'errors')).toBe(true);
  });

  it('应该加载英文翻译资源', () => {
    expect(i18n.hasResourceBundle('en-US', 'common')).toBe(true);
    expect(i18n.hasResourceBundle('en-US', 'database')).toBe(true);
    expect(i18n.hasResourceBundle('en-US', 'chat')).toBe(true);
    expect(i18n.hasResourceBundle('en-US', 'schema')).toBe(true);
    expect(i18n.hasResourceBundle('en-US', 'errors')).toBe(true);
  });

  it('应该返回正确的中文翻译', () => {
    expect(i18n.t('common:buttons.save')).toBe('保存');
    expect(i18n.t('common:buttons.cancel')).toBe('取消');
    expect(i18n.t('database:modal.title')).toBe('连接到数据库');
  });

  it('应该能够切换到英文', async () => {
    await i18n.changeLanguage('en-US');
    expect(i18n.language).toBe('en-US');
    expect(i18n.t('common:buttons.save')).toBe('Save');
    expect(i18n.t('common:buttons.cancel')).toBe('Cancel');
  });

  it('应该处理插值变量', () => {
    const result = i18n.t('common:status.connected', { name: '测试数据库' });
    expect(result).toBe('已连接: 测试数据库');
  });

  it('应该处理缺失的翻译键', () => {
    const result = i18n.t('nonexistent:key');
    // i18next 默认返回键的最后一部分
    expect(result).toBe('key');
  });

  it('应该使用 fallback 语言', async () => {
    // 切换到不存在的语言
    await i18n.changeLanguage('fr-FR');
    // 应该降级到 fallback 语言（中文）
    const result = i18n.t('common:buttons.save');
    expect(result).toBe('保存');
  });
});
