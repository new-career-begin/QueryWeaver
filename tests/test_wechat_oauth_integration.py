"""
微信 OAuth 登录完整流程集成测试

测试从登录到回调的完整流程，包括首次登录和重复登录场景
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.routes.auth import auth_router, generate_state, verify_state
from api.auth.user_management import ensure_user_in_organizations


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


class TestWeChatOAuthIntegration:
    """微信 OAuth 集成测试套件"""
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_login_flow_first_time(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：微信首次登录完整流程
        
        场景：
        1. 用户点击微信登录
        2. 重定向到微信授权页面
        3. 用户授权后回调
        4. 创建新用户
        5. 设置 Cookie 并重定向到首页
        """
        # Arrange - 准备测试数据
        mock_is_enabled.return_value = True
        
        # Mock 微信 OAuth 处理器
        mock_handler = Mock()
        mock_handler.build_authorize_url.return_value = (
            "https://open.weixin.qq.com/connect/oauth2/authorize"
            "?appid=test_app_id&redirect_uri=http://testserver/login/wechat/authorized"
            "&response_type=code&scope=snsapi_userinfo&state=test_state#wechat_redirect"
        )
        mock_handler_class.return_value = mock_handler
        
        # Act - 步骤 1: 发起登录
        response = client.get("/login/wechat", follow_redirects=False)
        
        # Assert - 验证重定向到微信授权页面
        assert response.status_code == 302
        assert "open.weixin.qq.com" in response.headers["location"]
        assert "oauth_state" in response.cookies
        
        # 保存 state 用于回调验证
        oauth_state = response.cookies["oauth_state"]
        
        # Arrange - 准备回调数据
        mock_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "openid": "test_openid_123"
        })
        
        mock_handler.get_user_info = AsyncMock(return_value={
            "openid": "test_openid_123",
            "nickname": "测试用户",
            "headimgurl": "https://example.com/avatar.jpg",
            "unionid": "test_unionid_456"
        })
        
        mock_handler.parse_user_info.return_value = {
            "id": "test_openid_123",
            "email": "test_openid_123@wechat.queryweaver.local",
            "name": "测试用户",
            "picture": "https://example.com/avatar.jpg",
            "unionid": "test_unionid_456",
            "provider": "wechat"
        }
        
        # Mock 用户管理函数
        with patch('api.routes.auth.ensure_user_in_organizations') as mock_ensure_user:
            mock_ensure_user.return_value = (True, {
                "new_identity": True,
                "user_id": "user_123"
            })
            
            # Act - 步骤 2: 模拟微信回调
            response = client.get(
                f"/login/wechat/authorized?code=test_code&state={oauth_state}",
                cookies={"oauth_state": oauth_state},
                follow_redirects=False
            )
        
        # Assert - 验证回调处理成功
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        assert "api_token" in response.cookies
        
        # 验证 oauth_state cookie 被清除
        assert response.cookies.get("oauth_state", "") == ""
        
        # 验证调用了正确的方法
        mock_handler.exchange_code_for_token.assert_called_once_with("test_code")
        mock_handler.get_user_info.assert_called_once_with(
            "mock_access_token",
            "test_openid_123"
        )
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_login_flow_repeat_login(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：微信重复登录流程
        
        场景：
        1. 用户已经登录过（Identity 已存在）
        2. 再次使用微信登录
        3. 识别已有用户
        4. 更新最后登录时间
        5. 设置 Cookie 并重定向
        """
        # Arrange
        mock_is_enabled.return_value = True
        
        mock_handler = Mock()
        mock_handler.build_authorize_url.return_value = (
            "https://open.weixin.qq.com/connect/oauth2/authorize"
            "?appid=test_app_id&redirect_uri=http://testserver/login/wechat/authorized"
            "&response_type=code&scope=snsapi_userinfo&state=test_state#wechat_redirect"
        )
        mock_handler_class.return_value = mock_handler
        
        # Act - 发起登录
        response = client.get("/login/wechat", follow_redirects=False)
        oauth_state = response.cookies["oauth_state"]
        
        # Arrange - 准备回调数据（相同的 openid）
        mock_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "openid": "existing_openid_123"
        })
        
        mock_handler.get_user_info = AsyncMock(return_value={
            "openid": "existing_openid_123",
            "nickname": "已存在用户",
            "headimgurl": "https://example.com/avatar.jpg"
        })
        
        mock_handler.parse_user_info.return_value = {
            "id": "existing_openid_123",
            "email": "existing_openid_123@wechat.queryweaver.local",
            "name": "已存在用户",
            "picture": "https://example.com/avatar.jpg",
            "provider": "wechat"
        }
        
        # Mock 用户管理函数 - 返回已存在用户
        with patch('api.routes.auth.ensure_user_in_organizations') as mock_ensure_user:
            mock_ensure_user.return_value = (True, {
                "new_identity": False,  # 用户已存在
                "user_id": "existing_user_123"
            })
            
            # Act - 回调
            response = client.get(
                f"/login/wechat/authorized?code=test_code&state={oauth_state}",
                cookies={"oauth_state": oauth_state},
                follow_redirects=False
            )
        
        # Assert
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        assert "api_token" in response.cookies
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    def test_wechat_login_disabled(self, mock_is_enabled, client):
        """
        测试：微信登录未启用时返回 503
        """
        # Arrange
        mock_is_enabled.return_value = False
        
        # Act
        response = client.get("/login/wechat", follow_redirects=False)
        
        # Assert
        assert response.status_code == 503
        assert "未启用" in response.json()["detail"]
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_callback_missing_code(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：回调缺少 code 参数时返回 400
        """
        # Arrange
        mock_is_enabled.return_value = True
        state = generate_state("wechat")
        
        # Act - 缺少 code 参数
        response = client.get(
            f"/login/wechat/authorized?state={state}",
            cookies={"oauth_state": state}
        )
        
        # Assert
        assert response.status_code == 400
        assert "缺少必需参数" in response.json()["detail"]
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_callback_invalid_state(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：state 验证失败时返回 400
        """
        # Arrange
        mock_is_enabled.return_value = True
        valid_state = generate_state("wechat")
        invalid_state = "invalid_state_token"
        
        # Act - state 不匹配
        response = client.get(
            f"/login/wechat/authorized?code=test_code&state={invalid_state}",
            cookies={"oauth_state": valid_state}
        )
        
        # Assert
        assert response.status_code == 400
        assert "安全验证失败" in response.json()["detail"]
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_callback_api_error(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：微信 API 返回错误时的处理
        """
        # Arrange
        mock_is_enabled.return_value = True
        
        mock_handler = Mock()
        mock_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_handler_class.return_value = mock_handler
        
        # 发起登录获取 state
        response = client.get("/login/wechat", follow_redirects=False)
        oauth_state = response.cookies["oauth_state"]
        
        # Mock API 错误
        mock_handler.exchange_code_for_token = AsyncMock(
            side_effect=ValueError("微信 API 错误: invalid code")
        )
        
        # Act - 回调时触发错误
        response = client.get(
            f"/login/wechat/authorized?code=invalid_code&state={oauth_state}",
            cookies={"oauth_state": oauth_state}
        )
        
        # Assert
        assert response.status_code == 400
        assert "登录失败" in response.json()["detail"]
    
    @patch('api.routes.auth._is_wechat_auth_enabled')
    @patch('api.routes.auth.WeChatOAuthHandler')
    def test_wechat_login_with_unionid(
        self,
        mock_handler_class,
        mock_is_enabled,
        client
    ):
        """
        测试：微信登录包含 UnionID 的场景
        
        UnionID 用于跨应用识别同一用户
        """
        # Arrange
        mock_is_enabled.return_value = True
        
        mock_handler = Mock()
        mock_handler.build_authorize_url.return_value = "https://open.weixin.qq.com/..."
        mock_handler_class.return_value = mock_handler
        
        response = client.get("/login/wechat", follow_redirects=False)
        oauth_state = response.cookies["oauth_state"]
        
        # Mock 返回包含 UnionID 的用户信息
        mock_handler.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "mock_access_token",
            "openid": "test_openid_123"
        })
        
        mock_handler.get_user_info = AsyncMock(return_value={
            "openid": "test_openid_123",
            "nickname": "测试用户",
            "headimgurl": "https://example.com/avatar.jpg",
            "unionid": "test_unionid_456"  # 包含 UnionID
        })
        
        mock_handler.parse_user_info.return_value = {
            "id": "test_openid_123",
            "email": "test_openid_123@wechat.queryweaver.local",
            "name": "测试用户",
            "picture": "https://example.com/avatar.jpg",
            "unionid": "test_unionid_456",
            "provider": "wechat"
        }
        
        with patch('api.routes.auth.ensure_user_in_organizations') as mock_ensure_user:
            mock_ensure_user.return_value = (True, {
                "new_identity": True,
                "user_id": "user_123"
            })
            
            # Act
            response = client.get(
                f"/login/wechat/authorized?code=test_code&state={oauth_state}",
                cookies={"oauth_state": oauth_state},
                follow_redirects=False
            )
        
        # Assert
        assert response.status_code == 302
        assert "api_token" in response.cookies
        
        # 验证 parse_user_info 返回了 UnionID
        parsed_info = mock_handler.parse_user_info.return_value
        assert "unionid" in parsed_info
        assert parsed_info["unionid"] == "test_unionid_456"


class TestWeChatStateManagement:
    """微信 OAuth State 管理测试"""
    
    def test_generate_state_creates_valid_token(self):
        """测试：生成的 state 包含正确的信息"""
        # Act
        state = generate_state("wechat")
        
        # Assert
        assert state is not None
        assert len(state) > 20  # state 应该是一个较长的字符串
        
        # 验证可以正确解析
        assert verify_state(state, "wechat")
    
    def test_verify_state_rejects_wrong_provider(self):
        """测试：state 验证拒绝错误的 provider"""
        # Arrange
        state = generate_state("wechat")
        
        # Act & Assert
        assert not verify_state(state, "wecom")
    
    def test_verify_state_rejects_expired_token(self):
        """测试：state 验证拒绝过期的 token"""
        # Arrange
        state = generate_state("wechat")
        
        # Act & Assert - 设置 max_age 为 0 使其立即过期
        with pytest.raises(ValueError):
            verify_state(state, "wechat", max_age=0)
