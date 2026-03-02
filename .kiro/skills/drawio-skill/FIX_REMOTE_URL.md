# 修复远程仓库 URL

## 问题

推送时出现错误：`Repository not found`

## 可能的原因

1. **用户名大小写问题**
   - GitHub 用户名可能是 `Kuang`（大写）而不是 `kuang`（小写）
   - 已更新为：`https://github.com/Kuang/drawio-skill.git`

2. **仓库名称不匹配**
   - 确认仓库名称确实是 `drawio-skill`

3. **需要身份认证**
   - 即使是公开仓库，推送也需要认证
   - 需要使用 Personal Access Token

## 已执行的修复

已更新远程仓库 URL 为：
```
https://github.com/Kuang/drawio-skill.git
```

## 下一步操作

### 1. 再次尝试推送

```bash
git push -u origin main
```

### 2. 如果仍然失败，检查以下内容

**确认仓库信息**：
- 访问你的 GitHub 仓库页面
- 从浏览器地址栏复制完整的 URL
- 格式应该是：`https://github.com/用户名/仓库名`

**确认用户名**：
- GitHub 用户名是 `Kuang` 还是 `kuang`？
- 检查你的 GitHub 个人资料页面

**使用正确的 URL**：
如果用户名或仓库名不同，更新远程 URL：

```bash
# 替换为正确的用户名和仓库名
git remote set-url origin https://github.com/正确的用户名/正确的仓库名.git
```

### 3. 如果 URL 正确但仍失败

这通常是认证问题。需要：

1. **生成 Personal Access Token**
   - 访问：https://github.com/settings/tokens
   - 生成新 token（classic）
   - 权限：勾选 `repo`

2. **推送时使用 Token**
   ```bash
   git push -u origin main
   ```
   - Username: `Kuang`（或你的 GitHub 用户名）
   - Password: 粘贴 Personal Access Token

## 验证仓库是否存在

访问以下 URL 确认仓库：
- https://github.com/Kuang/drawio-skill
- https://github.com/kuang/drawio-skill

如果显示 404，说明：
- 仓库名称不对
- 用户名不对
- 仓库是私有的且未登录

## 快速检查命令

```bash
# 查看当前远程配置
git remote -v

# 测试连接（需要认证）
git ls-remote origin
```

如果 `git ls-remote` 成功，说明 URL 正确，只是推送需要认证。

---

**当前远程 URL**: `https://github.com/Kuang/drawio-skill.git`

请再次尝试推送，如果还有问题，请告诉我具体的错误信息。
