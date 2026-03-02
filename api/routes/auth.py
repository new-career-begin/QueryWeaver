"""Authentication routes for the text2sql API."""
# pylint: disable=all

import hashlib
import hmac
import logging
import os
import re
import secrets

from pathlib import Path
from urllib.parse import urljoin
from itsdangerous import URLSafeTimedSerializer

from authlib.integrations.starlette_client import OAuth

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, FileSystemBytecodeCache, select_autoescape
from starlette.config import Config
from pydantic import BaseModel

from api.auth.user_management import delete_user_token, ensure_user_in_organizations, validate_user
from api.auth.oauth_handlers import WeChatOAuthHandler, WeComOAuthHandler
from api.extensions import db
from api.config import WECHAT_CONFIG, WECOM_CONFIG, _is_wechat_auth_enabled, _is_wecom_auth_enabled

# Import GENERAL_PREFIX from graphs route
GENERAL_PREFIX = os.getenv("GENERAL_PREFIX")

# Router
auth_router = APIRouter(tags=["Authentication"])
TEMPLATES_DIR = str((Path(__file__).resolve().parents[1] / "../app/templates").resolve())

TEMPLATES_CACHE_DIR = "/tmp/jinja_cache"
os.makedirs(TEMPLATES_CACHE_DIR, exist_ok=True)  # ✅ ensures the folder exists

templates = Jinja2Templates(
    env=Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        bytecode_cache=FileSystemBytecodeCache(
            directory=TEMPLATES_CACHE_DIR,
            pattern="%s.cache"
        ),
        auto_reload=True,
        autoescape=select_autoescape(['html', 'xml', 'j2'])
    )
)

templates.env.globals["google_tag_manager_id"] = os.getenv("GOOGLE_TAG_MANAGER_ID")

GOOGLE_AUTH = bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
GITHUB_AUTH = bool(os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET"))
EMAIL_AUTH = bool(os.getenv("EMAIL_AUTH_ENABLED", "").lower() in ["true", "1", "yes", "on"])

# 初始化序列化器（用于 state 参数）
serializer = URLSafeTimedSerializer(os.getenv("FASTAPI_SECRET_KEY", "default-secret-key"))


# ---- CSRF 防护函数 ----
def generate_state(provider: str) -> str:
    """
    生成 OAuth state 参数用于 CSRF 防护
    
    Args:
        provider: OAuth 提供商名称（如 "wechat", "wecom", "google", "github"）
        
    Returns:
        加密签名的 state 字符串
        
    Example:
        >>> state = generate_state("wechat")
        >>> print(state)
        'eyJwcm92aWRlciI6IndlY2hhdCIsIm5vbmNlIjoiLi4uIn0...'
    """
    # 生成随机 nonce 增加安全性
    nonce = secrets.token_urlsafe(16)
    
    # 创建 state 数据
    state_data = {
        "provider": provider,
        "nonce": nonce
    }
    
    # 使用 itsdangerous 序列化和签名
    state = serializer.dumps(state_data)
    
    logging.info("生成 CSRF state: provider=%s", provider)
    return state


def verify_state(state: str, expected_provider: str, max_age: int = 600) -> bool:
    """
    验证 OAuth state 参数
    
    Args:
        state: 待验证的 state 字符串
        expected_provider: 期望的提供商名称
        max_age: state 的最大有效期（秒），默认 10 分钟
        
    Returns:
        验证成功返回 True，失败返回 False
        
    Raises:
        ValueError: 当 state 格式不正确或已过期时抛出
        
    Example:
        >>> state = generate_state("wechat")
        >>> verify_state(state, "wechat")
        True
    """
    try:
        # 验证签名和时效性
        state_data = serializer.loads(state, max_age=max_age)
        
        # 验证提供商匹配
        if state_data.get("provider") != expected_provider:
            logging.error(
                "State provider 不匹配: expected=%s, actual=%s",
                expected_provider,
                state_data.get("provider")
            )
            return False
        
        # 验证必需字段存在
        if not state_data.get("nonce"):
            logging.error("State 缺少 nonce 字段")
            return False
        
        logging.info("State 验证成功: provider=%s", expected_provider)
        return True
        
    except Exception as e:
        logging.error("State 验证失败: %s", str(e))
        raise ValueError(f"State 验证失败: {str(e)}") from e

# ---- Authentication Configuration Helpers ----
def _is_email_auth_enabled() -> bool:
    """Check if email authentication is enabled via environment variable."""
    return EMAIL_AUTH or not (GOOGLE_AUTH or GITHUB_AUTH)

def _is_google_auth_enabled() -> bool:
    """Check if Google OAuth is enabled via environment variables."""
    return GOOGLE_AUTH

def _is_github_auth_enabled() -> bool:
    """Check if GitHub OAuth is enabled via environment variables."""
    return GITHUB_AUTH

def _get_auth_config() -> dict:
    """Get authentication configuration for templates."""
    return {
        "email_auth_enabled": _is_email_auth_enabled(),
        "google_auth_enabled": _is_google_auth_enabled(),
        "github_auth_enabled": _is_github_auth_enabled(),
    }

# Data models for email authentication
class EmailLoginRequest(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    email: str
    password: str

class EmailSignupRequest(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    firstName: str
    lastName: str
    email: str
    password: str

# ---- Password utilities ----
def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2 with a random salt."""
    salt = os.urandom(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return (salt + password_hash).hex()

def _verify_password(password: str, stored_password_hex: str) -> bool:
    """Verify a password against its hash using constant-time comparison."""
    try:
        stored_password = bytes.fromhex(stored_password_hex)
        salt = stored_password[:32]
        stored_hash = stored_password[32:]

        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

        return hmac.compare_digest(password_hash, stored_hash)
    except (ValueError, TypeError):
        return False

def _sanitize_for_log(value: str) -> str:
    """Sanitize user input for logging by removing newlines and carriage returns."""
    if not isinstance(value, str):
        return str(value)
    return value.replace('\r\n', '').replace('\n', '').replace('\r', '')

def _validate_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

async def _set_mail_hash(email: str, password_hash: str) -> bool:
    """Set email hash for the user in the database."""
    try:
        organizations_graph = db.select_graph("Organizations")

        # Sanitize inputs for logging
        safe_email = _sanitize_for_log(email)

        # Create new email identity and user
        create_query = """
        MERGE (i:Identity {
            provider_user_id: $email,
            email: $email
        })
        SET i.password_hash = $password_hash
        RETURN i
        """

        result = await organizations_graph.query(create_query, {
            "email": email,
            "password_hash": password_hash,
        })

        if result.result_set:
            return True
        else:
            logging.error("Failed to set email hash for user: %s", safe_email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Internal server error"
            )

    except Exception as e:
        logging.error("Error setting email hash for user %s: %s", safe_email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error"
        )
        
def _is_request_secure(request: Request) -> bool:
    """Determine if the request is secure (HTTPS)."""
    
    # Check X-Forwarded-Proto first (proxy-aware)
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        return forwarded_proto == "https"
    
    # Fallback to request URL scheme
    return request.url.scheme == "https"

async def _authenticate_email_user(email: str, password: str):
    """Authenticate an email user."""
    try:
        organizations_graph = db.select_graph("Organizations")

        # Find user by email
        query = """
        MATCH (i:Identity {provider: 'email', email: $email})-[:AUTHENTICATES]->(u:User)
        RETURN i, u
        """

        result = await organizations_graph.query(query, {"email": email})

        if not result.result_set:
            return False, "Invalid email or password"

        identity = result.result_set[0][0]
        user = result.result_set[0][1]

        # Verify password - access Node properties correctly
        stored_password_hash = identity.properties.get('password_hash')
        if not stored_password_hash or not _verify_password(password, stored_password_hash):
            return False, "Invalid email or password"

        # Update last login
        update_query = """
        MATCH (i:Identity {provider: 'email', email: $email})
        SET i.last_login = timestamp()
        """
        await organizations_graph.query(update_query, {"email": email})

        logging.info("EMAIL USER AUTHENTICATED: email=%r", _sanitize_for_log(email))
        return True, {"identity": identity, "user": user}

    except Exception as e:
        logging.error("Error authenticating email user: %s", e)
        return False, "Internal error"

# ---- Email Authentication Routes ----
@auth_router.post("/signup/email")
async def email_signup(request: Request, signup_data: EmailSignupRequest) -> JSONResponse:
    """Handle email/password user registration."""
    try:
        # Check if email authentication is enabled
        if not _is_email_auth_enabled():
            return JSONResponse(
                {"success": False, "error": "Email authentication is not enabled"},
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validate required fields
        if not all([signup_data.firstName, signup_data.lastName,
                    signup_data.email, signup_data.password]):
            return JSONResponse(
                {"success": False, "error": "All fields are required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        first_name = signup_data.firstName.strip()
        last_name = signup_data.lastName.strip()
        email = signup_data.email.strip().lower()
        password = signup_data.password

        # Validate email format
        if not _validate_email(email):
            return JSONResponse(
                {"success": False, "error": "Invalid email format"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Validate password strength
        if len(password) < 8:
            return JSONResponse(
                {"success": False, "error": "Password must be at least 8 characters long"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        api_token = secrets.token_urlsafe(32)
        # Create organization association
        success, user_info = await ensure_user_in_organizations(email, email,
                                            f"{first_name} {last_name}", "email", api_token)

        if success and user_info and user_info["new_identity"]:
            logging.info("New user created: %s", _sanitize_for_log(email))

            # Hash password
            password_hash = _hash_password(password)

            # Set email hash
            await _set_mail_hash(email, password_hash)

        else:
            logging.info("User already exists: %s", _sanitize_for_log(email))

        logging.info("User registration successful: %s", _sanitize_for_log(email))

        response = JSONResponse({
            "success": True,
        }, status_code=201)
        response.set_cookie(
            key="api_token",
            value=api_token,
            max_age=86400,  # 24 小时过期
            httponly=True,
            secure=_is_request_secure(request),
            samesite="lax"
        )
        return response

    except Exception as e:
        logging.error("Signup error: %s", e)
        return JSONResponse(
            {"success": False, "error": "Registration failed"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@auth_router.post("/login/email")
async def email_login(request: Request, login_data: EmailLoginRequest) -> JSONResponse:
    """Handle email/password user login."""
    try:
        # Check if email authentication is enabled
        if not _is_email_auth_enabled():
            return JSONResponse(
                {"success": False, "error": "Email authentication is not enabled"},
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validate required fields
        if not login_data.email or not login_data.password:
            return JSONResponse(
                {"success": False, "error": "Email and password are required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        email = login_data.email.strip().lower()
        password = login_data.password

        # Validate email format
        if not _validate_email(email):
            return JSONResponse(
                {"success": False, "error": "Invalid email format"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        success, result = await _authenticate_email_user(email, password)

        if not success:
            return JSONResponse(
                {"success": False, "error": result},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Set session data - result is a dict when success is True
        if isinstance(result, dict):
            identity_node = result.get("identity")

            identity_props = (
                identity_node.properties
                if identity_node and hasattr(identity_node, "properties")
                else {}
            )
            
            user_data = {
                'id': identity_props.get("provider_user_id", email),
                'email': identity_props.get('email', email),
                'name': identity_props.get('name', ''),
                'picture': identity_props.get('picture', ''),
            }

            # Call the registered Google callback handler if it exists to store user data.
            handler = getattr(request.app.state, "callback_handler", None)
            if handler:
                api_token = secrets.token_urlsafe(32)  # ~43 chars, hard to guess

                # Call the registered handler (await if async)
                await handler('email', user_data, api_token)
                response = JSONResponse({"success": True}, status_code=200)
                
                response.set_cookie(
                    key="api_token",
                    value=api_token,
                    max_age=86400,  # 24 小时过期
                    httponly=True,
                    secure=_is_request_secure(request),
                    samesite="lax"
                )
                return response
            
        return JSONResponse(
            {"success": False, "error": "Authentication failed"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        logging.error("Login error: %s", e)
        return JSONResponse(
            {"success": False, "error": "Login failed"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ---- Helpers ----
def _get_provider_client(request: Request, provider: str):
    """Get an OAuth provider client from app.state.oauth"""
    oauth = getattr(request.app.state, "oauth", None)
    if not oauth:
        raise HTTPException(status_code=500, detail="OAuth not configured")

    client = getattr(oauth, provider, None)
    if not client:
        raise HTTPException(status_code=500, detail=f"OAuth provider {provider} not configured")
    return client

def _build_callback_url(request: Request, path: str) -> str:
    """Build absolute callback URL, honoring OAUTH_BASE_URL if provided."""
    base_override = os.getenv("OAUTH_BASE_URL")
    base = base_override if base_override else str(request.base_url)
    if not base.endswith("/"):
        base += "/"
    return urljoin(base, path.lstrip("/"))

# ---- Routes ----
@auth_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    """
    Serve the React SPA (Single Page Application).
    The React app handles authentication state via /auth-status endpoint.
    """
    from fastapi.responses import FileResponse
    
    # Serve the React build's index.html
    dist_path = Path(__file__).resolve().parents[1] / "../app/dist"
    index_path = dist_path / "index.html"
    
    if not index_path.exists():
        return HTMLResponse(
            content="""
            <html>
                <head><title>QueryWeaver - Build Required</title></head>
                <body style="font-family: system-ui; padding: 2rem; max-width: 800px; margin: 0 auto;">
                    <h1>🛠️ Frontend Not Built</h1>
                    <p>Please build the React frontend first:</p>
                    <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px;">cd app && npm run build</pre>
                    <p>Or run in development mode (recommended for development):</p>
                    <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px;">cd app && npm run dev</pre>
                    <p><small>The dev server will run on <a href="http://localhost:8080">http://localhost:8080</a> with hot reload.</small></p>
                </body>
            </html>
            """,
            status_code=503
        )
    
    return FileResponse(index_path)

@auth_router.get("/login/google", name="google.login", response_class=RedirectResponse)
async def login_google(request: Request) -> RedirectResponse:
    """Initiate Google OAuth login flow.

    Args:
        request (Request): The incoming request.

    Returns:
        RedirectResponse: The redirect response to the Google OAuth endpoint.
    """

    # Check if Google auth is enabled
    if not _is_google_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google authentication is not configured"
        )

    google = _get_provider_client(request, "google")
    redirect_uri = _build_callback_url(request, "login/google/authorized")

    # Helpful hint if localhost vs 127.0.0.1 mismatch is likely
    if not os.getenv("OAUTH_BASE_URL") and "127.0.0.1" in str(request.base_url):
        logging.warning(
            "OAUTH_BASE_URL not set and base URL is 127.0.0.1; "
            "if your Google OAuth app uses 'http://localhost:5000', "
            "set OAUTH_BASE_URL=http://localhost:5000 to avoid redirect_uri mismatch."
        )

    return await google.authorize_redirect(request, redirect_uri)


@auth_router.get("/login/google/authorized", response_class=RedirectResponse)
async def google_authorized(request: Request) -> RedirectResponse:
    """
    Handle Google OAuth callback and user authorization.

    Args:
        request (Request): The incoming request.

    Returns:
        RedirectResponse: The redirect response after handling the callback.
    """
    # Check if Google auth is enabled
    if not _is_google_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google authentication is not configured"
        )

    try:
        google = _get_provider_client(request, "google")
        token = await google.authorize_access_token(request)
        resp = await google.get("userinfo", token=token)
        if resp.status_code != 200:
            logging.warning("Failed to retrieve user info from Google")
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        user_info = resp.json()

        if user_info:
            user_data = {
                'id': user_info.get('id') or user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
            }

            # Call the registered Google callback handler if it exists to store user data.
            handler = getattr(request.app.state, "callback_handler", None)
            if handler:
                api_token = secrets.token_urlsafe(32)  # ~43 chars, hard to guess

                # Call the registered handler (await if async)
                await handler('google', user_data, api_token)

                redirect = RedirectResponse(url="/", status_code=302)
                redirect.set_cookie(
                    key="api_token",
                    value=api_token,
                    max_age=86400,  # 24 小时过期
                    httponly=True,
                    secure=True,
                    samesite="lax"
                )

                return redirect

            # Handler not set - log and raise error to prevent silent failure
            logging.error("Google OAuth callback handler not registered in app state")
            raise HTTPException(status_code=500, detail="Authentication handler not configured")

        # If we reach here, user_info was falsy
        logging.warning("No user info received from Google OAuth")
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    except Exception as e:
        logging.error("Google OAuth authentication failed: %s", str(e))  # nosemgrep
        raise HTTPException(status_code=400, detail="Authentication failed") from e


@auth_router.get("/login/google/callback", response_class=RedirectResponse)
async def google_callback_compat(request: Request) -> RedirectResponse:
    """Handle Google OAuth callback redirect for compatibility."""
    qs = f"?{request.url.query}" if request.url.query else ""
    redirect = f"/login/google/authorized{qs}"
    return RedirectResponse(url=redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/login/github",  name="github.login", response_class=RedirectResponse)
async def login_github(request: Request) -> RedirectResponse:
    """Handle GitHub OAuth login redirect."""
    # Check if GitHub auth is enabled
    if not _is_github_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="GitHub authentication is not configured"
        )

    github = _get_provider_client(request, "github")
    redirect_uri = _build_callback_url(request, "login/github/authorized")

    # Helpful hint if localhost vs 127.0.0.1 mismatch is likely
    if not os.getenv("OAUTH_BASE_URL") and "127.0.0.1" in str(request.base_url):
        logging.warning(
            "OAUTH_BASE_URL not set and base URL is 127.0.0.1; "
            "if your GitHub OAuth app uses 'http://localhost:5000', "
            "set OAUTH_BASE_URL=http://localhost:5000 to avoid redirect_uri mismatch."
        )

    return await github.authorize_redirect(request, redirect_uri)


@auth_router.get("/login/github/authorized", response_class=RedirectResponse)
async def github_authorized(request: Request) -> RedirectResponse:
    """Handle GitHub OAuth authorization callback."""
    # Check if GitHub auth is enabled
    if not _is_github_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="GitHub authentication is not configured"
        )
    try:
        github = _get_provider_client(request, "github")
        token = await github.authorize_access_token(request)

        # Fetch GitHub user info
        resp = await github.get("user", token=token)
        if resp.status_code != 200:
            logging.error("Failed to fetch GitHub user info: %s", resp.text)  # nosemgrep
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        user_info = resp.json()

        # Get user email if not public
        email = user_info.get("email")
        if not email:
            # Try to get primary email from emails endpoint
            email_resp = await github.get("user/emails", token=token)
            if email_resp.status_code == 200:
                emails = email_resp.json()
                for email_obj in emails:
                    if email_obj.get("primary"):
                        email = email_obj.get("email")
                        break

        if user_info:
            user_data = {
                'id': user_info.get('id'),
                'email': email,
                'name': user_info.get('name'),
                'picture': user_info.get('avatar_url'),
            }

            # Call the registered GitHub callback handler if it exists to store user data.
            handler = getattr(request.app.state, "callback_handler", None)
            if handler:
                api_token = secrets.token_urlsafe(32)  # ~43 chars, hard to guess

                # Call the registered handler (await if async)
                await handler('github', user_data, api_token)

                redirect = RedirectResponse(url="/", status_code=302)
                redirect.set_cookie(
                    key="api_token",
                    value=api_token,
                    max_age=86400,  # 24 小时过期
                    httponly=True,
                    secure=True,
                    samesite="lax"
                )

                return redirect

            # Handler not set - log and raise error to prevent silent failure
            logging.error("GitHub OAuth callback handler not registered in app state")
            raise HTTPException(status_code=500, detail="Authentication handler not configured")

        # If we reach here, user_info was falsy
        logging.warning("No user info received from GitHub OAuth")
        raise HTTPException(status_code=400, detail="Failed to get user info from Github")

    except Exception as e:
        logging.error("GitHub OAuth authentication failed: %s", str(e))  # nosemgrep
        raise HTTPException(status_code=400, detail="Authentication failed") from e


@auth_router.get("/login/github/callback", response_class=RedirectResponse)
async def github_callback_compat(request: Request) -> RedirectResponse:
    """Handle GitHub OAuth callback redirect for compatibility."""
    qs = f"?{request.url.query}" if request.url.query else ""
    redirect = f"/login/github/authorized{qs}"
    return RedirectResponse(url=redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# ---- 微信 OAuth 路由 ----
@auth_router.get("/login/wechat", name="wechat.login", response_class=RedirectResponse)
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
    # 检查微信登录是否启用
    if not _is_wechat_auth_enabled():
        logging.warning("微信登录未配置")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信登录功能未启用，请联系管理员配置"
        )
    
    # 生成 CSRF token
    state = generate_state("wechat")
    
    # 构建回调 URL
    redirect_uri = _build_callback_url(request, "login/wechat/authorized")
    
    # 初始化微信 OAuth 处理器
    wechat_handler = WeChatOAuthHandler(WECHAT_CONFIG)
    
    # 构建授权 URL
    authorize_url = wechat_handler.build_authorize_url(redirect_uri, state)
    
    # 将 state 存储到 cookie（用于后续验证）
    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,  # 10 分钟有效期
        httponly=True,
        secure=_is_request_secure(request),
        samesite="lax"
    )
    
    logging.info("用户发起微信登录")
    return response


@auth_router.get("/login/wechat/authorized", response_class=RedirectResponse)
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
    # 检查微信登录是否启用
    if not _is_wechat_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信登录功能未启用"
        )
    
    # 获取查询参数
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # 验证必需参数
    if not code or not state:
        logging.error("微信回调缺少必需参数")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：缺少必需参数"
        )
    
    # 验证 state（CSRF 防护）
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        logging.error("State 验证失败: stored=%s, received=%s", stored_state, state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：安全验证失败，请重试"
        )
    
    try:
        # 验证 state 签名和时效性（10 分钟）
        if not verify_state(state, "wechat", max_age=600):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="授权失败：安全验证失败，请重试"
            )
    except ValueError as e:
        logging.error("State 验证失败: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：验证令牌已过期，请重新登录"
        ) from e
    
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
        handler = getattr(request.app.state, "callback_handler", None)
        if handler:
            success = await handler("wechat", user_info, api_token)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用户信息处理失败"
                )
            
            # 设置认证 Cookie
            response = RedirectResponse(url="/", status_code=302)
            response.set_cookie(
                key="api_token",
                value=api_token,
                max_age=86400,  # 24 小时过期
                httponly=True,
                secure=_is_request_secure(request),
                samesite="lax"
            )
            
            # 清除 oauth_state cookie
            response.delete_cookie("oauth_state")
            
            logging.info("微信登录成功: openid=%s", openid)
            return response
        
        # Handler 未设置
        logging.error("微信 OAuth 回调处理器未注册")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证处理器未配置"
        )
        
    except ValueError as e:
        # 微信 API 错误
        logging.error("微信 OAuth 处理失败: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登录失败: {str(e)}"
        ) from e
    except Exception as e:
        # 其他未预期错误
        logging.exception("微信登录处理异常: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        ) from e


# ---- 企业微信 OAuth 路由 ----
@auth_router.get("/login/wecom", name="wecom.login", response_class=RedirectResponse)
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
    # 检查企业微信登录是否启用
    if not _is_wecom_auth_enabled():
        logging.warning("企业微信登录未配置")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="企业微信登录功能未启用，请联系管理员配置"
        )
    
    # 生成 CSRF token
    state = generate_state("wecom")
    
    # 构建回调 URL
    redirect_uri = _build_callback_url(request, "login/wecom/authorized")
    
    # 初始化企业微信 OAuth 处理器
    wecom_handler = WeComOAuthHandler(WECOM_CONFIG)
    
    # 构建授权 URL
    authorize_url = wecom_handler.build_authorize_url(redirect_uri, state)
    
    # 将 state 存储到 cookie
    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,  # 10 分钟有效期
        httponly=True,
        secure=_is_request_secure(request),
        samesite="lax"
    )
    
    logging.info("用户发起企业微信登录")
    return response


@auth_router.get("/login/wecom/authorized", response_class=RedirectResponse)
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
    # 检查企业微信登录是否启用
    if not _is_wecom_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="企业微信登录功能未启用"
        )
    
    # 获取查询参数
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # 验证必需参数
    if not code or not state:
        logging.error("企业微信回调缺少必需参数")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：缺少必需参数"
        )
    
    # 验证 state（CSRF 防护）
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        logging.error("State 验证失败: stored=%s, received=%s", stored_state, state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：安全验证失败，请重试"
        )
    
    try:
        # 验证 state 签名和时效性
        if not verify_state(state, "wecom", max_age=600):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="授权失败：安全验证失败，请重试"
            )
    except ValueError as e:
        logging.error("State 验证失败: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权失败：验证令牌已过期，请重新登录"
        ) from e
    
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
        handler = getattr(request.app.state, "callback_handler", None)
        if handler:
            success = await handler("wecom", user_info, api_token)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用户信息处理失败"
                )
            
            # 设置认证 Cookie
            response = RedirectResponse(url="/", status_code=302)
            response.set_cookie(
                key="api_token",
                value=api_token,
                max_age=86400,  # 24 小时过期
                httponly=True,
                secure=_is_request_secure(request),
                samesite="lax"
            )
            
            # 清除 oauth_state cookie
            response.delete_cookie("oauth_state")
            
            logging.info("企业微信登录成功: userid=%s", user_info['id'])
            return response
        
        # Handler 未设置
        logging.error("企业微信 OAuth 回调处理器未注册")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证处理器未配置"
        )
        
    except ValueError as e:
        # 企业微信 API 错误
        logging.error("企业微信 OAuth 处理失败: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登录失败: {str(e)}"
        ) from e
    except Exception as e:
        # 其他未预期错误
        logging.exception("企业微信登录处理异常: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        ) from e


@auth_router.get("/auth-status")
async def auth_status(request: Request) -> JSONResponse:
    """
    检查认证状态
    
    返回用户认证状态和可用的登录方式
    
    Args:
        request: FastAPI 请求对象
    
    Returns:
        JSONResponse: 认证状态和用户信息
    """
    user_info, is_authenticated = await validate_user(request)
    
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
                "auth_methods": {
                    "google": _is_google_auth_enabled(),
                    "github": _is_github_auth_enabled(),
                    "wechat": _is_wechat_auth_enabled(),
                    "wecom": _is_wecom_auth_enabled(),
                    "email": _is_email_auth_enabled()
                }
            }
        )
    
    # 未认证 - 返回 200 和可用的登录方式
    return JSONResponse(
        content={
            "authenticated": False,
            "auth_methods": {
                "google": _is_google_auth_enabled(),
                "github": _is_github_auth_enabled(),
                "wechat": _is_wechat_auth_enabled(),
                "wecom": _is_wecom_auth_enabled(),
                "email": _is_email_auth_enabled()
            }
        },
        status_code=200
    )


@auth_router.get("/logout")
@auth_router.post("/logout")
async def logout(request: Request):
    """Handle user logout and delete session cookies.

    Supports both GET and POST methods for backward compatibility:
    - GET: For direct navigation (bookmarks, links, old clients)
    - POST: For programmatic logout from the app
    """
    # For GET requests, redirect to home page
    if request.method == "GET":
        response = RedirectResponse(url="/", status_code=302)
        api_token = request.cookies.get("api_token")
        if api_token:
            response.delete_cookie("api_token")
            await delete_user_token(api_token)
        return response

    # For POST requests, return JSON
    response = JSONResponse(content={"success": True})
    api_token = request.cookies.get("api_token")
    if api_token:
        response.delete_cookie("api_token")
        await delete_user_token(api_token)
    return response

# ---- Hook for app factory ----
def init_auth(app):
    """Initialize OAuth and sessions for the app."""

    config = Config(environ=os.environ)
    oauth = OAuth(config)

    # Only register Google OAuth if credentials are available
    if _is_google_auth_enabled():
        oauth.register(
            name="google",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            api_base_url="https://openidconnect.googleapis.com/v1/",
            client_kwargs={"scope": "openid email profile"},
        )
        logging.info("Google OAuth initialized successfully")
    else:
        logging.info("Google OAuth not configured - skipping registration")

    # Only register GitHub OAuth if credentials are available
    if _is_github_auth_enabled():
        oauth.register(
            name="github",
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )
        logging.info("GitHub OAuth initialized successfully")
    else:
        logging.info("GitHub OAuth not configured - skipping registration")

    # 注册微信 OAuth 客户端（如果配置可用）
    if _is_wechat_auth_enabled():
        oauth.register(
            name="wechat",
            client_id=WECHAT_CONFIG["app_id"],
            client_secret=WECHAT_CONFIG["app_secret"],
            authorize_url=WECHAT_CONFIG["authorize_url"],
            access_token_url=WECHAT_CONFIG["access_token_url"],
            api_base_url=WECHAT_CONFIG["userinfo_url"],
            client_kwargs={"scope": WECHAT_CONFIG["scope"]},
        )
        logging.info("微信 OAuth 初始化成功")
    else:
        logging.info("微信 OAuth 未配置 - 跳过注册")

    # 注册企业微信 OAuth 客户端（如果配置可用）
    if _is_wecom_auth_enabled():
        oauth.register(
            name="wecom",
            client_id=WECOM_CONFIG["corp_id"],
            client_secret=WECOM_CONFIG["corp_secret"],
            authorize_url=WECOM_CONFIG["authorize_url"],
            access_token_url=WECOM_CONFIG["access_token_url"],
            api_base_url=WECOM_CONFIG["userinfo_url"],
            client_kwargs={
                "scope": WECOM_CONFIG["scope"],
                "agentid": WECOM_CONFIG["agent_id"]
            },
        )
        logging.info("企业微信 OAuth 初始化成功")
    else:
        logging.info("企业微信 OAuth 未配置 - 跳过注册")

    app.state.oauth = oauth
