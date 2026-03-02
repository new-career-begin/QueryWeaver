# 快速发布指南

## 方式一：使用发布脚本（推荐）

```powershell
.\publish.ps1 -GitHubUsername "your-username" -Email "your-email@example.com" -Name "Your Name"
```

脚本会自动：
1. 配置 Git 用户信息
2. 添加所有文件
3. 创建提交
4. 配置远程仓库

然后：
1. 在 GitHub 创建仓库（https://github.com/new）
2. 运行 `git push -u origin main`

## 方式二：手动执行命令

### 1. 配置 Git（如果还没有）

```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

### 2. 提交代码

```bash
git commit -m "Initial commit: Add drawio skill for OpenSkills"
git branch -M main
```

### 3. 在 GitHub 创建仓库

访问 https://github.com/new，创建名为 `drawio` 的仓库（不要初始化 README）

### 4. 连接并推送

```bash
# SSH 方式（推荐）
git remote add origin git@github.com:<your-username>/drawio.git
git push -u origin main

# 或 HTTPS 方式
git remote add origin https://github.com/<your-username>/drawio.git
git push -u origin main
```

### 5. 测试安装

```bash
openskills install <your-username>/drawio -y
openskills read drawio
openskills sync -y
```

## 当前状态

✅ 所有文件已准备就绪
✅ Git 仓库已初始化
✅ 文件已添加到暂存区
⏳ 等待提交和推送到 GitHub

## 需要的信息

发布前请准备：
- GitHub 用户名
- Git 邮箱地址
- Git 用户名（显示名称）

## 详细文档

- [RELEASE_STEPS.md](RELEASE_STEPS.md) - 详细发布步骤
- [PUBLISH.md](PUBLISH.md) - 完整发布指南
