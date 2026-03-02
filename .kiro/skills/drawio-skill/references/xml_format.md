# Draw.io XML 格式参考

## 基本结构

Draw.io 文件是压缩的 XML 格式（.drawio 文件实际上是压缩的 XML）。核心图表数据存储在 `<mxGraphModel>` 元素中。

### 基本模板

```xml
<mxfile host="app.diagrams.net">
  <diagram id="diagram-id" name="Diagram Name">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- 图表元素 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 核心元素

### mxCell 元素

所有图形元素都是 `<mxCell>` 节点：

```xml
<mxCell id="unique-id" 
        value="文本内容" 
        style="样式字符串" 
        vertex="1" 
        parent="1">
  <mxGeometry x="x坐标" y="y坐标" width="宽度" height="高度" as="geometry" />
</mxCell>
```

### 连接线（Edge）

```xml
<mxCell id="edge-id" 
        value="" 
        style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" 
        edge="1" 
        parent="1" 
        source="source-id" 
        target="target-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

## 常见形状样式

### 矩形
```
style="rounded=0;whiteSpace=wrap;html=1;"
```

### 圆角矩形
```
style="rounded=1;whiteSpace=wrap;html=1;"
```

### 椭圆/圆形
```
style="ellipse;whiteSpace=wrap;html=1;"
```

### 菱形
```
style="rhombus;whiteSpace=wrap;html=1;"
```

### 六边形
```
style="shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;"
```

## 流程图常用形状

### 开始/结束（圆角矩形）
```
style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
```

### 处理（矩形）
```
style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
```

### 判断（菱形）
```
style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
```

### 输入/输出（平行四边形）
```
style="shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;"
```

## 颜色和样式

### 填充颜色
```
fillColor=#颜色代码
```

### 边框颜色
```
strokeColor=#颜色代码
```

### 字体颜色
```
fontColor=#颜色代码
```

### 字体大小
```
fontSize=12
```

### 字体样式
```
fontStyle=1  (1=粗体, 2=斜体, 4=下划线, 组合使用如 3=粗体+斜体)
```

## 连接线样式

### 直线
```
edgeStyle=orthogonalEdgeStyle;rounded=0;
```

### 曲线
```
edgeStyle=orthogonalEdgeStyle;rounded=1;curved=1;
```

### 箭头类型
```
endArrow=block;  (block, classic, diamond, open, etc.)
startArrow=block;
```

## 布局和定位

### 坐标系统
- 原点 (0,0) 在左上角
- x 向右递增，y 向下递增
- 单位通常是像素

### 对齐
```
align=left;verticalAlign=top;
```

### 自动调整大小
```
autosize=1;
```

## 常用图标和符号

Draw.io 支持通过 `image` 样式引用图标：

```
style="shape=image;html=1;image=图标URL;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;aspect=fixed;"
```

## 云架构图常用元素

### AWS 图标
```
image=https://raw.githubusercontent.com/aws/aws-icons/main/Architecture-Service-Icons/...
```

### GCP 图标
```
image=https://raw.githubusercontent.com/GoogleCloudPlatform/Professional-Services/main/tools/gcp-icons/...
```

### Azure 图标
```
image=https://raw.githubusercontent.com/microsoft/CloudAdoptionFramework/master/ready/azure-best-practices/...
```

## 最佳实践

1. **ID 唯一性**：确保每个 mxCell 的 id 是唯一的
2. **父节点**：所有元素都应该有正确的 parent 属性
3. **几何信息**：确保提供完整的 mxGeometry 信息
4. **样式字符串**：使用分号分隔的键值对
5. **压缩**：实际 .drawio 文件是压缩的 XML，但生成时可以先生成未压缩版本

## 示例：简单流程图

```xml
<mxfile host="app.diagrams.net">
  <diagram id="flowchart" name="流程图">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 开始 -->
        <mxCell id="start" value="开始" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="360" y="40" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 处理 -->
        <mxCell id="process" value="处理数据" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="360" y="140" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 判断 -->
        <mxCell id="decision" value="是否完成？" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
          <mxGeometry x="350" y="240" width="140" height="80" as="geometry" />
        </mxCell>
        
        <!-- 结束 -->
        <mxCell id="end" value="结束" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
          <mxGeometry x="360" y="380" width="120" height="60" as="geometry" />
        </mxCell>
        
        <!-- 连接线 -->
        <mxCell id="edge1" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="start" target="process">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="edge2" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="process" target="decision">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="edge3" value="是" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="decision" target="end">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
        <mxCell id="edge4" value="否" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0;exitY=0.5;entryX=0.5;entryY=0;" edge="1" parent="1" source="decision" target="process">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
