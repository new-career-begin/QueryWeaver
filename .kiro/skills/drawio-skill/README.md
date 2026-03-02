# Draw.io Skill

一个用于生成和编辑 Draw.io 格式图表的 OpenSkills 技能包。支持流程图、架构图、网络拓扑图、UML 图等多种图表类型。

## 功能特性

- **流程图和过程图**：创建标准的流程图和业务流程图表
- **系统架构图**：绘制系统组件和关系图
- **网络拓扑图**：表示网络设备和连接关系
- **UML 图表**：支持类图、序列图、用例图等
- **组织架构图**：创建组织结构和层次关系图
- **思维导图**：生成思维导图和概念图
- **云架构图**：支持 AWS、GCP、Azure 云服务图表
- **数据库 ER 图**：绘制实体关系图
- **状态图**：创建状态转换图

## 安装

使用 OpenSkills 安装此技能：

```bash
# 安装整个仓库
openskills install <your-username>/drawio -y

# 或者如果仓库中有多个技能，安装特定技能
openskills install <your-username>/drawio/drawio -y
```

## 使用方法

安装后，AI 代理可以通过以下方式使用此技能：

```bash
# 查看技能内容
openskills read drawio

# 同步到 AGENTS.md
openskills sync -y
```

## 技能结构

```
drawio/
├── SKILL.md              # 主要技能文件（必需）
├── references/           # 参考文档
│   ├── diagram_types.md  # 图表类型指南
│   └── xml_format.md     # XML 格式规范
├── scripts/              # 辅助脚本（可选）
└── assets/               # 资源文件（可选）
```

## 支持的图表类型

- 流程图 (Flowchart)
- 架构图 (Architecture Diagram)
- 网络拓扑图 (Network Topology)
- UML 图表 (UML Diagrams)
- 组织架构图 (Organizational Chart)
- 思维导图 (Mind Map)
- 云架构图 (Cloud Architecture)
- 数据库 ER 图 (Database ER Diagram)
- 状态图 (State Diagram)

## 文档

详细的文档和示例请参考：

- [SKILL.md](SKILL.md) - 主要技能文档
- [references/diagram_types.md](references/diagram_types.md) - 图表类型指南
- [references/xml_format.md](references/xml_format.md) - XML 格式规范

## 许可证

请根据你的需求添加适当的许可证文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [OpenSkills 文档](https://github.com/numman-ali/openskills)
- [Draw.io 官网](https://app.diagrams.net/)
