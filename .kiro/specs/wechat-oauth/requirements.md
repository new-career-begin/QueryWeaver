# 微信和企业微信 OAuth 登录需求文档

## 1. 功能概述

为 QueryWeaver 添加微信（WeChat）和企业微信（WeCom）OAuth 2.0 登录支持，使中国用户能够使用常用的身份认证方式登录系统。

### 1.1 业务价值

- **降低登录门槛**: 中国用户更熟悉微信登录，无需注册新账号
- **提高用户转化率**: 减少注册流程，提升用户体验
- **企业场景支持**: 企业微信登录支持企业内部使用场景
- **用户数据安全**: 利用微信的安全认证体系

### 1.2 目标用户

- **个人用户**: 使用微信登录的个人开发者、数据分析师
- **企业用户**: 使用企业微信的企业内部员工
- **中国市场用户**: 主要面向中国大陆用户

---

## 2. 功能需求

### 2.1 微信登录 (WeChat OAuth)

#### 2.1.1 用户故事

**作为** 个人用户  
**我希望** 能够使用微信账号登录 QueryWeaver  
**以便** 快速访问系统，无需记住额外的账号密码

#### 2.1.2 验收标准

- [ ] 用户可以在登录页面看到"微信登录"按钮
- [ ] 点击按钮后跳转到微信授权页面
- [ ] 用户授权后自动返回 QueryWeaver 并完成登录
- [ ] 首次登录自动创建用户账号
- [ ] 后续登录自动识别已有账号
- [ ] 支持微信扫码登录（PC 端）
- [ ] 支持微信内置浏览器直接授权（移动端）
- [ ] 获取用户基本信息：昵称、头像、OpenID
- [ ] 登录失败时显示友好的错误提示

#### 2.1.3 技术要求

**OAuth 2.0 流程**:
1. 用户点击"微信登录"
2. 重定向到微信授权页面: `https://open.weixin.qq.com/connect/oauth2/authorize`
3. 用户扫码或授权
4. 微信回调到: `http://your-domain.com/login/wechat/authorized`
5. 使用 code 换取 access_token
6. 使用 access_token 获取用户信息
7. 创建/更新用户记录
8. 生成 API Token 并设置 Cookie

**所需信息**:
- AppID (应用ID)
- AppSecret (应用密钥)
- 回调 URL
- 授权作用域: `snsapi_userinfo` (获取用户信息)

**API 端点**:
- 授权: `https://open.weixin.qq.com/connect/oauth2/authorize`
- 获取 Token: `https://api.weixin.qq.com/sns/oauth2/access_token`
- 获取用户信息: `https://api.weixin.qq.com/sns/userinfo`

### 2.2 企业微信登录 (WeCom OAuth)

#### 2.2.1 用户故事

**作为** 企业用户  
**我希望** 能够使用企业微信账号登录 QueryWeaver  
**以便** 在企业内部安全地使用数据查询功能

#### 2.2.2 验收标准

- [ ] 用户可以在登录页面看到"企业微信登录"按钮
- [ ] 点击按钮后跳转到企业微信授权页面
- [ ] 用户授权后自动返回 QueryWeaver 并完成登录
- [ ] 首次登录自动创建用户账号
- [ ] 后续登录自动识别已有账号
- [ ] 支持企业微信扫码登录（PC 端）
- [ ] 支持企业微信内置浏览器直接授权（移动端）
- [ ] 获取用户信息：姓名、头像、UserID、部门信息
- [ ] 支持企业内部应用和第三方应用两种模式
- [ ] 登录失败时显示友好的错误提示

#### 2.2.3 技术要求

**OAuth 2.0 流程**:
1. 用户点击"企业微信登录"
2. 重定向到企业微信授权页面: `https://open.weixin.qq.com/connect/oauth2/authorize`
3. 用户扫码或授权
4. 企业微信回调到: `http://your-domain.com/login/wecom/authorized`
5. 使用 code 换取 access_token
6. 使用 access_token 获取用户信息
7. 创建/更新用户记录
8. 生成 API Token 并设置 Cookie

**所需信息**:
- CorpID (企业ID)
- AgentID (应用ID)
- CorpSecret (应用密钥)
- 回调 URL
- 授权作用域: `snsapi_base` 或 `snsapi_userinfo`

**API 端点**:
- 授权: `https://open.weixin.qq.com/connect/oauth2/authorize`
- 获取 Token: `https://qyapi.weixin.qq.com/cgi-bin/gettoken`
- 获取用户信息: `https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo`
- 获取用户详情: `https://qyapi.weixin.qq.com/cgi-bin/user/get`

---

## 3. 非功能需求

### 3.1 安全性

- [ ] 使用 HTTPS 传输所有敏感数据
- [ ] AppSecret 和 CorpSecret 必须加密存储
- [ ] 实现 CSRF 防护（state 参数）
- [ ] Token 有效期管理（24 小时）
- [ ] 定期刷新 access_token
- [ ] 记录所有登录尝试日志
- [ ] 防止暴力破解攻击

### 3.2 性能

- [ ] OAuth 回调响应时间 < 2 秒
- [ ] 用户信息获取时间 < 1 秒
- [ ] 支持并发登录请求
- [ ] 缓存 access_token 减少 API 调用

### 3.3 可用性

- [ ] 登录按钮清晰可见
- [ ] 授权页面加载失败时显示友好提示
- [ ] 支持中文错误消息
- [ ] 移动端适配
- [ ] 微信内置浏览器优化

### 3.4 兼容性

- [ ] 支持 PC 端扫码登录
- [ ] 支持移动端微信内置浏览器
- [ ] 支持企业微信桌面客户端
- [ ] 兼容现有的 Google/GitHub 登录

---

## 4. 数据模型

### 4.1 Identity 节点扩展

```cypher
(identity:Identity {
    provider: "wechat",              # 或 "wecom"
    provider_user_id: "openid",      # 微信 OpenID 或企业微信 UserID
    email: "user@example.com",       # 可选，微信可能没有邮箱
    name: "张三",
    picture: "https://...",
    unionid: "unionid",              # 微信 UnionID (可选)
    corp_id: "corp_id",              # 企业微信企业ID (仅企业微信)
    department: [1, 2],              # 企业微信部门ID (仅企业微信)
    created_at: timestamp,
    last_login: timestamp
})
```

### 4.2 用户唯一标识

**微信登录**:
- 主键: `provider="wechat"` + `provider_user_id=openid`
- 如果有 UnionID，优先使用 UnionID 关联多个应用的同一用户
- 如果没有邮箱，使用 `openid@wechat.queryweaver.local` 作为虚拟邮箱

**企业微信登录**:
- 主键: `provider="wecom"` + `provider_user_id=userid`
- 企业邮箱作为 email
- 记录企业ID和部门信息

---

## 5. 用户界面

### 5.1 登录页面

```
┌─────────────────────────────────────┐
│      QueryWeaver                    │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  使用 Google 登录            │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  使用 GitHub 登录            │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  [微信图标] 使用微信登录     │  │ ← 新增
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │  [企业微信图标] 企业微信登录 │  │ ← 新增
│  └─────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### 5.2 扫码登录页面（PC 端）

```
┌─────────────────────────────────────┐
│      使用微信扫码登录                │
│                                     │
│      ┌─────────────────┐           │
│      │                 │           │
│      │   [二维码]      │           │
│      │                 │           │
│      └─────────────────┘           │
│                                     │
│   请使用微信扫描二维码登录          │
│                                     │
│   [返回] [刷新二维码]               │
└─────────────────────────────────────┘
```

---

## 6. 配置管理

### 6.1 环境变量

```bash
# 微信登录配置
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_wechat_app_secret

# 企业微信登录配置
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=your_wecom_corp_secret

# 回调 URL 配置（可选，默认自动生成）
WECHAT_REDIRECT_URI=http://localhost:5000/login/wechat/authorized
WECOM_REDIRECT_URI=http://localhost:5000/login/wecom/authorized
```

### 6.2 OAuth 配置示例

```python
# api/config.py
WECHAT_CONFIG = {
    "app_id": os.getenv("WECHAT_APP_ID"),
    "app_secret": os.getenv("WECHAT_APP_SECRET"),
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
    "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    "scope": "snsapi_userinfo"
}

WECOM_CONFIG = {
    "corp_id": os.getenv("WECOM_CORP_ID"),
    "agent_id": os.getenv("WECOM_AGENT_ID"),
    "corp_secret": os.getenv("WECOM_CORP_SECRET"),
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
    "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    "scope": "snsapi_base"
}
```

---

## 7. API 端点

### 7.1 微信登录端点

```
GET  /login/wechat
     - 重定向到微信授权页面

GET  /login/wechat/authorized
     - 微信回调端点
     - 参数: code, state
     - 返回: 重定向到首页或错误页面
```

### 7.2 企业微信登录端点

```
GET  /login/wecom
     - 重定向到企业微信授权页面

GET  /login/wecom/authorized
     - 企业微信回调端点
     - 参数: code, state
     - 返回: 重定向到首页或错误页面
```

---

## 8. 错误处理

### 8.1 常见错误场景

| 错误代码 | 错误描述 | 用户提示 | 处理方式 |
|---------|---------|---------|---------|
| 40001 | AppSecret 错误 | 系统配置错误，请联系管理员 | 记录日志，返回 500 |
| 40013 | AppID 无效 | 系统配置错误，请联系管理员 | 记录日志，返回 500 |
| 40029 | code 无效 | 登录失败，请重试 | 重定向到登录页 |
| 40163 | code 已使用 | 登录失败，请重试 | 重定向到登录页 |
| 41001 | 缺少 access_token | 登录失败，请重试 | 重定向到登录页 |
| 42001 | access_token 超时 | 登录已过期，请重新登录 | 重定向到登录页 |
| 用户取消授权 | 用户拒绝授权 | 您已取消登录 | 重定向到登录页 |
| 网络超时 | 网络连接失败 | 网络连接失败，请检查网络 | 重定向到登录页 |

### 8.2 错误日志

```python
# 记录所有 OAuth 错误
logger.error(json.dumps({
    "event": "oauth_error",
    "provider": "wechat",  # 或 "wecom"
    "error_code": error_code,
    "error_message": error_message,
    "user_id": user_id,
    "timestamp": datetime.now().isoformat()
}))
```

---

## 9. 测试需求

### 9.1 单元测试

- [ ] 测试微信 OAuth 配置加载
- [ ] 测试企业微信 OAuth 配置加载
- [ ] 测试授权 URL 生成
- [ ] 测试 access_token 获取
- [ ] 测试用户信息解析
- [ ] 测试错误处理逻辑
- [ ] 测试用户创建/更新逻辑

### 9.2 集成测试

- [ ] 测试完整的微信登录流程
- [ ] 测试完整的企业微信登录流程
- [ ] 测试首次登录创建用户
- [ ] 测试重复登录识别用户
- [ ] 测试跨提供商账号关联（同一邮箱）
- [ ] 测试 Token 过期处理
- [ ] 测试并发登录

### 9.3 端到端测试

- [ ] PC 端微信扫码登录
- [ ] 移动端微信内置浏览器登录
- [ ] PC 端企业微信扫码登录
- [ ] 移动端企业微信内置浏览器登录
- [ ] 登录后访问受保护资源
- [ ] 登出后重新登录

### 9.4 手动测试清单

- [ ] 在微信开放平台创建测试应用
- [ ] 在企业微信管理后台创建测试应用
- [ ] 配置回调 URL
- [ ] 测试扫码登录
- [ ] 测试移动端登录
- [ ] 测试错误场景
- [ ] 测试用户信息显示

---

## 10. 部署要求

### 10.1 微信开放平台配置

1. 注册微信开放平台账号: https://open.weixin.qq.com/
2. 创建网站应用
3. 配置授权回调域名
4. 获取 AppID 和 AppSecret
5. 提交审核（需要备案域名）

### 10.2 企业微信配置

1. 注册企业微信: https://work.weixin.qq.com/
2. 创建自建应用或第三方应用
3. 配置可信域名
4. 获取 CorpID、AgentID 和 CorpSecret
5. 配置应用权限

### 10.3 域名要求

- 必须使用已备案的域名（中国大陆）
- 必须支持 HTTPS
- 回调 URL 必须在授权域名下

---

## 11. 文档要求

### 11.1 用户文档

- [ ] 如何配置微信登录
- [ ] 如何配置企业微信登录
- [ ] 常见问题解答
- [ ] 故障排查指南

### 11.2 开发文档

- [ ] OAuth 流程说明
- [ ] API 接口文档
- [ ] 数据模型说明
- [ ] 错误代码参考

### 11.3 运维文档

- [ ] 环境变量配置
- [ ] 日志监控
- [ ] 性能优化
- [ ] 安全加固

---

## 12. 里程碑

### 12.1 阶段一：基础实现 (1 周)

- [ ] 实现微信 OAuth 基础流程
- [ ] 实现企业微信 OAuth 基础流程
- [ ] 用户数据存储到 FalkorDB
- [ ] 基础错误处理

### 12.2 阶段二：UI 集成 (3 天)

- [ ] 添加登录按钮
- [ ] 实现扫码登录页面
- [ ] 移动端适配
- [ ] 错误提示优化

### 12.3 阶段三：测试和优化 (3 天)

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 安全加固

### 12.4 阶段四：文档和发布 (2 天)

- [ ] 编写用户文档
- [ ] 编写开发文档
- [ ] 代码审查
- [ ] 发布上线

---

## 13. 风险和依赖

### 13.1 技术风险

- **微信 API 变更**: 微信可能更新 API，需要及时适配
- **网络问题**: 微信服务器在中国大陆，海外访问可能较慢
- **证书问题**: HTTPS 证书配置错误导致回调失败

### 13.2 业务风险

- **审核延迟**: 微信开放平台审核可能需要数天
- **域名备案**: 需要已备案的域名才能使用
- **用户隐私**: 需要遵守微信用户隐私政策

### 13.3 依赖项

- [ ] 已备案的域名
- [ ] HTTPS 证书
- [ ] 微信开放平台账号
- [ ] 企业微信账号
- [ ] FalkorDB 运行正常

---

## 14. 验收标准

### 14.1 功能验收

- [ ] 用户可以使用微信登录
- [ ] 用户可以使用企业微信登录
- [ ] 首次登录自动创建账号
- [ ] 重复登录正确识别用户
- [ ] 登录后可以正常使用所有功能
- [ ] 登出后需要重新登录

### 14.2 性能验收

- [ ] OAuth 回调响应时间 < 2 秒
- [ ] 支持 100 并发登录请求
- [ ] 无内存泄漏

### 14.3 安全验收

- [ ] 通过安全扫描
- [ ] 无 SQL 注入漏洞
- [ ] 无 XSS 漏洞
- [ ] CSRF 防护有效

### 14.4 兼容性验收

- [ ] PC 端 Chrome/Firefox/Safari 正常
- [ ] 移动端微信内置浏览器正常
- [ ] 企业微信客户端正常
- [ ] 与现有 Google/GitHub 登录兼容

---

## 15. 参考资料

### 15.1 官方文档

- [微信开放平台文档](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
- [企业微信 API 文档](https://developer.work.weixin.qq.com/document/path/91022)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)

### 15.2 相关库

- [Authlib](https://docs.authlib.org/) - Python OAuth 库
- [wechatpy](https://github.com/wechatpy/wechatpy) - 微信 Python SDK
- [work-weixin](https://github.com/sbzhu/weworkapi_python) - 企业微信 Python SDK

---

## 附录 A: 微信 OAuth 流程图

```
用户
  ↓ 点击"微信登录"
前端
  ↓ GET /login/wechat
后端
  ↓ 生成 state (CSRF token)
  ↓ 重定向到微信授权页面
微信授权页面
  ↓ 用户扫码/授权
  ↓ 回调 /login/wechat/authorized?code=xxx&state=xxx
后端
  ↓ 验证 state
  ↓ 使用 code 换取 access_token
  ↓ 使用 access_token 获取用户信息
  ↓ 在 FalkorDB 创建/更新用户
  ↓ 生成 API Token
  ↓ 设置 Cookie
  ↓ 重定向到首页
前端
  ↓ 显示用户信息
```

## 附录 B: 数据库查询示例

```cypher
// 创建微信用户
MERGE (user:User {email: "openid@wechat.queryweaver.local"})
ON CREATE SET
    user.first_name = "张",
    user.last_name = "三",
    user.created_at = timestamp()

MERGE (identity:Identity {
    provider: "wechat",
    provider_user_id: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M"
})
ON CREATE SET
    identity.name = "张三",
    identity.picture = "http://thirdwx.qlogo.cn/...",
    identity.unionid = "o6_bmasdasdsad6_2sgVt7hMZOPfL",
    identity.created_at = timestamp(),
    identity.last_login = timestamp()

MERGE (identity)-[:AUTHENTICATES]->(user)
```
