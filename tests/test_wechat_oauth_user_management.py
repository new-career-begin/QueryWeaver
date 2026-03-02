"""
微信和企业微信 OAuth 用户管理属性测试

测试用户创建和识别的正确性属性
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

# 导入被测试的模块
from api.auth.user_management import (
    ensure_user_in_organizations,
    update_identity_last_login,
    _validate_user_input,
)


class TestUserCreationAndIdentification:
    """用户创建和识别的属性测试套件"""

    @pytest.fixture
    def mock_graph(self):
        """
        模拟图数据库连接
        
        Returns:
            Mock: 模拟的图数据库对象
        """
        mock = Mock()
        mock.query = AsyncMock()
        return mock

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider,provider_user_id,email,name",
        [
            # 微信用户
            ("wechat", "o6_bmjrPTlm6_2sgVt7hMZOPfL2M", 
             "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local", "张三"),
            ("wechat", "o6_test123456789abcdef", 
             "o6_test123456789abcdef@wechat.queryweaver.local", "李四"),
            # 企业微信用户
            ("wecom", "ZhangSan", "zhangsan@company.com", "张三"),
            ("wecom", "LiSi", "lisi@company.com", "李四"),
            # 其他提供商（确保兼容性）
            ("google", "google_user_123", "user@gmail.com", "Google User"),
            ("github", "github_user_456", "user@github.com", "GitHub User"),
        ],
    )
    async def test_first_login_creates_user(
        self, mock_graph, provider, provider_user_id, email, name
    ):
        """
        属性 3: 首次登录创建用户
        
        验证需求: 2.1.2.4, 2.2.2.4
        
        对于任何新的 provider_user_id，首次调用 ensure_user_in_organizations()
        应该创建新用户并返回 is_new_identity=True
        """
        # Arrange - 准备测试数据
        api_token = "test_token_" + provider_user_id
        picture = f"https://example.com/avatar/{provider_user_id}.jpg"
        
        # 模拟数据库返回新创建的用户（is_new_identity=True）
        mock_result = Mock()
        mock_result.result_set = [
            [
                {
                    "provider": provider,
                    "provider_user_id": provider_user_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                },
                {
                    "email": email,
                    "first_name": name.split()[0] if " " in name else name,
                    "last_name": name.split()[1] if " " in name and len(name.split()) > 1 else "",
                },
                True,  # is_new_identity
            ]
        ]
        mock_graph.query.return_value = mock_result
        
        # Act - 执行测试
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            is_new, user_info = await ensure_user_in_organizations(
                provider_user_id=provider_user_id,
                email=email,
                name=name,
                provider=provider,
                api_token=api_token,
                picture=picture,
            )
        
        # Assert - 验证结果
        assert is_new is True, f"首次登录应该创建新用户: provider={provider}"
        assert user_info is not None, "应该返回用户信息"
        assert user_info["new_identity"] is True, "应该标记为新身份"
        assert user_info["identity"]["provider"] == provider
        assert user_info["identity"]["provider_user_id"] == provider_user_id
        assert user_info["identity"]["email"] == email
        
        # 验证数据库查询被调用
        mock_graph.query.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider,provider_user_id,email,name",
        [
            # 微信用户重复登录
            ("wechat", "o6_bmjrPTlm6_2sgVt7hMZOPfL2M", 
             "o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local", "张三"),
            # 企业微信用户重复登录
            ("wecom", "ZhangSan", "zhangsan@company.com", "张三"),
        ],
    )
    async def test_repeat_login_identifies_user(
        self, mock_graph, provider, provider_user_id, email, name
    ):
        """
        属性 4: 重复登录识别用户
        
        验证需求: 2.1.2.5, 2.2.2.5
        
        对于任何已存在的 provider_user_id，重复调用 ensure_user_in_organizations()
        应该返回相同的用户，且 is_new_identity=False
        """
        # Arrange - 准备测试数据
        api_token_1 = "test_token_1_" + provider_user_id
        api_token_2 = "test_token_2_" + provider_user_id
        picture = f"https://example.com/avatar/{provider_user_id}.jpg"
        
        # 模拟数据库返回已存在的用户（is_new_identity=False）
        mock_result = Mock()
        mock_result.result_set = [
            [
                {
                    "provider": provider,
                    "provider_user_id": provider_user_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                },
                {
                    "email": email,
                    "first_name": name.split()[0] if " " in name else name,
                    "last_name": name.split()[1] if " " in name and len(name.split()) > 1 else "",
                },
                False,  # is_new_identity
            ]
        ]
        mock_graph.query.return_value = mock_result
        
        # Act - 第一次登录
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            is_new_1, user_info_1 = await ensure_user_in_organizations(
                provider_user_id=provider_user_id,
                email=email,
                name=name,
                provider=provider,
                api_token=api_token_1,
                picture=picture,
            )
        
        # 重置 mock 调用计数
        mock_graph.query.reset_mock()
        
        # Act - 第二次登录（使用不同的 token）
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            is_new_2, user_info_2 = await ensure_user_in_organizations(
                provider_user_id=provider_user_id,
                email=email,
                name=name,
                provider=provider,
                api_token=api_token_2,
                picture=picture,
            )
        
        # Assert - 验证结果
        assert is_new_1 is False, "重复登录不应该创建新用户"
        assert is_new_2 is False, "重复登录不应该创建新用户"
        
        assert user_info_1 is not None, "应该返回用户信息"
        assert user_info_2 is not None, "应该返回用户信息"
        
        # 验证返回的是同一个用户
        assert (
            user_info_1["identity"]["provider_user_id"]
            == user_info_2["identity"]["provider_user_id"]
        ), "应该识别为同一用户"
        assert (
            user_info_1["user"]["email"] == user_info_2["user"]["email"]
        ), "应该返回相同的用户邮箱"

    @pytest.mark.asyncio
    async def test_wechat_virtual_email_format(self, mock_graph):
        """
        测试微信虚拟邮箱格式
        
        验证需求: 2.1.2.5
        
        微信用户如果没有真实邮箱，应该使用 {openid}@wechat.queryweaver.local 格式
        """
        # Arrange
        openid = "o6_bmjrPTlm6_2sgVt7hMZOPfL2M"
        virtual_email = f"{openid}@wechat.queryweaver.local"
        
        mock_result = Mock()
        mock_result.result_set = [
            [
                {
                    "provider": "wechat",
                    "provider_user_id": openid,
                    "email": virtual_email,
                    "name": "微信用户",
                },
                {"email": virtual_email, "first_name": "微信用户", "last_name": ""},
                True,
            ]
        ]
        mock_graph.query.return_value = mock_result
        
        # Act
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            is_new, user_info = await ensure_user_in_organizations(
                provider_user_id=openid,
                email=virtual_email,
                name="微信用户",
                provider="wechat",
                api_token="test_token",
            )
        
        # Assert
        assert is_new is True
        assert user_info["identity"]["email"] == virtual_email
        assert "@wechat.queryweaver.local" in user_info["identity"]["email"]

    @pytest.mark.asyncio
    async def test_wecom_real_email(self, mock_graph):
        """
        测试企业微信真实邮箱
        
        验证需求: 2.2.2.5
        
        企业微信用户应该使用企业邮箱
        """
        # Arrange
        userid = "ZhangSan"
        real_email = "zhangsan@company.com"
        
        mock_result = Mock()
        mock_result.result_set = [
            [
                {
                    "provider": "wecom",
                    "provider_user_id": userid,
                    "email": real_email,
                    "name": "张三",
                },
                {"email": real_email, "first_name": "张三", "last_name": ""},
                True,
            ]
        ]
        mock_graph.query.return_value = mock_result
        
        # Act
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            is_new, user_info = await ensure_user_in_organizations(
                provider_user_id=userid,
                email=real_email,
                name="张三",
                provider="wecom",
                api_token="test_token",
            )
        
        # Assert
        assert is_new is True
        assert user_info["identity"]["email"] == real_email
        assert "@company.com" in user_info["identity"]["email"]
        assert "@wecom.queryweaver.local" not in user_info["identity"]["email"]


class TestInputValidation:
    """输入验证测试"""

    @pytest.mark.parametrize(
        "provider_user_id,email,provider,should_pass",
        [
            # 有效输入
            ("valid_id", "user@example.com", "wechat", True),
            ("valid_id", "user@example.com", "wecom", True),
            ("valid_id", "user@example.com", "google", True),
            ("valid_id", "user@example.com", "github", True),
            # 无效输入 - 缺少参数
            ("", "user@example.com", "wechat", False),
            ("valid_id", "", "wechat", False),
            ("valid_id", "user@example.com", "", False),
            # 无效输入 - 邮箱格式错误
            ("valid_id", "invalid_email", "wechat", False),
            ("valid_id", "no_at_sign.com", "wechat", False),
            ("valid_id", "no_domain@", "wechat", False),
            # 无效输入 - 不支持的提供商
            ("valid_id", "user@example.com", "invalid_provider", False),
            ("valid_id", "user@example.com", "facebook", False),
        ],
    )
    def test_validate_user_input(
        self, provider_user_id, email, provider, should_pass
    ):
        """
        测试输入验证函数
        
        验证需求: 2.1.2.4, 2.2.2.4
        """
        result = _validate_user_input(provider_user_id, email, provider)
        
        if should_pass:
            assert result is None, f"有效输入应该通过验证: {provider_user_id}, {email}, {provider}"
        else:
            assert result == (False, None), f"无效输入应该被拒绝: {provider_user_id}, {email}, {provider}"


class TestLastLoginUpdate:
    """最后登录时间更新测试"""

    @pytest.fixture
    def mock_graph(self):
        """模拟图数据库连接"""
        mock = Mock()
        mock.query = AsyncMock()
        return mock

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider,provider_user_id",
        [
            ("wechat", "o6_bmjrPTlm6_2sgVt7hMZOPfL2M"),
            ("wecom", "ZhangSan"),
            ("google", "google_user_123"),
            ("github", "github_user_456"),
        ],
    )
    async def test_update_last_login(self, mock_graph, provider, provider_user_id):
        """
        测试更新最后登录时间
        
        验证需求: 2.1.2.5, 2.2.2.5
        """
        # Arrange
        mock_result = Mock()
        mock_result.result_set = [[{"provider": provider, "provider_user_id": provider_user_id}]]
        mock_graph.query.return_value = mock_result
        
        # Act
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            await update_identity_last_login(provider, provider_user_id)
        
        # Assert
        mock_graph.query.assert_called_once()
        call_args = mock_graph.query.call_args
        
        # 验证查询包含正确的参数
        assert "last_login" in call_args[0][0], "应该更新 last_login 字段"
        assert call_args[1]["provider"] == provider
        assert call_args[1]["provider_user_id"] == provider_user_id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider,provider_user_id",
        [
            ("", "valid_id"),  # 空 provider
            ("wechat", ""),  # 空 provider_user_id
            ("invalid_provider", "valid_id"),  # 无效 provider
        ],
    )
    async def test_update_last_login_invalid_input(
        self, mock_graph, provider, provider_user_id
    ):
        """
        测试更新最后登录时间 - 无效输入
        
        应该优雅地处理无效输入，不抛出异常
        """
        # Act - 不应该抛出异常
        with patch("api.extensions.db.select_graph", return_value=mock_graph):
            await update_identity_last_login(provider, provider_user_id)
        
        # Assert - 对于无效输入，不应该调用数据库
        if not provider or not provider_user_id or provider not in ["google", "github", "email", "wechat", "wecom"]:
            mock_graph.query.assert_not_called()
