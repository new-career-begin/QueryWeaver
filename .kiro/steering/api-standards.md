---

inclusion: fileMatch
fileMatchPattern: "app/api/*"

---

# API 设计标准

## 接口设计

### URL 设计原则

- 采用 RESTful 设计
- 资源名称使用复数形式（例如 /users, /products）
- 路径层级最多为三层
- 使用 kebab-case（例如 /user-profiles）

### HTTP 方法使用规范

- GET：获取资源（幂等）
- POST：创建资源
- PUT：整体更新资源
- PATCH：部分更新资源
- DELETE：删除资源

## 响应格式

### 成功响应示例

```json
{
  "success": true,
  "data": {
    // 实际数据内容
  },
  "meta": {
    "timestamp": "2025-01-20T10:00:00Z",
    "version": "1.0",
    "requestId": "uuid-here"
  }
}
```

### **错误响应（Error Responses）**

```JSON
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入值不合法",
    "details": [
      {
        "field": "email",
        "message": "请输入有效的邮箱地址"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-01-20T10:00:00Z",
    "requestId": "uuid-here"
  }
}