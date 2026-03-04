# QueryWeaver 国际化开发指南

本指南面向开发者，介绍如何在 QueryWeaver 项目中添加、维护和扩展国际化（i18n）功能。

## 目录

- [技术架构](#技术架构)
- [翻译键命名规范](#翻译键命名规范)
- [添加新翻译](#添加新翻译)
- [添加新语言](#添加新语言)
- [格式化工具](#格式化工具)
- [测试指南](#测试指南)
- [常见问题](#常见问题)

## 技术架构

### 核心技术栈

- **i18next**: 国际化框架核心
- **react-i18next**: React 集成
- **i18next-browser-languagedetector**: 浏览器语言检测
- **date-fns**: 日期时间格式化
- **Intl API**: 数字和货币格式化

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
│   │       └── ...
│   └── types.ts                # TypeScript 类型定义
├── components/
│   └── LanguageSwitcher.tsx    # 语言切换组件
└── utils/
    ├── formatDate.ts           # 日期格式化工具
    ├── formatNumber.ts         # 数字格式化工具
    └── errorMapping.ts         # 错误消息映射
```

## 翻译键命名规范

### 基本原则

1. **使用小写字母和点号分隔**: `module.category.key`
2. **保持层级清晰**: 最多 3-4 层嵌套
3. **使用描述性名称**: 键名应该清楚表达内容含义
4. **保持一致性**: 相同概念使用相同的键名模式

### 命名模式

```typescript
// ✅ 推荐
"common.buttons.save"           // 通用按钮
"database.modal.title"          // 数据库模态框标题
"chat.messages.querySuccess"    // 聊天成功消息
"errors.auth.notAuthenticated"  // 认证错误

// ❌ 不推荐
"SaveButton"                    // 缺少层级结构
"db_modal_title"                // 使用下划线
"chatQuerySuccessMessage"       // 过长且缺少层级
"error_not_auth"                // 不够描述性
```

### 模块分类

| 模块 | 用途 | 示例键 |
|------|------|--------|
| `common` | 通用文本、按钮、状态 | `common.buttons.save` |
| `auth` | 认证和授权 | `auth.login.title` |
| `database` | 数据库连接和管理 | `database.modal.title` |
| `chat` | 聊天界面和查询 | `chat.interface.placeholder` |
| `schema` | 模式查看器 | `schema.viewer.title` |
| `errors` | 错误消息 | `errors.network.timeout` |

### 特殊情况

#### 插值变量

使用双花括号 `{{variable}}` 表示插值变量：

```json
{
  "common.status.connected": "已连接: {{name}}",
  "chat.results.rows": "{{count}} 行"
}
```

#### 复数形式

使用 i18next 的复数规则：

```json
{
  "chat.results.row_one": "{{count}} 行",
  "chat.results.row_other": "{{count}} 行"
}
```

#### 长文本

对于长文本，可以使用数组或换行符：

```json
{
  "database.modal.description": "使用连接 URL 或手动输入连接到 PostgreSQL 或 MySQL 数据库。"
}
```

## 添加新翻译

### 步骤 1: 确定翻译键

根据命名规范确定合适的翻译键：

```typescript
// 示例: 添加一个新的按钮文本
const key = "common.buttons.export"; // 导出按钮
```

### 步骤 2: 添加到翻译文件

在所有支持的语言文件中添加翻译：

**中文 (app/src/i18n/locales/zh-CN/common.json)**:
```json
{
  "buttons": {
    "save": "保存",
    "cancel": "取消",
    "export": "导出"  // 新增
  }
}
```

**英文 (app/src/i18n/locales/en-US/common.json)**:
```json
{
  "buttons": {
    "save": "Save",
    "cancel": "Cancel",
    "export": "Export"  // 新增
  }
}
```

### 步骤 3: 在组件中使用

使用 `useTranslation` Hook 访问翻译：

```typescript
import { useTranslation } from 'react-i18next';

export const MyComponent = () => {
  const { t } = useTranslation();
  
  return (
    <button>
      {t('common.buttons.export')}
    </button>
  );
};
```

### 步骤 4: 处理插值变量

如果翻译包含变量：

```typescript
// 翻译文件
{
  "common.status.connected": "已连接: {{name}}"
}

// 组件中使用
const { t } = useTranslation();
const message = t('common.status.connected', { name: databaseName });
```

### 步骤 5: 更新类型定义（可选）

如果使用 TypeScript 类型检查，更新类型定义：

```typescript
// app/src/i18n/types.ts
export interface CommonTranslations {
  buttons: {
    save: string;
    cancel: string;
    export: string;  // 新增
  };
}
```

## 添加新语言

### 步骤 1: 创建语言目录

在 `app/src/i18n/locales/` 下创建新语言目录：

```bash
mkdir -p app/src/i18n/locales/ja-JP  # 日语示例
```

### 步骤 2: 复制翻译文件

复制现有语言的翻译文件作为模板：

```bash
cp -r app/src/i18n/locales/en-US/* app/src/i18n/locales/ja-JP/
```

### 步骤 3: 翻译内容

逐个文件翻译内容：

```json
// app/src/i18n/locales/ja-JP/common.json
{
  "appName": "QueryWeaver",
  "tagline": "グラフ駆動のText-to-SQLツール",
  "buttons": {
    "connect": "データベースに接続",
    "save": "保存",
    "cancel": "キャンセル"
  }
}
```

### 步骤 4: 注册新语言

在 i18n 配置中注册新语言：

```typescript
// app/src/i18n/index.ts
import jaJP from './locales/ja-JP';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': zhCN,
      'en-US': enUS,
      'ja-JP': jaJP,  // 新增
    },
    // ...
  });
```

### 步骤 5: 更新语言切换器

在语言切换器中添加新语言选项：

```typescript
// app/src/components/LanguageSwitcher.tsx
const languages = [
  { code: 'zh-CN', name: '简体中文', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
  { code: 'ja-JP', name: 'Japanese', nativeName: '日本語' },  // 新增
];
```

### 步骤 6: 添加 date-fns locale

如果需要日期格式化支持，导入 date-fns locale：

```typescript
// app/src/utils/formatDate.ts
import { ja } from 'date-fns/locale';

const getLocale = (language: string) => {
  switch (language) {
    case 'zh-CN':
      return zhCN;
    case 'en-US':
      return enUS;
    case 'ja-JP':
      return ja;  // 新增
    default:
      return zhCN;
  }
};
```

### 步骤 7: 测试新语言

1. 启动开发服务器
2. 切换到新语言
3. 检查所有页面和功能
4. 验证日期、数字格式化
5. 测试错误消息显示

## 格式化工具

### 日期时间格式化

使用 `formatDate` 工具函数：

```typescript
import { formatDate, formatRelativeTime, formatTimestamp } from '@/utils/formatDate';

// 格式化日期
const date = formatDate(new Date(), 'PPP', 'zh-CN');
// 输出: "2025年1月15日"

// 相对时间
const relative = formatRelativeTime(new Date(Date.now() - 3600000), 'zh-CN');
// 输出: "1小时前"

// 时间戳
const timestamp = formatTimestamp(new Date(), 'zh-CN');
// 输出: "2025年01月15日 14:30:00"
```

### 数字格式化

使用 `formatNumber` 工具函数：

```typescript
import { 
  formatNumber, 
  formatCurrency, 
  formatPercent, 
  formatLargeNumber 
} from '@/utils/formatNumber';

// 数字格式化
const num = formatNumber(1234567, 'zh-CN');
// 输出: "1,234,567"

// 货币格式化
const price = formatCurrency(99.99, 'CNY', 'zh-CN');
// 输出: "¥99.99"

// 百分比
const percent = formatPercent(0.856, 'zh-CN');
// 输出: "86%"

// 大数字（中文单位）
const large = formatLargeNumber(12345678, 'zh-CN');
// 输出: "1234.57万"
```

### 错误消息翻译

使用 `translateError` 工具函数：

```typescript
import { translateError } from '@/utils/errorMapping';

try {
  // 某些操作
} catch (error) {
  const message = translateError(error);
  toast({
    title: t('errors.common.title'),
    description: message,
    variant: 'destructive',
  });
}
```

## 测试指南

### 单元测试

测试翻译键是否存在：

```typescript
import i18n from '@/i18n';

describe('翻译完整性', () => {
  it('应该包含所有必需的翻译键', () => {
    expect(i18n.t('common.buttons.save')).not.toBe('common.buttons.save');
    expect(i18n.t('database.modal.title')).toBeDefined();
  });
  
  it('应该处理插值变量', () => {
    const result = i18n.t('common.status.connected', { name: '测试' });
    expect(result).toContain('测试');
  });
});
```

### 格式化测试

测试日期和数字格式化：

```typescript
import { formatDate, formatNumber } from '@/utils/formatDate';

describe('日期格式化', () => {
  it('应该格式化为中文日期', () => {
    const date = new Date('2025-01-15');
    const formatted = formatDate(date, 'PPP', 'zh-CN');
    expect(formatted).toContain('2025年');
    expect(formatted).toContain('1月');
    expect(formatted).toContain('15日');
  });
});

describe('数字格式化', () => {
  it('应该添加千位分隔符', () => {
    const formatted = formatNumber(1234567, 'zh-CN');
    expect(formatted).toBe('1,234,567');
  });
});
```

### 组件测试

测试组件中的翻译：

```typescript
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('应该显示翻译后的文本', () => {
    render(
      <I18nextProvider i18n={i18n}>
        <MyComponent />
      </I18nextProvider>
    );
    
    expect(screen.getByText('保存')).toBeInTheDocument();
  });
});
```

### 端到端测试

使用 Playwright 测试语言切换：

```typescript
import { test, expect } from '@playwright/test';

test('语言切换', async ({ page }) => {
  await page.goto('/');
  
  // 验证默认中文
  await expect(page.getByRole('button', { name: '连接数据库' })).toBeVisible();
  
  // 切换到英文
  await page.getByRole('button', { name: /语言/i }).click();
  await page.getByRole('menuitem', { name: 'English' }).click();
  
  // 验证英文界面
  await expect(page.getByRole('button', { name: 'Connect Database' })).toBeVisible();
});
```

## 常见问题

### Q: 翻译键不存在时会发生什么？

A: i18next 会返回翻译键本身。在开发模式下，控制台会显示警告。

```typescript
// 不存在的键
t('nonexistent.key')  // 返回: "nonexistent.key"
```

### Q: 如何处理动态翻译键？

A: 使用字符串拼接或模板字符串：

```typescript
const type = 'postgresql';
const label = t(`database.types.${type}`);
```

### Q: 如何在非组件代码中使用翻译？

A: 直接导入 i18n 实例：

```typescript
import i18n from '@/i18n';

const message = i18n.t('errors.network.timeout');
```

### Q: 如何处理 HTML 内容？

A: 使用 `Trans` 组件：

```typescript
import { Trans } from 'react-i18next';

<Trans i18nKey="database.modal.description">
  使用连接 URL 或<strong>手动输入</strong>连接到数据库。
</Trans>
```

### Q: 如何调试翻译问题？

A: 启用 i18next 调试模式：

```typescript
i18n.init({
  debug: true,  // 在控制台显示详细日志
  // ...
});
```

### Q: 如何处理缺失的翻译？

A: 提供默认值：

```typescript
t('some.key', { defaultValue: '默认文本' })
```

### Q: 如何优化性能？

A: 
1. 使用命名空间分割翻译文件
2. 启用懒加载
3. 使用 React.memo 优化组件
4. 缓存翻译结果

```typescript
// 懒加载配置
i18n.init({
  backend: {
    loadPath: '/locales/{{lng}}/{{ns}}.json',
  },
  ns: ['common', 'database', 'chat'],
  defaultNS: 'common',
});
```

## 最佳实践

### 1. 保持翻译文件同步

确保所有语言的翻译文件具有相同的键结构：

```bash
# 使用工具检查翻译完整性
npm run i18n:check
```

### 2. 使用命名空间

对于大型应用，使用命名空间组织翻译：

```typescript
const { t } = useTranslation('database');
t('modal.title');  // 等同于 t('database:modal.title')
```

### 3. 避免硬编码文本

所有用户可见的文本都应该使用翻译：

```typescript
// ❌ 不推荐
<button>保存</button>

// ✅ 推荐
<button>{t('common.buttons.save')}</button>
```

### 4. 提供上下文

为翻译者提供上下文注释：

```json
{
  "common.buttons.save": "保存",
  "_comment": "用于保存表单数据的按钮"
}
```

### 5. 测试所有语言

在发布前测试所有支持的语言：

```bash
# 运行 i18n 测试
npm run test:i18n
```

## 工具和资源

### 推荐工具

- **i18n Ally** (VS Code 扩展): 可视化翻译管理
- **i18next-parser**: 自动提取翻译键
- **i18next-scanner**: 扫描代码中的翻译键

### 有用的链接

- [i18next 官方文档](https://www.i18next.com/)
- [react-i18next 文档](https://react.i18next.com/)
- [date-fns 文档](https://date-fns.org/)
- [Intl API 文档](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)

## 贡献

如果您发现翻译问题或想要改进本指南，请：

1. 提交 Issue 描述问题
2. 创建 Pull Request 提供修复
3. 参考 [翻译贡献指南](i18n-contribution-guide.md)

---

**最后更新**: 2025-01-15
**维护者**: QueryWeaver 开发团队
