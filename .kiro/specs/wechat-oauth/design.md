# 微信和企业微信 OAuth 登录设计文档

## 1. 概述

本设计文档描述了为 QueryWeaver 添加微信（WeChat）和企业微信（WeCom）OAuth 2.0 登录功能的技术实现方案。该功能将与现有的 Google 和 GitHub OAuth 登录集成,遵循相同的架构模式和代码风格。

### 1.1 设计目标

- **一致性**: 与现有 OAuth 实现保持一致的架构和代码风格
- **可扩展性**: 易于添加更多 OAuth 提供商
- **安全性**: 实现完整的 OAuth 2.0 安全机制
- **用户体验**: 提供流畅的登录体验,支持 PC 和移动端

### 1.2 技术栈

- **后端**: FastAPI + Python 3.12+
- **OAuth 库**: Authlib (与现有实现一致)
- **数据库**: FalkorDB (图数据库)
- **前端**: React + TypeScript (登录按钮和UI)

### 1.3 设计原则

1. **复用现有架构**: 最大化复用 `oauth_handlers.py` 和 `user_management.py` 的代码
2. **配置驱动**: 通过环境变量控制功能开关
3. **错误友好**: 提供清晰的中文错误提示
4. **日志完整**: 记录所有关键操作和错误

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────┐
│   用户      │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│         前端 (React)                     │
│  - 登录按钮                              │
│  - 扫码页面                              │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│      后端 API (FastAPI)                  │
│  ┌─────────────────────────────────┐   │
│  │  api/routes/auth.py             │   │
│  │  - /login/wechat                │   │
│  │  - /login/wechat/authorized     │   │
│  │  - /login/wecom                 │   │
│  │  - /login/wecom/authorized      │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  api/auth/oauth_handlers.py     │   │
│  │  - handle_callback()            │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  api/auth/user_management.py    │   │
│  │  - ensure_user_in_organizations()│  │
│  └─────────────────────────────────┘   │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│      FalkorDB (Organizations 图)         │
│  - User 节点                             │
│  - Identity 节点                         │
│  - Token 节点                            │
└─────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│      微信/企业微信 API                   │
│  - 授权服务器                            │
│  - 用户信息接口                          │
└─────────────────────────────────────────┘
```


### 2.2 OAuth 2.0 流程

#### 2.2.1 微信登录流程

```
用户                前端              后端              微信服务器
 │                  │                 │                    │
 │  点击微信登录     │                 │                    │
 ├─────────────────>│                 │                    │
 │                  │  GET /login/wechat                   │
 │                  ├────────────────>│                    │
 │                  │                 │  生成 state (CSRF) │
 │                  │                 │  构建授权 URL      │
 │                  │  302 重定向     │                    │
 │                  │<────────────────┤                    │
 │                  │                 │                    │
 │  重定向到微信授权页面              │                    │
 ├────────────────────────────────────────────────────────>│
 │                  │                 │                    │
 │  扫码/授权       │                 │                    │
 │<─────────────────────────────────────────────────────────┤
 │                  │                 │                    │
 │  回调 /login/wechat/authorized?code=xxx&state=xxx       │
 ├─────────────────────────────────────>│                  │
 │                  │                 │  验证 state        │
 │                  │                 │  用 code 换 token  │
 │                  │                 ├───────────────────>│
 │                  │                 │  access_token      │
 │                  │                 │<───────────────────┤
 │                  │                 │  获取用户信息      │
 │                  │                 ├───────────────────>│
 │                  │                 │  用户信息          │
 │                  │                 │<───────────────────┤
 │                  │                 │  创建/更新用户     │
 │                  │                 │  生成 API Token    │
 │                  │  302 重定向 + Cookie                 │
 │                  │<────────────────┤                    │
 │  登录成功        │                 │                    │
 │<─────────────────┤                 │                    │
```

#### 2.2.2 企业微信登录流程

企业微信的流程与微信类似,但有以下区别:
1. 使用 CorpID 和 AgentID 而不是 AppID
2. 用户信息接口返回 UserID 而不是 OpenID
3. 可以获取部门信息

---

## 3. 组件和接口

### 3.1 后端路由 (api/routes/auth.py)

#### 3.1.1 微信登录路由

```python
@auth_router.get("/login/wechat", name="wechat.login", response_class=RedirectResponse)
async def login_wechat(request: Request) -> RedirectResponse:
    """
    发起微信 OAuth 登录流程
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向到微信授权页面
        
    Raises:
        HTTPException: 当微信登录未配置时返回 404
    """
    # 检查微信登录是否启用
    if not _is_wechat_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="微信登录未配置"
        )
    
    # 获取微信 OAuth 客户端
    wechat = _get_provider_client(request, "wechat")
    
    # 构建回调 URL
    redirect_uri = _build_callback_url(request, "login/wechat/authorized")
    
    # 重定向到微信授权页面
    return await wechat.authorize_redirect(request, redirect_uri)
```

```python
@auth_router.get("/login/wechat/authorized", response_class=RedirectResponse)
async def wechat_authorized(request: Request) -> RedirectResponse:
    """
    处理微信 OAuth 回调
    
    Args:
        request: FastAPI 请求对象,包含 code 和 state 参数
        
    Returns:
        重定向到首页,并设置 API Token Cookie
        
    Raises:
        HTTPException: 当授权失败时返回 400
    """
    # 检查微信登录是否启用
    if not _is_wechat_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="微信登录未配置"
        )
    
    try:
        # 获取微信 OAuth 客户端
        wechat = _get_provider_client(request, "wechat")
        
        # 用 code 换取 access_token
        token = await wechat.authorize_access_token(request)
        
        # 获取用户信息
        resp = await wechat.get("userinfo", token=token)
        if resp.status_code != 200:
            logging.warning("获取微信用户信息失败")
            raise HTTPException(status_code=400, detail="获取用户信息失败")
        
        user_info = resp.json()
        
        # 构建用户数据
        user_data = {
            'id': user_info.get('openid'),
            'email': f"{user_info.get('openid')}@wechat.queryweaver.local",
            'name': user_info.get('nickname'),
            'picture': user_info.get('headimgurl'),
            'unionid': user_info.get('unionid'),  # 可选
        }
        
        # 调用回调处理器
        handler = getattr(request.app.state, "callback_handler", None)
        if handler:
            api_token = secrets.token_urlsafe(32)
            await handler('wechat', user_data, api_token)
            
            # 设置 Cookie 并重定向
            redirect = RedirectResponse(url="/", status_code=302)
            redirect.set_cookie(
                key="api_token",
                value=api_token,
                httponly=True,
                secure=_is_request_secure(request)
            )
            return redirect
        
        logging.error("微信 OAuth 回调处理器未注册")
        raise HTTPException(status_code=500, detail="认证处理器未配置")
        
    except Exception as e:
        logging.error("微信 OAuth 认证失败: %s", str(e))
        raise HTTPException(status_code=400, detail="认证失败") from e
```


#### 3.1.2 企业微信登录路由

```python
@auth_router.get("/login/wecom", name="wecom.login", response_class=RedirectResponse)
async def login_wecom(request: Request) -> RedirectResponse:
    """
    发起企业微信 OAuth 登录流程
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向到企业微信授权页面
        
    Raises:
        HTTPException: 当企业微信登录未配置时返回 404
    """
    if not _is_wecom_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业微信登录未配置"
        )
    
    wecom = _get_provider_client(request, "wecom")
    redirect_uri = _build_callback_url(request, "login/wecom/authorized")
    
    return await wecom.authorize_redirect(request, redirect_uri)
```

```python
@auth_router.get("/login/wecom/authorized", response_class=RedirectResponse)
async def wecom_authorized(request: Request) -> RedirectResponse:
    """
    处理企业微信 OAuth 回调
    
    Args:
        request: FastAPI 请求对象,包含 code 和 state 参数
        
    Returns:
        重定向到首页,并设置 API Token Cookie
        
    Raises:
        HTTPException: 当授权失败时返回 400
    """
    if not _is_wecom_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业微信登录未配置"
        )
    
    try:
        wecom = _get_provider_client(request, "wecom")
        token = await wecom.authorize_access_token(request)
        
        # 获取用户信息
        resp = await wecom.get("userinfo", token=token)
        if resp.status_code != 200:
            logging.warning("获取企业微信用户信息失败")
            raise HTTPException(status_code=400, detail="获取用户信息失败")
        
        user_info = resp.json()
        
        # 构建用户数据
        user_data = {
            'id': user_info.get('userid'),
            'email': user_info.get('email') or f"{user_info.get('userid')}@wecom.queryweaver.local",
            'name': user_info.get('name'),
            'picture': user_info.get('avatar'),
            'corp_id': user_info.get('corpid'),
            'department': user_info.get('department', []),
        }
        
        handler = getattr(request.app.state, "callback_handler", None)
        if handler:
            api_token = secrets.token_urlsafe(32)
            await handler('wecom', user_data, api_token)
            
            redirect = RedirectResponse(url="/", status_code=302)
            redirect.set_cookie(
                key="api_token",
                value=api_token,
                httponly=True,
                secure=_is_request_secure(request)
            )
            return redirect
        
        logging.error("企业微信 OAuth 回调处理器未注册")
        raise HTTPException(status_code=500, detail="认证处理器未配置")
        
    except Exception as e:
        logging.error("企业微信 OAuth 认证失败: %s", str(e))
        raise HTTPException(status_code=400, detail="认证失败") from e
```

#### 3.1.3 配置检查辅助函数

```python
def _is_wechat_auth_enabled() -> bool:
    """检查微信 OAuth 是否通过环境变量启用"""
    return bool(os.getenv("WECHAT_APP_ID") and os.getenv("WECHAT_APP_SECRET"))

def _is_wecom_auth_enabled() -> bool:
    """检查企业微信 OAuth 是否通过环境变量启用"""
    return bool(
        os.getenv("WECOM_CORP_ID") and 
        os.getenv("WECOM_AGENT_ID") and 
        os.getenv("WECOM_CORP_SECRET")
    )
```

### 3.2 OAuth 初始化 (api/routes/auth.py - init_auth)

在 `init_auth()` 函数中添加微信和企业微信的 OAuth 注册:

```python
def init_auth(app):
    """初始化 OAuth 和会话"""
    config = Config(environ=os.environ)
    oauth = OAuth(config)
    
    # ... 现有的 Google 和 GitHub 注册代码 ...
    
    # 注册微信 OAuth
    if _is_wechat_auth_enabled():
        oauth.register(
            name="wechat",
            client_id=os.getenv("WECHAT_APP_ID"),
            client_secret=os.getenv("WECHAT_APP_SECRET"),
            authorize_url="https://open.weixin.qq.com/connect/oauth2/authorize",
            access_token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
            api_base_url="https://api.weixin.qq.com/sns/",
            client_kwargs={
                "scope": "snsapi_userinfo",
                "response_type": "code"
            },
        )
        logging.info("微信 OAuth 初始化成功")
    else:
        logging.info("微信 OAuth 未配置 - 跳过注册")
    
    # 注册企业微信 OAuth
    if _is_wecom_auth_enabled():
        oauth.register(
            name="wecom",
            client_id=os.getenv("WECOM_CORP_ID"),
            client_secret=os.getenv("WECOM_CORP_SECRET"),
            authorize_url="https://open.weixin.qq.com/connect/oauth2/authorize",
            access_token_url="https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            api_base_url="https://qyapi.weixin.qq.com/cgi-bin/",
            client_kwargs={
                "scope": "snsapi_base",
                "agentid": os.getenv("WECOM_AGENT_ID")
            },
        )
        logging.info("企业微信 OAuth 初始化成功")
    else:
        logging.info("企业微信 OAuth 未配置 - 跳过注册")
    
    app.state.oauth = oauth
```

### 3.3 用户管理扩展 (api/auth/user_management.py)

现有的 `ensure_user_in_organizations()` 函数已经支持多种 provider,只需要在允许的 provider 列表中添加 "wechat" 和 "wecom":

```python
def _validate_user_input(provider_user_id: str, email: str, provider: str):
    """验证用户输入参数"""
    # ... 现有验证代码 ...
    
    # 更新允许的 provider 列表
    allowed_providers = ["google", "github", "api", "email", "wechat", "wecom"]
    if provider not in allowed_providers:
        logging.error("无效的 provider: %s", provider)
        return False, None
    
    return None
```

### 3.4 OAuth 回调处理器 (api/auth/oauth_handlers.py)

现有的 `handle_callback()` 函数已经是通用的,可以直接处理微信和企业微信的回调,无需修改。

---

## 4. 数据模型

### 4.1 Identity 节点扩展

FalkorDB 中的 Identity 节点将支持微信和企业微信的属性:

```cypher
// 微信用户 Identity 节点
(identity:Identity {
    provider: "wechat",
    provider_user_id: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",  // OpenID
    email: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local",
    name: "张三",
    picture: "http://thirdwx.qlogo.cn/mmopen/...",
    unionid: "o6_bmasdasdsad6_2sgVt7hMZOPfL",  // 可选,用于跨应用识别
    created_at: 1704067200000,
    last_login: 1704067200000
})

// 企业微信用户 Identity 节点
(identity:Identity {
    provider: "wecom",
    provider_user_id: "zhangsan",  // UserID
    email: "zhangsan@company.com",
    name: "张三",
    picture: "https://wework.qpic.cn/...",
    corp_id: "ww1234567890abcdef",  // 企业ID
    department: [1, 2],  // 部门ID列表
    created_at: 1704067200000,
    last_login: 1704067200000
})
```

### 4.2 用户唯一标识策略

**微信登录**:
- 主键: `provider="wechat"` + `provider_user_id=openid`
- 如果用户没有提供邮箱,使用虚拟邮箱: `{openid}@wechat.queryweaver.local`
- 如果有 UnionID,可以用于关联同一用户在不同微信应用中的身份

**企业微信登录**:
- 主键: `provider="wecom"` + `provider_user_id=userid`
- 优先使用企业邮箱作为 email
- 记录企业ID (corp_id) 和部门信息 (department)

### 4.3 数据库查询示例

```cypher
// 创建微信用户
MERGE (user:User {email: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local"})
ON CREATE SET
    user.first_name = "张",
    user.last_name = "三",
    user.created_at = timestamp()

MERGE (identity:Identity {
    provider: "wechat",
    provider_user_id: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M"
})
ON CREATE SET
    identity.email = "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local",
    identity.name = "张三",
    identity.picture = "http://thirdwx.qlogo.cn/...",
    identity.unionid = "o6_bmasdasdsad6_2sgVt7hMZOPfL",
    identity.created_at = timestamp(),
    identity.last_login = timestamp()

MERGE (identity)-[:AUTHENTICATES]->(user)
```

---


## 5. 正确性属性 (Correctness Properties)

*属性 (Property) 是一个特征或行为,应该在系统的所有有效执行中保持为真。属性是人类可读规范和机器可验证正确性保证之间的桥梁。*

基于需求文档中的验收标准,我们定义以下正确性属性:

### 5.1 授权 URL 生成属性

**属性 1: 微信授权 URL 包含必需参数**

*对于任何*微信登录请求,生成的授权 URL 必须包含 `appid`、`redirect_uri`、`response_type=code`、`scope=snsapi_userinfo` 和 `state` 参数

**验证需求: 2.1.2.2, 2.1.2.6**

**属性 2: 企业微信授权 URL 包含必需参数**

*对于任何*企业微信登录请求,生成的授权 URL 必须包含 `corpid`、`redirect_uri`、`response_type=code`、`scope=snsapi_base`、`agentid` 和 `state` 参数

**验证需求: 2.2.2.2, 2.2.2.6**

### 5.2 用户创建和识别属性

**属性 3: 首次登录创建用户**

*对于任何*新的微信或企业微信用户 (provider + provider_user_id 组合不存在),系统必须在 FalkorDB 中创建新的 User 和 Identity 节点,并建立 AUTHENTICATES 关系

**验证需求: 2.1.2.4, 2.2.2.4**

**属性 4: 重复登录识别用户**

*对于任何*已存在的微信或企业微信用户 (provider + provider_user_id 组合已存在),系统必须正确识别并更新 last_login 时间戳,而不是创建新用户

**验证需求: 2.1.2.5, 2.2.2.5**

### 5.3 用户信息获取属性

**属性 5: 微信用户信息完整性**

*对于任何*成功的微信授权回调,系统必须获取并存储用户的 openid、nickname 和 headimgurl (如果可用)

**验证需求: 2.1.2.8**

**属性 6: 企业微信用户信息完整性**

*对于任何*成功的企业微信授权回调,系统必须获取并存储用户的 userid、name、avatar 和 department (如果可用)

**验证需求: 2.2.2.8**

### 5.4 CSRF 防护属性

**属性 7: State 参数生成和验证**

*对于任何*OAuth 授权请求,系统必须生成随机的 state 参数,并在回调时验证该参数匹配,防止 CSRF 攻击

**验证需求: 3.1.3**

### 5.5 Token 管理属性

**属性 8: API Token 有效期设置**

*对于任何*成功的登录,系统必须生成 API Token 并设置 24 小时的过期时间 (expires_at = timestamp() + 86400000)

**验证需求: 3.1.4**

**属性 9: Token 与 Identity 关联**

*对于任何*生成的 API Token,系统必须在 FalkorDB 中创建 Token 节点,并建立 Identity-[:HAS_TOKEN]->Token 关系

**验证需求: 3.1.4**

### 5.6 错误处理属性

**属性 10: 配置缺失时返回友好错误**

*对于任何*微信或企业微信登录请求,如果相应的环境变量未配置,系统必须返回 404 状态码和中文错误提示

**验证需求: 2.1.2.9, 2.2.2.9**

**属性 11: 授权失败时返回友好错误**

*对于任何*OAuth 回调失败 (如 code 无效、网络错误),系统必须捕获异常并返回 400 状态码和中文错误提示

**验证需求: 2.1.2.9, 2.2.2.9**

### 5.7 日志记录属性

**属性 12: 登录操作日志记录**

*对于任何*登录尝试 (成功或失败),系统必须记录结构化日志,包含 provider、user_id、timestamp 和操作结果

**验证需求: 3.1.6**

### 5.8 配置安全属性

**属性 13: 敏感配置从环境变量读取**

*对于所有*OAuth 配置 (AppSecret、CorpSecret),系统必须从环境变量读取,而不是硬编码在代码中

**验证需求: 3.1.2**

---

## 6. 错误处理

### 6.1 错误分类和处理策略

| 错误类型 | HTTP 状态码 | 错误消息 | 处理方式 |
|---------|-----------|---------|---------|
| 配置缺失 | 404 | "微信登录未配置" | 记录警告日志,返回错误响应 |
| 授权被拒绝 | 400 | "用户取消授权" | 记录信息日志,重定向到登录页 |
| Code 无效 | 400 | "授权码无效或已过期" | 记录警告日志,重定向到登录页 |
| 网络超时 | 400 | "网络连接失败,请重试" | 记录错误日志,重定向到登录页 |
| Token 获取失败 | 400 | "获取访问令牌失败" | 记录错误日志,重定向到登录页 |
| 用户信息获取失败 | 400 | "获取用户信息失败" | 记录错误日志,重定向到登录页 |
| 数据库错误 | 500 | "系统内部错误" | 记录异常日志,返回 500 |
| 未知错误 | 500 | "认证失败,请稍后重试" | 记录异常日志,返回 500 |

### 6.2 错误日志格式

```python
# 成功登录日志
logger.info(json.dumps({
    "event": "oauth_login_success",
    "provider": "wechat",  # 或 "wecom"
    "provider_user_id": "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",
    "email": "user@example.com",
    "new_user": True,  # 是否是新用户
    "timestamp": datetime.now().isoformat()
}))

# 失败登录日志
logger.error(json.dumps({
    "event": "oauth_login_failed",
    "provider": "wechat",
    "error_type": "token_exchange_failed",
    "error_message": "Invalid code",
    "timestamp": datetime.now().isoformat()
}))
```

### 6.3 微信 API 错误码映射

```python
WECHAT_ERROR_MESSAGES = {
    40001: "AppSecret 错误,请检查配置",
    40013: "AppID 无效,请检查配置",
    40029: "授权码无效或已过期",
    40163: "授权码已被使用",
    41001: "缺少 access_token 参数",
    42001: "access_token 已过期",
    42007: "用户修改微信密码,access_token 已失效",
}

def _handle_wechat_error(error_code: int) -> str:
    """将微信错误码转换为用户友好的错误消息"""
    return WECHAT_ERROR_MESSAGES.get(error_code, "微信服务异常,请稍后重试")
```

---

## 7. 测试策略

### 7.1 测试方法

本功能采用**双重测试方法**:

1. **单元测试**: 验证具体示例、边缘情况和错误条件
2. **属性测试**: 验证跨所有输入的通用属性

两者是互补的,共同确保全面覆盖:
- 单元测试捕获具体的 bug
- 属性测试验证通用正确性

### 7.2 单元测试范围

**配置测试**:
- 测试 `_is_wechat_auth_enabled()` 在不同环境变量配置下的返回值
- 测试 `_is_wecom_auth_enabled()` 在不同环境变量配置下的返回值

**路由测试**:
- 测试 `/login/wechat` 在配置缺失时返回 404
- 测试 `/login/wecom` 在配置缺失时返回 404
- 测试授权 URL 重定向的正确性

**回调处理测试**:
- 测试有效 code 的处理流程
- 测试无效 code 的错误处理
- 测试用户信息解析的正确性

**用户管理测试**:
- 测试新用户创建逻辑
- 测试已有用户识别逻辑
- 测试虚拟邮箱生成逻辑

**错误处理测试**:
- 测试各种错误场景的错误消息
- 测试日志记录的完整性

### 7.3 属性测试配置

**测试库**: pytest + hypothesis (Python 属性测试库)

**测试配置**:
```python
# 每个属性测试至少运行 100 次迭代
@settings(max_examples=100)
@given(...)
def test_property_...():
    pass
```

**测试标签格式**:
```python
# Feature: wechat-oauth, Property 1: 微信授权 URL 包含必需参数
@pytest.mark.property
def test_wechat_authorize_url_contains_required_params():
    """
    属性测试: 验证微信授权 URL 包含所有必需参数
    
    对于任何微信登录请求,生成的授权 URL 必须包含:
    - appid
    - redirect_uri
    - response_type=code
    - scope=snsapi_userinfo
    - state (随机生成的 CSRF token)
    """
    pass
```

### 7.4 集成测试

**测试场景**:
1. 完整的微信登录流程 (使用 mock 微信 API)
2. 完整的企业微信登录流程 (使用 mock 企业微信 API)
3. 首次登录创建用户
4. 重复登录识别用户
5. 跨 provider 账号关联 (同一邮箱)
6. Token 过期处理
7. 并发登录请求

### 7.5 端到端测试

**测试工具**: Playwright

**测试场景**:
1. PC 端微信扫码登录 (需要真实微信测试账号)
2. 移动端微信内置浏览器登录
3. PC 端企业微信扫码登录
4. 移动端企业微信内置浏览器登录
5. 登录后访问受保护资源
6. 登出后重新登录

---


## 8. 前端集成

### 8.1 登录按钮组件

在前端登录页面添加微信和企业微信登录按钮:

```typescript
// app/src/components/LoginButtons.tsx

interface LoginButtonsProps {
  wechatEnabled: boolean;
  wecomEnabled: boolean;
}

export function LoginButtons({ wechatEnabled, wecomEnabled }: LoginButtonsProps) {
  const handleWechatLogin = () => {
    window.location.href = '/login/wechat';
  };

  const handleWecomLogin = () => {
    window.location.href = '/login/wecom';
  };

  return (
    <div className="space-y-3">
      {/* 现有的 Google 和 GitHub 按钮 */}
      
      {wechatEnabled && (
        <button
          onClick={handleWechatLogin}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <WechatIcon className="w-5 h-5" />
          <span>使用微信登录</span>
        </button>
      )}
      
      {wecomEnabled && (
        <button
          onClick={handleWecomLogin}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <WecomIcon className="w-5 h-5" />
          <span>使用企业微信登录</span>
        </button>
      )}
    </div>
  );
}
```

### 8.2 认证状态检查

更新 `/auth-status` 端点的响应,包含微信和企业微信的配置状态:

```python
@auth_router.get("/auth-status")
async def auth_status(request: Request) -> JSONResponse:
    """检查认证状态和可用的登录方式"""
    user_info, is_authenticated = await validate_user(request)
    
    auth_config = {
        "google_enabled": _is_google_auth_enabled(),
        "github_enabled": _is_github_auth_enabled(),
        "wechat_enabled": _is_wechat_auth_enabled(),
        "wecom_enabled": _is_wecom_auth_enabled(),
        "email_enabled": _is_email_auth_enabled(),
    }
    
    if is_authenticated and user_info:
        return JSONResponse(
            content={
                "authenticated": True,
                "user": {
                    "id": str(user_info.get("id")),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "provider": user_info.get("provider")
                },
                "auth_config": auth_config
            }
        )
    
    return JSONResponse(
        content={
            "authenticated": False,
            "auth_config": auth_config
        },
        status_code=200
    )
```

### 8.3 扫码登录页面 (可选)

对于 PC 端,可以提供专门的扫码登录页面:

```typescript
// app/src/pages/WechatQRLogin.tsx

export function WechatQRLogin() {
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [status, setStatus] = useState<'loading' | 'ready' | 'scanning' | 'success' | 'error'>('loading');

  useEffect(() => {
    // 生成微信登录二维码
    // 注意: 这需要微信开放平台的网站应用支持
    const generateQRCode = async () => {
      try {
        // 调用后端 API 生成二维码
        const response = await fetch('/api/wechat/qrcode');
        const data = await response.json();
        setQrCodeUrl(data.qrcode_url);
        setStatus('ready');
        
        // 轮询检查扫码状态
        pollScanStatus(data.ticket);
      } catch (error) {
        setStatus('error');
      }
    };

    generateQRCode();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="bg-white p-8 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold text-center mb-6">
          使用微信扫码登录
        </h2>
        
        {status === 'loading' && <LoadingSpinner />}
        
        {status === 'ready' && (
          <div className="flex flex-col items-center">
            <img src={qrCodeUrl} alt="微信登录二维码" className="w-64 h-64" />
            <p className="mt-4 text-gray-600">请使用微信扫描二维码登录</p>
          </div>
        )}
        
        {status === 'scanning' && (
          <div className="text-center">
            <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto" />
            <p className="mt-4 text-gray-600">扫码成功,请在手机上确认登录</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="text-center">
            <XCircleIcon className="w-16 h-16 text-red-500 mx-auto" />
            <p className="mt-4 text-gray-600">二维码加载失败</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              刷新重试
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 9. 配置管理

### 9.1 环境变量

在 `.env` 文件中添加以下配置:

```bash
# 微信登录配置
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_wechat_app_secret

# 企业微信登录配置
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=your_wecom_corp_secret

# OAuth 回调 URL 基础地址 (可选,默认使用 request.base_url)
OAUTH_BASE_URL=https://your-domain.com
```

### 9.2 配置验证

在应用启动时验证配置的完整性:

```python
def validate_oauth_config():
    """验证 OAuth 配置的完整性"""
    warnings = []
    
    # 检查微信配置
    if os.getenv("WECHAT_APP_ID") and not os.getenv("WECHAT_APP_SECRET"):
        warnings.append("WECHAT_APP_ID 已设置但缺少 WECHAT_APP_SECRET")
    
    if os.getenv("WECHAT_APP_SECRET") and not os.getenv("WECHAT_APP_ID"):
        warnings.append("WECHAT_APP_SECRET 已设置但缺少 WECHAT_APP_ID")
    
    # 检查企业微信配置
    wecom_vars = [
        os.getenv("WECOM_CORP_ID"),
        os.getenv("WECOM_AGENT_ID"),
        os.getenv("WECOM_CORP_SECRET")
    ]
    if any(wecom_vars) and not all(wecom_vars):
        warnings.append("企业微信配置不完整,需要 WECOM_CORP_ID, WECOM_AGENT_ID 和 WECOM_CORP_SECRET")
    
    # 输出警告
    for warning in warnings:
        logging.warning("配置警告: %s", warning)
    
    return len(warnings) == 0
```

### 9.3 配置文档

在 `README.md` 中添加配置说明:

```markdown
## 微信登录配置

### 1. 注册微信开放平台账号

访问 [微信开放平台](https://open.weixin.qq.com/) 注册账号并创建网站应用。

### 2. 配置授权回调域名

在微信开放平台的应用设置中,配置授权回调域名为你的应用域名,例如:
- `https://your-domain.com`

### 3. 获取 AppID 和 AppSecret

在应用详情页面获取 AppID 和 AppSecret。

### 4. 配置环境变量

在 `.env` 文件中添加:

```bash
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

### 5. 重启应用

重启 QueryWeaver 应用,微信登录按钮将自动显示。

## 企业微信登录配置

### 1. 注册企业微信

访问 [企业微信](https://work.weixin.qq.com/) 注册企业账号。

### 2. 创建自建应用

在企业微信管理后台,创建自建应用或第三方应用。

### 3. 配置可信域名

在应用设置中,配置可信域名为你的应用域名。

### 4. 获取配置信息

获取以下信息:
- CorpID (企业ID)
- AgentID (应用ID)
- CorpSecret (应用密钥)

### 5. 配置环境变量

在 `.env` 文件中添加:

```bash
WECOM_CORP_ID=your_corp_id
WECOM_AGENT_ID=your_agent_id
WECOM_CORP_SECRET=your_corp_secret
```

### 6. 重启应用

重启 QueryWeaver 应用,企业微信登录按钮将自动显示。
```

---

## 10. 安全考虑

### 10.1 CSRF 防护

使用 state 参数防止 CSRF 攻击:

```python
import secrets

def generate_state() -> str:
    """生成随机的 state 参数用于 CSRF 防护"""
    return secrets.token_urlsafe(32)

def verify_state(request: Request, state: str) -> bool:
    """验证 state 参数"""
    # 从 session 或 cookie 中获取原始 state
    original_state = request.session.get('oauth_state')
    return original_state and hmac.compare_digest(original_state, state)
```

### 10.2 敏感信息保护

- AppSecret 和 CorpSecret 必须通过环境变量配置,不能硬编码
- 日志中不能记录完整的 access_token 和用户敏感信息
- 使用 HTTPS 传输所有 OAuth 请求

### 10.3 Token 安全

```python
# API Token 生成
api_token = secrets.token_urlsafe(32)  # 生成 256 位随机 token

# Cookie 设置
response.set_cookie(
    key="api_token",
    value=api_token,
    httponly=True,  # 防止 XSS 攻击
    secure=True,    # 仅通过 HTTPS 传输
    samesite="lax", # 防止 CSRF 攻击
    max_age=86400   # 24 小时过期
)
```

### 10.4 输入验证

```python
def validate_oauth_callback(code: str, state: str) -> bool:
    """验证 OAuth 回调参数"""
    # 验证 code 格式
    if not code or len(code) > 512:
        return False
    
    # 验证 state 格式
    if not state or len(state) > 128:
        return False
    
    # 验证 state 匹配
    if not verify_state(request, state):
        return False
    
    return True
```

---

## 11. 性能优化

### 11.1 Token 缓存

缓存微信和企业微信的 access_token,减少 API 调用:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class TokenCache:
    """OAuth Token 缓存"""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存的 token"""
        if key in self._cache:
            token, expires_at = self._cache[key]
            if datetime.now() < expires_at:
                return token
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, token: str, expires_in: int):
        """设置 token 缓存"""
        expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 提前 5 分钟过期
        self._cache[key] = (token, expires_at)

# 全局 token 缓存实例
token_cache = TokenCache()
```

### 11.2 异步请求

使用异步 HTTP 请求提高性能:

```python
import httpx

async def fetch_wechat_user_info(access_token: str, openid: str) -> dict:
    """异步获取微信用户信息"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.weixin.qq.com/sns/userinfo",
            params={
                "access_token": access_token,
                "openid": openid,
                "lang": "zh_CN"
            },
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
```

### 11.3 数据库查询优化

使用索引优化用户查询:

```cypher
// 为 Identity 节点创建索引
CREATE INDEX FOR (i:Identity) ON (i.provider, i.provider_user_id)
CREATE INDEX FOR (i:Identity) ON (i.email)
```

---

## 12. 监控和日志

### 12.1 关键指标

监控以下指标:

1. **登录成功率**: 成功登录次数 / 总登录尝试次数
2. **登录响应时间**: OAuth 回调处理的平均时间
3. **错误率**: 各类错误的发生频率
4. **用户增长**: 新用户注册数量

### 12.2 日志记录

```python
# 结构化日志
logger.info(json.dumps({
    "event": "oauth_login",
    "provider": "wechat",
    "step": "authorize_redirect",
    "user_agent": request.headers.get("user-agent"),
    "ip_address": request.client.host,
    "timestamp": datetime.now().isoformat()
}))
```

### 12.3 告警规则

设置以下告警:

1. 登录错误率 > 10% (5 分钟内)
2. OAuth API 响应时间 > 5 秒
3. 数据库连接失败
4. 配置缺失或无效

---

## 13. 部署清单

### 13.1 微信开放平台配置

- [ ] 注册微信开放平台账号
- [ ] 创建网站应用
- [ ] 配置授权回调域名
- [ ] 获取 AppID 和 AppSecret
- [ ] 提交审核 (需要备案域名)

### 13.2 企业微信配置

- [ ] 注册企业微信
- [ ] 创建自建应用或第三方应用
- [ ] 配置可信域名
- [ ] 获取 CorpID、AgentID 和 CorpSecret
- [ ] 配置应用权限

### 13.3 应用配置

- [ ] 配置环境变量
- [ ] 验证 HTTPS 证书
- [ ] 测试 OAuth 回调 URL 可访问性
- [ ] 运行配置验证脚本

### 13.4 测试清单

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 端到端测试通过
- [ ] 性能测试通过
- [ ] 安全扫描通过

---

## 14. 文档更新

### 14.1 用户文档

- [ ] 添加微信登录使用指南
- [ ] 添加企业微信登录使用指南
- [ ] 更新常见问题解答
- [ ] 添加故障排查指南

### 14.2 开发文档

- [ ] 更新 API 文档
- [ ] 更新架构图
- [ ] 添加代码示例
- [ ] 更新贡献指南

### 14.3 运维文档

- [ ] 添加配置说明
- [ ] 添加监控指标说明
- [ ] 添加告警规则说明
- [ ] 添加故障处理流程

---

## 15. 风险和缓解措施

### 15.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| 微信 API 变更 | 高 | 中 | 监控官方文档,及时适配 |
| 网络不稳定 | 中 | 中 | 实现重试机制,增加超时时间 |
| 证书过期 | 高 | 低 | 设置证书过期告警 |
| 并发性能问题 | 中 | 低 | 负载测试,优化数据库查询 |

### 15.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| 审核延迟 | 中 | 高 | 提前申请,准备备用方案 |
| 域名备案问题 | 高 | 中 | 使用已备案域名 |
| 用户隐私投诉 | 高 | 低 | 遵守隐私政策,最小化数据收集 |
| 账号关联错误 | 中 | 低 | 完善测试,提供账号解绑功能 |

---

## 16. 未来扩展

### 16.1 短期扩展 (1-3 个月)

- 支持微信小程序登录
- 支持企业微信第三方应用
- 添加账号绑定/解绑功能
- 支持多账号关联

### 16.2 中期扩展 (3-6 个月)

- 支持钉钉登录
- 支持飞书登录
- 添加社交账号管理页面
- 支持账号合并

### 16.3 长期扩展 (6-12 个月)

- 支持 SAML 2.0
- 支持 LDAP
- 企业级 SSO 集成
- 多因素认证 (MFA)

---

## 附录 A: 微信 API 参考

### A.1 授权 URL

```
https://open.weixin.qq.com/connect/oauth2/authorize?appid=APPID&redirect_uri=REDIRECT_URI&response_type=code&scope=SCOPE&state=STATE#wechat_redirect
```

### A.2 获取 Access Token

```
GET https://api.weixin.qq.com/sns/oauth2/access_token?appid=APPID&secret=SECRET&code=CODE&grant_type=authorization_code
```

### A.3 获取用户信息

```
GET https://api.weixin.qq.com/sns/userinfo?access_token=ACCESS_TOKEN&openid=OPENID&lang=zh_CN
```

## 附录 B: 企业微信 API 参考

### B.1 授权 URL

```
https://open.weixin.qq.com/connect/oauth2/authorize?appid=CORPID&redirect_uri=REDIRECT_URI&response_type=code&scope=SCOPE&agentid=AGENTID&state=STATE#wechat_redirect
```

### B.2 获取 Access Token

```
GET https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=CORPID&corpsecret=SECRET
```

### B.3 获取用户信息

```
GET https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo?access_token=ACCESS_TOKEN&code=CODE
```

