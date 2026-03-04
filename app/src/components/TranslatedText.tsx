import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * 翻译文本组件属性
 */
interface TranslatedTextProps {
  /** 翻译键 */
  tKey: string;
  /** 插值变量 (可选) */
  values?: Record<string, any>;
  /** 默认值 (可选) */
  defaultValue?: string;
  /** HTML 标签类型 (默认 'span') */
  as?: keyof JSX.IntrinsicElements;
  /** CSS 类名 */
  className?: string;
}

/**
 * 优化的翻译文本组件
 * 
 * 使用 React.memo 和 useMemo 优化性能，避免不必要的重新渲染
 * 
 * @example
 * ```tsx
 * <TranslatedText tKey="common.buttons.save" />
 * <TranslatedText 
 *   tKey="common.status.connected" 
 *   values={{ name: '数据库' }}
 * />
 * ```
 */
export const TranslatedText = memo<TranslatedTextProps>(({
  tKey,
  values,
  defaultValue,
  as: Component = 'span',
  className,
}) => {
  const { t } = useTranslation();

  /**
   * 缓存翻译结果
   * 
   * 只有当 tKey 或 values 变化时才重新翻译
   */
  const translatedText = useMemo(() => {
    return t(tKey, { defaultValue, ...values });
  }, [t, tKey, defaultValue, values]);

  return <Component className={className}>{translatedText}</Component>;
});

// 设置显示名称
TranslatedText.displayName = 'TranslatedText';
