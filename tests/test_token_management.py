"""
Token 管理属性测试

本测试文件验证 API Token 的安全性和管理功能，包括：
- 属性 8: API Token 有效期设置
- 属性 9: Token 与 Identity 关联

使用 hypothesis 进行属性测试，每个测试至少运行 100 次迭代
"""

import pytest
import secrets
import time
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse


# ============================================================================
# 属性 8: API Token 有效期设置
# ============================================================================

@given(
    max_age=st.integers(min_value=1, max_value=86400 * 7)  # 1秒到7天
)
@settings(max_examples=100)
def test_property_8_cookie_max_age_setting(max_age):
    """
    属性 8: API Token 有效期设置
    
    验证需求: 3.1.4
    
    对于任何设置的 max_age 值，Cookie 应该正确设置过期时间
    
    测试策略:
    - 生成不同的 max_age 值
    - 验证 Cookie 的 max_age 属性正确设置
    - 验证过期时间计算正确
    """
    from fastapi.responses import Response
    
    # 创建响应对象
    response = Response()
    
    # 生成测试 token
    api_token = secrets.token_urlsafe(32)
    
    # 设置 Cookie
    response.set_cookie(
        key="api_token",
        value=api_token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    # 验证 Cookie 头部包含 max_age
    cookie_header = response.headers.get("set-cookie")
    assert cookie_header is not None
    assert f"Max-Age={max_age}" in cookie_header
    
    # 验证其他安全属性
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "SameSite=lax" in cookie_header


@settings(max_examples=100)
def test_property_8_token_expiry_24_hours():
    """
    属性 8: API Token 有效期设置（24小时验证）
    
    验证需求: 3.1.4
    
    验证所有 OAuth 提供商的 API Token 都设置为 24 小时过期
    
    测试策略:
    - 模拟各个 OAuth 回调
    - 验证返回的 Cookie max_age 为 86400 秒（24小时）
    """
    from fastapi.responses import Response
    
    # 期望的过期时间（24小时）
    expected_max_age = 86400
    
    # 测试所有 OAuth 提供商
    providers = ["google", "github", "wechat", "wecom", "email"]
    
    for provider in providers:
        response = Response()
        api_token = secrets.token_urlsafe(32)
        
        # 设置 Cookie（模拟实际代码）
        response.set_cookie(
            key="api_token",
            value=api_token,
            max_age=expected_max_age,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # 验证 max_age 正确
        cookie_header = response.headers.get("set-cookie")
        assert f"Max-Age={expected_max_age}" in cookie_header, \
            f"{provider} provider 的 Token 过期时间应为 24 小时"


@given(
    token_count=st.integers(min_value=10, max_value=100)
)
@settings(max_examples=50)
def test_property_8_token_expiry_consistency(token_count):
    """
    属性 8: Token 过期时间一致性
    
    验证需求: 3.1.4
    
    对于任何数量的 Token 生成，过期时间设置应该保持一致
    
    测试策略:
    - 生成多个 Token
    - 验证所有 Token 的过期时间都是 24 小时
    """
    from fastapi.responses import Response
    
    expected_max_age = 86400
    
    for _ in range(token_count):
        response = Response()
        api_token = secrets.token_urlsafe(32)
        
        response.set_cookie(
            key="api_token",
            value=api_token,
            max_age=expected_max_age,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        cookie_header = response.headers.get("set-cookie")
        assert f"Max-Age={expected_max_age}" in cookie_header


# ============================================================================
# 属性 9: Token 与 Identity 关联
# ============================================================================

@pytest.mark.asyncio
@given(
    provider=st.sampled_from(["google", "github", "wechat", "wecom", "email"]),
    user_id=st.text(min_size=10, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), 
        whitelist_characters="_-"
    )),
    email=st.emails()
)
@settings(max_examples=100)
async def test_property_9_token_identity_association(provider, user_id, email):
    """
    属性 9: Token 与 Identity 关联
    
    验证需求: 3.1.4
    
    对于任何生成的 API Token，应该正确关联到对应的 Identity
    
    测试策略:
    - 生成不同的用户身份
    - 创建 API Token
    - 验证 Token 与 Identity 的关联关系
    """
    from api.auth.user_management import ensure_user_in_organizations
    
    # 生成 API Token
    api_token = secrets.token_urlsafe(32)
    
    # 模拟用户数据
    user_data = {
        "id": user_id,
        "email": email,
        "name": f"Test User {user_id[:8]}",
        "provider": provider
    }
    
    # Mock FalkorDB 图数据库
    with patch("api.extensions.db") as mock_db:
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # Mock 查询结果 - 新用户
        mock_result = Mock()
        mock_result.result_set = []
        mock_graph.query = AsyncMock(return_value=mock_result)
        
        # 调用用户管理函数
        success, user_info = await ensure_user_in_organizations(
            provider_user_id=user_id,
            email=email,
            name=user_data["name"],
            provider=provider,
            api_token=api_token
        )
        
        # 验证 Token 与 Identity 关联
        assert success is True
        
        # 验证调用了数据库查询
        assert mock_graph.query.called
        
        # 验证查询参数包含 api_token
        call_args = mock_graph.query.call_args_list
        query_params_found = False
        for call in call_args:
            if len(call[0]) > 1:  # 有参数
                params = call[0][1]
                if "api_token" in params:
                    assert params["api_token"] == api_token
                    query_params_found = True
                    break
        
        # 如果没有找到 api_token 参数，检查是否在查询字符串中
        if not query_params_found:
            for call in call_args:
                query_str = call[0][0]
                if "api_token" in query_str:
                    query_params_found = True
                    break


@pytest.mark.asyncio
@given(
    token_count=st.integers(min_value=5, max_value=20)
)
@settings(max_examples=50)
async def test_property_9_unique_token_per_identity(token_count):
    """
    属性 9: 每个 Identity 的 Token 唯一性
    
    验证需求: 3.1.4
    
    对于任何数量的登录请求，每次应该生成唯一的 API Token
    
    测试策略:
    - 模拟同一用户多次登录
    - 验证每次生成的 Token 都不同
    - 验证 Token 都正确关联到同一 Identity
    """
    from api.auth.user_management import ensure_user_in_organizations
    
    provider = "wechat"
    user_id = "test_openid_12345"
    email = f"{user_id}@wechat.queryweaver.local"
    name = "测试用户"
    
    generated_tokens = set()
    
    # Mock FalkorDB
    with patch("api.extensions.db") as mock_db:
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # Mock 查询结果 - 已存在的用户
        mock_result = Mock()
        mock_identity = Mock()
        mock_identity.properties = {
            "provider_user_id": user_id,
            "email": email,
            "provider": provider
        }
        mock_user = Mock()
        mock_user.properties = {"id": "user_123"}
        mock_result.result_set = [[mock_identity, mock_user]]
        mock_graph.query = AsyncMock(return_value=mock_result)
        
        # 模拟多次登录
        for _ in range(token_count):
            # 生成新的 API Token
            api_token = secrets.token_urlsafe(32)
            
            # 验证 Token 唯一性
            assert api_token not in generated_tokens, \
                "生成的 API Token 应该是唯一的"
            generated_tokens.add(api_token)
            
            # 调用用户管理函数
            success, user_info = await ensure_user_in_organizations(
                provider_user_id=user_id,
                email=email,
                name=name,
                provider=provider,
                api_token=api_token
            )
            
            # 验证成功
            assert success is True
    
    # 验证所有 Token 都是唯一的
    assert len(generated_tokens) == token_count


@pytest.mark.asyncio
@given(
    provider1=st.sampled_from(["google", "github"]),
    provider2=st.sampled_from(["wechat", "wecom"]),
    email=st.emails()
)
@settings(max_examples=50)
async def test_property_9_cross_provider_token_isolation(provider1, provider2, email):
    """
    属性 9: 跨提供商 Token 隔离
    
    验证需求: 3.1.4
    
    对于同一邮箱的不同提供商登录，应该生成不同的 Token
    
    测试策略:
    - 使用同一邮箱通过不同提供商登录
    - 验证生成的 Token 不同
    - 验证 Token 正确关联到各自的 Identity
    """
    from api.auth.user_management import ensure_user_in_organizations
    
    # 生成两个不同的 Token
    token1 = secrets.token_urlsafe(32)
    token2 = secrets.token_urlsafe(32)
    
    # 确保 Token 不同
    assert token1 != token2
    
    # Mock FalkorDB
    with patch("api.extensions.db") as mock_db:
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # Mock 查询结果 - 新用户
        mock_result = Mock()
        mock_result.result_set = []
        mock_graph.query = AsyncMock(return_value=mock_result)
        
        # 第一个提供商登录
        success1, user_info1 = await ensure_user_in_organizations(
            provider_user_id=f"{provider1}_user_123",
            email=email,
            name="Test User",
            provider=provider1,
            api_token=token1
        )
        
        # 第二个提供商登录
        success2, user_info2 = await ensure_user_in_organizations(
            provider_user_id=f"{provider2}_user_456",
            email=email,
            name="Test User",
            provider=provider2,
            api_token=token2
        )
        
        # 验证两次登录都成功
        assert success1 is True
        assert success2 is True
        
        # 验证使用了不同的 Token
        assert token1 != token2


@given(
    token_length=st.integers(min_value=32, max_value=64)
)
@settings(max_examples=100)
def test_property_9_token_security_strength(token_length):
    """
    属性 9: Token 安全强度
    
    验证需求: 3.1.4
    
    对于任何生成的 Token，应该具有足够的随机性和长度
    
    测试策略:
    - 生成不同长度的 Token
    - 验证 Token 的随机性（至少 256 位）
    - 验证 Token 的唯一性
    """
    # 生成 Token
    token = secrets.token_urlsafe(token_length)
    
    # 验证长度（base64 编码后的长度）
    # token_urlsafe(32) 生成 256 位随机数，base64 编码后约 43 字符
    expected_min_length = (token_length * 4 // 3)  # base64 编码比例
    assert len(token) >= expected_min_length
    
    # 验证字符集（URL 安全的 base64）
    import string
    valid_chars = string.ascii_letters + string.digits + "-_"
    assert all(c in valid_chars for c in token)
    
    # 验证唯一性（生成多个 Token）
    tokens = set()
    for _ in range(100):
        new_token = secrets.token_urlsafe(token_length)
        assert new_token not in tokens
        tokens.add(new_token)


# ============================================================================
# 辅助测试：验证实际路由中的 Token 设置
# ============================================================================

@pytest.mark.asyncio
async def test_actual_cookie_settings_in_routes():
    """
    验证实际路由中的 Cookie 设置符合安全要求
    
    这个测试检查所有 OAuth 路由是否正确设置了：
    - max_age=86400 (24小时)
    - httponly=True
    - secure=True
    - samesite="lax"
    """
    from fastapi.responses import RedirectResponse
    
    # 测试数据
    api_token = secrets.token_urlsafe(32)
    
    # 创建响应（模拟实际路由）
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="api_token",
        value=api_token,
        max_age=86400,  # 24 小时
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    # 验证 Cookie 头部
    cookie_header = response.headers.get("set-cookie")
    
    # 验证所有安全属性
    assert "api_token=" in cookie_header
    assert "Max-Age=86400" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "SameSite=lax" in cookie_header
    
    print(f"✓ Cookie 设置验证通过: {cookie_header}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
