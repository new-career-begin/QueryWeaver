# 在 GitHub 创建仓库指南

## 当前状态

✅ 本地代码已准备就绪
✅ Git 提交已完成
⏳ 等待在 GitHub 创建仓库

## 创建仓库步骤

### 方法一：通过网页创建（推荐）

1. **访问创建页面**
   - 打开：https://github.com/new
   - 或登录 GitHub 后点击右上角 "+" → "New repository"

2. **填写仓库信息**
   ```
   Repository name: drawio
   Description: Draw.io diagram generation skill for OpenSkills
   Visibility: 
     ○ Public (推荐，让其他人可以使用)
     ● Private (仅自己可见)
   ```

3. **重要：不要勾选以下选项**
   - ❌ ❌ ❌ **不要**勾选 "Add a README file"
   - ❌ ❌ ❌ **不要**勾选 "Add .gitignore"
   - ❌ ❌ ❌ **不要**勾选 "Choose a license"
   
   **原因**：我们已经有了这些文件，如果勾选会导致冲突

4. **创建仓库**
   - 点击绿色的 "Create repository" 按钮

5. **创建完成后**
   - GitHub 会显示一个页面，上面有推送代码的指令
   - **不要**按照那个页面的指令操作（因为我们已经准备好了）
   - 直接运行下面的推送命令即可

### 方法二：使用 GitHub CLI（如果已安装）

```bash
gh repo create drawio --public --description "Draw.io diagram generation skill for OpenSkills"
```

## 创建仓库后执行推送

仓库创建后，运行以下命令：

```bash
# 如果使用 HTTPS（推荐，更简单）
git remote add origin https://github.com/Kuang/drawio.git
git push -u origin main

# 或如果使用 SSH（需要配置 SSH 密钥）
git remote add origin git@github.com:Kuang/drawio.git
git push -u origin main
```

## 快速推送脚本

我已经为你准备好了推送命令，仓库创建后直接复制运行：

### Windows PowerShell

```powershell
# 添加远程仓库（HTTPS）
git remote add origin https://github.com/Kuang/drawio.git

# 推送到 GitHub
git push -u origin main
```

### 如果遇到认证问题

如果推送时要求输入用户名和密码：
- **用户名**：Kuang
- **密码**：使用 GitHub Personal Access Token（不是账户密码）

**获取 Personal Access Token**：
1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 选择权限：至少勾选 `repo`
4. 生成后复制 token
5. 推送时密码处粘贴 token

## 验证发布

推送成功后，测试安装：

```bash
# 安装技能
openskills install Kuang/drawio -y

# 验证
openskills list
openskills read drawio
openskills sync -y
```

## 发布后的仓库信息

- **仓库 URL**: https://github.com/Kuang/drawio
- **安装命令**: `openskills install Kuang/drawio -y`
- **技能名称**: `drawio`

## 需要帮助？

如果遇到问题：
1. 确保仓库名称是 `drawio`（小写）
2. 确保没有初始化 README
3. 如果使用 HTTPS，可能需要 Personal Access Token

---

**下一步**：访问 https://github.com/new 创建仓库，然后运行推送命令！
