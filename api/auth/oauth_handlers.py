"""OAuth signal handlers for Google and GitHub authentication.

Lightweight handlers are stored on the FastAPI app state so route
callbacks can invoke them when processing OAuth responses.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI
from authlib.integrations.starlette_client import OAuth

from .user_management import ensure_user_in_organizations
from .token_cache import token_cache


# -----------------------------
# 微信 API 错误码映射
# -----------------------------
WECHAT_ERROR_MESSAGES = {
    40001: "AppSecret 错误，请联系管理员",
    40002: "请确保 grant_type 字段值为 authorization_code",
    40003: "无效的 OpenID，请重新登录",
    40013: "AppID 无效，请联系管理员",
    40029: "授权码无效，请重新登录",
    40163: "授权码已使用，请重新登录",
    41001: "缺少 access_token 参数，请重新登录",
    41002: "缺少 appid 参数",
    41003: "缺少 refresh_token 参数",
    41004: "缺少 secret 参数",
    41005: "缺少多媒体文件数据",
    41006: "缺少 media_id 参数",
    42001: "access_token 已过期，请重新登录",
    42002: "refresh_token 已过期，请重新登录",
    42003: "订阅时间已过期",
    42007: "用户修改微信密码，access_token 已失效，请重新登录",
    43001: "需要 GET 请求",
    43002: "需要 POST 请求",
    43003: "需要 HTTPS 请求",
    43004: "需要接收者关注",
    43005: "需要好友关系",
    45001: "多媒体文件大小超过限制",
    45002: "消息内容超过限制",
    45003: "标题字段超过限制",
    45004: "描述字段超过限制",
    45005: "链接字段超过限制",
    45006: "图片链接字段超过限制",
    45007: "语音播放时间超过限制",
    45008: "图文消息超过限制",
    45009: "接口调用超过限制",
    45010: "创建菜单个数超过限制",
    45011: "API 调用太频繁，请稍候再试",
    45015: "回复时间超过限制",
    45016: "系统分组，不允许修改",
    45017: "分组名字过长",
    45018: "分组数量超过上限",
    50001: "用户未授权该 API",
    50002: "用户受限，无法使用该功能",
}


def _handle_wechat_error(errcode: int, errmsg: str = "") -> str:
    """
    处理微信 API 错误，返回友好的错误消息
    
    Args:
        errcode: 微信 API 错误码
        errmsg: 微信 API 原始错误消息
        
    Returns:
        友好的中文错误消息
    """
    friendly_message = WECHAT_ERROR_MESSAGES.get(
        errcode,
        f"微信服务错误（错误码：{errcode}），请稍后重试"
    )
    
    # 记录详细错误日志
    logging.error(
        "微信 API 错误: errcode=%s, errmsg=%s, friendly_message=%s",
        errcode,
        errmsg,
        friendly_message
    )
    
    return friendly_message


# -----------------------------
# 企业微信 API 错误码映射
# -----------------------------
WECOM_ERROR_MESSAGES = {
    -1: "系统繁忙，请稍后重试",
    0: "请求成功",
    40001: "不合法的 secret 参数，请联系管理员",
    40003: "无效的 UserID，请重新登录",
    40013: "不合法的 CorpID，请联系管理员",
    40014: "不合法的 access_token，请重新登录",
    40029: "不合法的 oauth_code，请重新登录",
    40054: "不合法的子菜单 URL 长度",
    40055: "不合法的菜单 URL 域名",
    40056: "不合法的按钮个数",
    40057: "不合法的按钮类型",
    40058: "不合法的按钮名字长度",
    40059: "不合法的按钮 KEY 长度",
    40060: "不合法的按钮 URL 长度",
    40061: "不合法的菜单版本号",
    40062: "不合法的子菜单级数",
    40063: "不合法的子菜单按钮个数",
    40064: "不合法的子菜单按钮类型",
    40065: "不合法的子菜单按钮名字长度",
    40066: "不合法的子菜单按钮 KEY 长度",
    40067: "不合法的子菜单按钮 URL 长度",
    40068: "不合法的自定义菜单使用成员",
    40069: "不合法的自定义菜单使用部门",
    40070: "不合法的自定义菜单使用标签",
    40071: "不合法的自定义菜单使用标签",
    40072: "不合法的自定义菜单使用部门",
    41001: "缺少 access_token 参数，请重新登录",
    41002: "缺少 corpid 参数",
    41004: "缺少 secret 参数",
    41006: "缺少 media_id 参数",
    42001: "access_token 已过期，请重新登录",
    42007: "用户修改密码，access_token 已失效，请重新登录",
    42009: "接口调用超过限制",
    43001: "需要 GET 请求",
    43002: "需要 POST 请求",
    43003: "需要 HTTPS 请求",
    43004: "需要成员已关注",
    43005: "需要企业已认证",
    44001: "多媒体文件为空",
    44002: "POST 的数据包为空",
    44003: "图文消息内容为空",
    44004: "文本消息内容为空",
    45001: "多媒体文件大小超过限制",
    45002: "消息内容大小超过限制",
    45004: "描述字段超过限制",
    45007: "语音播放时间超过限制",
    45008: "图文消息的文章数量超过限制",
    45009: "接口调用超过限制",
    45022: "应用已被禁用",
    46001: "不存在媒体数据",
    46002: "不存在的菜单版本",
    46003: "不存在的菜单数据",
    46004: "不存在的成员",
    47001: "解析 JSON/XML 内容错误",
    48001: "API 功能未授权",
    48002: "API 禁止调用",
    48003: "子用户 API 禁止调用",
    48004: "API 接口被封禁",
    50001: "redirect_uri 未授权",
    50002: "成员不在权限范围",
    50003: "应用已被禁用",
    60001: "部门长度不符合限制",
    60002: "部门层级深度超过限制",
    60003: "部门不存在",
    60004: "父部门不存在",
    60005: "部门下存在成员",
    60006: "部门下存在子部门",
    60007: "不允许删除根部门",
    60008: "部门已存在",
    60009: "部门名称含有非法字符",
    60010: "部门存在循环关系",
    60011: "指定的成员/部门/标签参数无效",
    60012: "不允许删除默认应用",
    60020: "访客模式不允许修改部门",
    60021: "不允许设置企业",
    60028: "不允许修改第三方应用的主页 URL",
    60102: "UserID 已存在",
    60103: "手机号码不合法",
    60104: "手机号码已存在",
    60105: "邮箱不合法",
    60106: "邮箱已存在",
    60107: "微信号不合法",
    60110: "用户已禁用",
    60111: "UserID 不存在",
    60112: "成员 name 不合法",
    60123: "无效的部门 ID",
    60124: "无效的父部门 ID",
    60125: "非法部门名字",
    60127: "缺少 department 或 department 为空",
    81001: "内部错误",
    81013: "UserID、部门 ID、标签 ID 全部非法或无权限",
    81014: "标签添加成员，包含的 UserID、部门 ID 全部非法或无权限",
    81015: "标签删除成员，包含的 UserID 全部非法或无权限",
    81016: "标签 ID 不存在",
    81017: "标签名已存在",
    82001: "指定的成员/部门/标签全部为空",
    82002: "不合法的 PartyID 列表长度",
    82003: "不合法的 TagID 列表长度",
    84014: "成员票据过期",
    84015: "成员票据无效",
    84019: "缺少 templateid 参数",
    84020: "templateid 不存在",
    84021: "缺少 register_code 参数",
    84022: "无效的 register_code 参数",
    84023: "不允许调用设置通讯录同步完成接口",
    84024: "无注册信息",
    84025: "不允许修改第三方应用的主页 URL",
    85002: "包含不合法的词语",
    85004: "每企业每个月设置的可信域名不可超过 20 个",
    85005: "可信域名不能超过 200 个字符",
    86001: "不合法的会话 ID",
    86003: "不存在的会话 ID",
    86004: "不合法的会话名",
    86005: "不合法的会话管理员",
    86006: "不合法的成员列表大小",
    86007: "不存在的成员",
    86101: "需要会话管理员权限",
    86201: "缺少会话 ID",
    86202: "缺少会话名",
    86203: "缺少会话管理员",
    86204: "缺少成员",
    86205: "非法的会话 ID 长度",
    86206: "非法的会话 ID 数值",
    86207: "会话管理员不在用户列表中",
    86208: "消息服务未开启",
    86209: "缺少操作者",
    86210: "缺少会话类型",
    86211: "缺少会话 chatid",
    86213: "会话已存在",
    86214: "会话名称已存在",
    86215: "会话成员不在权限范围",
    86216: "会话不存在",
    86217: "不允许操作外部会话",
    86218: "不允许设置多个会话管理员",
    86219: "设置会话管理员失败",
    86220: "会话成员不在权限范围",
    88001: "缺少 checkin_data 参数",
    88002: "打卡数据已存在",
    90001: "未认证摇一摇周边",
    90002: "缺少摇一摇周边 ticket 参数",
    90003: "摇一摇周边 ticket 参数不合法",
    91004: "secret 不合法",
    301002: "无权限操作指定的应用",
    301005: "不允许删除创建者",
    301012: "参数 position 不合法",
    301013: "标签个数超过限制",
    301014: "成员不在应用可见范围",
    301021: "应用 ID 不存在",
    301022: "应用名称不合法",
    301024: "不合法的应用类型",
    600001: "不合法的 agentid",
    600002: "不合法的消息类型",
    600003: "不合法的 secret",
    600004: "不合法的模板 ID",
    610001: "永久素材数量已达上限",
    610002: "素材不存在",
}


def _handle_wecom_error(errcode: int, errmsg: str = "") -> str:
    """
    处理企业微信 API 错误，返回友好的错误消息
    
    Args:
        errcode: 企业微信 API 错误码
        errmsg: 企业微信 API 原始错误消息
        
    Returns:
        友好的中文错误消息
    """
    friendly_message = WECOM_ERROR_MESSAGES.get(
        errcode,
        f"企业微信服务错误（错误码：{errcode}），请稍后重试"
    )
    
    # 记录详细错误日志
    logging.error(
        "企业微信 API 错误: errcode=%s, errmsg=%s, friendly_message=%s",
        errcode,
        errmsg,
        friendly_message
    )
    
    return friendly_message


def setup_oauth_handlers(app: FastAPI, oauth: OAuth):
    """Set up OAuth handlers for both Google and GitHub."""

    # Store oauth in app state for access in routes
    app.state.oauth = oauth

    async def handle_callback(provider: str, user_info: Dict[str, Any], api_token: str):
        """Handle Provider OAuth callback processing"""
        try:
            user_id = user_info.get("id")
            email = user_info.get("email")
            name = user_info.get("name")

            # Validate required fields
            if not user_id or not email:
                logging.error("Missing required fields from %s OAuth response", provider)
                return False

            # Check if identity exists in Organizations graph, create if new
            _, _ = await ensure_user_in_organizations(
                user_id,
                email,
                name,
                provider,
                api_token,
                user_info.get("picture"),
            )

            return True
        except Exception as exc:  # capture exception for logging, pylint: disable=broad-exception-caught
            logging.error("Error handling %s OAuth callback: %s", provider, exc)
            return False

    # Store handlers in app state for use in route callbacks
    app.state.callback_handler = handle_callback


# -----------------------------
# 微信 OAuth 处理器
# -----------------------------
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
        
        # 缓存键
        self._cache_key = f"wechat:{self.app_id}"

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

        logging.info("构建微信授权 URL: %s", url)
        return url

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        使用授权码换取 access_token

        Args:
            code: 微信返回的授权码

        Returns:
            包含 access_token, openid 等信息的字典

        Raises:
            ValueError: 当请求失败时抛出
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
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    friendly_message = _handle_wechat_error(errcode, errmsg)
                    raise ValueError(friendly_message)

                # 缓存 token 到全局缓存
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)
                
                if access_token:
                    # 使用 openid 作为缓存键的一部分，支持多用户
                    openid = data.get("openid")
                    cache_key = f"{self._cache_key}:{openid}"
                    token_cache.set(cache_key, access_token, expires_in)

                logging.info("成功获取微信 access_token, openid: %s", data.get('openid'))
                return data

            except httpx.HTTPError as e:
                logging.error("请求微信 access_token 失败: %s", str(e))
                raise ValueError(f"网络请求失败: {str(e)}") from e

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
            ValueError: 当请求失败时抛出
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
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    friendly_message = _handle_wechat_error(errcode, errmsg)
                    raise ValueError(friendly_message)

                logging.info("成功获取微信用户信息, openid: %s", openid)
                return data

            except httpx.HTTPError as e:
                logging.error("请求微信用户信息失败: %s", str(e))
                raise ValueError(f"网络请求失败: {str(e)}") from e

    def parse_user_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析微信用户信息为标准格式

        Args:
            user_data: 微信返回的原始用户数据

        Returns:
            标准化的用户信息字典
        """
        openid = user_data.get("openid")
        return {
            "id": openid,
            "email": f"{openid}@wechat.queryweaver.local",
            "name": user_data.get("nickname", "微信用户"),
            "picture": user_data.get("headimgurl"),
            "unionid": user_data.get("unionid"),  # 可选
            "provider": "wechat"
        }


# -----------------------------
# 企业微信 OAuth 处理器
# -----------------------------
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
        
        # 缓存键
        self._cache_key = f"wecom:{self.corp_id}"

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

        logging.info("构建企业微信授权 URL: %s", url)
        return url

    async def get_access_token(self) -> str:
        """
        获取企业微信 access_token（企业内部应用）

        Returns:
            access_token 字符串

        Raises:
            ValueError: 当请求失败时抛出
        """
        # 检查缓存
        cached_token = token_cache.get(self._cache_key)
        if cached_token:
            logging.debug("使用缓存的企业微信 access_token")
            return cached_token

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
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    friendly_message = _handle_wecom_error(errcode, errmsg)
                    raise ValueError(friendly_message)

                # 缓存 token 到全局缓存（提前 5 分钟过期）
                access_token = data["access_token"]
                expires_in = data.get("expires_in", 7200)
                token_cache.set(self._cache_key, access_token, expires_in, buffer_seconds=300)

                logging.info("成功获取企业微信 access_token")
                return access_token

            except httpx.HTTPError as e:
                logging.error("请求企业微信 access_token 失败: %s", str(e))
                raise ValueError(f"网络请求失败: {str(e)}") from e

    async def get_user_info(self, code: str) -> Dict[str, Any]:
        """
        使用授权码获取用户信息

        Args:
            code: 企业微信返回的授权码

        Returns:
            用户信息字典

        Raises:
            ValueError: 当请求失败时抛出
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
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    friendly_message = _handle_wecom_error(errcode, errmsg)
                    raise ValueError(friendly_message)

                user_id = data.get("userid") or data.get("UserId")
                logging.info("成功获取企业微信用户信息, userid: %s", user_id)

                # 获取详细用户信息
                return await self.get_user_detail(user_id)

            except httpx.HTTPError as e:
                logging.error("请求企业微信用户信息失败: %s", str(e))
                raise ValueError(f"网络请求失败: {str(e)}") from e

    async def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户详细信息

        Args:
            user_id: 企业微信用户 ID

        Returns:
            详细用户信息字典

        Raises:
            ValueError: 当请求失败时抛出
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
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    friendly_message = _handle_wecom_error(errcode, errmsg)
                    raise ValueError(friendly_message)

                return data

            except httpx.HTTPError as e:
                logging.error("请求企业微信用户详情失败: %s", str(e))
                raise ValueError(f"网络请求失败: {str(e)}") from e

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
