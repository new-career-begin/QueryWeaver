"""Application factory for the text2sql FastAPI app."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from api.auth.oauth_handlers import setup_oauth_handlers
from api.auth.user_management import SECRET_KEY
from api.routes.auth import auth_router, init_auth
from api.routes.graphs import graphs_router
from api.routes.database import database_router
from api.routes.tokens import tokens_router
from api.routes.config import router as config_router
from api.config import validate_oauth_config
from api.logging_config import configure_logging
from api.connection_pool import ConnectionPoolManager

# Load environment variables from .env file
load_dotenv()

# 配置日志
# 使用环境变量控制日志格式：USE_JSON_LOGS=true 启用 JSON 格式（生产环境推荐）
use_json_logs = os.getenv("USE_JSON_LOGS", "true").lower() in ("1", "true", "yes")
configure_logging(use_json=use_json_logs, level=logging.INFO)

# 验证 OAuth 配置
validate_oauth_config()


class SecurityMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Middleware for security checks including static file access"""

    STATIC_PREFIX = "/static/"

    async def dispatch(self, request: Request, call_next):
        # Block directory access in static files
        if request.url.path.startswith(self.STATIC_PREFIX):
            # Remove /static/ prefix to get the actual path
            filename = request.url.path[len(self.STATIC_PREFIX) :]
            # Basic security check for directory traversal
            if not filename or "../" in filename or filename.endswith("/"):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        response = await call_next(request)

        # Add HSTS header to prevent man-in-the-middle attacks
        # max-age=31536000: 1 year in seconds
        # includeSubDomains: apply to all subdomains
        # preload: eligible for browser HSTS preload lists
        hsts_value = "max-age=31536000; includeSubDomains; preload"
        response.headers["Strict-Transport-Security"] = hsts_value

        return response


def create_app():
    """Create and configure the FastAPI application."""

    # 初始化 HTTP 连接池
    # 在应用启动时配置全局连接池，用于复用 HTTP 连接
    ConnectionPoolManager.initialize()

    # Create the FastAPI app instance just to set the o routes
    # Will be merged with MCP app later if MCP is enabled
    app = FastAPI(
        title="QueryWeaver"
    )

    # Include routers
    app.include_router(auth_router)
    app.include_router(graphs_router, prefix="/graphs")
    app.include_router(database_router)
    app.include_router(tokens_router, prefix="/tokens")
    app.include_router(config_router)  # LLM 配置管理路由



    # Control MCP endpoints via environment variable DISABLE_MCP
    # Default: MCP is enabled unless DISABLE_MCP is set to true
    disable_mcp = os.getenv("DISABLE_MCP", "false").lower() in ("1", "true", "yes")
    mcp_app = None
    if disable_mcp:
        logging.info("MCP endpoints disabled via DISABLE_MCP environment variable")
        routes=[
            *app.routes,  # Original API routes only
        ]
    else:
        mcp = FastMCP.from_fastapi(
            app=app,
            name="queryweaver",
            route_maps=[
                RouteMap(tags={"mcp_resource"}, mcp_type=MCPType.RESOURCE),
                RouteMap(
                    tags={"mcp_resource_template"},
                    mcp_type=MCPType.RESOURCE_TEMPLATE,
                ),
                RouteMap(tags={"mcp_tool"}, mcp_type=MCPType.TOOL),
                RouteMap(mcp_type=MCPType.EXCLUDE),
            ],
        )
        mcp_app = mcp.http_app(path="/mcp")

        # Combine routes from both apps
        routes = [
            *mcp_app.routes,  # MCP routes
            *app.routes,  # Original API routes
        ]

    # Combine the MCP app and original app
    app = FastAPI(
        title="QueryWeaver",
        description="Text2SQL with Graph-Powered Schema Understanding",
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "User authentication and OAuth operations",
            },
            {
                "name": "Graphs & Databases",
                "description": "Database schema management and querying",
            },
            {
                "name": "Database Connection",
                "description": "Connect to external databases",
            },
            {
                "name": "API Tokens",
                "description": "Manage API tokens for authentication",
            },
        ],
        routes=routes,
        lifespan=mcp_app.lifespan if mcp_app else None,
    )

    # Add security schemes to OpenAPI after app creation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        # pylint: disable=import-outside-toplevel
        from fastapi.openapi.utils import get_openapi

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "ApiTokenAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "api_token",
                "description": "API token for programmatic access. "
                "Generate via POST /tokens/generate after OAuth login.",
            },
            "SessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session",
                "description": "Session cookie for web browsers. "
                "Login via Google/GitHub at /login/google or /login/github.",
            },
        }

        # Add security requirements to protected endpoints
        for _, path_item in openapi_schema["paths"].items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Check if endpoint has token_required (look for 401 response)
                    if "401" in operation.get("responses", {}):
                        # Use OR logic - user needs EITHER ApiTokenAuth OR
                        # SessionAuth (not both)
                        operation["security"] = [
                            {"ApiTokenAuth": []},  # Option 1: API Token
                            {"SessionAuth": []},  # Option 2: OAuth Session
                        ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        same_site="lax",  # allow top-level OAuth GET redirects to send cookies
        https_only=False,  # True for HTTPS environments (staging/prod), False for HTTP dev
        max_age=60 * 60 * 24 * 14,  # 14 days - measured by seconds
    )

    # Add security middleware
    app.add_middleware(SecurityMiddleware)

    # Mount static files from the React build (app/dist)
    # This serves the bundled assets (JS, CSS, images, etc.)
    dist_path = os.path.join(os.path.dirname(__file__), "../app/dist")
    if os.path.exists(dist_path):
        # Mount the built React app's static assets
        # Vite bundles JS/CSS into assets/, and copies public/ files to dist root
        app.mount(
            "/assets",
            StaticFiles(directory=os.path.join(dist_path, "assets")),
            name="assets"
        )

        # Mount public folders if they exist
        if os.path.exists(os.path.join(dist_path, "icons")):
            app.mount(
                "/icons",
                StaticFiles(directory=os.path.join(dist_path, "icons")),
                name="icons"
            )
        if os.path.exists(os.path.join(dist_path, "img")):
            app.mount(
                "/img",
                StaticFiles(directory=os.path.join(dist_path, "img")),
                name="img"
            )
        
        # Mount locales folder for i18n translations
        if os.path.exists(os.path.join(dist_path, "locales")):
            app.mount(
                "/locales",
                StaticFiles(directory=os.path.join(dist_path, "locales")),
                name="locales"
            )

        # Serve favicon and other root files
        app.mount("/static", StaticFiles(directory=dist_path), name="static")
    else:
        logging.warning(
            "React build directory not found at %s. "
            "Run 'cd app && npm run build' to build the frontend.",
            dist_path
        )

    # Initialize authentication (OAuth and sessions)
    init_auth(app)

    setup_oauth_handlers(app, app.state.oauth)

    # 添加应用关闭事件处理器，清理连接池资源
    @app.on_event("shutdown")
    async def shutdown_event():
        """
        应用关闭时的事件处理器
        
        清理 HTTP 连接池资源，确保所有连接正确关闭
        """
        logging.info("应用关闭，清理连接池资源")
        await ConnectionPoolManager.close_all()
        logging.info("连接池资源已清理")

    # Serve favicon
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Serve the favicon from the React build directory."""
        favicon_path = os.path.join(dist_path, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/x-icon")
        return JSONResponse({"error": "Favicon not found"}, status_code=404)

    # Handle Chrome DevTools well-known requests
    @app.get("/.well-known/{path:path}", include_in_schema=False)
    async def well_known(path: str):
        """
        处理 .well-known 路径请求
        
        Chrome 开发者工具会请求这些路径，返回 404 而不是 422
        避免在日志中产生不必要的错误信息
        """
        return JSONResponse(
            {"error": "Not found"},
            status_code=404
        )

    @app.exception_handler(Exception)
    async def handle_oauth_error(
        request: Request, exc: Exception
    ):  # pylint: disable=unused-argument
        """Handle OAuth-related errors gracefully"""
        # Check if it's an OAuth-related error
        # TODO check this scenario, pylint: disable=fixme
        if "token" in str(exc).lower() or "oauth" in str(exc).lower():
            logging.warning("OAuth error occurred: %s", exc)
            return RedirectResponse(url="/", status_code=302)

        # If it's an HTTPException, re-raise so FastAPI handles it properly
        if isinstance(exc, HTTPException):
            raise exc

        # For other errors, let them bubble up
        raise exc

    # Serve React app for all non-API routes (SPA catch-all)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(_full_path: str):
        """Serve the React app for all routes not handled by API endpoints."""
        # Serve index.html for the React SPA
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"error": "React app not found"}, status_code=404)

    return app
