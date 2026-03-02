# 微信和企业微信 OAuth 登录设计文档

## 1. 概述

本文档描述了为 QueryWeaver 添加微信（WeChat）和企业微信（WeCom）OAuth 2.0 登录功能的详细设计方案。该功能将与现有的 Google 和 GitHub OAuth 登录保持一致的架构模式，使用 FastAPI + Authlib 实现后端认证，React 实现前端界面。

### 1.1 设计目标

- **统一架构**: 与现有 OAuth 提供商（Google/GitHub）保持一致的代码结构
- **安全可靠**: 实现完整的 OAuth 2.0 安全机制，包括 CSRF 防护和 Token 管理
- **用户友好**: 提供流畅的登录体验，支持 PC 扫码和移动端直接授权
- **可扩展性**: 设计易于添加更多 OAuth 提供商的架构
- **可测试性**: 所有核心逻辑都可以通过单元测试和属性测试验证

### 1.2 技术栈

- **后端**: Python 3.12+, FastAPI 0.131.0, Authlib 1.6.4
- **前端**: React 18.3.1, TypeScript 5.8.3
- **数据库**: FalkorDB 1.6.0 (图数据库)
- **HTTP 客户端**: httpx (异步 HTTP 请求)

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Google 登录  │  │ GitHub 登录  │  │  微信登录    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐                                           │
│  │ 企业微信登录 │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              OAuth 路由层 (auth.py)                   │  │
│  │  /login/wechat  /login/wecom                         │  │
│  │  /login/wechat/authorized  /login/wecom/authorized   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         OAuth 处理器层 (oauth_handlers.py)           │  │
│  │  - WeChatOAuthHandler                                │  │
│  │  - WeComOAuthHandler                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         用户管理层 (user_management.py)              │  │
│  │  - ensure_user_in_organizations()                    │  │
│  │  - update_identity_last_login()                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Cypher
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   FalkorDB (图数据库)                        │
│  (User) ←─[:AUTHENTICATES]─ (Identity)                     │
└─────────────────────────────────────────────────────────────┘


### 2.2 OAuth 2.0 流程

#### 2.2.1 微信登录流程

```
用户                前端              后端              微信服务器         FalkorDB
 │                  │                 │                    │                 │
 │  点击微信登录    │                 │                    │                 │
 │─────────────────>│                 │                    │                 │
 │                  │  GET /login/wechat                   │                 │
 │                  │────────────────>│                    │                 │
 │                  │                 │ 生成 state (CSRF)  │                 │
 │                  │                 │ 构建授权 URL       │                 │
 │                  │<────────────────│                    │                 │
 │                  │  302 重定向     │                    │                 │
 │<─────────────────│                 │                    │                 │
 │                                    │                    │                 │
 │  扫码/授权                          │                    │                 │
 │────────────────────────────────────────────────────────>│                 │
 │                                    │                    │                 │
 │  回调 /login/wechat/authorized?code=xxx&state=xxx       │                 │
 │────────────────────────────────────>│                    │                 │
 │                                    │  验证 state        │                 │
 │                                    │  用 code 换 token  │                 │
 │                                    │───────────────────>│                 │
 │                                    │<───────────────────│                 │
 │                                    │  access_token      │                 │
 │                                    │                    │                 │
 │                                    │  获取用户信息      │                 │
 │                                    │───────────────────>│                 │
 │                                    │<───────────────────│                 │
 │                                    │  用户信息          │                 │
 │                                    │                    │                 │
 │                                    │  创建/更新用户     │                 │
 │                                    │────────────────────────────────────>│
 │                                    │<────────────────────────────────────│
 │                                    │  生成 API Token    │                 │
 │                                    │  设置 Cookie       │                 │
 │<────────────────────────────────────│                    │                 │
 │  302 重定向到首页                   │                    │                 │
```

#### 2.2.2 企业微信登录流程

企业微信的流程与微信类似，主要区别在于：
1. 使用不同的 API 端点（qyapi.weixin.qq.com）
2. 需要 CorpID 和 AgentID
3. 用户标识使用 UserID 而不是 OpenID
4. 可以获取部门信息

---

## 3. 组件设计

### 3.1 配置模块 (config.py)

#### 3.1.1 微信配置

```python
# api/config.py

# 微信 OAuth 配置
WECHAT_CONFIG = {
    "app_id": os.getenv("WECHAT_APP_ID"),
    "app_secret": os.getenv("WECHAT_APP_SECRET"),
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
    "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    "scope": "snsapi_userinfo",
    "response_type": "code"
}

# 企业微信 OAuth 配置
WECOM_CONFIG = {
    "corp_id": os.getenv("WECOM_CORP_ID"),
    "agent_id": os.getenv("WECOM_AGENT_ID"),
    "corp_secret": os.getenv("WECOM_CORP_SECRET"),
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
    "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
    "scope": "snsapi_base"
}


def _is_wechat_auth_enabled() -> bool:
    """检查微信登录是否启用"""
    return bool(WECHAT_CONFIG.get("app_id") and WECHAT_CONFIG.get("app_secret"))

def _is_wecom_auth_enabled() -> bool:
    """检查企业微信登录是否启用"""
    return bool(
        WECOM_CONFIG.get("corp_id") 
        and WECOM_CONFIG.get("corp_secret")
        and WECOM_CONFIG.get("agent_id")
    )
```

#### 3.1.2 配置验证

```python
def validate_wechat_config() -> None:
    """
    验证微信配置的完整性
    
    Raises:
        ValueError: 当配置不完整时抛出
    """
    if not WECHAT_CONFIG.get("app_id"):
        raise ValueError("缺少 WECHAT_APP_ID 环境变量")
    if not WECHAT_CONFIG.get("app_secret"):
        raise ValueError("缺少 WECHAT_APP_SECRET 环境变量")

def validate_wecom_config() -> None:
    """
    验证企业微信配置的完整性
    
    Raises:
        ValueError: 当配置不完整时抛出
    """
    if not WECOM_CONFIG.get("corp_id"):
        raise ValueError("缺少 WECOM_CORP_ID 环境变量")
    if not WECOM_CONFIG.get("corp_secret"):
        raise ValueError("缺少 WECOM_CORP_SECRET 环境变量")
    if not WECOM_CONFIG.get("agent_id"):
        raise ValueError("缺少 WECOM_AGENT_ID 环境变量")
```

---

### 3.2 OAuth 处理器模块 (oauth_handlers.py)

#### 3.2.1 微信 OAuth 处理器

```python
# api/auth/oauth_handlers.py

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeChatOAuthHandler:
    """微信 OAuth 2.0 处理器"""
    
    def __init__(self, config: Dict[str, str]):
        """
        初始化微信 OAuth 处理器
        
        Args:
            config: 微信配置字典，包含 app_id, app_secret 等
        """
        self.app_id = config["app_id"]
        self.app_secret = config["app_secret"]
        self.authorize_url = config["authorize_url"]
        self.access_token_url = config["access_token_url"]
        self.userinfo_url = config["userinfo_url"]
        self.scope = config["scope"]
        
        # Token 缓存（避免频繁请求）
        self._token_cache: Optional[Dict[str, Any]] = None
        self._token_expire_time: Optional[datetime] = None
    
    def build_authorize_url(self, redirect_uri: str, state: str) -> str:
        """
        构建微信授权 URL
        
        Args:
            redirect_uri: 回调 URL
            state: CSRF 防护 token
            
        Returns:
            完整的授权 URL
        """
        params = {
            "appid": self.app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state
        }
        
        # 构建查询字符串
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.authorize_url}?{query_string}#wechat_redirect"
        
        logger.info(f"构建微信授权 URL: {url}")
        return url
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        使用授权码换取 access_token
        
        Args:
            code: 微信返回的授权码
            
        Returns:
            包含 access_token, openid 等信息的字典
            
        Raises:
            HTTPException: 当请求失败时抛出
        """
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.access_token_url,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                # 检查微信 API 错误
                if "errcode" in data:
                    error_msg = f"微信 API 错误: {data.get('errmsg', '未知错误')}"
                    logger.error(f"{error_msg}, errcode: {data['errcode']}")
                    raise ValueError(error_msg)
                
                # 缓存 token
                self._token_cache = data
                self._token_expire_time = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 7200)
                )
                
                logger.info(f"成功获取微信 access_token, openid: {data.get('openid')}")
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"请求微信 access_token 失败: {str(e)}")
                raise
    
    async def get_user_info(
        self, 
        access_token: str, 
        openid: str
    ) -> Dict[str, Any]:
        """
        获取微信用户信息
        
        Args:
            access_token: 访问令牌
            openid: 用户的 OpenID
            
        Returns:
            用户信息字典，包含 nickname, headimgurl 等
            
        Raises:
            HTTPException: 当请求失败时抛出
        """
        params = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.userinfo_url,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                # 检查微信 API 错误
                if "errcode" in data:
                    error_msg = f"获取用户信息失败: {data.get('errmsg', '未知错误')}"
                    logger.error(f"{error_msg}, errcode: {data['errcode']}")
                    raise ValueError(error_msg)
                
                logger.info(f"成功获取微信用户信息, openid: {openid}")
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"请求微信用户信息失败: {str(e)}")
                raise
    
    def parse_user_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析微信用户信息为标准格式
        
        Args:
            user_data: 微信返回的原始用户数据
            
        Returns:
            标准化的用户信息字典
        """
        return {
            "id": user_data.get("openid"),
            "email": f"{user_data.get('openid')}@wechat.queryweaver.local",
            "name": user_data.get("nickname", "微信用户"),
            "picture": user_data.get("headimgurl"),
            "unionid": user_data.get("unionid"),  # 可选
            "provider": "wechat"
        }
```

#### 3.2.2 企业微信 OAuth 处理器

```python
class WeComOAuthHandler:
    """企业微信 OAuth 2.0 处理器"""
    
    def __init__(self, config: Dict[str, str]):
        """
        初始化企业微信 OAuth 处理器
        
        Args:
            config: 企业微信配置字典
        """
        self.corp_id = config["corp_id"]
        self.agent_id = config["agent_id"]
        self.corp_secret = config["corp_secret"]
        self.authorize_url = config["authorize_url"]
        self.access_token_url = config["access_token_url"]
        self.userinfo_url = config["userinfo_url"]
        self.user_detail_url = config["user_detail_url"]
        self.scope = config["scope"]
        
        # Token 缓存
        self._access_token: Optional[str] = None
        self._token_expire_time: Optional[datetime] = None
    
    def build_authorize_url(self, redirect_uri: str, state: str) -> str:
        """
        构建企业微信授权 URL
        
        Args:
            redirect_uri: 回调 URL
            state: CSRF 防护 token
            
        Returns:
            完整的授权 URL
        """
        params = {
            "appid": self.corp_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "agentid": self.agent_id,
            "state": state
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.authorize_url}?{query_string}#wechat_redirect"
        
        logger.info(f"构建企业微信授权 URL: {url}")
        return url
    
    async def get_access_token(self) -> str:
        """
        获取企业微信 access_token（企业内部应用）
        
        Returns:
            access_token 字符串
            
        Raises:
            HTTPException: 当请求失败时抛出
        """
        # 检查缓存
        if (self._access_token 
            and self._token_expire_time 
            and datetime.now() < self._token_expire_time):
            return self._access_token
        
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.access_token_url,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    error_msg = f"企业微信 API 错误: {data.get('errmsg', '未知错误')}"
                    logger.error(f"{error_msg}, errcode: {data.get('errcode')}")
                    raise ValueError(error_msg)
                
                # 缓存 token（提前 5 分钟过期）
                self._access_token = data["access_token"]
                self._token_expire_time = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 7200) - 300
                )
                
                logger.info("成功获取企业微信 access_token")
                return self._access_token
                
            except httpx.HTTPError as e:
                logger.error(f"请求企业微信 access_token 失败: {str(e)}")
                raise
    
    async def get_user_info(self, code: str) -> Dict[str, Any]:
        """
        使用授权码获取用户信息
        
        Args:
            code: 企业微信返回的授权码
            
        Returns:
            用户信息字典
            
        Raises:
            HTTPException: 当请求失败时抛出
        """
        access_token = await self.get_access_token()
        
        params = {
            "access_token": access_token,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.userinfo_url,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    error_msg = f"获取用户信息失败: {data.get('errmsg', '未知错误')}"
                    logger.error(f"{error_msg}, errcode: {data.get('errcode')}")
                    raise ValueError(error_msg)
                
                user_id = data.get("userid") or data.get("UserId")
                logger.info(f"成功获取企业微信用户信息, userid: {user_id}")
                
                # 获取详细用户信息
                return await self.get_user_detail(user_id)
                
            except httpx.HTTPError as e:
                logger.error(f"请求企业微信用户信息失败: {str(e)}")
                raise
    
    async def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户详细信息
        
        Args:
            user_id: 企业微信用户 ID
            
        Returns:
            详细用户信息字典
        """
        access_token = await self.get_access_token()
        
        params = {
            "access_token": access_token,
            "userid": user_id
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_detail_url,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    error_msg = f"获取用户详情失败: {data.get('errmsg', '未知错误')}"
                    logger.error(f"{error_msg}, errcode: {data.get('errcode')}")
                    raise ValueError(error_msg)
                
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"请求企业微信用户详情失败: {str(e)}")
                raise
    
    def parse_user_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析企业微信用户信息为标准格式
        
        Args:
            user_data: 企业微信返回的原始用户数据
            
        Returns:
            标准化的用户信息字典
        """
        user_id = user_data.get("userid")
        email = user_data.get("email") or f"{user_id}@wecom.queryweaver.local"
        
        return {
            "id": user_id,
            "email": email,
            "name": user_data.get("name", "企业微信用户"),
            "picture": user_data.get("avatar"),
            "corp_id": self.corp_id,
            "department": user_data.get("department", []),
            "provider": "wecom"
        }
```


---

### 3.3 路由模块 (routes/auth.py)

#### 3.3.1 微信登录路由

```python
# api/routes/auth.py

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
import secrets

# 初始化序列化器（用于 state 参数）
serializer = URLSafeTimedSerializer(os.getenv("FASTAPI_SECRET_KEY"))


@router.get("/login/wechat")
async def login_wechat(request: Request) -> RedirectResponse:
    """
    微信登录入口
    
    生成 CSRF token (state) 并重定向到微信授权页面
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向响应到微信授权页面
        
    Raises:
        HTTPException: 当微信登录未配置时抛出 503
    """
    if not _is_wechat_auth_enabled():
        logger.warning("微信登录未配置")
        raise HTTPException(
            status_code=503,
            detail="微信登录功能未启用，请联系管理员配置"
        )
    
    # 生成 CSRF token
    state = serializer.dumps({"provider": "wechat", "nonce": secrets.token_urlsafe(16)})
    
    # 构建回调 URL
    redirect_uri = _build_callback_url(request, "/login/wechat/authorized")
    
    # 初始化微信 OAuth 处理器
    wechat_handler = WeChatOAuthHandler(WECHAT_CONFIG)
    
    # 构建授权 URL
    authorize_url = wechat_handler.build_authorize_url(redirect_uri, state)
    
    # 将 state 存储到 session（用于后续验证）
    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,  # 10 分钟有效期
        httponly=True,
        secure=_is_request_secure(request),
        samesite="lax"
    )
    
    logger.info("用户发起微信登录")
    return response


@router.get("/login/wechat/authorized")
async def wechat_authorized(request: Request) -> RedirectResponse:
    """
    微信 OAuth 回调端点
    
    处理微信授权回调，验证 state，获取用户信息，创建/更新用户
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向响应到首页或错误页面
        
    Raises:
        HTTPException: 当授权失败时抛出
    """
    # 获取查询参数
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # 验证必需参数
    if not code or not state:
        logger.error("微信回调缺少必需参数")
        raise HTTPException(
            status_code=400,
            detail="授权失败：缺少必需参数"
        )
    
    # 验证 state（CSRF 防护）
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        logger.error(f"State 验证失败: stored={stored_state}, received={state}")
        raise HTTPException(
            status_code=400,
            detail="授权失败：安全验证失败，请重试"
        )
    
    try:
        # 验证 state 签名和时效性（10 分钟）
        serializer.loads(state, max_age=600)
    except Exception as e:
        logger.error(f"State 解析失败: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="授权失败：验证令牌已过期，请重新登录"
        )
    
    # 初始化微信 OAuth 处理器
    wechat_handler = WeChatOAuthHandler(WECHAT_CONFIG)
    
    try:
        # 使用 code 换取 access_token
        token_data = await wechat_handler.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        openid = token_data["openid"]
        
        # 获取用户信息
        user_data = await wechat_handler.get_user_info(access_token, openid)
        
        # 解析为标准格式
        user_info = wechat_handler.parse_user_info(user_data)
        
        # 生成 API Token
        api_token = secrets.token_urlsafe(32)
        
        # 调用统一的回调处理器
        success = await request.app.state.callback_handler(
            provider="wechat",
            user_info=user_info,
            api_token=api_token
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="用户信息处理失败"
            )
        
        # 设置认证 Cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="api_token",
            value=api_token,
            max_age=86400 * 365,  # 1 年
            httponly=True,
            secure=_is_request_secure(request),
            samesite="lax"
        )
        
        # 清除 oauth_state cookie
        response.delete_cookie("oauth_state")
        
        logger.info(f"微信登录成功: openid={openid}")
        return response
        
    except ValueError as e:
        # 微信 API 错误
        logger.error(f"微信 OAuth 处理失败: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"登录失败: {str(e)}"
        )
    except Exception as e:
        # 其他未预期错误
        logger.exception(f"微信登录处理异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="登录失败，请稍后重试"
        )
```

#### 3.3.2 企业微信登录路由

```python
@router.get("/login/wecom")
async def login_wecom(request: Request) -> RedirectResponse:
    """
    企业微信登录入口
    
    生成 CSRF token (state) 并重定向到企业微信授权页面
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向响应到企业微信授权页面
        
    Raises:
        HTTPException: 当企业微信登录未配置时抛出 503
    """
    if not _is_wecom_auth_enabled():
        logger.warning("企业微信登录未配置")
        raise HTTPException(
            status_code=503,
            detail="企业微信登录功能未启用，请联系管理员配置"
        )
    
    # 生成 CSRF token
    state = serializer.dumps({"provider": "wecom", "nonce": secrets.token_urlsafe(16)})
    
    # 构建回调 URL
    redirect_uri = _build_callback_url(request, "/login/wecom/authorized")
    
    # 初始化企业微信 OAuth 处理器
    wecom_handler = WeComOAuthHandler(WECOM_CONFIG)
    
    # 构建授权 URL
    authorize_url = wecom_handler.build_authorize_url(redirect_uri, state)
    
    # 将 state 存储到 session
    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=_is_request_secure(request),
        samesite="lax"
    )
    
    logger.info("用户发起企业微信登录")
    return response


@router.get("/login/wecom/authorized")
async def wecom_authorized(request: Request) -> RedirectResponse:
    """
    企业微信 OAuth 回调端点
    
    处理企业微信授权回调，验证 state，获取用户信息，创建/更新用户
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        重定向响应到首页或错误页面
        
    Raises:
        HTTPException: 当授权失败时抛出
    """
    # 获取查询参数
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # 验证必需参数
    if not code or not state:
        logger.error("企业微信回调缺少必需参数")
        raise HTTPException(
            status_code=400,
            detail="授权失败：缺少必需参数"
        )
    
    # 验证 state（CSRF 防护）
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        logger.error(f"State 验证失败: stored={stored_state}, received={state}")
        raise HTTPException(
            status_code=400,
            detail="授权失败：安全验证失败，请重试"
        )
    
    try:
        # 验证 state 签名和时效性
        serializer.loads(state, max_age=600)
    except Exception as e:
        logger.error(f"State 解析失败: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="授权失败：验证令牌已过期，请重新登录"
        )
    
    # 初始化企业微信 OAuth 处理器
    wecom_handler = WeComOAuthHandler(WECOM_CONFIG)
    
    try:
        # 使用 code 获取用户信息
        user_data = await wecom_handler.get_user_info(code)
        
        # 解析为标准格式
        user_info = wecom_handler.parse_user_info(user_data)
        
        # 生成 API Token
        api_token = secrets.token_urlsafe(32)
        
        # 调用统一的回调处理器
        success = await request.app.state.callback_handler(
            provider="wecom",
            user_info=user_info,
            api_token=api_token
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="用户信息处理失败"
            )
        
        # 设置认证 Cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="api_token",
            value=api_token,
            max_age=86400 * 365,
            httponly=True,
            secure=_is_request_secure(request),
            samesite="lax"
        )
        
        # 清除 oauth_state cookie
        response.delete_cookie("oauth_state")
        
        logger.info(f"企业微信登录成功: userid={user_info['id']}")
        return response
        
    except ValueError as e:
        # 企业微信 API 错误
        logger.error(f"企业微信 OAuth 处理失败: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"登录失败: {str(e)}"
        )
    except Exception as e:
        # 其他未预期错误
        logger.exception(f"企业微信登录处理异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="登录失败，请稍后重试"
        )
```

#### 3.3.3 认证状态查询

```python
@router.get("/auth/config")
async def get_auth_config() -> Dict[str, Any]:
    """
    获取认证配置信息
    
    返回可用的登录方式，供前端动态显示登录按钮
    
    Returns:
        认证配置字典
    """
    return {
        "google": _is_google_auth_enabled(),
        "github": _is_github_auth_enabled(),
        "wechat": _is_wechat_auth_enabled(),
        "wecom": _is_wecom_auth_enabled(),
        "email": _is_email_auth_enabled()
    }
```

---

### 3.4 用户管理模块扩展

现有的 `user_management.py` 已经提供了 `ensure_user_in_organizations()` 函数，可以直接复用。只需要确保传入正确的参数：

```python
# 微信用户创建示例
await ensure_user_in_organizations(
    provider_user_id=openid,  # 微信 OpenID
    email=f"{openid}@wechat.queryweaver.local",  # 虚拟邮箱
    name="张三",  # 用户昵称
    provider="wechat",
    api_token=api_token,
    picture="https://..."  # 头像 URL
)

# 企业微信用户创建示例
await ensure_user_in_organizations(
    provider_user_id=userid,  # 企业微信 UserID
    email="zhangsan@company.com",  # 企业邮箱
    name="张三",
    provider="wecom",
    api_token=api_token,
    picture="https://..."
)
```

---

## 4. 数据模型设计

### 4.1 FalkorDB 图数据模型

#### 4.1.1 Identity 节点（微信）

```cypher
(identity:Identity {
    provider: "wechat",
    provider_user_id: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M",  # OpenID
    email: "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local",
    name: "张三",
    picture: "http://thirdwx.qlogo.cn/mmopen/...",
    unionid: "o6_bmasdasdsad6_2sgVt7hMZOPfL",  # 可选
    created_at: 1704067200000,
    last_login: 1704153600000
})
```

#### 4.1.2 Identity 节点（企业微信）

```cypher
(identity:Identity {
    provider: "wecom",
    provider_user_id: "ZhangSan",  # UserID
    email: "zhangsan@company.com",
    name: "张三",
    picture: "https://wework.qpic.cn/...",
    corp_id: "ww1234567890abcdef",
    department: "[1, 2]",  # JSON 字符串
    created_at: 1704067200000,
    last_login: 1704153600000
})
```

#### 4.1.3 关系模型

```cypher
(identity:Identity)-[:AUTHENTICATES]->(user:User)
```

### 4.2 用户唯一标识策略

#### 4.2.1 微信用户

- **主键**: `provider="wechat"` + `provider_user_id=openid`
- **UnionID 处理**: 如果有 UnionID，可以用于关联同一用户在不同微信应用的身份
- **虚拟邮箱**: `{openid}@wechat.queryweaver.local`

#### 4.2.2 企业微信用户

- **主键**: `provider="wecom"` + `provider_user_id=userid`
- **企业隔离**: 通过 `corp_id` 区分不同企业
- **真实邮箱**: 优先使用企业邮箱

---

## 5. 错误处理设计

### 5.1 错误分类

#### 5.1.1 配置错误（500）

```python
# 示例：缺少必需配置
if not WECHAT_CONFIG.get("app_id"):
    raise HTTPException(
        status_code=503,
        detail="微信登录功能未启用，请联系管理员配置"
    )
```

#### 5.1.2 用户操作错误（400）

```python
# 示例：用户取消授权
if not code:
    raise HTTPException(
        status_code=400,
        detail="您已取消登录"
    )
```

#### 5.1.3 微信 API 错误（400）

```python
# 微信错误码映射
WECHAT_ERROR_MESSAGES = {
    40001: "AppSecret 错误，请联系管理员",
    40013: "AppID 无效，请联系管理员",
    40029: "授权码无效，请重新登录",
    40163: "授权码已使用，请重新登录",
    41001: "缺少 access_token，请重新登录",
    42001: "access_token 已过期，请重新登录",
    42007: "用户修改微信密码，access_token 已失效，请重新登录"
}

def get_wechat_error_message(errcode: int) -> str:
    """获取友好的错误消息"""
    return WECHAT_ERROR_MESSAGES.get(
        errcode,
        f"微信服务错误（错误码：{errcode}），请稍后重试"
    )
```

### 5.2 日志记录

```python
# 成功日志
logger.info(json.dumps({
    "event": "oauth_login_success",
    "provider": "wechat",
    "user_id": openid,
    "timestamp": datetime.now().isoformat()
}))

# 错误日志
logger.error(json.dumps({
    "event": "oauth_login_failed",
    "provider": "wechat",
    "error_code": errcode,
    "error_message": errmsg,
    "timestamp": datetime.now().isoformat()
}))
```

---

## 6. 安全设计

### 6.1 CSRF 防护

使用 `state` 参数防止 CSRF 攻击：

```python
# 生成 state
state = serializer.dumps({
    "provider": "wechat",
    "nonce": secrets.token_urlsafe(16),
    "timestamp": datetime.now().isoformat()
})

# 验证 state
try:
    data = serializer.loads(state, max_age=600)  # 10 分钟有效期
except SignatureExpired:
    raise HTTPException(status_code=400, detail="验证令牌已过期")
```

### 6.2 密钥管理

```python
# 从环境变量读取密钥（不硬编码）
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET")
WECOM_CORP_SECRET = os.getenv("WECOM_CORP_SECRET")

# 日志中脱敏
logger.info(f"AppSecret: {WECHAT_APP_SECRET[:4]}****")
```

### 6.3 Token 安全

```python
# 生成安全的 API Token
api_token = secrets.token_urlsafe(32)  # 256 位随机性

# 设置安全的 Cookie
response.set_cookie(
    key="api_token",
    value=api_token,
    max_age=86400 * 365,
    httponly=True,  # 防止 XSS
    secure=True,    # 仅 HTTPS
    samesite="lax"  # 防止 CSRF
)
```

### 6.4 频率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/login/wechat")
@limiter.limit("10/minute")  # 每分钟最多 10 次
async def login_wechat(request: Request):
    ...
```

---

## 7. 性能优化设计

### 7.1 Token 缓存

```python
class WeChatOAuthHandler:
    def __init__(self, config):
        self._token_cache = None
        self._token_expire_time = None
    
    async def get_access_token(self):
        # 检查缓存
        if (self._token_cache 
            and self._token_expire_time 
            and datetime.now() < self._token_expire_time):
            return self._token_cache
        
        # 请求新 token
        ...
```

### 7.2 异步 HTTP 请求

```python
# 使用 httpx 异步客户端
async with httpx.AsyncClient() as client:
    response = await client.get(url, params=params, timeout=10.0)
```

### 7.3 并发处理

```python
# 支持并发登录请求
import asyncio

# 使用异步锁保护共享资源
token_lock = asyncio.Lock()

async def get_access_token(self):
    async with token_lock:
        # 获取 token 的逻辑
        ...
```

---

## 8. 可测试性设计

### 8.1 依赖注入

```python
# 使处理器可测试
class WeChatOAuthHandler:
    def __init__(self, config, http_client=None):
        self.config = config
        self.http_client = http_client or httpx.AsyncClient()
```

### 8.2 Mock 友好的接口

```python
# 提取可 mock 的方法
async def _make_api_request(self, url, params):
    """发起 API 请求（可 mock）"""
    async with self.http_client as client:
        return await client.get(url, params=params)
```


---

## 9. 正确性属性 (Correctness Properties)

### 9.1 什么是正确性属性

正确性属性是对系统行为的形式化描述，它定义了系统在所有有效输入下应该满足的不变量和规则。通过属性测试（Property-Based Testing），我们可以自动生成大量测试用例来验证这些属性，从而提高代码的可靠性和正确性。

### 9.2 OAuth 流程属性

#### 属性 1: 授权 URL 生成的确定性

*对于任何* 给定的 redirect_uri 和 state，多次调用 `build_authorize_url()` 应该生成相同的 URL

**验证需求**: 2.1.2.2, 2.2.2.2

**测试策略**: 使用相同的参数多次调用，验证结果一致性

```python
# 伪代码
for all redirect_uri, state:
    url1 = handler.build_authorize_url(redirect_uri, state)
    url2 = handler.build_authorize_url(redirect_uri, state)
    assert url1 == url2
```

#### 属性 2: State 参数的往返一致性

*对于任何* 生成的 state 参数，在有效期内解析应该返回原始数据

**验证需求**: 3.1.3

**测试策略**: 生成随机 state，验证序列化和反序列化的一致性

```python
# 伪代码
for all provider, nonce:
    state = serializer.dumps({"provider": provider, "nonce": nonce})
    data = serializer.loads(state, max_age=600)
    assert data["provider"] == provider
    assert data["nonce"] == nonce
```

#### 属性 3: 过期 State 拒绝

*对于任何* 超过有效期的 state 参数，解析应该抛出异常

**验证需求**: 3.1.4

**测试策略**: 生成过期的 state，验证是否正确拒绝

```python
# 伪代码
for all state:
    # 等待超过 max_age
    time.sleep(max_age + 1)
    with pytest.raises(SignatureExpired):
        serializer.loads(state, max_age=max_age)
```

### 9.3 用户管理属性

#### 属性 4: 首次登录创建用户

*对于任何* 新的 provider_user_id，首次调用 `ensure_user_in_organizations()` 应该创建新用户

**验证需求**: 2.1.2.4, 2.2.2.4

**测试策略**: 使用随机生成的 OpenID/UserID，验证用户创建

```python
# 伪代码
for all new_provider_user_id:
    user_count_before = count_users()
    await ensure_user_in_organizations(
        provider_user_id=new_provider_user_id,
        email=f"{new_provider_user_id}@test.local",
        name="测试用户",
        provider="wechat",
        api_token="test_token"
    )
    user_count_after = count_users()
    assert user_count_after == user_count_before + 1
```

#### 属性 5: 重复登录识别用户

*对于任何* 已存在的 provider_user_id，重复调用 `ensure_user_in_organizations()` 应该返回相同的用户

**验证需求**: 2.1.2.5, 2.2.2.5

**测试策略**: 多次使用相同的 OpenID/UserID 登录，验证用户 ID 一致

```python
# 伪代码
for all existing_provider_user_id:
    user1, _ = await ensure_user_in_organizations(...)
    user2, _ = await ensure_user_in_organizations(...)
    assert user1["id"] == user2["id"]
```


### 9.4 数据解析属性

#### 属性 6: 用户信息解析完整性

*对于任何* 有效的微信/企业微信用户数据，`parse_user_info()` 应该返回包含所有必需字段的字典

**验证需求**: 2.1.2.8, 2.2.2.8

**测试策略**: 生成随机用户数据，验证解析结果包含必需字段

```python
# 伪代码
for all valid_user_data:
    parsed = handler.parse_user_info(valid_user_data)
    assert "id" in parsed
    assert "email" in parsed
    assert "name" in parsed
    assert "provider" in parsed
```

### 9.5 错误处理属性

#### 属性 7: API 错误正确映射

*对于任何* 微信/企业微信 API 返回的错误码，系统应该返回友好的错误消息

**验证需求**: 2.1.2.9, 2.2.2.10

**测试策略**: 模拟各种 API 错误响应，验证错误消息

```python
# 伪代码
for all error_code in KNOWN_ERROR_CODES:
    mock_response = {"errcode": error_code, "errmsg": "..."}
    with pytest.raises(ValueError) as exc_info:
        await handler.exchange_code_for_token("invalid_code")
    assert "友好的错误消息" in str(exc_info.value)
```

### 9.6 安全属性

#### 属性 8: CSRF 防护有效性

*对于任何* 不匹配的 state 参数，回调处理应该拒绝请求

**验证需求**: 3.1.3

**测试策略**: 使用不同的 state 参数，验证是否正确拒绝

```python
# 伪代码
for all state1, state2 where state1 != state2:
    # 存储 state1
    set_cookie("oauth_state", state1)
    # 回调时使用 state2
    with pytest.raises(HTTPException) as exc_info:
        await wechat_authorized(request_with_state=state2)
    assert exc_info.value.status_code == 400
```

#### 属性 9: Token 安全性

*对于任何* 生成的 API Token，应该具有足够的随机性（至少 256 位）

**验证需求**: 3.1.4

**测试策略**: 生成多个 Token，验证唯一性和长度

```python
# 伪代码
tokens = set()
for i in range(1000):
    token = secrets.token_urlsafe(32)
    assert len(token) >= 43  # base64 编码后的长度
    assert token not in tokens
    tokens.add(token)
```

### 9.7 并发属性

#### 属性 10: 并发登录安全性

*对于任何* 并发的登录请求，系统应该正确处理而不产生竞态条件

**验证需求**: 3.2.3

**测试策略**: 并发执行多个登录请求，验证结果正确性

```python
# 伪代码
async def concurrent_logins():
    tasks = [login_user(user_id) for user_id in range(100)]
    results = await asyncio.gather(*tasks)
    # 验证所有登录都成功
    assert all(r.status_code == 200 for r in results)
    # 验证没有重复的 API Token
    tokens = [r.cookies["api_token"] for r in results]
    assert len(tokens) == len(set(tokens))
```

### 9.8 缓存属性

#### 属性 11: Token 缓存一致性

*对于任何* 缓存的 access_token，在有效期内多次获取应该返回相同的 token

**验证需求**: 3.2.4

**测试策略**: 在有效期内多次调用，验证返回相同的 token

```python
# 伪代码
for all handler:
    token1 = await handler.get_access_token()
    token2 = await handler.get_access_token()
    assert token1 == token2
```

---

## 10. 测试策略

### 10.1 单元测试

#### 10.1.1 配置测试

```python
def test_wechat_config_validation():
    """测试微信配置验证"""
    # 缺少 app_id
    with pytest.raises(ValueError, match="缺少 WECHAT_APP_ID"):
        validate_wechat_config()

def test_wecom_config_validation():
    """测试企业微信配置验证"""
    # 缺少 corp_id
    with pytest.raises(ValueError, match="缺少 WECOM_CORP_ID"):
        validate_wecom_config()
```

#### 10.1.2 URL 构建测试

```python
def test_wechat_authorize_url_building():
    """测试微信授权 URL 构建"""
    handler = WeChatOAuthHandler(WECHAT_CONFIG)
    url = handler.build_authorize_url(
        redirect_uri="http://localhost/callback",
        state="test_state"
    )
    
    assert "appid=" in url
    assert "redirect_uri=" in url
    assert "state=test_state" in url
    assert "scope=snsapi_userinfo" in url
```

#### 10.1.3 用户信息解析测试

```python
def test_wechat_user_info_parsing():
    """测试微信用户信息解析"""
    handler = WeChatOAuthHandler(WECHAT_CONFIG)
    
    raw_data = {
        "openid": "test_openid",
        "nickname": "测试用户",
        "headimgurl": "http://example.com/avatar.jpg",
        "unionid": "test_unionid"
    }
    
    parsed = handler.parse_user_info(raw_data)
    
    assert parsed["id"] == "test_openid"
    assert parsed["name"] == "测试用户"
    assert parsed["picture"] == "http://example.com/avatar.jpg"
    assert parsed["provider"] == "wechat"
    assert "@wechat.queryweaver.local" in parsed["email"]
```

### 10.2 属性测试 (Property-Based Testing)

使用 `pytest` + `hypothesis` 进行属性测试：

```python
from hypothesis import given, strategies as st

@given(
    redirect_uri=st.text(min_size=10, max_size=100),
    state=st.text(min_size=10, max_size=50)
)
def test_authorize_url_deterministic(redirect_uri, state):
    """
    属性测试：授权 URL 生成的确定性
    
    Feature: wechat-oauth, Property 1: 授权 URL 生成的确定性
    """
    handler = WeChatOAuthHandler(WECHAT_CONFIG)
    url1 = handler.build_authorize_url(redirect_uri, state)
    url2 = handler.build_authorize_url(redirect_uri, state)
    assert url1 == url2


@given(
    provider=st.sampled_from(["wechat", "wecom"]),
    nonce=st.text(min_size=16, max_size=32)
)
def test_state_roundtrip(provider, nonce):
    """
    属性测试：State 参数的往返一致性
    
    Feature: wechat-oauth, Property 2: State 参数的往返一致性
    """
    serializer = URLSafeTimedSerializer("test_secret")
    state = serializer.dumps({"provider": provider, "nonce": nonce})
    data = serializer.loads(state, max_age=600)
    
    assert data["provider"] == provider
    assert data["nonce"] == nonce


@given(
    openid=st.text(min_size=20, max_size=50),
    nickname=st.text(min_size=1, max_size=50)
)
def test_user_info_parsing_completeness(openid, nickname):
    """
    属性测试：用户信息解析完整性
    
    Feature: wechat-oauth, Property 6: 用户信息解析完整性
    """
    handler = WeChatOAuthHandler(WECHAT_CONFIG)
    
    raw_data = {
        "openid": openid,
        "nickname": nickname,
        "headimgurl": "http://example.com/avatar.jpg"
    }
    
    parsed = handler.parse_user_info(raw_data)
    
    # 验证必需字段存在
    assert "id" in parsed
    assert "email" in parsed
    assert "name" in parsed
    assert "provider" in parsed
    
    # 验证值正确
    assert parsed["id"] == openid
    assert parsed["name"] == nickname
    assert parsed["provider"] == "wechat"
```

### 10.3 集成测试

```python
@pytest.mark.asyncio
async def test_wechat_login_flow():
    """测试完整的微信登录流程"""
    # 1. 发起登录
    response = await client.get("/login/wechat")
    assert response.status_code == 302
    assert "open.weixin.qq.com" in response.headers["location"]
    
    # 2. 模拟微信回调
    state = response.cookies["oauth_state"]
    callback_response = await client.get(
        f"/login/wechat/authorized?code=test_code&state={state}"
    )
    
    # 3. 验证登录成功
    assert callback_response.status_code == 302
    assert callback_response.headers["location"] == "/"
    assert "api_token" in callback_response.cookies


@pytest.mark.asyncio
async def test_wecom_login_flow():
    """测试完整的企业微信登录流程"""
    # 类似微信登录流程
    ...
```

### 10.4 端到端测试

使用 Playwright 进行 E2E 测试：

```python
async def test_wechat_login_e2e(page):
    """端到端测试：微信登录"""
    # 1. 访问登录页面
    await page.goto("http://localhost:5000")
    
    # 2. 点击微信登录按钮
    await page.click("text=微信登录")
    
    # 3. 验证跳转到微信授权页面
    await page.wait_for_url("**/open.weixin.qq.com/**")
    
    # 4. 模拟扫码授权（需要 mock 微信服务）
    # ...
    
    # 5. 验证登录成功
    await page.wait_for_url("http://localhost:5000/")
    user_menu = page.locator(".user-menu")
    await expect(user_menu).to_be_visible()
```

---

## 11. 前端集成设计

### 11.1 登录按钮组件

```typescript
// app/src/components/modals/LoginModal.tsx

interface AuthConfig {
  google: boolean;
  github: boolean;
  wechat: boolean;
  wecom: boolean;
  email: boolean;
}

export const LoginModal: React.FC = () => {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  
  useEffect(() => {
    // 获取认证配置
    fetch('/auth/config')
      .then(res => res.json())
      .then(setAuthConfig);
  }, []);
  
  if (!authConfig) return <LoadingSpinner />;
  
  return (
    <Dialog>
      <DialogContent>
        <DialogTitle>登录 QueryWeaver</DialogTitle>
        
        {authConfig.google && (
          <Button onClick={() => window.location.href = '/login/google'}>
            <GoogleIcon /> 使用 Google 登录
          </Button>
        )}
        
        {authConfig.github && (
          <Button onClick={() => window.location.href = '/login/github'}>
            <GitHubIcon /> 使用 GitHub 登录
          </Button>
        )}
        
        {authConfig.wechat && (
          <Button onClick={() => window.location.href = '/login/wechat'}>
            <WeChatIcon /> 使用微信登录
          </Button>
        )}
        
        {authConfig.wecom && (
          <Button onClick={() => window.location.href = '/login/wecom'}>
            <WeComIcon /> 使用企业微信登录
          </Button>
        )}
      </DialogContent>
    </Dialog>
  );
};
```

### 11.2 图标组件

```typescript
// app/src/components/icons/WeChatIcon.tsx

export const WeChatIcon: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <svg 
      className={className} 
      viewBox="0 0 24 24" 
      fill="currentColor"
    >
      {/* 微信图标 SVG 路径 */}
      <path d="M8.5 9.5c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1z..." />
    </svg>
  );
};

export const WeComIcon: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <svg 
      className={className} 
      viewBox="0 0 24 24" 
      fill="currentColor"
    >
      {/* 企业微信图标 SVG 路径 */}
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z..." />
    </svg>
  );
};
```

---

## 12. 部署配置

### 12.1 环境变量

```bash
# .env.example

# 微信登录配置
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_wechat_app_secret_here

# 企业微信登录配置
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=your_wecom_corp_secret_here

# 应用密钥（用于 state 签名）
FASTAPI_SECRET_KEY=your_secret_key_here

# 回调 URL（可选，默认自动生成）
# WECHAT_REDIRECT_URI=https://your-domain.com/login/wechat/authorized
# WECOM_REDIRECT_URI=https://your-domain.com/login/wecom/authorized
```

### 12.2 Docker 配置

```dockerfile
# Dockerfile

FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv sync --system

# 复制应用代码
COPY api/ ./api/
COPY app/dist/ ./app/dist/

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "5000"]
```

### 12.3 Nginx 配置

```nginx
# nginx.conf

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 代理到 FastAPI
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 13. 监控和日志

### 13.1 关键指标

```python
# 登录成功率
login_success_rate = successful_logins / total_login_attempts

# 平均响应时间
avg_response_time = sum(response_times) / len(response_times)

# 错误率
error_rate = failed_requests / total_requests
```

### 13.2 日志格式

```python
# 结构化日志
logger.info(json.dumps({
    "event": "oauth_login",
    "provider": "wechat",
    "status": "success",
    "user_id": openid,
    "response_time_ms": 1234,
    "timestamp": datetime.now().isoformat()
}))
```

---

## 14. 文档和维护

### 14.1 API 文档

FastAPI 自动生成 Swagger 文档，访问 `/docs` 查看。

### 14.2 用户文档

需要编写以下用户文档：
- 如何配置微信开放平台
- 如何配置企业微信应用
- 常见问题解答
- 故障排查指南

### 14.3 开发者文档

需要编写以下开发者文档：
- OAuth 流程说明
- 代码结构说明
- 如何添加新的 OAuth 提供商
- 测试指南

---

## 15. 总结

本设计文档详细描述了微信和企业微信 OAuth 登录功能的实现方案，包括：

1. **架构设计**: 与现有 OAuth 提供商保持一致的分层架构
2. **组件设计**: 配置模块、OAuth 处理器、路由模块的详细实现
3. **数据模型**: FalkorDB 图数据库的节点和关系设计
4. **错误处理**: 完善的错误分类和友好的错误消息
5. **安全设计**: CSRF 防护、密钥管理、Token 安全
6. **性能优化**: Token 缓存、异步请求、并发处理
7. **可测试性**: 单元测试、属性测试、集成测试、E2E 测试
8. **正确性属性**: 11 个形式化的正确性属性，确保系统行为符合预期
9. **前端集成**: 登录按钮和图标组件
10. **部署配置**: 环境变量、Docker、Nginx 配置
11. **监控日志**: 关键指标和结构化日志

该设计遵循了 QueryWeaver 的产品原则和技术规范，确保了功能的完整性、安全性和可维护性。
