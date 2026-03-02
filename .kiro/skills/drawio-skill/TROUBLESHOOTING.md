# 推送问题排查指南

## 当前问题

推送时出现错误：`Repository not found`

## 可能的原因和解决方案

### 1. 仓库名称不匹配

**检查**：确认 GitHub 仓库的确切名称

- 访问：https://github.com/Kuang?tab=repositories
- 查看你刚创建的仓库名称
- 确认是 `drawio` 还是其他名称

**如果名称不同**，更新远程仓库 URL：

```bash
git remote set-url origin https://github.com/Kuang/实际仓库名.git
git push -u origin main
```

### 2. 需要身份认证

如果仓库是私有的，或者需要认证：

**使用 Personal Access Token**：

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写信息：
   - Note: `OpenSkills Push`
   - Expiration: 选择有效期
   - Scopes: 至少勾选 `repo`
4. 点击 "Generate token"
5. 复制生成的 token（只显示一次！）

**推送时使用 token**：

```bash
# 推送时会提示输入用户名和密码
# 用户名：Kuang
# 密码：粘贴刚才复制的 token
git push -u origin main
```

### 3. 使用 GitHub CLI（如果已安装）

```bash
gh auth login
git push -u origin main
```

### 4. 配置 Git Credential Manager

Windows 可以使用 Git Credential Manager：

```bash
# 配置凭据助手
git config --global credential.helper manager-core

# 然后推送（会弹出窗口输入凭据）
git push -u origin main
```

### 5. 使用 SSH（如果已配置 SSH 密钥）

```bash
# 切换到 SSH URL
git remote set-url origin git@github.com:Kuang/drawio.git
git push -u origin main
```

## 快速检查清单

- [ ] 确认仓库名称是否正确
- [ ] 确认仓库 URL 是否正确
- [ ] 如果私有仓库，确认有访问权限
- [ ] 如果使用 HTTPS，准备好 Personal Access Token
- [ ] 确认已登录 GitHub

## 验证仓库是否存在

访问以下 URL 确认仓库：
- https://github.com/Kuang/drawio

如果页面显示 404，说明：
1. 仓库名称不对
2. 仓库是私有的且未登录
3. 仓库还未创建完成

## 下一步

请告诉我：
1. 仓库的确切名称是什么？
2. 仓库是公开的还是私有的？
3. 你是否已经配置了 SSH 密钥或 Personal Access Token？
