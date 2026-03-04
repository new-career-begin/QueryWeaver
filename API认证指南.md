# API 认证指南

## 问题说明

访问 `/api/config/llm` 返回 401 错误:
```json
{"detail":"Unauthorized - Please log in or provide a valid API token"}
```

这是因为该接口需要用户认证。

## 认证方式

QueryWeaver 支持两种认证方式:

### 1. Session 认证 (浏览器)

**适用场景**: 通过浏览器访问 Web 界面

**步骤**:
1. 访问 `http://127.0.0.1:5000`
2. 点击右上角 "Sign In" 按钮
3. 选择 Google 或 GitHub 登录
4. 登录成功后,浏览器会自动保存 Session Cookie
5. 之后访问任何需要认证的接口都会自动携带认证信息

**验证登录状态**:
- 登录后,右上角会显示你的头像
- 可以访问 `/api/config/llm` 查看配置

### 2. API Token 认证 (程序调用)

**适用场景**: 通过程序或 API 工具 (Postman, curl) 访问

#### 步骤 1: 获取 API Token

首先需要通过浏览器登录并生成 Token:

1. 访问 `http://127.0.0.1:5000` 并登录
2. 点击右上角头像 → "API Tokens"
3. 点击 "Generate New Token"
4. 输入 Token 名称 (如: "开发测试")
5. 复制生成的 Token (只显示一次!)

#### 步骤 2: 使用 Token 访问 API

**使用 curl**:
```bash
curl -X GET "http://127.0.0.1:5000/api/config/llm" \
  -H "Cookie: api_token=你的Token"
```

**使用 Python requests**:
```python
import requests

# 你的 API Token
api_token = "your_token_here"

# 设置 Cookie
cookies = {
    "api_token": api_token
}

# 发送请求
response = requests.get(
    "http://127.0.0.1:5000/api/config/llm",
    cookies=cookies
)

print(response.json())
```

**使用 Postman**:
1. 打开 Postman
2. 创建新请求: GET `http://127.0.0.1:5000/api/config/llm`
3. 切换到 "Headers" 标签
4. 添加 Header:
   - Key: `Cookie`
   - Value: `api_token=你的Token`
5. 发送请求

**使用 JavaScript (fetch)**:
```javascript
const apiToken = "your_token_here";

fetch("http://127.0.0.1:5000/api/config/llm", {
  method: "GET",
  credentials: "include",  // 包含 Cookie
  headers: {
    "Cookie": `api_token=${apiToken}`
  }
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error("Error:", error));
```

## 配置 OAuth (如果未配置)

如果你还没有配置 OAuth,需要先配置才能登录:

### 配置 Google OAuth

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目或选择现有项目
3. 启用 "Google+ API"
4. 创建 OAuth 2.0 凭据:
   - 应用类型: Web 应用
   - 授权重定向 URI: `http://127.0.0.1:5000/auth/google/callback`
5. 获取 Client ID 和 Client Secret
6. 在 `.env` 文件中配置:
   ```env
   GOOGLE_CLIENT_ID=你的Client_ID
   GOOGLE_CLIENT_SECRET=你的Client_Secret
   ```

### 配置 GitHub OAuth

1. 访问 [GitHub Settings](https://github.com/settings/developers)
2. 点击 "New OAuth App"
3. 填写信息:
   - Application name: QueryWeaver
   - Homepage URL: `http://127.0.0.1:5000`
   - Authorization callback URL: `http://127.0.0.1:5000/auth/github/callback`
4. 获取 Client ID 和 Client Secret
5. 在 `.env` 文件中配置:
   ```env
   GITHUB_CLIENT_ID=你的Client_ID
   GITHUB_CLIENT_SECRET=你的Client_Secret
   ```

### 重启后端

配置完成后重启后端服务:
```powershell
# 停止当前服务 (Ctrl + C)
# 重新启动
python -m api.main
```

## 测试认证

### 测试 Session 认证

1. 打开浏览器访问 `http://127.0.0.1:5000`
2. 登录
3. 打开浏览器开发者工具 (F12)
4. 切换到 Console 标签
5. 运行以下代码:
   ```javascript
   fetch("/api/config/llm", {
     credentials: "include"
   })
     .then(r => r.json())
     .then(d => console.log(d));
   ```
6. 应该看到配置信息或 `{"success": true, "config": null}`

### 测试 API Token 认证

使用 curl 测试:
```bash
curl -X GET "http://127.0.0.1:5000/api/config/llm" \
  -H "Cookie: api_token=你的Token" \
  -v
```

成功响应示例:
```json
{
  "success": true,
  "config": null,
  "message": "使用默认配置"
}
```

或者 (如果已配置):
```json
{
  "success": true,
  "config": {
    "provider": "deepseek",
    "completion_model": "deepseek-chat",
    "embedding_model": "text-embedding-ada-002",
    "api_key": "sk-abc...xyz",
    "base_url": "https://api.deepseek.com"
  }
}
```

## 常见问题

### Q1: 为什么需要认证?

**A**: LLM 配置包含敏感信息 (API Key),需要确保只有授权用户才能访问和修改。

### Q2: 可以禁用认证吗?

**A**: 不建议在生产环境禁用认证。如果只是本地开发测试,可以修改代码移除 `@token_required` 装饰器,但这会带来安全风险。

### Q3: Token 会过期吗?

**A**: API Token 默认不会过期,除非用户手动删除。Session Cookie 会在 14 天后过期。

### Q4: 忘记 Token 怎么办?

**A**: 
1. 登录 Web 界面
2. 进入 API Tokens 页面
3. 删除旧 Token
4. 生成新 Token

### Q5: 可以同时使用多个 Token 吗?

**A**: 可以。你可以为不同的应用或环境生成多个 Token。

## 安全建议

1. **不要分享 Token**: Token 等同于你的登录凭证
2. **定期轮换 Token**: 建议定期删除旧 Token 并生成新的
3. **使用 HTTPS**: 生产环境必须使用 HTTPS 传输
4. **限制 Token 权限**: 只给必要的应用分配 Token
5. **监控 Token 使用**: 定期检查 Token 使用情况

## API 文档

完整的 API 文档可以访问:
- Swagger UI: `http://127.0.0.1:5000/docs`
- ReDoc: `http://127.0.0.1:5000/redoc`

在文档页面可以:
- 查看所有 API 接口
- 测试 API 调用
- 查看请求/响应示例
- 了解认证要求

---

**相关文档**:
- [启动指南.md](./启动指南.md) - 如何启动项目
- [问题排查指南.md](./问题排查指南.md) - 常见问题解决
