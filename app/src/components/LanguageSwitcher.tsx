import { useState, useMemo, useCallback, memo } from 'react';
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
 * 语言配置接口
 */
interface LanguageConfig {
  /** 语言代码 (如 'zh-CN') */
  code: string;
  /** 英文名称 (如 'Chinese') */
  name: string;
  /** 本地名称 (如 '简体中文') */
  nativeName: string;
}

/**
 * 支持的语言列表 (常量，避免重复创建)
 */
const SUPPORTED_LANGUAGES: readonly LanguageConfig[] = [
  { code: 'zh-CN', name: 'Chinese', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
] as const;

/**
 * 语言切换组件
 * 
 * 功能:
 * - 显示当前语言
 * - 提供语言选择下拉菜单
 * - 切换语言并保存到 localStorage
 * 
 * 性能优化:
 * - 使用 React.memo 避免不必要的重新渲染
 * - 使用 useMemo 缓存计算结果
 * - 使用 useCallback 缓存回调函数
 * 
 * @example
 * ```tsx
 * <LanguageSwitcher />
 * ```
 */
export const LanguageSwitcher = memo(() => {
  const { i18n, t } = useTranslation();
  const [isChanging, setIsChanging] = useState(false);

  /**
   * 获取当前语言配置 (使用 useMemo 缓存)
   */
  const currentLanguage = useMemo(() => {
    return SUPPORTED_LANGUAGES.find(
      (lang) => lang.code === i18n.language
    ) || SUPPORTED_LANGUAGES[0];
  }, [i18n.language]);

  /**
   * 缓存翻译文本 (避免每次渲染都调用 t 函数)
   */
  const changeLanguageLabel = useMemo(() => {
    return t('common.changeLanguage');
  }, [t]);

  /**
   * 处理语言切换 (使用 useCallback 缓存函数)
   * 
   * @param languageCode - 目标语言代码
   */
  const handleLanguageChange = useCallback(async (languageCode: string) => {
    setIsChanging(true);
    try {
      await i18n.changeLanguage(languageCode);
      // i18next 会自动保存到 localStorage (通过 LanguageDetector 配置)
    } catch (error) {
      console.error('语言切换失败:', error);
    } finally {
      setIsChanging(false);
    }
  }, [i18n]);

  /**
   * 渲染语言菜单项 (使用 useCallback 缓存)
   */
  const renderLanguageItem = useCallback((language: LanguageConfig) => {
    const isActive = currentLanguage.code === language.code;
    
    return (
      <DropdownMenuItem
        key={language.code}
        onClick={() => handleLanguageChange(language.code)}
        className={isActive ? 'bg-accent' : ''}
      >
        {language.nativeName}
        {isActive && <span className="ml-2">✓</span>}
      </DropdownMenuItem>
    );
  }, [currentLanguage.code, handleLanguageChange]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          disabled={isChanging}
          title={changeLanguageLabel}
          aria-label={changeLanguageLabel}
        >
          <Globe className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {SUPPORTED_LANGUAGES.map(renderLanguageItem)}
      </DropdownMenuContent>
    </DropdownMenu>
  );
});

// 设置显示名称 (用于 React DevTools)
LanguageSwitcher.displayName = 'LanguageSwitcher';
