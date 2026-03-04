"""
安全性单元测试

测试加密密钥管理、API Key 验证和日志脱敏功能。
验证需求：11.1, 11.2, 11.3, 11.4
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from api.config_manager import (
    LLMConfigManager,
    ConfigurationError,
    EncryptionError,
    mask_api_key
)


class TestEncryptionKeyManagement:
    """测试加密密钥管理功能"""
    
    def test_load_encryption_key_from_env(self):
        """测试从环境变量加载加密密钥"""
        # 生成测试密钥
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            # 验证密钥已加载
            assert manager.encryption_key is not None
            assert isinstance(manager.encryption_key, bytes)
            
            # 验证可以使用密钥进行加密
            test_data = "test_api_key"
            encrypted = manager.encrypt_api_key(test_data)
            assert encrypted != test_data
    
    def test_generate_default_key_when_not_configured(self):
        """测试未配置密钥时生成默认密钥"""
        with patch.dict(os.environ, {}, clear=True):
            # 移除环境变量
            if 'LLM_CONFIG_ENCRYPTION_KEY' in os.environ:
                del os.environ['LLM_CONFIG_ENCRYPTION_KEY']
            
            # 应该生成默认密钥并记录警告
            with patch('api.config_manager.logger') as mock_logger:
                manager = LLMConfigManager()
                
                # 验证记录了警告
                assert mock_logger.warning.called
                warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                assert any('加密密钥未配置' in msg for msg in warning_calls)
                assert any('默认加密密钥' in msg for msg in warning_calls)
                
                # 验证密钥可用
                assert manager.encryption_key is not None
                test_data = "test_api_key"
                encrypted = manager.encrypt_api_key(test_data)
                decrypted = manager.decrypt_api_key(encrypted)
                assert decrypted == test_data
    
    def test_invalid_encryption_key_format(self):
        """测试无效的加密密钥格式"""
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': 'invalid_key'}):
            with pytest.raises(EncryptionError) as exc_info:
                LLMConfigManager()
            
            assert '加密密钥格式无效' in str(exc_info.value)
    
    def test_generate_encryption_key(self):
        """测试生成加密密钥方法"""
        key = LLMConfigManager.generate_encryption_key()
        
        # 验证密钥格式
        assert isinstance(key, str)
        assert len(key) > 0
        
        # 验证密钥可用
        key_bytes = key.encode('utf-8')
        cipher = Fernet(key_bytes)
        
        # 测试加密解密
        test_data = b"test_data"
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == test_data


class TestAPIKeyValidation:
    """测试 API Key 验证功能"""
    
    def test_validate_api_key_format_deepseek_valid(self):
        """测试 DeepSeek API Key 格式验证 - 有效"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "sk-abc123def456ghi789",
            "deepseek"
        )
        
        assert valid is True
        assert error is None
    
    def test_validate_api_key_format_deepseek_invalid_prefix(self):
        """测试 DeepSeek API Key 格式验证 - 无效前缀"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "abc123def456ghi789",
            "deepseek"
        )
        
        assert valid is False
        assert "必须以 'sk-' 开头" in error
    
    def test_validate_api_key_format_empty(self):
        """测试空 API Key"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "",
            "deepseek"
        )
        
        assert valid is False
        assert "不能为空" in error
    
    def test_validate_api_key_format_too_short(self):
        """测试过短的 API Key"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "sk-abc",
            "deepseek"
        )
        
        assert valid is False
        assert "长度过短" in error
    
    def test_validate_api_key_format_invalid_characters(self):
        """测试包含非法字符的 API Key"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "sk-abc@123#def",
            "deepseek"
        )
        
        assert valid is False
        assert "非法字符" in error
    
    def test_validate_api_key_format_openai(self):
        """测试 OpenAI API Key 格式验证"""
        valid, error = LLMConfigManager.validate_api_key_format(
            "sk-proj-abc123def456",
            "openai"
        )
        
        assert valid is True
        assert error is None
    
    def test_validate_api_key_format_azure(self):
        """测试 Azure API Key 格式验证"""
        # Azure 使用 32 位十六进制
        valid, error = LLMConfigManager.validate_api_key_format(
            "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "azure"
        )
        
        # Azure 格式检查较宽松，只要不是空或太短即可
        assert valid is True
    
    @pytest.mark.asyncio
    async def test_validate_api_key_active_success(self):
        """测试 API Key 有效性验证 - 成功"""
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            # Mock test_connection 方法
            with patch.object(manager, 'test_connection') as mock_test:
                mock_test.return_value = {
                    'success': True,
                    'message': '连接成功',
                    'latency': 100.0
                }
                
                valid, error = await manager.validate_api_key_active(
                    "sk-test123456789",
                    "deepseek"
                )
                
                assert valid is True
                assert error is None
                mock_test.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_active_failure(self):
        """测试 API Key 有效性验证 - 失败"""
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            # Mock test_connection 方法
            with patch.object(manager, 'test_connection') as mock_test:
                mock_test.return_value = {
                    'success': False,
                    'message': 'API Key 无效',
                    'latency': 0
                }
                
                valid, error = await manager.validate_api_key_active(
                    "sk-invalid123456",
                    "deepseek"
                )
                
                assert valid is False
                assert error == 'API Key 无效'
    
    @pytest.mark.asyncio
    async def test_save_config_with_invalid_api_key_format(self):
        """测试保存配置时验证 API Key 格式"""
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            config = {
                'provider': 'deepseek',
                'completion_model': 'deepseek-chat',
                'api_key': 'invalid_key'  # 无效格式
            }
            
            with pytest.raises(ConfigurationError) as exc_info:
                await manager.save_user_config(
                    'test@example.com',
                    config,
                    validate_api_key=False  # 只验证格式，不验证有效性
                )
            
            assert 'API Key 格式无效' in str(exc_info.value)


class TestLogSanitization:
    """测试日志脱敏功能"""
    
    def test_mask_api_key_standard(self):
        """测试标准 API Key 遮蔽"""
        api_key = "sk-abc123def456ghi789jkl012"
        masked = mask_api_key(api_key)
        
        # 验证遮蔽格式
        assert masked.startswith("sk-abc")
        assert masked.endswith("l012")
        assert "..." in masked
        
        # 验证不包含完整密钥
        assert api_key != masked
        assert len(masked) < len(api_key)
    
    def test_mask_api_key_short(self):
        """测试短 API Key 遮蔽"""
        api_key = "short"
        masked = mask_api_key(api_key)
        
        # 短密钥应该完全遮蔽
        assert masked == "***"
    
    def test_mask_api_key_empty(self):
        """测试空 API Key 遮蔽"""
        masked = mask_api_key("")
        assert masked == "***"
    
    def test_mask_api_key_none(self):
        """测试 None API Key 遮蔽"""
        masked = mask_api_key(None)
        assert masked == "***"
    
    def test_api_key_not_in_logs(self):
        """测试日志中不包含完整 API Key"""
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            api_key = "sk-test123456789abcdef"
            
            # 捕获日志输出
            with patch('api.config_manager.logger') as mock_logger:
                encrypted = manager.encrypt_api_key(api_key)
                
                # 检查所有日志调用
                for call in mock_logger.debug.call_args_list:
                    log_message = str(call)
                    # 确保完整的 API Key 不在日志中
                    assert api_key not in log_message


class TestEncryptionRoundtrip:
    """测试加密解密往返"""
    
    def test_encryption_decryption_roundtrip(self):
        """测试加密解密往返保持数据完整性"""
        test_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': test_key}):
            manager = LLMConfigManager()
            
            # 测试多个不同的 API Key
            test_keys = [
                "sk-abc123",
                "sk-very-long-api-key-with-many-characters-123456789",
                "sk-special_chars-123",
                "sk-unicode-测试-123"
            ]
            
            for original_key in test_keys:
                # 加密
                encrypted = manager.encrypt_api_key(original_key)
                
                # 验证已加密
                assert encrypted != original_key
                
                # 解密
                decrypted = manager.decrypt_api_key(encrypted)
                
                # 验证往返一致
                assert decrypted == original_key
    
    def test_encryption_with_different_keys_fails(self):
        """测试使用不同密钥解密失败"""
        # 使用第一个密钥加密
        key1 = Fernet.generate_key().decode('utf-8')
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': key1}):
            manager1 = LLMConfigManager()
            encrypted = manager1.encrypt_api_key("sk-test123")
        
        # 使用第二个密钥尝试解密
        key2 = Fernet.generate_key().decode('utf-8')
        with patch.dict(os.environ, {'LLM_CONFIG_ENCRYPTION_KEY': key2}):
            manager2 = LLMConfigManager()
            
            with pytest.raises(EncryptionError) as exc_info:
                manager2.decrypt_api_key(encrypted)
            
            assert '解密失败' in str(exc_info.value)


class TestKeyRotation:
    """测试密钥轮换功能"""
    
    def test_generate_new_key(self):
        """测试生成新密钥用于轮换"""
        # 生成两个不同的密钥
        key1 = LLMConfigManager.generate_encryption_key()
        key2 = LLMConfigManager.generate_encryption_key()
        
        # 验证密钥不同
        assert key1 != key2
        
        # 验证密钥格式正确
        assert isinstance(key1, str)
        assert isinstance(key2, str)
        
        # 验证密钥可用
        cipher1 = Fernet(key1.encode('utf-8'))
        cipher2 = Fernet(key2.encode('utf-8'))
        
        # 测试加密解密
        test_data = b"test_data"
        encrypted1 = cipher1.encrypt(test_data)
        encrypted2 = cipher2.encrypt(test_data)
        
        # 验证不同密钥产生不同的加密结果
        assert encrypted1 != encrypted2
        
        # 验证各自可以解密
        assert cipher1.decrypt(encrypted1) == test_data
        assert cipher2.decrypt(encrypted2) == test_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
