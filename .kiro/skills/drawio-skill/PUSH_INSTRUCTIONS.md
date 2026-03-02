# 推送代码到 GitHub - 详细步骤

## 当前状态

✅ 远程仓库已配置：`https://github.com/Kuang/drawio-skill.git`
✅ 代码已准备好推送
⏳ 需要身份认证

## 推送步骤

### 方法一：在命令行中手动输入（推荐）

1. **打开 PowerShell 或命令提示符**
   - 在项目目录：`C:\Users\kuang\drawio`

2. **运行推送命令**
   ```bash
   git push -u origin main
   ```

3. **当提示输入时**：
   - **Username for 'https://github.com'**: 输入 `Kuang`（或你的 GitHub 用户名）
   - **Password for 'https://Kuang@github.com'**: 输入你的 **Personal Access Token**（不是 GitHub 密码）

### 方法二：在 URL 中包含用户名

```bash
# 更新远程 URL，包含用户名
git remote set-url origin https://Kuang@github.com/Kuang/drawio-skill.git

# 推送（只需要输入 token）
git push -u origin main
```

### 方法三：使用 SSH（如果已配置）

```bash
# 切换到 SSH
git remote set-url origin git@github.com:Kuang/drawio-skill.git

# 推送
git push -u origin main
```

## 如何获取 Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写：
   - **Note**: `OpenSkills Push`
   - **Expiration**: 选择有效期
   - **Scopes**: 勾选 `repo`（完整仓库访问权限）
4. 点击 "Generate token"
5. **立即复制 token**（只显示一次！）

## 推送成功后的验证

推送成功后，你会看到类似输出：

```
Enumerating objects: 13, done.
Counting objects: 100% (13/13), done.
Delta compression using up to X threads
Compressing objects: 100% (XX/XX), done.
Writing objects: 100% (XX/XX), XX.XX KiB | XX.XX MiB/s, done.
Total XX (delta X), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (X/X), done.
To https://github.com/Kuang/drawio-skill.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## 发布后的信息

推送成功后：

- **仓库 URL**: https://github.com/Kuang/drawio-skill
- **安装命令**: `openskills install Kuang/drawio-skill -y`
- **技能名称**: `drawio`（在 SKILL.md 中定义）

## 测试安装

推送后，测试安装：

```bash
openskills install Kuang/drawio-skill -y
openskills list
openskills read drawio
openskills sync -y
```

## 如果遇到问题

### 问题：提示 "Repository not found"
- 检查仓库名称是否正确：`drawio-skill`
- 检查 GitHub 用户名是否正确：`Kuang` 或 `kuang`
- 确认仓库已创建

### 问题：提示 "Authentication failed"
- 确认使用的是 Personal Access Token，不是密码
- 确认 token 有 `repo` 权限
- 确认 token 未过期

### 问题：提示 "Permission denied"
- 确认有仓库的写入权限
- 确认 token 有正确的权限范围

---

**下一步**：在终端运行 `git push -u origin main`，然后输入用户名和 token。
