---
name: drawio
description: "Comprehensive diagram creation and editing using Draw.io XML format. Use when Claude needs to create, modify, or generate diagrams (.drawio files or Draw.io XML) for: (1) Flowcharts and process diagrams, (2) System architecture diagrams, (3) Network topology diagrams, (4) UML diagrams (class, sequence, use case), (5) Organizational charts, (6) Mind maps, (7) Cloud architecture diagrams (AWS/GCP/Azure), (8) Database ER diagrams, (9) State diagrams, or (10) Any other visual diagrams that can be represented in Draw.io format. The skill provides XML format specifications, diagram templates, styling guidelines, and best practices for generating professional diagrams programmatically."
---

# Draw.io 图表生成技能

生成和编辑 Draw.io 格式的图表。支持流程图、架构图、网络拓扑图、UML 图等多种图表类型。

## 快速开始

### 生成基本流程图

生成 Draw.io XML 格式的图表，包含以下核心元素：

1. **文件结构**：使用 `<mxfile>` 作为根元素
2. **图表模型**：使用 `<mxGraphModel>` 定义画布
3. **图形元素**：使用 `<mxCell>` 创建节点和连接

### 基本模板

```xml
<mxfile host="app.diagrams.net">
  <diagram id="diagram-id" name="图表名称">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- 在此添加图表元素 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 创建图表元素

### 创建节点（Vertex）

```xml
<mxCell id="node-id" 
        value="节点文本" 
        style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" 
        vertex="1" 
        parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry" />
</mxCell>
```

### 创建连接线（Edge）

```xml
<mxCell id="edge-id" 
        value="标签文本" 
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" 
        edge="1" 
        parent="1" 
        source="source-id" 
        target="target-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

## 图表类型

### 流程图

使用标准流程图元素：
- **开始/结束**：圆角矩形，绿色填充
- **处理**：矩形，蓝色填充
- **判断**：菱形，黄色填充
- **输入/输出**：平行四边形，红色填充

参考：[diagram_types.md](references/diagram_types.md#流程图flowchart)

### 架构图

表示系统组件和关系：
- 使用容器表示系统边界
- 标注组件名称和类型
- 使用箭头表示数据流或调用关系

参考：[diagram_types.md](references/diagram_types.md#架构图architecture-diagram)

### 网络拓扑图

表示网络设备和连接：
- 使用网络设备图标
- 标注网络段和 IP 地址
- 使用颜色区分不同网络区域

参考：[diagram_types.md](references/diagram_types.md#网络拓扑图network-topology)

### 云架构图

支持 AWS、GCP、Azure 云服务：
- 使用官方图标库
- 按服务类型分组
- 标注服务配置

参考：[diagram_types.md](references/diagram_types.md#云架构图cloud-architecture)

## 样式和格式

### 常用样式

**矩形节点**：
```
style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
```

**圆角矩形**：
```
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
```

**菱形（判断）**：
```
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
```

**椭圆/圆形**：
```
style="ellipse;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
```

### 颜色方案

- **蓝色系**：`#dae8fc` / `#6c8ebf` - 用于处理、操作
- **绿色系**：`#d5e8d4` / `#82b366` - 用于开始/结束、成功状态
- **黄色系**：`#fff2cc` / `#d6b656` - 用于判断、警告
- **红色系**：`#f8cecc` / `#b85450` - 用于输入/输出、错误
- **紫色系**：`#e1d5e7` / `#9673a6` - 用于数据、存储

### 连接线样式

**直线连接**：
```
style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
```

**曲线连接**：
```
style="edgeStyle=orthogonalEdgeStyle;rounded=1;curved=1;orthogonalLoop=1;jettySize=auto;html=1;"
```

**带箭头**：
```
style="edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;html=1;"
```

## 布局原则

1. **间距**：节点之间保持 40-60 像素间距
2. **对齐**：相关元素垂直或水平对齐
3. **分组**：使用容器或背景色区分相关元素
4. **层次**：使用大小、颜色、位置表示层次关系
5. **流向**：流程图通常从上到下或从左到右

## 文件输出

### 生成 .drawio 文件

Draw.io 文件是压缩的 XML 格式。生成时：

1. **未压缩版本**：直接生成 XML 文本，用户可以在 Draw.io 中打开
2. **压缩版本**：如果需要，可以使用 gzip 压缩（通常不需要，Draw.io 会自动处理）

### 文件扩展名

- `.drawio` - Draw.io 原生格式（压缩 XML）
- `.xml` - 未压缩的 XML 格式（也可被 Draw.io 打开）

## 详细参考

- **XML 格式规范**：参见 [xml_format.md](references/xml_format.md)
- **图表类型指南**：参见 [diagram_types.md](references/diagram_types.md)

## 最佳实践

1. **ID 唯一性**：确保每个 mxCell 的 id 在整个文档中唯一
2. **父节点关系**：所有元素都应该有正确的 parent 属性（通常是 "1"）
3. **几何信息完整**：提供完整的 x, y, width, height 信息
4. **样式一致性**：同类元素使用相同的样式
5. **可读性**：添加适当的文本标签和说明
6. **测试验证**：生成的 XML 应该在 Draw.io 中打开验证

## 工作流程

当用户请求创建图表时：

1. **确定图表类型**：根据用户需求确定是流程图、架构图等
2. **规划布局**：确定节点位置和连接关系
3. **生成 XML**：按照 Draw.io XML 格式生成完整结构
4. **应用样式**：使用合适的颜色和样式方案
5. **验证输出**：确保 XML 格式正确，ID 唯一

## 示例场景

**场景 1：创建简单流程图**
- 用户："创建一个用户登录流程图"
- 生成包含开始、输入、验证、判断、成功/失败的流程图

**场景 2：创建系统架构图**
- 用户："创建一个微服务架构图，包含 API 网关、用户服务、订单服务、数据库"
- 生成分层架构图，标注服务名称和连接关系

**场景 3：创建网络拓扑图**
- 用户："创建一个包含路由器、交换机、服务器的网络拓扑图"
- 生成网络设备连接图，标注设备类型

**场景 4：创建 UML 类图**
- 用户："创建一个包含 User、Order、Product 类的 UML 类图"
- 生成类图，包含属性、方法和关系
