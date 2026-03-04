# 格式化工具函数

本目录包含用于日期时间和数字格式化的工具函数，支持中英文本地化。

## 日期时间格式化 (formatDate.ts)

### formatDate

格式化日期为指定格式。

```typescript
import { formatDate } from '@/utils/formatDate';

// 中文格式
formatDate(new Date(), 'PPP', 'zh-CN');
// 输出: "2025年1月15日"

// 英文格式
formatDate(new Date(), 'PPP', 'en-US');
// 输出: "January 15, 2025"

// 自定义格式
formatDate(new Date(), 'yyyy-MM-dd', 'zh-CN');
// 输出: "2025-01-15"
```

### formatRelativeTime

格式化相对时间（如"5分钟前"）。

```typescript
import { formatRelativeTime } from '@/utils/formatDate';

const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);

// 中文格式
formatRelativeTime(fiveMinutesAgo, 'zh-CN');
// 输出: "5分钟前"

// 英文格式
formatRelativeTime(fiveMinutesAgo, 'en-US');
// 输出: "5 minutes ago"
```

### formatTimestamp

格式化时间戳为完整的日期时间字符串。

```typescript
import { formatTimestamp } from '@/utils/formatDate';

// 中文格式
formatTimestamp(new Date(), 'zh-CN');
// 输出: "2025年01月15日 14:30:45"

// 英文格式
formatTimestamp(new Date(), 'en-US');
// 输出: "Jan 15, 2025, 2:30:45 PM"
```

## 数字格式化 (formatNumber.ts)

### formatNumber

格式化数字，添加千位分隔符。

```typescript
import { formatNumber } from '@/utils/formatNumber';

formatNumber(1234567, 'zh-CN');
// 输出: "1,234,567"

formatNumber(1234.56, 'zh-CN');
// 输出: "1,234.56"
```

### formatCurrency

格式化货币。

```typescript
import { formatCurrency } from '@/utils/formatNumber';

// 人民币
formatCurrency(1234.56, 'CNY', 'zh-CN');
// 输出: "¥1,234.56"

// 美元
formatCurrency(1234.56, 'USD', 'en-US');
// 输出: "$1,234.56"
```

### formatPercent

格式化百分比。

```typescript
import { formatPercent } from '@/utils/formatNumber';

formatPercent(0.1234, 'zh-CN');
// 输出: "12.34%"

formatPercent(0.5, 'zh-CN');
// 输出: "50%"
```

### formatLargeNumber

格式化大数字，使用中文单位（万、亿）或英文单位（K、M、B）。

```typescript
import { formatLargeNumber } from '@/utils/formatNumber';

// 中文格式
formatLargeNumber(50000, 'zh-CN');
// 输出: "5.00万"

formatLargeNumber(500000000, 'zh-CN');
// 输出: "5.00亿"

// 英文格式
formatLargeNumber(50000, 'en-US');
// 输出: "50.00K"

formatLargeNumber(5000000, 'en-US');
// 输出: "5.00M"
```

## 在组件中使用

### 结合 i18n 使用

```typescript
import { useTranslation } from 'react-i18next';
import { formatDate, formatRelativeTime } from '@/utils/formatDate';
import { formatNumber, formatCurrency } from '@/utils/formatNumber';

export const MyComponent = () => {
  const { i18n } = useTranslation();
  const currentLanguage = i18n.language;

  return (
    <div>
      <p>日期: {formatDate(new Date(), 'PPP', currentLanguage)}</p>
      <p>时间: {formatRelativeTime(new Date(), currentLanguage)}</p>
      <p>数字: {formatNumber(1234567, currentLanguage)}</p>
      <p>金额: {formatCurrency(1234.56, 'CNY', currentLanguage)}</p>
    </div>
  );
};
```

### 在查询结果中使用

```typescript
import { formatNumber, formatTimestamp } from '@/utils/formatNumber';
import { formatTimestamp } from '@/utils/formatDate';

export const QueryResults = ({ data, executionTime }) => {
  const { i18n } = useTranslation();
  
  return (
    <div>
      <p>结果行数: {formatNumber(data.length, i18n.language)}</p>
      <p>执行时间: {executionTime}ms</p>
      <p>查询时间: {formatTimestamp(new Date(), i18n.language)}</p>
    </div>
  );
};
```

## 测试

运行单元测试：

```bash
npm test -- formatDate.test.ts formatNumber.test.ts --run
```

## 注意事项

1. **语言代码**: 默认使用 'zh-CN'（简体中文），也支持 'en-US'（美式英语）
2. **date-fns**: 日期格式化依赖 date-fns 库，确保已安装
3. **Intl API**: 数字格式化使用浏览器原生的 Intl API，兼容性良好
4. **性能**: 这些函数都是纯函数，可以安全地在 React 组件中使用
5. **扩展性**: 如需支持更多语言，只需在 getLocale 函数中添加对应的 locale

## 相关文档

- [date-fns 文档](https://date-fns.org/)
- [Intl.NumberFormat 文档](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat)
- [Intl.DateTimeFormat 文档](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat)
