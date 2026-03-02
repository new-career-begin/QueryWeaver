"""
微信和企业微信 OAuth 错误处理单元测试

测试错误码映射和错误消息的友好性
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

# 导入被测试的模块
from api.auth.oauth_handlers import (
    WeChatOAuthHandler,
    WeComOAuthHandler,
    _handle_wechat_error,
    _handle_wecom_error,
    WECHAT_ERROR_MESSAGES,
    WECOM_ERROR_MESSAGES,
)


class TestWeChatErrorHandling:
    """微信错误处理测试套件"""

    @pytest.fixture
    def wechat_config(self):
        """微信配置"""
        return {
            "app_id": "test_app_id",
            "app_secret": "test_app_secret",
            "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
            "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
            "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
            "scope": "snsapi_userinfo",
        }

    @pytest.fixture
    def wechat_handler(self, wechat_config):
        """微信 OAuth 处理器实例"""
        return WeChatOAuthHandler(wechat_config)

    @pytest.mark.parametrize(
        "errcode,expected_message",
        [
            (40001, "AppSecret 错误，请联系管理员"),
            (40013, "AppID 无效，请联系管理员"),
            (40029, "授权码无效，请重新登录"),
            (40163, "授权码已使用，请重新登录"),
            (41001, "缺少 access_token 参数，请重新登录"),
            (42001, "access_token 已过期，请重新登录"),
            (42007, "用户修改微信密码，access_token 已失效，请重新登录"),
            (50001, "用户未授权该 API"),
            (50002, "用户受限，无法使用该功能"),
        ],
    )
    def test_wechat_error_messages(self, errcode, expected_message):
        """
        测试微信错误码映射
        
        验证需求: 2.1.2.9
        
        确保常见错误码都有友好的中文错误消息
        """
        # Act
        friendly_message = _handle_wechat_error(errcode, "原始错误消息")
        
        # Assert
        assert friendly_message == expected_message
        assert "请" in friendly_message or "错误" in friendly_message, "错误消息应该是友好的中文"

    def test_wechat_unknown_error_code(self):
        """
        测试未知错误码
        
        验证需求: 2.1.2.9
        
        对于未知错误码，应该返回通用错误消息
        """
        # Arrange
        unknown_errcode = 99999
        
        # Act
        friendly_message = _handle_wechat_error(unknown_errcode, "未知错误")
        
        # Assert
        assert "微信服务错误" in friendly_message
        assert str(unknown_errcode) in friendly_message
        assert "请稍后重试" in friendly_message

    @pytest.mark.asyncio
    async def test_exchange_code_with_invalid_code(self, wechat_handler):
        """
        测试无效授权码
        
        验证需求: 2.1.2.9
        
        当授权码无效时，应该抛出友好的错误消息
        """
        # Arrange
        invalid_code = "invalid_code_123"
        
        # Mock API 响应 - 返回错误码 40029
        mock_response = Mock()
        mock_response.json.return_value = {
            "errcode": 40029,
            "errmsg": "invalid code"
        }
        mock_response.raise_for_status = Mock()
        
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError) as exc_info:
                await wechat_handler.exchange_code_for_token(invalid_code)
            
            # 验证错误消息是友好的中文
            assert "授权码无效" in str(exc_info.value)
            assert "请重新登录" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exchange_code_with_expired_code(self, wechat_handler):
        """
        测试过期授权码
        
        验证需求: 2.1.2.9
        
        当授权码已使用时，应该抛出友好的错误消息
        """
        # Arrange
        expired_code = "expired_code_123"
        
        # Mock API 响应 - 返回错误码 40163
        mock_response = Mock()
        mock_response.json.return_value = {
            "errcode": 40163,
            "errmsg": "code been used"
        }
        mock_response.raise_for_status = Mock()
        
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError) as exc_info:
                await wechat_handler.exchange_code_for_token(expired_code)
            
            # 验证错误消息是友好的中文
            assert "授权码已使用" in str(exc_info.value)
            assert "请重新登录" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_info_with_expired_token(self, wechat_handler):
        """
        测试过期 access_token
        
        验证需求: 2.1.2.9
        
        当 access_token 过期时，应该抛出友好的错误消息
        """
        # Arrange
        expired_token = "expired_token_123"
        openid = "test_openid"
        
        # Mock API 响应 - 返回错误码 42001
        mock_response = Mock()
        mock_response.json.return_value = {
            "errcode": 42001,
            "errmsg": "access_token expired"
        }
        mock_response.raise_for_status = Mock()
        
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError) as exc_info:
                await wechat_handler.get_user_info(expired_token, openid)
            
            # 验证错误消息是友好的中文
            assert "access_token 已过期" in str(exc_info.value)
            assert "请重新登录" in str(exc_info.value)


class TestWeComErrorHandling:
    """企业微信错误处理测试套件"""

    @pytest.fixture
    def wecom_config(self):
        """企业微信配置"""
        return {
            "corp_id": "test_corp_id",
            "agent_id": "1000001",
            "corp_secret": "test_corp_secret",
            "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
            "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
            "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
            "scope": "snsapi_base",
        }

    @pytest.fixture
    def wecom_handler(self, wecom_config):
        """企业微信 OAuth 处理器实例"""
        return WeComOAuthHandler(wecom_config)

    @pytest.mark.parametrize(
        "errcode,expected_message",
        [
            (40001, "不合法的 secret 参数，请联系管理员"),
            (40003, "无效的 UserID，请重新登录"),
            (40013, "不合法的 CorpID，请联系管理员"),
            (40014, "不合法的 access_token，请重新登录"),
            (40029, "不合法的 oauth_code，请重新登录"),
            (41001, "缺少 access_token 参数，请重新登录"),
            (42001, "access_token 已过期，请重新登录"),
            (42007, "用户修改密码，access_token 已失效，请重新登录"),
            (48001, "API 功能未授权"),
            (50001, "redirect_uri 未授权"),
            (60111, "UserID 不存在"),
        ],
    )
    def test_wecom_error_messages(self, errcode, expected_message):
        """
        测试企业微信错误码映射
        
        验证需求: 2.2.2.9
        
        确保常见错误码都有友好的中文错误消息
        """
        # Act
        friendly_message = _handle_wecom_error(errcode, "原始错误消息")
        
        # Assert
        assert friendly_message == expected_message
        assert "请" in friendly_message or "错误" in friendly_message or "不" in friendly_message, \
            "错误消息应该是友好的中文"

    def test_wecom_unknown_error_code(self):
        """
        测试未知错误码
        
        验证需求: 2.2.2.9
        
        对于未知错误码，应该返回通用错误消息
        """
        # Arrange
        unknown_errcode = 99999
        
        # Act
        friendly_message = _handle_wecom_error(unknown_errcode, "未知错误")
        
        # Assert
        assert "企业微信服务错误" in friendly_message
        assert str(unknown_errcode) in friendly_message
        assert "请稍后重试" in friendly_message

    @pytest.mark.asyncio
    async def test_get_access_token_with_invalid_secret(self, wecom_handler):
        """
        测试无效 secret
        
        验证需求: 2.2.2.9
        
        当 secret 无效时，应该抛出友好的错误消息
        """
        # Mock API 响应 - 返回错误码 40001
        mock_response = Mock()
        mock_response.json.return_value = {
            "errcode": 40001,
            "errmsg": "invalid secret"
        }
        mock_response.raise_for_status = Mock()
        
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(ValueError) as exc_info:
                await wecom_handler.get_access_token()
            
            # 验证错误消息是友好的中文
            assert "不合法的 secret 参数" in str(exc_info.value)
            assert "请联系管理员" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_info_with_invalid_code(self, wecom_handler):
        """
        测试无效授权码
        
        验证需求: 2.2.2.9
        
        当授权码无效时，应该抛出友好的错误消息
        """
        # Arrange
        invalid_code = "invalid_code_123"
        
        # Mock get_access_token 成功
        wecom_handler._access_token = "valid_token"
        wecom_handler._token_expire_time = None  # 强制重新获取
        
        # Mock get_access_token API 响应
        mock_token_response = Mock()
        mock_token_response.json.return_value = {
            "errcode": 0,
            "access_token": "valid_token",
            "expires_in": 7200
        }
        mock_token_response.raise_for_status = Mock()
        
        # Mock get_user_info API 响应 - 返回错误码 40029
        mock_userinfo_response = Mock()
        mock_userinfo_response.json.return_value = {
            "errcode": 40029,
            "errmsg": "invalid oauth_code"
        }
        mock_userinfo_response.raise_for_status = Mock()
        
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_token_response, mock_userinfo_response]
            )
            
            with pytest.raises(ValueError) as exc_info:
                await wecom_handler.get_user_info(invalid_code)
            
            # 验证错误消息是友好的中文
            assert "不合法的 oauth_code" in str(exc_info.value)
            assert "请重新登录" in str(exc_info.value)


class TestErrorMessageQuality:
    """错误消息质量测试"""

    def test_all_wechat_errors_are_chinese(self):
        """
        测试所有微信错误消息都是中文
        
        验证需求: 2.1.2.9
        """
        for errcode, message in WECHAT_ERROR_MESSAGES.items():
            # 验证消息包含中文字符
            assert any('\u4e00' <= char <= '\u9fff' for char in message), \
                f"错误码 {errcode} 的消息应该包含中文: {message}"
            
            # 验证消息不为空
            assert len(message) > 0, f"错误码 {errcode} 的消息不能为空"
            
            # 验证消息长度合理（不超过 100 个字符）
            assert len(message) <= 100, \
                f"错误码 {errcode} 的消息过长: {message}"

    def test_all_wecom_errors_are_chinese(self):
        """
        测试所有企业微信错误消息都是中文
        
        验证需求: 2.2.2.9
        """
        for errcode, message in WECOM_ERROR_MESSAGES.items():
            # 验证消息包含中文字符
            assert any('\u4e00' <= char <= '\u9fff' for char in message), \
                f"错误码 {errcode} 的消息应该包含中文: {message}"
            
            # 验证消息不为空
            assert len(message) > 0, f"错误码 {errcode} 的消息不能为空"
            
            # 验证消息长度合理（不超过 100 个字符）
            assert len(message) <= 100, \
                f"错误码 {errcode} 的消息过长: {message}"

    @pytest.mark.parametrize(
        "errcode",
        [40001, 40013, 40029, 40163, 41001, 42001, 42007, 50001, 50002]
    )
    def test_critical_wechat_errors_covered(self, errcode):
        """
        测试关键微信错误码都有映射
        
        验证需求: 2.1.2.9
        """
        assert errcode in WECHAT_ERROR_MESSAGES, \
            f"关键错误码 {errcode} 应该有错误消息映射"

    @pytest.mark.parametrize(
        "errcode",
        [40001, 40003, 40013, 40014, 40029, 41001, 42001, 42007, 48001, 50001, 60111]
    )
    def test_critical_wecom_errors_covered(self, errcode):
        """
        测试关键企业微信错误码都有映射
        
        验证需求: 2.2.2.9
        """
        assert errcode in WECOM_ERROR_MESSAGES, \
            f"关键错误码 {errcode} 应该有错误消息映射"
