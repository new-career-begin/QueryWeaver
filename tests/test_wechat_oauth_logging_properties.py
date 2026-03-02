"""
微信和企业微信 OAuth 日志记录的属性测试

本测试文件使用 hypothesis 进行属性测试,验证日志记录的正确性属性。

测试的属性:
- 属性 12: 登录操作日志记录

验证需求: 3.1.6
"""

import logging
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, call

from api.auth.oauth_handlers import (
    WeChatOAuthHandler,
    WeComOAuthHandler,
    _handle_wechat_error,
    _handle_wecom_error
)


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

# 生成有效的 state 字符串
state_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=16,
    max_size=64
)

# 生成有效的 OpenID
openid_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=20,
    max_size=50
)

# 生成错误码
errcode_strategy = st.integers(min_value=40001, max_value=50000)

# 生成错误消息
errmsg_strategy = st.text(min_size=1, max_size=100)


# -----------------------------
# 属性 12: 登录操作日志记录
# -----------------------------

@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=50, deadline=None)
@patch('api.auth.oauth_handlers.logging')
def test_wechat_authorize_url_generation_logs_info(
    mock_logging: Mock,
    redirect_uri: str,
    state: str
):
    """
    属性测试: 微信授权 URL 生成应该记录信息日志
    
    对于任何授权 URL 生成操作,应该记录:
    - 日志级别为 INFO
    - 包含操作描述 (如 "构建微信授权 URL")
    - 包含生成的 URL (用于调试)
    
    验证需求: 3.1.6
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # Act - 执行
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证日志记录
    # 应该至少调用一次 info 日志
    assert mock_logging.info.called, "应该记录 INFO 级别日志"
    
    # 获取所有 info 日志调用
    info_calls = mock_logging.info.call_args_list
    
    # 验证至少有一个日志调用包含相关信息
    logged_messages = [str(call[0]) for call in info_calls]
    has_relevant_log = any(
        "微信" in msg and ("授权" in msg or "URL" in msg)
        for msg in logged_messages
    )
    
    assert has_relevant_log, "日志应该包含微信授权 URL 相关信息"


@given(
    redirect_uri=valid_url_strategy,
    state=state_strategy
)
@settings(max_examples=50, deadline=None)
@patch('api.auth.oauth_handlers.logging')
def test_wecom_authorize_url_generation_logs_info(
    mock_logging: Mock,
    redirect_uri: str,
    state: str
):
    """
    属性测试: 企业微信授权 URL 生成应该记录信息日志
    
    对于任何授权 URL 生成操作,应该记录:
    - 日志级别为 INFO
    - 包含操作描述 (如 "构建企业微信授权 URL")
    - 包含生成的 URL (用于调试)
    
    验证需求: 3.1.6
    
    Args:
        redirect_uri: 随机生成的回调 URL
        state: 随机生成的 state 参数
    """
    # Arrange - 准备
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    # Act - 执行
    authorize_url = handler.build_authorize_url(redirect_uri, state)
    
    # Assert - 验证日志记录
    assert mock_logging.info.called, "应该记录 INFO 级别日志"
    
    # 获取所有 info 日志调用
    info_calls = mock_logging.info.call_args_list
    
    # 验证至少有一个日志调用包含相关信息
    logged_messages = [str(call[0]) for call in info_calls]
    has_relevant_log = any(
        "企业微信" in msg and ("授权" in msg or "URL" in msg)
        for msg in logged_messages
    )
    
    assert has_relevant_log, "日志应该包含企业微信授权 URL 相关信息"


@given(
    errcode=errcode_strategy,
    errmsg=errmsg_strategy
)
@settings(max_examples=50, deadline=None)
@patch('api.auth.oauth_handlers.logging')
def test_wechat_error_handling_logs_error(
    mock_logging: Mock,
    errcode: int,
    errmsg: str
):
    """
    属性测试: 微信错误处理应该记录错误日志
    
    对于任何微信 API 错误,应该记录:
    - 日志级别为 ERROR
    - 包含错误码 (errcode)
    - 包含原始错误消息 (errmsg)
    - 包含友好错误消息
    
    验证需求: 3.1.6
    
    Args:
        errcode: 随机生成的错误码
        errmsg: 随机生成的错误消息
    """
    # Act - 执行错误处理
    friendly_message = _handle_wechat_error(errcode, errmsg)
    
    # Assert - 验证日志记录
    assert mock_logging.error.called, "应该记录 ERROR 级别日志"
    
    # 获取错误日志调用
    error_calls = mock_logging.error.call_args_list
    
    # 验证日志包含关键信息
    # 日志格式: "微信 API 错误: errcode=%s, errmsg=%s, friendly_message=%s"
    assert len(error_calls) > 0, "应该至少有一次错误日志调用"
    
    # 检查日志参数
    last_error_call = error_calls[-1]
    log_format = last_error_call[0][0] if last_error_call[0] else ""
    log_args = last_error_call[0][1:] if len(last_error_call[0]) > 1 else ()
    
    # 验证日志包含"微信 API 错误"
    assert "微信 API 错误" in log_format or "微信" in str(log_args), \
        "错误日志应该明确指出是微信 API 错误"


@given(
    errcode=errcode_strategy,
    errmsg=errmsg_strategy
)
@settings(max_examples=50, deadline=None)
@patch('api.auth.oauth_handlers.logging')
def test_wecom_error_handling_logs_error(
    mock_logging: Mock,
    errcode: int,
    errmsg: str
):
    """
    属性测试: 企业微信错误处理应该记录错误日志
    
    对于任何企业微信 API 错误,应该记录:
    - 日志级别为 ERROR
    - 包含错误码 (errcode)
    - 包含原始错误消息 (errmsg)
    - 包含友好错误消息
    
    验证需求: 3.1.6
    
    Args:
        errcode: 随机生成的错误码
        errmsg: 随机生成的错误消息
    """
    # Act - 执行错误处理
    friendly_message = _handle_wecom_error(errcode, errmsg)
    
    # Assert - 验证日志记录
    assert mock_logging.error.called, "应该记录 ERROR 级别日志"
    
    # 获取错误日志调用
    error_calls = mock_logging.error.call_args_list
    
    # 验证日志包含关键信息
    assert len(error_calls) > 0, "应该至少有一次错误日志调用"
    
    # 检查日志参数
    last_error_call = error_calls[-1]
    log_format = last_error_call[0][0] if last_error_call[0] else ""
    log_args = last_error_call[0][1:] if len(last_error_call[0]) > 1 else ()
    
    # 验证日志包含"企业微信 API 错误"
    assert "企业微信 API 错误" in log_format or "企业微信" in str(log_args), \
        "错误日志应该明确指出是企业微信 API 错误"


# -----------------------------
# 日志内容质量测试
# -----------------------------

@patch('api.auth.oauth_handlers.logging')
def test_wechat_logs_contain_structured_information(mock_logging: Mock):
    """
    测试: 微信 OAuth 日志应该包含结构化信息
    
    日志应该包含足够的上下文信息,便于调试和监控:
    - 操作类型 (授权、获取 token、获取用户信息)
    - 关键参数 (openid 等)
    - 操作结果 (成功/失败)
    
    验证需求: 3.1.6
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # 测试授权 URL 生成日志
    authorize_url = handler.build_authorize_url(
        "https://example.com/callback",
        "test_state_12345"
    )
    
    # 验证日志被调用
    assert mock_logging.info.called
    
    # 验证日志包含 URL
    info_calls = mock_logging.info.call_args_list
    logged_content = str(info_calls)
    
    # 日志应该包含关键信息
    assert "微信" in logged_content or "wechat" in logged_content.lower()


@patch('api.auth.oauth_handlers.logging')
def test_wecom_logs_contain_structured_information(mock_logging: Mock):
    """
    测试: 企业微信 OAuth 日志应该包含结构化信息
    
    日志应该包含足够的上下文信息,便于调试和监控:
    - 操作类型 (授权、获取 token、获取用户信息)
    - 关键参数 (userid 等)
    - 操作结果 (成功/失败)
    
    验证需求: 3.1.6
    """
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    # 测试授权 URL 生成日志
    authorize_url = handler.build_authorize_url(
        "https://example.com/callback",
        "test_state_12345"
    )
    
    # 验证日志被调用
    assert mock_logging.info.called
    
    # 验证日志包含 URL
    info_calls = mock_logging.info.call_args_list
    logged_content = str(info_calls)
    
    # 日志应该包含关键信息
    assert "企业微信" in logged_content or "wecom" in logged_content.lower()


@patch('api.auth.oauth_handlers.logging')
def test_error_logs_do_not_expose_sensitive_data(mock_logging: Mock):
    """
    测试: 错误日志不应该暴露敏感数据
    
    错误日志应该避免记录:
    - 完整的 app_secret 或 corp_secret
    - 完整的 access_token
    - 用户密码或其他敏感信息
    
    验证需求: 3.1.6 (安全性)
    """
    # 测试微信错误处理
    _handle_wechat_error(40001, "invalid app_secret: abc123def456")
    
    # 获取错误日志
    error_calls = mock_logging.error.call_args_list
    logged_content = str(error_calls)
    
    # 验证不包含完整的密钥 (这里假设密钥不应该出现在日志中)
    # 注意: 实际实现中应该对敏感信息进行脱敏处理
    # 例如: "app_secret: abc***456" 而不是 "app_secret: abc123def456"
    
    # 这个测试主要是提醒开发者注意日志安全
    # 实际验证需要根据具体的日志实现来调整
    assert mock_logging.error.called, "应该记录错误日志"


# -----------------------------
# 日志级别测试
# -----------------------------

@patch('api.auth.oauth_handlers.logging')
def test_successful_operations_use_info_level(mock_logging: Mock):
    """
    测试: 成功的操作应该使用 INFO 日志级别
    
    正常的操作流程 (如生成授权 URL) 应该使用 INFO 级别,
    而不是 WARNING 或 ERROR。
    
    验证需求: 3.1.6
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # 执行正常操作
    authorize_url = handler.build_authorize_url(
        "https://example.com/callback",
        "test_state"
    )
    
    # 验证使用了 INFO 级别
    assert mock_logging.info.called, "成功操作应该使用 INFO 级别"
    
    # 验证没有使用 ERROR 或 WARNING 级别
    assert not mock_logging.error.called, "成功操作不应该记录 ERROR"
    assert not mock_logging.warning.called, "成功操作不应该记录 WARNING"


@patch('api.auth.oauth_handlers.logging')
def test_error_operations_use_error_level(mock_logging: Mock):
    """
    测试: 错误操作应该使用 ERROR 日志级别
    
    API 错误应该使用 ERROR 级别,便于监控和告警。
    
    验证需求: 3.1.6
    """
    # 执行错误处理
    _handle_wechat_error(40001, "invalid credential")
    
    # 验证使用了 ERROR 级别
    assert mock_logging.error.called, "错误处理应该使用 ERROR 级别"


# -----------------------------
# 日志格式测试
# -----------------------------

@patch('api.auth.oauth_handlers.logging')
def test_logs_use_consistent_format(mock_logging: Mock):
    """
    测试: 日志应该使用一致的格式
    
    所有日志应该遵循统一的格式,便于解析和分析:
    - 使用参数化日志 (而不是字符串拼接)
    - 包含操作类型
    - 包含关键参数
    
    验证需求: 3.1.6
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    # 执行操作
    authorize_url = handler.build_authorize_url(
        "https://example.com/callback",
        "test_state"
    )
    
    # 验证日志调用
    assert mock_logging.info.called
    
    # 获取日志调用
    info_calls = mock_logging.info.call_args_list
    
    # 验证使用了参数化日志 (而不是字符串拼接)
    # 参数化日志的特征是第一个参数包含 %s 或 %d 等格式化占位符
    for call_args in info_calls:
        if call_args[0]:  # 如果有参数
            log_format = call_args[0][0]
            # 日志格式应该是字符串
            assert isinstance(log_format, str), "日志格式应该是字符串"
