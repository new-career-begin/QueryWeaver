# 发布步骤 - Draw.io Skill

## 当前状态
✅ Git 仓库已初始化
✅ 所有文件已添加到暂存区
⏳ 等待提交和推送到 GitHub

## 发布步骤

### 步骤 1: 配置 Git 用户信息（如果还没有配置）

```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

或者仅为当前仓库配置：

```bash
git config user.email "your-email@example.com"
git config user.name "Your Name"
```

### 步骤 2: 创建初始提交

```bash
git commit -m "Initial commit: Add drawio skill for OpenSkills"
```

### 步骤 3: 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `drawio`
   - **Description**: `Draw.io diagram generation skill for OpenSkills`
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"
3. 点击 "Create repository"

### 步骤 4: 连接到 GitHub 并推送

**使用 SSH（推荐）**:
```bash
git remote add origin git@github.com:<your-username>/drawio.git
git branch -M main
git push -u origin main
```

**或使用 HTTPS**:
```bash
git remote add origin https://github.com/<your-username>/drawio.git
git branch -M main
git push -u origin main
```

### 步骤 5: 验证发布

发布后，测试安装：

```bash
# 从 GitHub 安装
openskills install <your-username>/drawio -y

# 验证安装
openskills list

# 读取技能内容
openskills read drawio

# 同步到 AGENTS.md
openskills sync -y
```

## 快速命令序列

```bash
# 1. 配置 Git（如果还没有）
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"

# 2. 提交代码
git commit -m "Initial commit: Add drawio skill for OpenSkills"

# 3. 添加远程仓库（替换 <your-username>）
git remote add origin git@github.com:<your-username>/drawio.git

# 4. 推送到 GitHub
git branch -M main
git push -u origin main
```

## 发布后的后续步骤

### 可选：创建版本标签

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 可选：提交到 OpenSkills 注册表

如果你想在 [openskills.cc](https://openskills.cc/) 上被发现：

1. 访问 [OpenSkills GitHub 仓库](https://github.com/numman-ali/openskills)
2. 提交 Pull Request 将你的技能添加到注册表

## 文件清单

以下文件将被发布：

- ✅ SKILL.md - 主要技能文件
- ✅ README.md - 仓库说明
- ✅ references/diagram_types.md - 图表类型参考
- ✅ references/xml_format.md - XML 格式参考
- ✅ COMPLIANCE_CHECK.md - 合规性检查报告
- ✅ FIXES_NEEDED.md - 修复建议（可选）
- ✅ PUBLISH.md - 发布指南
- ✅ drawio.skill - 二进制文件（如果保留）

## 注意事项

1. 确保 GitHub 仓库名称与技能名称一致（`drawio`）
2. 如果仓库是私有的，确保有访问权限的用户可以安装
3. 发布后可以随时更新，用户可以通过 `openskills install` 重新安装获取更新

## 需要帮助？

如果遇到问题，请参考：
- [PUBLISH.md](PUBLISH.md) - 详细的发布指南
- [OpenSkills 文档](https://github.com/numman-ali/openskills)
