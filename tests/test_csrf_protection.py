"""
CSRF 防护属性测试

验证需求: 3.1.3 - CSRF 防护
属性 7: State 参数生成和验证

测试 OAuth state 参数的生成、验证和安全性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import time
from itsdangerous import URLSafeTimedSerializer

# 导入待测试的函数
from api.routes.auth import generate_state, verify_state


# ---- 属性 7: State 参数生成和验证 ----

class TestStateGeneration:
    """测试 state 参数生成的属性"""
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generate_state_returns_non_empty_string(self, provider: str):
        """
        属性: 生成的 state 必须是非空字符串
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        assert isinstance(state, str), "State 必须是字符串类型"
        assert len(state) > 0, "State 不能为空"
        assert state.strip() == state, "State 不应包含前后空格"
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generate_state_is_unique(self, provider: str):
        """
        属性: 每次生成的 state 应该是唯一的
        
        验证需求: 3.1.3
        """
        state1 = generate_state(provider)
        state2 = generate_state(provider)
        
        assert state1 != state2, "连续生成的 state 应该不同（包含随机 nonce）"
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generate_state_contains_provider_info(self, provider: str):
        """
        属性: 生成的 state 应该包含提供商信息（可解码验证）
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # 使用相同的序列化器解码
        import os
        serializer = URLSafeTimedSerializer(os.getenv("FASTAPI_SECRET_KEY", "default-secret-key"))
        
        try:
            state_data = serializer.loads(state, max_age=600)
            assert state_data.get("provider") == provider, "State 应包含正确的 provider"
            assert "nonce" in state_data, "State 应包含 nonce 字段"
            assert len(state_data["nonce"]) > 0, "Nonce 不应为空"
        except Exception as e:
            pytest.fail(f"State 解码失败: {str(e)}")


class TestStateVerification:
    """测试 state 参数验证的属性"""
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_accepts_valid_state(self, provider: str):
        """
        属性: 刚生成的有效 state 应该通过验证
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # 验证应该成功
        result = verify_state(state, provider, max_age=600)
        assert result is True, "有效的 state 应该通过验证"
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"]),
        wrong_provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_rejects_wrong_provider(self, provider: str, wrong_provider: str):
        """
        属性: 使用错误的 provider 验证应该失败
        
        验证需求: 3.1.3
        """
        # 确保 provider 不同
        assume(provider != wrong_provider)
        
        state = generate_state(provider)
        
        # 使用错误的 provider 验证应该失败
        result = verify_state(state, wrong_provider, max_age=600)
        assert result is False, "使用错误的 provider 验证应该失败"
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"]),
        invalid_state=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_rejects_invalid_format(self, provider: str, invalid_state: str):
        """
        属性: 无效格式的 state 应该被拒绝
        
        验证需求: 3.1.3
        """
        # 确保不是有效的 state 格式
        assume(not invalid_state.startswith("eyJ"))  # 避免偶然生成有效的 base64
        
        # 验证应该抛出异常或返回 False
        try:
            result = verify_state(invalid_state, provider, max_age=600)
            # 如果没有抛出异常，结果应该是 False
            assert result is False, "无效格式的 state 应该被拒绝"
        except ValueError:
            # 抛出 ValueError 也是可接受的
            pass
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_rejects_expired_state(self, provider: str):
        """
        属性: 过期的 state 应该被拒绝
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # 使用非常短的 max_age（1 秒）并等待过期
        time.sleep(2)
        
        # 验证应该失败（已过期）
        with pytest.raises(ValueError, match="State 验证失败"):
            verify_state(state, provider, max_age=1)
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_is_idempotent(self, provider: str):
        """
        属性: 多次验证同一个 state 应该得到相同结果（幂等性）
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # 多次验证应该得到相同结果
        result1 = verify_state(state, provider, max_age=600)
        result2 = verify_state(state, provider, max_age=600)
        result3 = verify_state(state, provider, max_age=600)
        
        assert result1 == result2 == result3, "多次验证应该得到相同结果"
        assert result1 is True, "有效的 state 应该始终通过验证"


class TestStateSecurityProperties:
    """测试 state 安全属性"""
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_state_cannot_be_forged_without_secret(self, provider: str):
        """
        属性: 没有密钥无法伪造有效的 state
        
        验证需求: 3.1.3
        """
        # 尝试手动构造一个 state
        import json
        import base64
        
        fake_data = {
            "provider": provider,
            "nonce": "fake_nonce_12345"
        }
        
        # 简单的 base64 编码（没有签名）
        fake_state = base64.urlsafe_b64encode(
            json.dumps(fake_data).encode()
        ).decode()
        
        # 验证应该失败
        try:
            result = verify_state(fake_state, provider, max_age=600)
            assert result is False, "伪造的 state 应该被拒绝"
        except ValueError:
            # 抛出异常也是可接受的
            pass
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_state_contains_sufficient_entropy(self, provider: str):
        """
        属性: State 应该包含足够的熵（随机性）
        
        验证需求: 3.1.3
        """
        # 生成多个 state
        states = [generate_state(provider) for _ in range(10)]
        
        # 所有 state 应该不同
        assert len(set(states)) == len(states), "生成的 state 应该都不相同"
        
        # 每个 state 的长度应该足够长（包含足够的随机性）
        for state in states:
            assert len(state) > 20, "State 长度应该足够长以确保安全性"


class TestStateCrossBoundary:
    """测试 state 的边界条件"""
    
    def test_verify_state_with_empty_string(self):
        """
        边界测试: 空字符串应该被拒绝
        
        验证需求: 3.1.3
        """
        with pytest.raises(ValueError):
            verify_state("", "wechat", max_age=600)
    
    def test_verify_state_with_none(self):
        """
        边界测试: None 应该被拒绝
        
        验证需求: 3.1.3
        """
        with pytest.raises((ValueError, AttributeError, TypeError)):
            verify_state(None, "wechat", max_age=600)
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_with_zero_max_age(self, provider: str):
        """
        边界测试: max_age=0 应该立即过期
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # max_age=0 应该导致验证失败
        with pytest.raises(ValueError, match="State 验证失败"):
            verify_state(state, provider, max_age=0)
    
    @given(
        provider=st.sampled_from(["wechat", "wecom", "google", "github"])
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_state_with_very_large_max_age(self, provider: str):
        """
        边界测试: 非常大的 max_age 应该正常工作
        
        验证需求: 3.1.3
        """
        state = generate_state(provider)
        
        # 使用非常大的 max_age（1 年）
        result = verify_state(state, provider, max_age=365*24*60*60)
        assert result is True, "使用大的 max_age 应该正常验证"


# ---- 集成测试 ----

class TestStateIntegration:
    """测试 state 在实际场景中的使用"""
    
    @given(
        provider=st.sampled_from(["wechat", "wecom"])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_complete_oauth_flow_state_handling(self, provider: str):
        """
        集成测试: 模拟完整的 OAuth 流程中的 state 处理
        
        验证需求: 3.1.3
        """
        # 1. 用户发起登录，生成 state
        state = generate_state(provider)
        
        # 2. 模拟存储到 cookie（这里只是保存到变量）
        stored_state = state
        
        # 3. 模拟 OAuth 回调，验证 state
        received_state = state  # 在实际场景中，这来自查询参数
        
        # 4. 验证 stored_state 和 received_state 匹配
        assert stored_state == received_state, "Cookie 中的 state 应该与回调中的 state 匹配"
        
        # 5. 验证 state 的有效性
        result = verify_state(received_state, provider, max_age=600)
        assert result is True, "完整流程中的 state 应该通过验证"
    
    def test_state_replay_attack_prevention(self):
        """
        安全测试: 防止 state 重放攻击
        
        验证需求: 3.1.3
        
        注意: 当前实现允许 state 重复使用（幂等性），
        在生产环境中应该配合服务器端的 state 使用记录来防止重放攻击
        """
        provider = "wechat"
        state = generate_state(provider)
        
        # 第一次使用 state
        result1 = verify_state(state, provider, max_age=600)
        assert result1 is True
        
        # 尝试重复使用同一个 state（当前实现允许）
        result2 = verify_state(state, provider, max_age=600)
        assert result2 is True
        
        # 注意: 在生产环境中，应该在服务器端记录已使用的 state
        # 并在第二次使用时拒绝，以防止重放攻击
