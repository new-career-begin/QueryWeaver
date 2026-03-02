"""
微信和企业微信 OAuth 错误处理的属性测试

本测试文件使用 hypothesis 进行属性测试,验证错误处理的正确性属性。

测试的属性:
- 属性 10: 配置缺失时返回友好错误
- 属性 11: 授权失败时返回友好错误

验证需求: 2.1.2.9, 2.2.2.9
"""

import pytest
from hypothesis import given, strategies as st, settings

from api.auth.oauth_handlers import (
    WeChatOAuthHandler,
    WeComOAuthHandler,
    _handle_wechat_error,
    _handle_wecom_error,
    WECHAT_ERROR_MESSAGES,
    WECOM_ERROR_MESSAGES
)


# -----------------------------
# 测试配置
# -----------------------------

# 完整的微信测试配置
WECHAT_COMPLETE_CONFIG = {
    "app_id": "wx_test_app_id_12345",
    "app_secret": "test_secret_key",
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
    "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    "scope": "snsapi_userinfo"
}

# 完整的企业微信测试配置
WECOM_COMPLETE_CONFIG = {
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

# 生成已知的微信错误码
known_wechat_errcode_strategy = st.sampled_from(list(WECHAT_ERROR_MESSAGES.keys()))

# 生成未知的微信错误码 (不在映射表中)
unknown_wechat_errcode_strategy = st.integers(min_value=90000, max_value=99999)

# 生成已知的企业微信错误码
known_wecom_errcode_strategy = st.sampled_from(list(WECOM_ERROR_MESSAGES.keys()))

# 生成未知的企业微信错误码
unknown_wecom_errcode_strategy = st.integers(min_value=900000, max_value=999999)

# 生成错误消息字符串
error_message_strategy = st.text(min_size=1, max_size=100)


# -----------------------------
# 属性 10: 配置缺失时返回友好错误
# -----------------------------

def test_wechat_handler_requires_app_id():
    """
    属性测试: 微信 OAuth 处理器必须要求 app_id 配置
    
    当配置中缺少 app_id 时,应该抛出 KeyError 或提供清晰的错误信息。
    
    验证需求: 2.1.2.9
    """
    # Arrange - 准备缺少 app_id 的配置
    incomplete_config = {
        "app_secret": "test_secret",
        "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
        "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
        "scope": "snsapi_userinfo"
    }
    
    # Act & Assert - 应该抛出错误
    with pytest.raises(KeyError):
        WeChatOAuthHandler(incomplete_config)


def test_wechat_handler_requires_app_secret():
    """
    属性测试: 微信 OAuth 处理器必须要求 app_secret 配置
    
    当配置中缺少 app_secret 时,应该抛出 KeyError 或提供清晰的错误信息。
    
    验证需求: 2.1.2.9
    """
    # Arrange - 准备缺少 app_secret 的配置
    incomplete_config = {
        "app_id": "wx_test_app_id",
        "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
        "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
        "scope": "snsapi_userinfo"
    }
    
    # Act & Assert - 应该抛出错误
    with pytest.raises(KeyError):
        WeChatOAuthHandler(incomplete_config)


def test_wecom_handler_requires_corp_id():
    """
    属性测试: 企业微信 OAuth 处理器必须要求 corp_id 配置
    
    当配置中缺少 corp_id 时,应该抛出 KeyError 或提供清晰的错误信息。
    
    验证需求: 2.2.2.9
    """
    # Arrange - 准备缺少 corp_id 的配置
    incomplete_config = {
        "agent_id": "1000001",
        "corp_secret": "test_secret",
        "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
        "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
        "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
        "scope": "snsapi_base"
    }
    
    # Act & Assert - 应该抛出错误
    with pytest.raises(KeyError):
        WeComOAuthHandler(incomplete_config)


def test_wecom_handler_requires_agent_id():
    """
    属性测试: 企业微信 OAuth 处理器必须要求 agent_id 配置
    
    当配置中缺少 agent_id 时,应该抛出 KeyError 或提供清晰的错误信息。
    
    验证需求: 2.2.2.9
    """
    # Arrange - 准备缺少 agent_id 的配置
    incomplete_config = {
        "corp_id": "ww_test_corp_id",
        "corp_secret": "test_secret",
        "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
        "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
        "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
        "scope": "snsapi_base"
    }
    
    # Act & Assert - 应该抛出错误
    with pytest.raises(KeyError):
        WeComOAuthHandler(incomplete_config)


# -----------------------------
# 属性 11: 授权失败时返回友好错误
# -----------------------------

@given(errcode=known_wechat_errcode_strategy)
@settings(max_examples=50, deadline=None)
def test_wechat_error_handler_returns_friendly_message_for_known_errors(errcode: int):
    """
    属性测试: 微信错误处理器应该为已知错误码返回友好的中文错误消息
    
    对于任何已知的微信错误码,错误处理器应该返回:
    - 非空的错误消息
    - 中文错误消息
    - 不包含原始错误码的技术细节 (对用户友好)
    
    验证需求: 2.1.2.9
    
    Args:
        errcode: 随机选择的已知微信错误码
    """
    # Act - 执行错误处理
    friendly_message = _handle_wechat_error(errcode, "原始错误消息")
    
    # Assert - 验证友好错误消息
    assert friendly_message is not None, "错误消息不应该为 None"
    assert len(friendly_message) > 0, "错误消息不应该为空"
    assert isinstance(friendly_message, str), "错误消息应该是字符串"
    
    # 验证是预定义的友好消息
    assert friendly_message == WECHAT_ERROR_MESSAGES[errcode], \
        "应该返回预定义的友好错误消息"
    
    # 验证消息是中文 (至少包含一些中文字符)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in friendly_message)
    assert has_chinese, "错误消息应该包含中文字符"


@given(
    errcode=unknown_wechat_errcode_strategy,
    errmsg=error_message_strategy
)
@settings(max_examples=50, deadline=None)
def test_wechat_error_handler_returns_generic_message_for_unknown_errors(
    errcode: int,
    errmsg: str
):
    """
    属性测试: 微信错误处理器应该为未知错误码返回通用错误消息
    
    对于任何未知的微信错误码,错误处理器应该返回:
    - 包含错误码的通用消息
    - 提示用户稍后重试
    - 中文错误消息
    
    验证需求: 2.1.2.9
    
    Args:
        errcode: 随机生成的未知错误码
        errmsg: 随机生成的原始错误消息
    """
    # Act - 执行错误处理
    friendly_message = _handle_wechat_error(errcode, errmsg)
    
    # Assert - 验证通用错误消息
    assert friendly_message is not None
    assert len(friendly_message) > 0
    
    # 验证包含错误码
    assert str(errcode) in friendly_message, \
        "未知错误的消息应该包含错误码"
    
    # 验证包含"微信服务错误"或类似提示
    assert "微信服务错误" in friendly_message or "微信" in friendly_message, \
        "应该明确指出是微信服务错误"
    
    # 验证包含"稍后重试"或类似建议
    assert "稍后重试" in friendly_message or "重试" in friendly_message, \
        "应该建议用户稍后重试"


@given(errcode=known_wecom_errcode_strategy)
@settings(max_examples=50, deadline=None)
def test_wecom_error_handler_returns_friendly_message_for_known_errors(errcode: int):
    """
    属性测试: 企业微信错误处理器应该为已知错误码返回友好的中文错误消息
    
    对于任何已知的企业微信错误码,错误处理器应该返回:
    - 非空的错误消息
    - 中文错误消息
    - 不包含原始错误码的技术细节 (对用户友好)
    
    验证需求: 2.2.2.9
    
    Args:
        errcode: 随机选择的已知企业微信错误码
    """
    # Act - 执行错误处理
    friendly_message = _handle_wecom_error(errcode, "原始错误消息")
    
    # Assert - 验证友好错误消息
    assert friendly_message is not None
    assert len(friendly_message) > 0
    assert isinstance(friendly_message, str)
    
    # 验证是预定义的友好消息
    assert friendly_message == WECOM_ERROR_MESSAGES[errcode], \
        "应该返回预定义的友好错误消息"
    
    # 验证消息是中文
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in friendly_message)
    assert has_chinese, "错误消息应该包含中文字符"


@given(
    errcode=unknown_wecom_errcode_strategy,
    errmsg=error_message_strategy
)
@settings(max_examples=50, deadline=None)
def test_wecom_error_handler_returns_generic_message_for_unknown_errors(
    errcode: int,
    errmsg: str
):
    """
    属性测试: 企业微信错误处理器应该为未知错误码返回通用错误消息
    
    对于任何未知的企业微信错误码,错误处理器应该返回:
    - 包含错误码的通用消息
    - 提示用户稍后重试
    - 中文错误消息
    
    验证需求: 2.2.2.9
    
    Args:
        errcode: 随机生成的未知错误码
        errmsg: 随机生成的原始错误消息
    """
    # Act - 执行错误处理
    friendly_message = _handle_wecom_error(errcode, errmsg)
    
    # Assert - 验证通用错误消息
    assert friendly_message is not None
    assert len(friendly_message) > 0
    
    # 验证包含错误码
    assert str(errcode) in friendly_message, \
        "未知错误的消息应该包含错误码"
    
    # 验证包含"企业微信服务错误"或类似提示
    assert "企业微信服务错误" in friendly_message or "企业微信" in friendly_message, \
        "应该明确指出是企业微信服务错误"
    
    # 验证包含"稍后重试"或类似建议
    assert "稍后重试" in friendly_message or "重试" in friendly_message, \
        "应该建议用户稍后重试"


# -----------------------------
# 特定错误场景测试
# -----------------------------

def test_wechat_error_40001_app_secret_error():
    """
    测试: 微信错误码 40001 (AppSecret 错误) 应该返回明确的错误消息
    
    这是配置错误,应该提示用户联系管理员。
    """
    friendly_message = _handle_wechat_error(40001, "invalid credential")
    
    assert "AppSecret" in friendly_message
    assert "管理员" in friendly_message
    assert "错误" in friendly_message


def test_wechat_error_40029_invalid_code():
    """
    测试: 微信错误码 40029 (授权码无效) 应该返回明确的错误消息
    
    这是用户操作问题,应该提示用户重新登录。
    """
    friendly_message = _handle_wechat_error(40029, "invalid code")
    
    assert "授权码" in friendly_message or "code" in friendly_message.lower()
    assert "重新登录" in friendly_message or "重试" in friendly_message


def test_wechat_error_42001_token_expired():
    """
    测试: 微信错误码 42001 (access_token 已过期) 应该返回明确的错误消息
    
    这是 token 过期问题,应该提示用户重新登录。
    """
    friendly_message = _handle_wechat_error(42001, "access_token expired")
    
    assert "过期" in friendly_message
    assert "重新登录" in friendly_message


def test_wecom_error_40001_invalid_secret():
    """
    测试: 企业微信错误码 40001 (secret 不合法) 应该返回明确的错误消息
    
    这是配置错误,应该提示用户联系管理员。
    """
    friendly_message = _handle_wecom_error(40001, "invalid secret")
    
    assert "secret" in friendly_message
    assert "管理员" in friendly_message


def test_wecom_error_40029_invalid_oauth_code():
    """
    测试: 企业微信错误码 40029 (oauth_code 不合法) 应该返回明确的错误消息
    
    这是用户操作问题,应该提示用户重新登录。
    """
    friendly_message = _handle_wecom_error(40029, "invalid oauth_code")
    
    assert "oauth_code" in friendly_message or "code" in friendly_message.lower()
    assert "重新登录" in friendly_message


def test_wecom_error_42001_token_expired():
    """
    测试: 企业微信错误码 42001 (access_token 已过期) 应该返回明确的错误消息
    
    这是 token 过期问题,应该提示用户重新登录。
    """
    friendly_message = _handle_wecom_error(42001, "access_token expired")
    
    assert "过期" in friendly_message
    assert "重新登录" in friendly_message


# -----------------------------
# 错误消息质量测试
# -----------------------------

def test_all_wechat_error_messages_are_chinese():
    """
    测试: 所有预定义的微信错误消息都应该是中文
    
    确保用户面向的错误消息都是中文,便于理解。
    """
    for errcode, message in WECHAT_ERROR_MESSAGES.items():
        # 验证消息包含中文字符
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in message)
        assert has_chinese, f"错误码 {errcode} 的消息应该包含中文: {message}"
        
        # 验证消息不为空
        assert len(message) > 0, f"错误码 {errcode} 的消息不应该为空"


def test_all_wecom_error_messages_are_chinese():
    """
    测试: 所有预定义的企业微信错误消息都应该是中文
    
    确保用户面向的错误消息都是中文,便于理解。
    """
    for errcode, message in WECOM_ERROR_MESSAGES.items():
        # 验证消息包含中文字符
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in message)
        assert has_chinese, f"错误码 {errcode} 的消息应该包含中文: {message}"
        
        # 验证消息不为空
        assert len(message) > 0, f"错误码 {errcode} 的消息不应该为空"


def test_wechat_error_messages_provide_actionable_guidance():
    """
    测试: 微信错误消息应该提供可操作的指导
    
    错误消息应该告诉用户该怎么做,而不仅仅是描述问题。
    """
    # 检查一些关键错误码是否提供了指导
    actionable_keywords = ["请", "联系", "重新", "重试", "检查"]
    
    # 配置错误应该提示联系管理员
    assert any(keyword in WECHAT_ERROR_MESSAGES[40001] for keyword in actionable_keywords)
    
    # 授权码错误应该提示重新登录
    assert any(keyword in WECHAT_ERROR_MESSAGES[40029] for keyword in actionable_keywords)


def test_wecom_error_messages_provide_actionable_guidance():
    """
    测试: 企业微信错误消息应该提供可操作的指导
    
    错误消息应该告诉用户该怎么做,而不仅仅是描述问题。
    """
    # 检查一些关键错误码是否提供了指导
    actionable_keywords = ["请", "联系", "重新", "重试", "检查"]
    
    # 配置错误应该提示联系管理员
    assert any(keyword in WECOM_ERROR_MESSAGES[40001] for keyword in actionable_keywords)
    
    # 授权码错误应该提示重新登录
    assert any(keyword in WECOM_ERROR_MESSAGES[40029] for keyword in actionable_keywords)
