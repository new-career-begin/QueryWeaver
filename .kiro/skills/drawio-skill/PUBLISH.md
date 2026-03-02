# 发布指南

本指南将帮助你将 drawio skill 发布到 OpenSkills 平台。

## 发布步骤

### 1. 准备项目

确保项目结构完整：

```
drawio/
├── SKILL.md              # ✅ 已存在
├── README.md             # ✅ 已创建
├── references/           # ✅ 已存在
│   ├── diagram_types.md
│   └── xml_format.md
├── scripts/              # ✅ 已存在（可选）
└── assets/               # ✅ 已存在（可选）
```

### 2. 初始化 Git 仓库

如果还没有初始化 Git 仓库，执行：

```bash
git init
git add .
git commit -m "Initial commit: Add drawio skill"
```

### 3. 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `drawio` (或你喜欢的名称)
   - **Description**: "Draw.io diagram generation skill for OpenSkills"
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"（我们已经有了）
4. 点击 "Create repository"

### 4. 连接到 GitHub 并推送

在本地项目目录执行：

```bash
# 添加远程仓库（替换 <your-username> 为你的 GitHub 用户名）
git remote add origin git@github.com:<your-username>/drawio.git

# 或者使用 HTTPS（如果使用 HTTPS）
git remote add origin https://github.com/<your-username>/drawio.git

# 重命名主分支为 main（如果需要）
git branch -M main

# 推送代码
git push -u origin main
```

### 5. 测试安装

发布后，你可以测试安装：

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

### 6. 提交到 OpenSkills 注册表（可选）

如果你想在 [openskills.cc](https://openskills.cc/) 上被更多人发现：

1. 访问 [OpenSkills GitHub 仓库](https://github.com/numman-ali/openskills)
2. 提交 Pull Request，将你的技能添加到注册表中
3. 确保你的技能符合 OpenSkills 的格式要求

## 版本管理

建议使用 Git 标签进行版本管理：

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

用户可以通过标签安装特定版本：

```bash
openskills install <your-username>/drawio@v1.0.0 -y
```

## 更新技能

当你需要更新技能时：

```bash
# 修改文件后
git add .
git commit -m "Update: 描述你的更改"
git push origin main
```

用户可以通过以下方式更新：

```bash
openskills install <your-username>/drawio -y --force
```

## 注意事项

1. **SKILL.md 格式**：确保 SKILL.md 包含有效的 YAML frontmatter（name 和 description）
2. **相对路径**：在 SKILL.md 中引用资源时使用相对路径（如 `references/diagram_types.md`）
3. **许可证**：考虑添加 LICENSE 文件
4. **文档**：保持 README.md 和文档的更新

## 故障排除

### 安装失败

- 检查仓库是否为公开的（或你有访问权限）
- 确认仓库路径正确
- 检查 SKILL.md 格式是否正确

### 技能未出现在列表中

- 运行 `openskills sync -y` 同步到 AGENTS.md
- 检查技能名称是否正确

## 相关资源

- [OpenSkills 文档](https://github.com/numman-ali/openskills)
- [创建技能指南](https://deepwiki.com/numman-ali/openskills/5.3-creating-your-own-skills)
- [SKILL.md 格式规范](https://deepwiki.com/numman-ali/openskills/5.1-skill.md-format-specification)
