# GitHub 认证指南

## 当前问题

推送时出现 `Repository not found` 错误，可能是认证问题。

## 解决方案

### 方法一：使用 Personal Access Token（推荐）

1. **生成 Token**
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 填写信息：
     - Note: `OpenSkills Push`
     - Expiration: 选择有效期（建议 90 天或自定义）
     - Scopes: **至少勾选 `repo`**（完整仓库访问权限）
   - 点击 "Generate token"
   - **重要**：复制生成的 token（只显示一次！）

2. **推送时使用 Token**
   ```bash
   git push -u origin main
   ```
   - 当提示输入用户名时：输入 `Kuang`（或 `kuang`）
   - 当提示输入密码时：**粘贴刚才复制的 token**（不是 GitHub 密码）

### 方法二：配置 Git Credential Manager

Windows 可以使用 Git Credential Manager 保存凭据：

```bash
# 配置凭据助手
git config --global credential.helper manager-core

# 然后推送（会弹出窗口输入凭据）
git push -u origin main
```

在弹出窗口中：
- 用户名：`Kuang`
- 密码：粘贴 Personal Access Token

### 方法三：在 URL 中包含 Token（不推荐，但快速）

```bash
# 替换 YOUR_TOKEN 为你的 token
git remote set-url origin https://YOUR_TOKEN@github.com/Kuang/drawio-skill.git
git push -u origin main
```

**注意**：这种方式 token 会保存在 Git 配置中，安全性较低。

### 方法四：使用 SSH（如果已配置 SSH 密钥）

```bash
# 切换到 SSH URL
git remote set-url origin git@github.com:Kuang/drawio-skill.git
git push -u origin main
```

## 验证仓库信息

请确认：
1. **仓库名称**：`drawio-skill` ✅
2. **GitHub 用户名**：`Kuang` 还是 `kuang`？
3. **仓库 URL**：https://github.com/Kuang/drawio-skill 或 https://github.com/kuang/drawio-skill
4. **仓库可见性**：公开还是私有？

## 快速测试

访问以下 URL 确认仓库存在：
- https://github.com/Kuang/drawio-skill
- https://github.com/kuang/drawio-skill

如果显示 404，说明：
- 仓库名称不对
- 仓库是私有的且未登录
- 用户名大小写不对

## 下一步

1. 生成 Personal Access Token
2. 运行 `git push -u origin main`
3. 输入用户名和 token
