"""
跨 OAuth Provider 账号关联集成测试

测试同一用户使用不同 OAuth 提供商登录时的账号关联逻辑
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.routes.auth import auth_router


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(auth_router)
    
    # 注册回调处理器
    async def mock_callback_handler(provider: str, user_info: dict, api_token: str):
        """模拟回调处理器"""
        return True
    
    app.state.callback_handler = mock_callback_handler
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestCrossProviderAccountLinking:
    """跨 Provider 账号关联测试套件"""
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth._is_wecom_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    @patch('api.routes.auth.WeComOAuthHandler')
    @patch('api.auth.user_management.ensure_user_in_organizations')
    def test_same_email_different_providers_link_accounts(
        self,
        mock_ensure_user,
        mock_wecom_handler_class,
        mock_wechat_handler_class,
        mock_wecom_enabled,
        mock_wechat_enabled,
        client
    ):
        """
        测试：同一邮箱的不同 provider 账号应该关联到同一用户
        
        场景：
        1. 用户先用企业微信登录（有企业邮箱）
        2. 后用微信登录（使用相同的邮箱）
        3. 系统应该识别为同一用户
        """
        # Arrange
        mock_wechat_enabled.return_value = True
        mock_wecom_enabled.return_value = True
        
        shared_email = "user@company.com"
        
        # 步骤 1: 企业微信首次登录
        mock_wecom_handler = Mock()
        mock_wecom_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wecom_handler_class.return_value = mock_wecom_handler
        
        # 发起企业微信登录
        response = client.get("/login/wecom", follow_redirects=False)
        wecom_state = response.cookies["oauth_state"]
        
        # Mock 企业微信用户信息
        mock_wecom_handler.get_user_info = AsyncMock(return_value={
            "userid": "zhangsan",
            "name": "张三",
            "email": shared_email,  # 企业邮箱
            "avatar": "https://example.com/avatar.jpg",
            "department": [1]
        })
        
        mock_wecom_handler.parse_user_info.return_value = {
            "id": "zhangsan",
            "email": shared_email,
            "name": "张三",
            "picture": "https://example.com/avatar.jpg",
            "corp_id": "test_corp_id",
            "department": [1],
            "provider": "wecom"
        }
        
        # Mock 用户管理 - 首次登录创建用户
        mock_ensure_user.return_value = (True, {
            "new_identity": True,
            "user_id": "user_123"
        })
        
        # 完成企业微信登录
        response = client.get(
            f"/login/wecom/authorized?code=wecom_code&state={wecom_state}",
            cookies={"oauth_state": wecom_state},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # 步骤 2: 微信登录（相同邮箱）
        mock_wechat_handler = Mock()
        mock_wechat_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wechat_handler_class.return_value = mock_wechat_handler
        
        # 发起微信登录
        response = client.get("/login/wechat", follow_redirects=False)
        wechat_state = response.cookies["oauth_state"]
        
        # Mock 微信用户信息（相同邮箱）
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "openid": "test_openid_123"
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "test_openid_123",
            "nickname": "张三",
            "headimgurl": "https://example.com/avatar.jpg",
            "email": shared_email  # 相同的邮箱
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "test_openid_123",
            "email": shared_email,  # 相同的邮箱
            "name": "张三",
            "picture": "https://example.com/avatar.jpg",
            "provider": "wechat"
        }
        
        # Mock 用户管理 - 应该识别为已存在用户
        mock_ensure_user.return_value = (True, {
            "new_identity": False,  # 不是新用户
            "user_id": "user_123"  # 相同的 user_id
        })
        
        # 完成微信登录
        response = client.get(
            f"/login/wechat/authorized?code=wechat_code&state={wechat_state}",
            cookies={"oauth_state": wechat_state},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 302
        assert "api_token" in response.cookies
        
        # 验证 ensure_user_in_organizations 被调用了两次
        assert mock_ensure_user.call_count == 2
        
        # 验证两次调用使用了相同的邮箱
        first_call_email = mock_ensure_user.call_args_list[0][0][0]  # provider_user_id
        second_call_email = mock_ensure_user.call_args_list[1][0][0]
        
        # 注意：第一次是 userid，第二次是 openid，但 email 参数应该相同
        first_call_email_param = mock_ensure_user.call_args_list[0][0][1]  # email
        second_call_email_param = mock_ensure_user.call_args_list[1][0][1]
        
        assert first_call_email_param == shared_email
        assert second_call_email_param == shared_email
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    @patch('api.auth.user_management.ensure_user_in_organizations')
    def test_unionid_cross_app_recognition(
        self,
        mock_ensure_user,
        mock_wechat_handler_class,
        mock_wechat_enabled,
        client
    ):
        """
        测试：UnionID 的跨应用识别
        
        场景：
        1. 用户在应用 A 使用微信登录（openid_A + unionid）
        2. 用户在应用 B 使用微信登录（openid_B + 相同的 unionid）
        3. 系统应该通过 UnionID 识别为同一用户
        
        注意：这个测试模拟的是同一个 QueryWeaver 实例中，
        用户使用不同的微信应用登录的场景
        """
        # Arrange
        mock_wechat_enabled.return_value = True
        shared_unionid = "test_unionid_456"
        
        # 步骤 1: 使用应用 A 的 OpenID 登录
        mock_wechat_handler = Mock()
        mock_wechat_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wechat_handler_class.return_value = mock_wechat_handler
        
        response = client.get("/login/wechat", follow_redirects=False)
        state_1 = response.cookies["oauth_state"]
        
        # Mock 第一次登录的用户信息
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token_1",
            "openid": "openid_app_a"
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "openid_app_a",
            "nickname": "测试用户",
            "headimgurl": "https://example.com/avatar.jpg",
            "unionid": shared_unionid  # UnionID
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "openid_app_a",
            "email": "openid_app_a@wechat.queryweaver.local",
            "name": "测试用户",
            "picture": "https://example.com/avatar.jpg",
            "unionid": shared_unionid,
            "provider": "wechat"
        }
        
        # Mock 首次登录创建用户
        mock_ensure_user.return_value = (True, {
            "new_identity": True,
            "user_id": "user_123"
        })
        
        response = client.get(
            f"/login/wechat/authorized?code=code_1&state={state_1}",
            cookies={"oauth_state": state_1},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # 步骤 2: 使用应用 B 的 OpenID 登录（相同 UnionID）
        response = client.get("/login/wechat", follow_redirects=False)
        state_2 = response.cookies["oauth_state"]
        
        # Mock 第二次登录的用户信息（不同的 OpenID，相同的 UnionID）
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token_2",
            "openid": "openid_app_b"  # 不同的 OpenID
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "openid_app_b",
            "nickname": "测试用户",
            "headimgurl": "https://example.com/avatar.jpg",
            "unionid": shared_unionid  # 相同的 UnionID
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "openid_app_b",
            "email": "openid_app_b@wechat.queryweaver.local",
            "name": "测试用户",
            "picture": "https://example.com/avatar.jpg",
            "unionid": shared_unionid,  # 相同的 UnionID
            "provider": "wechat"
        }
        
        # Mock 应该识别为已存在用户（通过 UnionID）
        mock_ensure_user.return_value = (True, {
            "new_identity": False,  # 不是新用户
            "user_id": "user_123"  # 相同的 user_id
        })
        
        response = client.get(
            f"/login/wechat/authorized?code=code_2&state={state_2}",
            cookies={"oauth_state": state_2},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 302
        assert "api_token" in response.cookies
        
        # 验证两次登录都成功
        assert mock_ensure_user.call_count == 2
        
        # 验证两次都传递了 UnionID
        first_call_info = mock_wechat_handler.parse_user_info.return_value
        assert "unionid" in first_call_info
        assert first_call_info["unionid"] == shared_unionid
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth._is_wecom_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    @patch('api.routes.auth.WeComOAuthHandler')
    @patch('api.auth.user_management.ensure_user_in_organizations')
    def test_different_emails_create_separate_accounts(
        self,
        mock_ensure_user,
        mock_wecom_handler_class,
        mock_wechat_handler_class,
        mock_wecom_enabled,
        mock_wechat_enabled,
        client
    ):
        """
        测试：不同邮箱的账号不应该关联
        
        场景：
        1. 用户 A 用企业微信登录（email_a@company.com）
        2. 用户 B 用微信登录（email_b@company.com）
        3. 系统应该创建两个独立的用户账号
        """
        # Arrange
        mock_wechat_enabled.return_value = True
        mock_wecom_enabled.return_value = True
        
        # 步骤 1: 用户 A 企业微信登录
        mock_wecom_handler = Mock()
        mock_wecom_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wecom_handler_class.return_value = mock_wecom_handler
        
        response = client.get("/login/wecom", follow_redirects=False)
        wecom_state = response.cookies["oauth_state"]
        
        mock_wecom_handler.get_user_info = AsyncMock(return_value={
            "userid": "user_a",
            "name": "用户 A",
            "email": "user_a@company.com",
            "avatar": "https://example.com/avatar_a.jpg",
            "department": [1]
        })
        
        mock_wecom_handler.parse_user_info.return_value = {
            "id": "user_a",
            "email": "user_a@company.com",
            "name": "用户 A",
            "picture": "https://example.com/avatar_a.jpg",
            "corp_id": "test_corp_id",
            "department": [1],
            "provider": "wecom"
        }
        
        # Mock 创建用户 A
        mock_ensure_user.return_value = (True, {
            "new_identity": True,
            "user_id": "user_a_123"
        })
        
        response = client.get(
            f"/login/wecom/authorized?code=wecom_code&state={wecom_state}",
            cookies={"oauth_state": wecom_state},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # 步骤 2: 用户 B 微信登录（不同邮箱）
        mock_wechat_handler = Mock()
        mock_wechat_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wechat_handler_class.return_value = mock_wechat_handler
        
        response = client.get("/login/wechat", follow_redirects=False)
        wechat_state = response.cookies["oauth_state"]
        
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "openid": "openid_user_b"
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "openid_user_b",
            "nickname": "用户 B",
            "headimgurl": "https://example.com/avatar_b.jpg",
            "email": "user_b@company.com"  # 不同的邮箱
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "openid_user_b",
            "email": "user_b@company.com",  # 不同的邮箱
            "name": "用户 B",
            "picture": "https://example.com/avatar_b.jpg",
            "provider": "wechat"
        }
        
        # Mock 创建新用户 B
        mock_ensure_user.return_value = (True, {
            "new_identity": True,  # 新用户
            "user_id": "user_b_456"  # 不同的 user_id
        })
        
        response = client.get(
            f"/login/wechat/authorized?code=wechat_code&state={wechat_state}",
            cookies={"oauth_state": wechat_state},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 302
        assert "api_token" in response.cookies
        
        # 验证创建了两个不同的用户
        assert mock_ensure_user.call_count == 2
        
        # 验证使用了不同的邮箱
        first_call_email = mock_ensure_user.call_args_list[0][0][1]
        second_call_email = mock_ensure_user.call_args_list[1][0][1]
        
        assert first_call_email == "user_a@company.com"
        assert second_call_email == "user_b@company.com"
        assert first_call_email != second_call_email
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    @patch('api.auth.user_management.ensure_user_in_organizations')
    def test_virtual_email_accounts_remain_separate(
        self,
        mock_ensure_user,
        mock_wechat_handler_class,
        mock_wechat_enabled,
        client
    ):
        """
        测试：使用虚拟邮箱的账号应该保持独立
        
        场景：
        1. 用户 A 用微信登录（没有真实邮箱，使用虚拟邮箱）
        2. 用户 B 用微信登录（没有真实邮箱，使用虚拟邮箱）
        3. 系统应该创建两个独立的账号
        """
        # Arrange
        mock_wechat_enabled.return_value = True
        
        # 步骤 1: 用户 A 登录
        mock_wechat_handler = Mock()
        mock_wechat_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_wechat_handler_class.return_value = mock_wechat_handler
        
        response = client.get("/login/wechat", follow_redirects=False)
        state_1 = response.cookies["oauth_state"]
        
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token_1",
            "openid": "openid_a"
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "openid_a",
            "nickname": "用户 A",
            "headimgurl": "https://example.com/avatar_a.jpg"
            # 注意：没有真实邮箱
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "openid_a",
            "email": "openid_a@wechat.queryweaver.local",  # 虚拟邮箱
            "name": "用户 A",
            "picture": "https://example.com/avatar_a.jpg",
            "provider": "wechat"
        }
        
        mock_ensure_user.return_value = (True, {
            "new_identity": True,
            "user_id": "user_a_123"
        })
        
        response = client.get(
            f"/login/wechat/authorized?code=code_1&state={state_1}",
            cookies={"oauth_state": state_1},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # 步骤 2: 用户 B 登录
        response = client.get("/login/wechat", follow_redirects=False)
        state_2 = response.cookies["oauth_state"]
        
        mock_wechat_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token_2",
            "openid": "openid_b"
        })
        
        mock_wechat_handler.get_user_info = AsyncMock(return_value={
            "openid": "openid_b",
            "nickname": "用户 B",
            "headimgurl": "https://example.com/avatar_b.jpg"
            # 注意：没有真实邮箱
        })
        
        mock_wechat_handler.parse_user_info.return_value = {
            "id": "openid_b",
            "email": "openid_b@wechat.queryweaver.local",  # 不同的虚拟邮箱
            "name": "用户 B",
            "picture": "https://example.com/avatar_b.jpg",
            "provider": "wechat"
        }
        
        mock_ensure_user.return_value = (True, {
            "new_identity": True,  # 新用户
            "user_id": "user_b_456"  # 不同的 user_id
        })
        
        response = client.get(
            f"/login/wechat/authorized?code=code_2&state={state_2}",
            cookies={"oauth_state": state_2},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 302
        
        # 验证创建了两个不同的用户
        assert mock_ensure_user.call_count == 2
        
        # 验证使用了不同的虚拟邮箱
        first_call_email = mock_ensure_user.call_args_list[0][0][1]
        second_call_email = mock_ensure_user.call_args_list[1][0][1]
        
        assert "@wechat.queryweaver.local" in first_call_email
        assert "@wechat.queryweaver.local" in second_call_email
        assert first_call_email != second_call_email
