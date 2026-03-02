# OAuth 认证 API 文档

## 概述

QueryWeaver 支持多种 OAuth 2.0 认证提供商,包括 Google、GitHub、微信(WeChat)和企业微信(WeCom)。本文档详细说明了所有 OAuth 相关的 API 端点。

## 认证流程

所有 OAuth 提供商遵循标准的 OAuth 2.0 授权码流程:

1. 用户点击登录按钮
2. 重定向到 OAuth 提供商的授权页面
3. 用户授权后,提供商回调到应用
4. 应用使用授权码换取访问令牌
5. 使用访问令牌获取用户信息
6. 创建或更新用户账号
7. 生成 API Token 并设置 Cookie
8. 重定向到应用首页

## 认证配置查询

### GET /auth/config

获取当前启用的认证方式配置。

**请求**

```http
GET /auth/config HTTP/1.1
Host: localhost:5000
```

**响应**

```json
{
  "google": true,
  "github": true,
  "wechat": true,
  "wecom": false,
  "email": false
}
```

**字段说明**

- `google`: Google OAuth 是否启用
- `github`: GitHub OAuth 是否启用
- `wechat`: 微信 OAuth 是否启用
- `wecom`: 企业微信 OAuth 是否启用
- `email`: 邮箱密码登录是否启用

**使用场景**

前端根据此配置动态显示或隐藏相应的登录按钮。

---

## Google OAuth

### GET /login/google

发起 Google OAuth 登录流程。

**请求**

```http
GET /login/google HTTP/1.1
Host: localhost:5000
```

**响应**

```http
HTTP/1.1 302 Found
Location: https://accounts.google.com/o/oauth2/v2/auth?...
Set-Cookie: oauth_state=...; HttpOnly; Secure; SameSite=Lax
```

重定向到 Google 授权页面。

### GET /login/google/authorized

Google OAuth 回调端点。

**请求**

```http
GET /login/google/authorized?code=xxx&state=xxx HTTP/1.1
Host: localhost:5000
Cookie: oauth_state=...
```

**查询参数**

- `code`: Google 返回的授权码
- `state`: CSRF 防护令牌

**响应**

成功时重定向到首页:

```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: api_token=...; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000
```

失败时返回错误:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "授权失败：缺少必需参数"
}
```

---

## GitHub OAuth

### GET /login/github

发起 GitHub OAuth 登录流程。

**请求**

```http
GET /login/github HTTP/1.1
Host: localhost:5000
```

**响应**

```http
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?...
Set-Cookie: oauth_state=...; HttpOnly; Secure; SameSite=Lax
```

重定向到 GitHub 授权页面。

### GET /login/github/authorized

GitHub OAuth 回调端点。

**请求**

```http
GET /login/github/authorized?code=xxx&state=xxx HTTP/1.1
Host: localhost:5000
Cookie: oauth_state=...
```

**查询参数**

- `code`: GitHub 返回的授权码
- `state`: CSRF 防护令牌

**响应**

成功时重定向到首页:

```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: api_token=...; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000
```

---

## 微信 OAuth (WeChat)

### GET /login/wechat

发起微信 OAuth 登录流程。

**请求**

```http
GET /login/wechat HTTP/1.1
Host: localhost:5000
```

**响应**

成功时重定向到微信授权页面:

```http
HTTP/1.1 302 Found
Location: https://open.weixin.qq.com/connect/oauth2/authorize?appid=...&redirect_uri=...&response_type=code&scope=snsapi_userinfo&state=...#wechat_redirect
Set-Cookie: oauth_state=...; HttpOnly; Secure; SameSite=Lax; Max-Age=600
```

未配置时返回错误:

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "微信登录功能未启用,请联系管理员配置"
}
```

**授权 URL 参数**

- `appid`: 微信应用 ID
- `redirect_uri`: 回调 URL (URL 编码)
- `response_type`: 固定为 `code`
- `scope`: 授权作用域,`snsapi_userinfo` 获取用户信息
- `state`: CSRF 防护令牌

**注意事项**

- 微信 OAuth 需要在微信开放平台配置回调域名
- 生产环境必须使用 HTTPS
- 支持 PC 端扫码和移动端内置浏览器授权

### GET /login/wechat/authorized

微信 OAuth 回调端点。

**请求**

```http
GET /login/wechat/authorized?code=xxx&state=xxx HTTP/1.1
Host: localhost:5000
Cookie: oauth_state=...
```

**查询参数**

- `code`: 微信返回的授权码 (有效期 5 分钟,只能使用一次)
- `state`: CSRF 防护令牌

**响应**

成功时重定向到首页:

```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: api_token=...; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000
```

**错误响应**

缺少必需参数:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "授权失败：缺少必需参数"
}
```

State 验证失败:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "授权失败：安全验证失败,请重试"
}
```

State 已过期:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "授权失败：验证令牌已过期,请重新登录"
}
```

微信 API 错误:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "登录失败: 微信 API 错误: invalid code"
}
```

**用户信息处理**

- 微信用户的唯一标识为 `openid`
- 如果用户没有绑定邮箱,系统会生成虚拟邮箱: `{openid}@wechat.queryweaver.local`
- 如果返回了 `unionid`,会用于跨应用识别同一用户
- 用户昵称和头像会从微信 API 获取

---

## 企业微信 OAuth (WeCom)

### GET /login/wecom

发起企业微信 OAuth 登录流程。

**请求**

```http
GET /login/wecom HTTP/1.1
Host: localhost:5000
```

**响应**

成功时重定向到企业微信授权页面:

```http
HTTP/1.1 302 Found
Location: https://open.weixin.qq.com/connect/oauth2/authorize?appid=...&redirect_uri=...&response_type=code&scope=snsapi_base&agentid=...&state=...#wechat_redirect
Set-Cookie: oauth_state=...; HttpOnly; Secure; SameSite=Lax; Max-Age=600
```

未配置时返回错误:

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "企业微信登录功能未启用,请联系管理员配置"
}
```

**授权 URL 参数**

- `appid`: 企业 ID (CorpID)
- `redirect_uri`: 回调 URL (URL 编码)
- `response_type`: 固定为 `code`
- `scope`: 授权作用域,`snsapi_base` 或 `snsapi_userinfo`
- `agentid`: 应用 ID
- `state`: CSRF 防护令牌

**注意事项**

- 企业微信 OAuth 需要在企业微信管理后台配置可信域名
- 生产环境必须使用 HTTPS
- 支持 PC 端扫码和移动端内置浏览器授权
- 仅企业内部成员可以登录

### GET /login/wecom/authorized

企业微信 OAuth 回调端点。

**请求**

```http
GET /login/wecom/authorized?code=xxx&state=xxx HTTP/1.1
Host: localhost:5000
Cookie: oauth_state=...
```

**查询参数**

- `code`: 企业微信返回的授权码 (有效期 5 分钟,只能使用一次)
- `state`: CSRF 防护令牌

**响应**

成功时重定向到首页:

```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: api_token=...; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000
```

**错误响应**

与微信 OAuth 类似,包括:

- 缺少必需参数 (400)
- State 验证失败 (400)
- State 已过期 (400)
- 企业微信 API 错误 (400)

**用户信息处理**

- 企业微信用户的唯一标识为 `userid`
- 如果用户有企业邮箱,使用企业邮箱;否则生成虚拟邮箱: `{userid}@wecom.queryweaver.local`
- 获取用户姓名、头像、部门信息等
- 记录企业 ID (CorpID) 用于多企业场景

---

## 安全机制

### CSRF 防护

所有 OAuth 流程都使用 `state` 参数进行 CSRF 防护:

1. 发起授权时生成随机 `state` 值
2. 使用 `itsdangerous.URLSafeTimedSerializer` 对 `state` 进行签名
3. 将 `state` 存储在 HttpOnly Cookie 中
4. 回调时验证 `state` 的签名和时效性 (10 分钟)
5. 验证通过后删除 `oauth_state` Cookie

### Token 安全

- API Token 使用 `secrets.token_urlsafe(32)` 生成 (256 位随机性)
- Cookie 设置 `HttpOnly=True` 防止 XSS 攻击
- Cookie 设置 `Secure=True` (生产环境) 仅通过 HTTPS 传输
- Cookie 设置 `SameSite=Lax` 防止 CSRF 攻击
- Token 有效期为 1 年 (`Max-Age=31536000`)

### 环境配置

根据 `APP_ENV` 环境变量自动调整安全设置:

- `development`: 允许 HTTP,Cookie 不设置 Secure 标志
- `production` / `staging`: 强制 HTTPS,Cookie 设置 Secure 标志

---

## 错误码参考

### HTTP 状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 302 | 重定向 | 成功发起授权或登录成功 |
| 400 | 请求错误 | 缺少参数、State 验证失败、OAuth API 错误 |
| 500 | 服务器错误 | 用户信息处理失败、数据库错误 |
| 503 | 服务不可用 | OAuth 提供商未配置 |

### 微信 API 错误码

| 错误码 | 说明 | 用户提示 |
|--------|------|----------|
| 40001 | AppSecret 错误 | 系统配置错误,请联系管理员 |
| 40013 | AppID 无效 | 系统配置错误,请联系管理员 |
| 40029 | code 无效 | 登录失败,请重试 |
| 40163 | code 已使用 | 登录失败,请重试 |
| 41001 | 缺少 access_token | 登录失败,请重试 |
| 42001 | access_token 超时 | 登录已过期,请重新登录 |

### 企业微信 API 错误码

| 错误码 | 说明 | 用户提示 |
|--------|------|----------|
| 40001 | CorpSecret 错误 | 系统配置错误,请联系管理员 |
| 40013 | CorpID 无效 | 系统配置错误,请联系管理员 |
| 40029 | code 无效 | 登录失败,请重试 |
| 40163 | code 已使用 | 登录失败,请重试 |
| 41001 | 缺少 access_token | 登录失败,请重试 |
| 42001 | access_token 超时 | 登录已过期,请重新登录 |
| 60011 | 部门不存在 | 用户部门信息异常,请联系管理员 |
| 60102 | UserID 不存在 | 用户不存在,请联系管理员 |

---

## 数据模型

### Identity 节点

所有 OAuth 登录的用户都会在 FalkorDB 中创建 Identity 节点:

```cypher
(identity:Identity {
    provider: "wechat",              // 或 "wecom", "google", "github"
    provider_user_id: "openid",      // 提供商的用户唯一标识
    email: "user@example.com",       // 用户邮箱 (可能是虚拟邮箱)
    name: "张三",                     // 用户姓名或昵称
    picture: "https://...",          // 用户头像 URL
    unionid: "unionid",              // 微信 UnionID (可选)
    corp_id: "corp_id",              // 企业微信企业 ID (仅企业微信)
    department: [1, 2],              // 企业微信部门 ID (仅企业微信)
    created_at: timestamp,           // 创建时间
    last_login: timestamp            // 最后登录时间
})
```

### User 节点

Identity 节点通过 `AUTHENTICATES` 关系连接到 User 节点:

```cypher
(identity:Identity)-[:AUTHENTICATES]->(user:User)
```

同一用户可以有多个 Identity (例如同时使用 Google 和微信登录)。

---

## 测试

### 使用 curl 测试

1. 获取认证配置:

```bash
curl http://localhost:5000/auth/config
```

2. 发起微信登录 (会重定向):

```bash
curl -L http://localhost:5000/login/wechat
```

3. 模拟回调 (需要有效的 code 和 state):

```bash
curl -b "oauth_state=xxx" \
  "http://localhost:5000/login/wechat/authorized?code=xxx&state=xxx"
```

### 使用浏览器测试

1. 访问 http://localhost:5000
2. 点击"微信登录"或"企业微信登录"按钮
3. 扫码或授权
4. 自动返回应用并完成登录

### 单元测试

参考 `tests/` 目录下的测试文件:

- `tests/test_wechat_oauth.py`: 微信 OAuth 单元测试
- `tests/test_wecom_oauth.py`: 企业微信 OAuth 单元测试
- `tests/test_oauth_security.py`: OAuth 安全机制测试

---

## 常见问题

### Q: 为什么微信登录后没有邮箱?

A: 微信 OAuth 不一定返回用户邮箱。系统会自动生成虚拟邮箱 `{openid}@wechat.queryweaver.local` 作为用户标识。

### Q: 如何区分同一用户的多个微信应用登录?

A: 如果微信返回了 `unionid`,系统会使用 `unionid` 关联同一用户在不同应用的账号。

### Q: 企业微信登录失败,提示"用户不存在"?

A: 确保用户是企业成员,并且应用已授权给该用户。检查企业微信管理后台的应用可见范围设置。

### Q: 生产环境 OAuth 回调失败?

A: 检查以下配置:
1. `APP_ENV` 设置为 `production`
2. 使用 HTTPS
3. 回调 URL 在 OAuth 提供商后台正确配置
4. 域名已完成 ICP 备案 (微信/企业微信)

### Q: 如何禁用某个 OAuth 提供商?

A: 不设置对应的环境变量即可。例如不设置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`,微信登录就会被禁用。

---

## 相关文档

- [README.md](../README.md): 项目总体说明
- [微信开放平台文档](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
- [企业微信 API 文档](https://developer.work.weixin.qq.com/document/path/91022)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
