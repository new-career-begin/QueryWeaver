"""
微信和企业微信 OAuth 授权 URL 生成的属性测试

本测试文件使用 hypothesis 进行属性测试,验证授权 URL 生成的正确性属性。

属性测试 (Property-Based Testing) 通过生成大量随机测试用例,
验证系统在各种输入下都满足预定义的属性。

测试的属性:
- 属性 1: 微信授权 URL 包含必需参数
- 属性 2: 企业微信授权 URL 包含必需参数

验证需求: 2.1.2.2, 2.1.2.6, 2.2.2.2, 2.2.2.6
"""

import pytest
from hypothesis import given, strategies as st, settings
from urllib.parse import urlparse, parse_qs

from api.auth.oauth_handlers import WeChatOAuthHandler, WeComOAuthHandler


# -----------------------------
# 测试配置
# -----------------------------

# 微信测试配置
WECHAT_TEST_CONFIG = {
    "app_id": "wx_test_app_id_12345",
    "app_secret": "test_secret_key",
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
    "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    "scope": "snsapi_userinfo"
}

# 企业微信测试配置
WECOM_TEST_CONFIG = {
    "corp_id": "ww_test_corp_id_12345",
    "agent_id": "1000001",
    "corp_secret": "test_corp_secret",
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
    "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
    "scope": "snsapi_base"
}


# -----------------------------
# Hypothesis 策略定义
# -----------------------------

# 生成有效的 URL 字符串
valid_url_strategy = st.builds(
    lambda scheme, host, path: f"{scheme}://{host}{path}",
    scheme=st.sampled_from(["http", "https"]),
    host=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
        min_size=5,
        max_size=30
    ).map(lambda s: s + ".com"),
    path=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=50
    ).map(lambda s: "/" + s)
)

# 生成有效的 state 字符串 (用于 CSRF 防护)
state_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=16,
    max_size=64
)


# -----------------------------
# 属性 1: 微信授权 URL 包含必需参数
# -----------------------------

@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=100, deadline=None)
def test_wechat_authorize_url_contains_required_params(redirect_uri: str, state: str):
    """
    属性测试: 微信授权 URL 必须包含所有必需参数
    
    对于任何有效的 redirect_uri 和 state,生成的微信授权 URL 必须包含:
    - appid: 应用ID
    - redirect_uri: 回调URL
    - response_type: 固定为 "code"
    - scope: 授权作用域
    - state: CSRF 防护令牌
    
    验证需求: 2.1.2.2, 2.1.2.6
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # Act - 执行
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证
    # 1. URL 应该以微信授权地址开头
    assert authorize_url.startswith(WECHAT_TEST_CONFIG["authorize_url"])
    
    # 2. 解析 URL 参数
    parsed_url = urlparse(authorize_url)
    query_params = parse_qs(parsed_url.query)
    
    # 3. 验证必需参数存在
    assert "appid" in query_params, "缺少 appid 参数"
    assert "redirect_uri" in query_params, "缺少 redirect_uri 参数"
    assert "response_type" in query_params, "缺少 response_type 参数"
    assert "scope" in query_params, "缺少 scope 参数"
    assert "state" in query_params, "缺少 state 参数"
    
    # 4. 验证参数值正确
    assert query_params["appid"][0] == WECHAT_TEST_CONFIG["app_id"], \
        "appid 参数值不正确"
    assert query_params["redirect_uri"][0] == redirect_uri, \
        "redirect_uri 参数值不正确"
    assert query_params["response_type"][0] == "code", \
        "response_type 必须为 'code'"
    assert query_params["scope"][0] == WECHAT_TEST_CONFIG["scope"], \
        "scope 参数值不正确"
    assert query_params["state"][0] == state, \
        "state 参数值不正确"
    
    # 5. URL 应该以 #wechat_redirect 结尾
    assert authorize_url.endswith("#wechat_redirect"), \
        "微信授权 URL 必须以 #wechat_redirect 结尾"


@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=100, deadline=None)
def test_wechat_authorize_url_deterministic(redirect_uri: str, state: str):
    """
    属性测试: 微信授权 URL 生成的确定性
    
    对于相同的输入参数,多次调用应该生成完全相同的 URL。
    这确保了 URL 生成逻辑是纯函数,没有副作用。
    
    验证需求: 2.1.2.2
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # Act - 执行两次
    url1 = handler.build_authorize_url(redirect_uri, state)
    url2 = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证
    assert url1 == url2, \
        "相同输入应该生成相同的授权 URL (确定性)"


# -----------------------------
# 属性 2: 企业微信授权 URL 包含必需参数
# -----------------------------

@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=100, deadline=None)
def test_wecom_authorize_url_contains_required_params(redirect_uri: str, state: str):
    """
    属性测试: 企业微信授权 URL 必须包含所有必需参数
    
    对于任何有效的 redirect_uri 和 state,生成的企业微信授权 URL 必须包含:
    - appid: 企业ID (CorpID)
    - redirect_uri: 回调URL
    - response_type: 固定为 "code"
    - scope: 授权作用域
    - agentid: 应用ID
    - state: CSRF 防护令牌
    
    验证需求: 2.2.2.2, 2.2.2.6
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    # Act - 执行
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证
    # 1. URL 应该以企业微信授权地址开头
    assert authorize_url.startswith(WECOM_TEST_CONFIG["authorize_url"])
    
    # 2. 解析 URL 参数
    parsed_url = urlparse(authorize_url)
    query_params = parse_qs(parsed_url.query)
    
    # 3. 验证必需参数存在
    assert "appid" in query_params, "缺少 appid 参数"
    assert "redirect_uri" in query_params, "缺少 redirect_uri 参数"
    assert "response_type" in query_params, "缺少 response_type 参数"
    assert "scope" in query_params, "缺少 scope 参数"
    assert "agentid" in query_params, "缺少 agentid 参数"
    assert "state" in query_params, "缺少 state 参数"
    
    # 4. 验证参数值正确
    assert query_params["appid"][0] == WECOM_TEST_CONFIG["corp_id"], \
        "appid 参数值应该等于 corp_id"
    assert query_params["redirect_uri"][0] == redirect_uri, \
        "redirect_uri 参数值不正确"
    assert query_params["response_type"][0] == "code", \
        "response_type 必须为 'code'"
    assert query_params["scope"][0] == WECOM_TEST_CONFIG["scope"], \
        "scope 参数值不正确"
    assert query_params["agentid"][0] == WECOM_TEST_CONFIG["agent_id"], \
        "agentid 参数值不正确"
    assert query_params["state"][0] == state, \
        "state 参数值不正确"
    
    # 5. URL 应该以 #wechat_redirect 结尾
    assert authorize_url.endswith("#wechat_redirect"), \
        "企业微信授权 URL 必须以 #wechat_redirect 结尾"


@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=100, deadline=None)
def test_wecom_authorize_url_deterministic(redirect_uri: str, state: str):
    """
    属性测试: 企业微信授权 URL 生成的确定性
    
    对于相同的输入参数,多次调用应该生成完全相同的 URL。
    这确保了 URL 生成逻辑是纯函数,没有副作用。
    
    验证需求: 2.2.2.2
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    # Act - 执行两次
    url1 = handler.build_authorize_url(redirect_uri, state)
    url2 = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证
    assert url1 == url2, \
        "相同输入应该生成相同的授权 URL (确定性)"


# -----------------------------
# 边界条件测试
# -----------------------------

def test_wechat_authorize_url_with_special_characters():
    """
    测试: 微信授权 URL 应该正确处理特殊字符
    
    验证 URL 编码是否正确处理特殊字符
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # 包含特殊字符的参数
    redirect_uri = "https://example.com/callback?param=value&other=测试"
    state = "state_with_special_chars_!@#$%"
    
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # URL 应该成功生成
    assert authorize_url is not None
    assert len(authorize_url) > 0
    
    # 解析参数
    parsed_url = urlparse(authorize_url)
    query_params = parse_qs(parsed_url.query)
    
    # 参数应该存在
    assert "redirect_uri" in query_params
    assert "state" in query_params


def test_wecom_authorize_url_with_special_characters():
    """
    测试: 企业微信授权 URL 应该正确处理特殊字符
    
    验证 URL 编码是否正确处理特殊字符
    """
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    # 包含特殊字符的参数
    redirect_uri = "https://example.com/callback?param=value&other=测试"
    state = "state_with_special_chars_!@#$%"
    
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # URL 应该成功生成
    assert authorize_url is not None
    assert len(authorize_url) > 0
    
    # 解析参数
    parsed_url = urlparse(authorize_url)
    query_params = parse_qs(parsed_url.query)
    
    # 参数应该存在
    assert "redirect_uri" in query_params
    assert "state" in query_params
