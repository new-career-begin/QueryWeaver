# 需要修复的合规性问题

## 1. 语言风格问题（重要）

OpenSkills 要求使用**命令式语言**（imperative form），但当前 SKILL.md 中部分内容使用了描述性语言。

### 需要修改的示例

#### ❌ 当前写法（描述性）
```markdown
生成 Draw.io XML 格式的图表，包含以下核心元素：

1. **文件结构**：使用 `<mxfile>` 作为根元素
2. **图表模型**：使用 `<mxGraphModel>` 定义画布
3. **图形元素**：使用 `<mxCell>` 创建节点和连接
```

#### ✅ 应该改为（命令式）
```markdown
To generate Draw.io XML format diagrams, include these core elements:

1. **File structure**: Use `<mxfile>` as the root element
2. **Graph model**: Use `<mxGraphModel>` to define the canvas
3. **Graph elements**: Use `<mxCell>` to create nodes and connections
```

### 需要修改的部分列表

1. **第 8 行**: "生成和编辑 Draw.io 格式的图表"
   - 改为: "To generate and edit Draw.io format diagrams"

2. **第 14 行**: "生成 Draw.io XML 格式的图表，包含以下核心元素"
   - 改为: "To generate Draw.io XML format diagrams, include these core elements"

3. **第 16-18 行**: "使用..." 的描述
   - 改为: "Use..." 的命令式

4. **第 68 行**: "使用标准流程图元素"
   - 改为: "Use standard flowchart elements"

5. **第 79 行**: "表示系统组件和关系"
   - 改为: "To represent system components and relationships"

6. **第 87 行**: "表示网络设备和连接"
   - 改为: "To represent network devices and connections"

7. **第 97 行**: "支持 AWS、GCP、Azure 云服务"
   - 改为: "To create cloud architecture diagrams for AWS, GCP, and Azure"

## 2. Description 字段长度（可选）

当前 description 字段约 400+ 字符，OpenSkills 建议 80-200 字符。

### 当前 description
```
"Comprehensive diagram creation and editing using Draw.io XML format. Use when Claude needs to create, modify, or generate diagrams (.drawio files or Draw.io XML) for: (1) Flowcharts and process diagrams, (2) System architecture diagrams, (3) Network topology diagrams, (4) UML diagrams (class, sequence, use case), (5) Organizational charts, (6) Mind maps, (7) Cloud architecture diagrams (AWS/GCP/Azure), (8) Database ER diagrams, (9) State diagrams, or (10) Any other visual diagrams that can be represented in Draw.io format. The skill provides XML format specifications, diagram templates, styling guidelines, and best practices for generating professional diagrams programmatically."
```

### 建议的简短版本
```
"Create and edit Draw.io diagrams (flowcharts, architecture diagrams, UML, network topologies, and more) using XML format. Provides templates, styling guidelines, and best practices."
```

### 或者保持详细版本（也可以）
如果详细描述更有利于 AI 理解何时使用此技能，可以保持当前长度。

## 3. 文件清理（可选）

- `drawio.skill` - 如果这是旧格式文件且不再需要，可以删除

## 修复优先级

### 🔴 高优先级（发布前建议修复）
1. **语言风格** - 将描述性语言改为命令式
   - 影响: 技能的可读性和 AI 理解
   - 建议: 修复主要章节的标题和说明

### 🟡 中优先级（可选但推荐）
2. **Description 长度** - 考虑缩短或保持详细
   - 影响: 在技能列表中的显示
   - 建议: 根据需求决定

### 🟢 低优先级（可选）
3. **文件清理** - 删除不需要的文件
   - 影响: 仓库整洁度
   - 建议: 如果确认不需要，可以删除

## 快速修复指南

### 修复语言风格的关键模式

| 当前模式 | 应该改为 |
|---------|---------|
| "生成..." | "To generate..." |
| "使用..." | "Use..." |
| "创建..." | "To create..." / "Create..." |
| "表示..." | "To represent..." |
| "支持..." | "To support..." / "Supports..." |
| "绘制..." | "To draw..." / "Draw..." |
| "标注..." | "Label..." / "To label..." |

### 修复示例模板

**标题部分**:
```markdown
# Draw.io Diagram Generation Skill

To generate and edit Draw.io format diagrams. Supports flowcharts, architecture diagrams, network topologies, UML diagrams, and more.
```

**章节部分**:
```markdown
## Quick Start

### Generating Basic Flowcharts

To generate Draw.io XML format diagrams, include these core elements:

1. **File structure**: Use `<mxfile>` as the root element
2. **Graph model**: Use `<mxGraphModel>` to define the canvas
3. **Graph elements**: Use `<mxCell>` to create nodes and connections
```

## 自动化检查

可以使用以下命令检查语言风格：

```bash
# 查找可能的问题模式
grep -E "^(生成|使用|创建|表示|支持|绘制|标注)" SKILL.md
```

## 结论

**当前状态**: 可以发布，但建议修复语言风格问题

**建议操作**:
1. 修复主要章节的命令式语言（高优先级）
2. 考虑优化 description（可选）
3. 清理不需要的文件（可选）

修复后，技能将更符合 OpenSkills 的最佳实践，并提升 AI 代理的使用体验。
