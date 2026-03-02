# Git 用户名 vs GitHub 用户名

## 区别说明

### Git 用户名（user.name）

**用途**：标识 Git 提交的作者

**特点**：
- 显示在 Git 提交历史中（`git log`）
- 可以是任何名字，比如真实姓名或显示名称
- 用于标识"谁做了这个提交"
- 本地配置，可以每个仓库不同

**示例**：
- `张三`
- `John Doe`
- `Kuang`
- `Your Display Name`

**设置方式**：
```bash
git config --global user.name "你的名字"
# 或仅为当前仓库设置
git config user.name "你的名字"
```

**在提交中的显示**：
```
commit abc123
Author: 张三 <email@example.com>
Date:   Mon Jan 23 2026
    Initial commit
```

---

### GitHub 用户名（GitHub Username）

**用途**：GitHub 账户的唯一标识符

**特点**：
- 用于 GitHub 仓库 URL
- 必须是唯一的（全 GitHub 平台）
- 通常是小写字母、数字和连字符
- 用于访问你的 GitHub 账户和仓库
- 显示在你的 GitHub 个人资料中

**示例**：
- `kuang`
- `john-doe`
- `zhangsan123`
- `my-github-username`

**在 URL 中的使用**：
```
https://github.com/kuang/drawio
git@github.com:kuang/drawio.git
```

**查看方式**：
- 登录 GitHub，右上角头像旁边就是你的用户名
- 或者访问 `https://github.com/settings/profile`

---

## 实际例子

假设你的信息是：

| 项目 | 值 | 说明 |
|------|-----|------|
| **Git 用户名** | `Kuang` | 显示在提交历史中 |
| **Git 邮箱** | `kuang@example.com` | 关联提交 |
| **GitHub 用户名** | `kuang` | 用于仓库 URL |

**Git 配置**：
```bash
git config --global user.name "Kuang"
git config --global user.email "kuang@example.com"
```

**GitHub 仓库 URL**：
```
https://github.com/kuang/drawio
```

**提交显示**：
```
Author: Kuang <kuang@example.com>
```

---

## 常见情况

### 情况 1：两者相同
- Git 用户名：`Kuang`
- GitHub 用户名：`kuang`
- **最常见的情况**

### 情况 2：两者不同
- Git 用户名：`张三`（真实姓名）
- GitHub 用户名：`zhangsan`（账户名）
- **也完全正常**

### 情况 3：公司/组织账户
- Git 用户名：`John Doe`
- GitHub 用户名：`company-org`（组织账户）
- **使用组织账户发布**

---

## 在发布脚本中的使用

### Git 用户名（user.name）
```powershell
.\publish.ps1 -Name "Kuang"  # 显示在提交中
```

### GitHub 用户名
```powershell
.\publish.ps1 -GitHubUsername "kuang"  # 用于仓库 URL
```

**实际效果**：
- 提交作者显示：`Kuang`
- 仓库 URL：`github.com/kuang/drawio`

---

## 如何查找你的信息

### 查找 Git 配置
```bash
# 查看当前 Git 用户名
git config user.name

# 查看当前 Git 邮箱
git config user.email

# 查看全局配置
git config --global user.name
git config --global user.email
```

### 查找 GitHub 用户名
1. 登录 GitHub
2. 点击右上角头像
3. 查看 URL 或用户名显示
4. 或访问：`https://github.com/settings/profile`

---

## 总结

| 特性 | Git 用户名 | GitHub 用户名 |
|------|-----------|--------------|
| **用途** | 标识提交作者 | 账户标识符 |
| **格式** | 任意名称 | 小写字母、数字、连字符 |
| **唯一性** | 本地配置 | 全平台唯一 |
| **显示位置** | Git 提交历史 | GitHub URL、个人资料 |
| **示例** | `Kuang`、`张三` | `kuang`、`zhangsan` |

**简单记忆**：
- **Git 用户名** = 你的名字（显示在提交中）
- **GitHub 用户名** = 你的账户名（用于访问仓库）

---

## 发布时需要的三个信息

1. **Git 用户名** (`-Name`)：显示在提交历史中
   - 例如：`"Kuang"` 或 `"张三"`

2. **Git 邮箱** (`-Email`)：关联提交
   - 例如：`"kuang@example.com"`

3. **GitHub 用户名** (`-GitHubUsername`)：用于仓库 URL
   - 例如：`"kuang"`

**完整示例**：
```powershell
.\publish.ps1 `
  -GitHubUsername "kuang" `
  -Email "kuang@example.com" `
  -Name "Kuang"
```
