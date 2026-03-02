---
inclusion: fileMatch
fileMatchPattern: "app/**/*.{tsx,ts,css}"
---

# QueryWeaver 设计系统规范

## 概述

QueryWeaver 使用基于 **shadcn/ui Clean Slate** 主题的设计系统，采用 **OKLch 颜色空间**实现感知均匀的颜色系统，支持亮色/暗色主题无缝切换。

### 核心技术栈
- **UI 框架**: Radix UI + shadcn/ui
- **样式方案**: Tailwind CSS v3
- **颜色空间**: OKLch (感知均匀)
- **字体系统**: Inter (Sans) + Merriweather (Serif) + JetBrains Mono (Mono)
- **主题切换**: CSS 变量 + data-theme 属性

---

## 颜色系统

### 主色调 (Primary)

**用途**: 主要操作按钮、链接、重要元素高亮

```css
/* 亮色模式 */
--primary: oklch(0.5531 0.2471 301.88);           /* 紫色 */
--primary-foreground: oklch(1.0000 0 0);          /* 白色文字 */

/* 暗色模式 */
--primary: oklch(0.6801 0.1583 276.9349);         /* 浅紫色 */
--primary-foreground: oklch(0.2077 0.0398 265.7549); /* 深色文字 */
```

**使用示例**:
```tsx
<Button className="bg-primary text-primary-foreground">
  提交查询
</Button>
```

### 语义色系统

#### 背景色 (Background)

```css
/* 亮色模式 */
--background: oklch(0.9842 0.0034 247.8575);      /* 极浅灰 */
--foreground: oklch(0.2795 0.0368 260.0310);      /* 深灰文字 */

/* 暗色模式 */
--background: oklch(0.1158 0 0);                  /* 深黑色 */
--foreground: oklch(0.9288 0.0126 255.5078);      /* 浅灰文字 */
```

#### 卡片色 (Card)
```css
/* 亮色模式 */
--card: oklch(1.0000 0 0);                        /* 纯白 */
--card-foreground: oklch(0.2795 0.0368 260.0310); /* 深灰文字 */

/* 暗色模式 */
--card: oklch(0.1158 0 0);                        /* 深黑色 */
--card-foreground: oklch(0.9288 0.0126 255.5078); /* 浅灰文字 */
```

#### 次要色 (Secondary)
```css
/* 亮色模式 */
--secondary: oklch(0.9276 0.0058 264.5313);       /* 浅灰 */
--secondary-foreground: oklch(0.3729 0.0306 259.7328); /* 中灰文字 */

/* 暗色模式 */
--secondary: oklch(0.3351 0.0331 260.9120);       /* 深灰 */
--secondary-foreground: oklch(0.8717 0.0093 258.3382); /* 浅灰文字 */
```

#### 柔和色 (Muted)
```css
/* 亮色模式 */
--muted: oklch(0.9670 0.0029 264.5419);           /* 极浅灰 */
--muted-foreground: oklch(0.5510 0.0234 264.3637); /* 中灰文字 */

/* 暗色模式 */
--muted: oklch(0.1800 0 0);                       /* 深灰 */
--muted-foreground: oklch(0.7137 0.0192 261.3246); /* 浅灰文字 */
```

#### 强调色 (Accent)
```css
/* 亮色模式 */
--accent: oklch(0.9299 0.0334 272.7879);          /* 浅蓝灰 */
--accent-foreground: oklch(0.3729 0.0306 259.7328); /* 深灰文字 */

/* 暗色模式 */
--accent: oklch(0.2400 0 0);                      /* 深灰 */
--accent-foreground: oklch(0.8717 0.0093 258.3382); /* 浅灰文字 */
```

### 状态色系统

#### 成功 (Success)
```css
--success: oklch(0.6500 0.1800 145.0000);         /* 绿色 */
--success-foreground: oklch(1.0000 0 0);          /* 白色文字 (亮色) */
--success-foreground: oklch(0.1158 0 0);          /* 黑色文字 (暗色) */
```

**使用场景**: 查询成功、数据加载完成、操作成功提示

#### 警告 (Warning)
```css
--warning: oklch(0.7500 0.1500 90.0000);          /* 黄色 */
--warning-foreground: oklch(0.2000 0.0300 90.0000); /* 深色文字 (亮色) */
--warning-foreground: oklch(0.1158 0 0);          /* 黑色文字 (暗色) */
```

**使用场景**: 查询超时警告、数据量过大提示

#### 错误 (Error/Destructive)
```css
--error: oklch(0.6368 0.2078 25.3313);            /* 红色 */
--error-foreground: oklch(1.0000 0 0);            /* 白色文字 (亮色) */
--error-foreground: oklch(0.1158 0 0);            /* 黑色文字 (暗色) */
```

**使用场景**: SQL 错误、连接失败、删除操作

#### 信息 (Info)
```css
--info: oklch(0.6500 0.1800 240.0000);            /* 蓝色 */
--info-foreground: oklch(1.0000 0 0);             /* 白色文字 (亮色) */
--info-foreground: oklch(0.1158 0 0);             /* 黑色文字 (暗色) */
```

**使用场景**: 提示信息、帮助文本、系统通知

### 边框和输入框
```css
/* 亮色模式 */
--border: oklch(0.8717 0.0093 258.3382);          /* 浅灰边框 */
--input: oklch(0.8717 0.0093 258.3382);           /* 输入框边框 */
--ring: oklch(0.5531 0.2471 301.88);              /* 焦点环 (紫色) */

/* 暗色模式 */
--border: oklch(0.4461 0.0263 256.8018);          /* 深灰边框 */
--input: oklch(0.4461 0.0263 256.8018);           /* 输入框边框 */
--ring: oklch(0.6801 0.1583 276.9349);            /* 焦点环 (浅紫) */
```

### 图表色板
```css
--chart-1: oklch(0.5531 0.2471 301.88);           /* 紫色 */
--chart-2: oklch(0.5106 0.2301 276.9656);         /* 蓝紫 */
--chart-3: oklch(0.4568 0.2146 277.0229);         /* 深蓝紫 */
--chart-4: oklch(0.3984 0.1773 277.3662);         /* 更深蓝紫 */
--chart-5: oklch(0.3588 0.1354 278.6973);         /* 最深蓝紫 */
```

### 侧边栏色系
```css
/* 亮色模式 */
--sidebar: oklch(0.9670 0.0029 264.5419);         /* 浅灰背景 */
--sidebar-foreground: oklch(0.2795 0.0368 260.0310); /* 深灰文字 */
--sidebar-primary: oklch(0.5531 0.2471 301.88);   /* 紫色高亮 */
--sidebar-accent: oklch(0.9299 0.0334 272.7879);  /* 浅蓝灰悬停 */
--sidebar-border: oklch(0.8717 0.0093 258.3382);  /* 边框 */

/* 暗色模式 */
--sidebar: oklch(0.1158 0 0);                     /* 深黑背景 */
--sidebar-foreground: oklch(0.9288 0.0126 255.5078); /* 浅灰文字 */
--sidebar-primary: oklch(0.6801 0.1583 276.9349); /* 浅紫高亮 */
--sidebar-accent: oklch(0.3729 0.0306 259.7328);  /* 深灰悬停 */
--sidebar-border: oklch(0.4461 0.0263 256.8018);  /* 边框 */
```

---

## 字体系统

### 字体族定义
```css
--font-sans: Inter, system-ui, sans-serif;        /* 无衬线字体 */
--font-serif: Merriweather, serif;                /* 衬线字体 */
--font-mono: JetBrains Mono, Fira Code, monospace; /* 等宽字体 */
```

### 字体使用规范

#### Sans-serif (Inter) - 默认字体
**用途**: 界面文本、按钮、标签、正文

```tsx
<body className="font-sans">
  <p className="text-base">这是默认的界面文本</p>
</body>
```

#### Serif (Merriweather) - 装饰字体
**用途**: 标题、引用、强调内容

```tsx
<h1 className="font-serif text-4xl font-bold">
  QueryWeaver
</h1>
```

#### Monospace (JetBrains Mono) - 代码字体
**用途**: SQL 代码、JSON 数据、技术信息

```tsx
<pre className="font-mono text-sm bg-muted p-4 rounded-lg">
  <code>SELECT * FROM users WHERE id = 1;</code>
</pre>
```

### 字号系统 (Tailwind 默认)
```
text-xs:   0.75rem  (12px)  - 辅助文本、标签
text-sm:   0.875rem (14px)  - 次要文本、说明
text-base: 1rem     (16px)  - 正文、默认大小
text-lg:   1.125rem (18px)  - 小标题
text-xl:   1.25rem  (20px)  - 标题
text-2xl:  1.5rem   (24px)  - 大标题
text-3xl:  1.875rem (30px)  - 主标题
text-4xl:  2.25rem  (36px)  - 超大标题
```

### 字重系统
```
font-light:    300  - 轻量文本
font-normal:   400  - 正常文本
font-medium:   500  - 中等强调
font-semibold: 600  - 半粗体
font-bold:     700  - 粗体
```

### 行高系统
```
leading-none:    1      - 紧凑行高
leading-tight:   1.25   - 紧密行高
leading-snug:    1.375  - 舒适行高
leading-normal:  1.5    - 正常行高 (默认)
leading-relaxed: 1.625  - 宽松行高
leading-loose:   2      - 松散行高
```

---

## 间距系统

### Spacing Scale (Tailwind 默认)
```
0:    0px
0.5:  0.125rem  (2px)
1:    0.25rem   (4px)
1.5:  0.375rem  (6px)
2:    0.5rem    (8px)
2.5:  0.625rem  (10px)
3:    0.75rem   (12px)
3.5:  0.875rem  (14px)
4:    1rem      (16px)
5:    1.25rem   (20px)
6:    1.5rem    (24px)
8:    2rem      (32px)
10:   2.5rem    (40px)
12:   3rem      (48px)
16:   4rem      (64px)
20:   5rem      (80px)
24:   6rem      (96px)
```

### 常用间距模式

#### 组件内边距
```tsx
// 小组件
<div className="p-2">...</div>          // 8px

// 中等组件
<div className="p-4">...</div>          // 16px

// 大组件 (Card)
<div className="p-6">...</div>          // 24px
```

#### 组件间距
```tsx
// 紧密间距
<div className="space-y-2">...</div>    // 8px

// 正常间距
<div className="space-y-4">...</div>    // 16px

// 宽松间距
<div className="space-y-6">...</div>    // 24px
```

#### 容器边距
```tsx
// 页面容器
<div className="container px-4 py-8">...</div>

// 侧边栏
<aside className="p-4">...</aside>

// 内容区域
<main className="p-6 md:p-8">...</main>
```

---

## 圆角系统

### 圆角变量
```css
--radius: 0.5rem;                       /* 基础圆角 8px */
```

### 圆角类名
```
rounded-sm:  calc(var(--radius) - 4px)  /* 4px  - 小圆角 */
rounded-md:  calc(var(--radius) - 2px)  /* 6px  - 中圆角 */
rounded-lg:  var(--radius)              /* 8px  - 大圆角 (默认) */
rounded-xl:  0.75rem                    /* 12px - 超大圆角 */
rounded-2xl: 1rem                       /* 16px - 极大圆角 */
rounded-full: 9999px                    /* 完全圆形 */
```

### 使用规范

#### 按钮
```tsx
<Button className="rounded-md">默认按钮</Button>
```

#### 卡片
```tsx
<Card className="rounded-lg">卡片内容</Card>
```

#### 输入框
```tsx
<Input className="rounded-md" />
```

#### 头像
```tsx
<Avatar className="rounded-full" />
```

---

## 阴影系统

### 阴影变量
```css
--shadow-2xs: 0px 4px 8px -1px hsl(0 0% 0% / 0.05);
--shadow-xs:  0px 4px 8px -1px hsl(0 0% 0% / 0.05);
--shadow-sm:  0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 1px 2px -2px hsl(0 0% 0% / 0.10);
--shadow:     0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 1px 2px -2px hsl(0 0% 0% / 0.10);
--shadow-md:  0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 2px 4px -2px hsl(0 0% 0% / 0.10);
--shadow-lg:  0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 4px 6px -2px hsl(0 0% 0% / 0.10);
--shadow-xl:  0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 8px 10px -2px hsl(0 0% 0% / 0.10);
--shadow-2xl: 0px 4px 8px -1px hsl(0 0% 0% / 0.25);
```

### 使用规范

#### 卡片阴影
```tsx
<Card className="shadow-sm">轻微阴影</Card>
<Card className="shadow-md">中等阴影</Card>
<Card className="shadow-lg">明显阴影</Card>
```

#### 悬浮效果
```tsx
<div className="shadow-sm hover:shadow-md transition-shadow">
  悬浮时阴影加深
</div>
```

#### 模态框
```tsx
<Dialog className="shadow-2xl">
  模态框内容
</Dialog>
```

---

## 响应式断点

### 断点定义
```
sm:  640px   - 小屏幕 (手机横屏)
md:  768px   - 中等屏幕 (平板)
lg:  1024px  - 大屏幕 (笔记本)
xl:  1280px  - 超大屏幕 (桌面)
2xl: 1536px  - 超超大屏幕 (大桌面)
```

### 容器断点
```tsx
<div className="container">
  {/* 最大宽度 1400px (2xl) */}
</div>
```

### 响应式设计模式

#### 移动优先
```tsx
<div className="
  text-sm          /* 默认小字号 */
  md:text-base     /* 平板及以上正常字号 */
  lg:text-lg       /* 桌面大字号 */
">
  响应式文本
</div>
```

#### 布局响应
```tsx
<div className="
  flex flex-col    /* 默认垂直布局 */
  md:flex-row      /* 平板及以上水平布局 */
  gap-4
">
  <aside className="w-full md:w-64">侧边栏</aside>
  <main className="flex-1">主内容</main>
</div>
```

#### 隐藏/显示
```tsx
{/* 移动端隐藏 */}
<div className="hidden md:block">
  桌面端显示的内容
</div>

{/* 桌面端隐藏 */}
<div className="block md:hidden">
  移动端显示的内容
</div>
```

---

## 组件规范

### Button 组件

#### 变体 (Variants)
```tsx
// 主要按钮
<Button variant="default">提交查询</Button>

// 次要按钮
<Button variant="secondary">取消</Button>

// 危险按钮
<Button variant="destructive">删除</Button>

// 轮廓按钮
<Button variant="outline">编辑</Button>

// 幽灵按钮
<Button variant="ghost">更多</Button>

// 链接按钮
<Button variant="link">了解更多</Button>
```

#### 尺寸 (Sizes)
```tsx
<Button size="sm">小按钮</Button>
<Button size="default">默认按钮</Button>
<Button size="lg">大按钮</Button>
<Button size="icon"><Icon /></Button>
```

#### 状态
```tsx
<Button disabled>禁用按钮</Button>
<Button loading>加载中...</Button>
```

### Input 组件

#### 基础输入框
```tsx
<Input
  type="text"
  placeholder="请输入查询..."
  className="w-full"
/>
```

#### 带标签
```tsx
<div className="space-y-2">
  <Label htmlFor="query">查询内容</Label>
  <Input id="query" placeholder="输入 SQL 查询" />
</div>
```

#### 错误状态
```tsx
<Input
  className="border-error focus-visible:ring-error"
  aria-invalid="true"
/>
<p className="text-sm text-error mt-1">请输入有效的查询</p>
```

### Card 组件

#### 基础卡片
```tsx
<Card>
  <CardHeader>
    <CardTitle>数据库连接</CardTitle>
    <CardDescription>管理您的数据库连接</CardDescription>
  </CardHeader>
  <CardContent>
    <p>卡片内容</p>
  </CardContent>
  <CardFooter>
    <Button>保存</Button>
  </CardFooter>
</Card>
```

#### 交互卡片
```tsx
<Card className="hover:shadow-md transition-shadow cursor-pointer">
  <CardHeader>
    <CardTitle>PostgreSQL</CardTitle>
  </CardHeader>
  <CardContent>
    <p>已连接</p>
  </CardContent>
</Card>
```

### Dialog 组件

#### 模态框
```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogTrigger asChild>
    <Button>打开设置</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>设置</DialogTitle>
      <DialogDescription>
        配置您的应用设置
      </DialogDescription>
    </DialogHeader>
    <div className="space-y-4">
      {/* 设置内容 */}
    </div>
    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        取消
      </Button>
      <Button onClick={handleSave}>保存</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Alert 组件

#### 信息提示
```tsx
<Alert>
  <InfoIcon className="h-4 w-4" />
  <AlertTitle>提示</AlertTitle>
  <AlertDescription>
    这是一条信息提示
  </AlertDescription>
</Alert>
```

#### 成功提示
```tsx
<Alert className="border-success bg-success/10">
  <CheckIcon className="h-4 w-4 text-success" />
  <AlertTitle className="text-success">成功</AlertTitle>
  <AlertDescription>
    查询执行成功
  </AlertDescription>
</Alert>
```

#### 错误提示
```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>错误</AlertTitle>
  <AlertDescription>
    SQL 语法错误，请检查您的查询
  </AlertDescription>
</Alert>
```

---

## 动画系统

### 过渡动画
```tsx
// 基础过渡
<div className="transition-colors duration-200">
  颜色过渡
</div>

// 阴影过渡
<div className="transition-shadow duration-300">
  阴影过渡
</div>

// 全属性过渡
<div className="transition-all duration-200">
  全属性过渡
</div>
```

### 内置动画

#### Accordion 动画
```css
@keyframes accordion-down {
  from { height: 0; }
  to { height: var(--radix-accordion-content-height); }
}

@keyframes accordion-up {
  from { height: var(--radix-accordion-content-height); }
  to { height: 0; }
}
```

#### 使用示例
```tsx
<Accordion type="single" collapsible>
  <AccordionItem value="item-1">
    <AccordionTrigger>数据库设置</AccordionTrigger>
    <AccordionContent className="animate-accordion-down">
      设置内容
    </AccordionContent>
  </AccordionItem>
</Accordion>
```

### 自定义动画

#### 淡入动画
```tsx
<div className="animate-in fade-in duration-300">
  淡入内容
</div>
```

#### 滑入动画
```tsx
<div className="animate-in slide-in-from-bottom duration-500">
  从底部滑入
</div>
```

---

## 滚动条样式

### 隐藏滚动条
```tsx
<div className="scrollbar-hide overflow-auto">
  内容区域
</div>
```

### 可见滚动条
```tsx
<div className="scrollbar-visible overflow-auto">
  内容区域
</div>
```

### 滚动条颜色

#### 亮色模式
- 轨道: #F3F4F6 (gray-100)
- 滑块: #D1D5DB (gray-300)
- 悬停: #9CA3AF (gray-400)

#### 暗色模式
- 轨道: #374151 (gray-700)
- 滑块: #6B7280 (gray-500)
- 悬停: #9CA3AF (gray-400)

---

## 暗色模式实现

### 主题切换
```tsx
import { useTheme } from "@/contexts/ThemeContext";

export const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      {theme === "light" ? <MoonIcon /> : <SunIcon />}
    </Button>
  );
};
```

### 主题应用
```tsx
// App.tsx
import { useEffect } from "react";
import { useTheme } from "@/contexts/ThemeContext";

export const App = () => {
  const { theme } = useTheme();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return <div>...</div>;
};
```

### 条件样式
```tsx
// 根据主题应用不同样式
<div className="
  bg-white dark:bg-gray-900
  text-gray-900 dark:text-gray-100
">
  自适应主题的内容
</div>
```

---

## 可访问性规范

### 颜色对比度
- **正常文本**: 对比度 ≥ 4.5:1 (WCAG AA)
- **大文本**: 对比度 ≥ 3:1 (WCAG AA)
- **UI 组件**: 对比度 ≥ 3:1

### 焦点指示器
```tsx
// 所有交互元素必须有清晰的焦点状态
<Button className="
  focus-visible:outline-none
  focus-visible:ring-2
  focus-visible:ring-ring
  focus-visible:ring-offset-2
">
  可访问按钮
</Button>
```

### 语义化 HTML
```tsx
// 使用正确的 HTML 标签
<nav aria-label="主导航">
  <ul>
    <li><a href="/">首页</a></li>
  </ul>
</nav>

<main>
  <h1>页面标题</h1>
  <article>
    <h2>文章标题</h2>
    <p>文章内容</p>
  </article>
</main>
```

### ARIA 属性
```tsx
// 为交互元素添加 ARIA 标签
<Button
  aria-label="关闭对话框"
  aria-pressed={isPressed}
>
  <CloseIcon />
</Button>

<Input
  aria-invalid={hasError}
  aria-describedby="error-message"
/>
{hasError && (
  <p id="error-message" className="text-error text-sm">
    错误信息
  </p>
)}
```

---

## 设计原则

### 1. 一致性
- 使用统一的颜色、字体、间距系统
- 保持组件行为和交互模式一致
- 遵循既定的设计模式

### 2. 层次结构
- 使用字号、字重、颜色建立视觉层次
- 重要信息使用更大字号和更高对比度
- 次要信息使用较小字号和较低对比度

### 3. 可读性
- 正文使用 16px (text-base) 或更大字号
- 行高至少 1.5 (leading-normal)
- 段落间距至少 1em

### 4. 响应式
- 移动优先设计
- 使用流式布局和弹性单位
- 在不同屏幕尺寸下测试

### 5. 性能
- 避免过度使用阴影和模糊效果
- 优化动画性能 (使用 transform 和 opacity)
- 懒加载图片和组件

---

## 工具函数

### cn 工具函数
```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * 合并 Tailwind CSS 类名
 * 
 * 使用 clsx 处理条件类名，使用 twMerge 解决类名冲突
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 使用示例
```tsx
import { cn } from "@/lib/utils";

<div className={cn(
  "base-class",
  isActive && "active-class",
  isPrimary ? "primary-class" : "secondary-class",
  className // 允许外部覆盖
)}>
  内容
</div>
```

---

## 检查清单

在创建新组件或页面时，请确保:

- [ ] 使用 CSS 变量定义的颜色系统
- [ ] 支持亮色/暗色主题
- [ ] 遵循间距和圆角规范
- [ ] 使用正确的字体族和字号
- [ ] 实现响应式布局
- [ ] 添加焦点状态和键盘导航
- [ ] 使用语义化 HTML 和 ARIA 属性
- [ ] 测试颜色对比度
- [ ] 优化动画性能
- [ ] 在不同设备和浏览器测试

---

## 参考资源

- [shadcn/ui 文档](https://ui.shadcn.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Radix UI 文档](https://www.radix-ui.com/)
- [WCAG 2.1 指南](https://www.w3.org/WAI/WCAG21/quickref/)
- [OKLch 颜色空间](https://oklch.com/)
