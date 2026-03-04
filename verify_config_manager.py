"""
配置管理器验证脚本

验证 LLMConfigManager 的核心功能
"""

import os
import sys
from cryptography.fernet import Fernet
import base64

# 设置测试环境变量
# Fernet.generate_key() 已经返回 Base64 编码的密钥
test_key = Fernet.generate_key()
os.environ['LLM_CONFIG_ENCRYPTION_KEY'] = test_key.decode()

# 导入配置管理器
from api.config_manager import LLMConfigManager, mask_api_key

def test_initialization():
    """测试初始化"""
    print("测试 1: 初始化配置管理器...")
    try:
        manager = LLMConfigManager()
        print("✓ 初始化成功")
        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False

def test_encryption_roundtrip():
    """测试加密往返"""
    print("\n测试 2: API Key 加密往返...")
    try:
        manager = LLMConfigManager()
        
        test_keys = [
            "sk-test123456789",
            "sk-very-long-api-key-with-many-characters",
            "sk-中文测试"
        ]
        
        for original_key in test_keys:
            encrypted = manager.encrypt_api_key(original_key)
            decrypted = manager.decrypt_api_key(encrypted)
            
            if decrypted != original_key:
                print(f"✗ 往返失败: {original_key}")
                return False
            
            if encrypted == original_key:
                print(f"✗ 加密未生效: {original_key}")
                return False
        
        print("✓ 加密往返测试通过")
        return True
    except Exception as e:
        print(f"✗ 加密往返失败: {e}")
        return False

def test_validation():
    """测试配置验证"""
    print("\n测试 3: 配置验证...")
    try:
        manager = LLMConfigManager()
        
        # 有效配置
        valid_config = {
            'provider': 'deepseek',
            'completion_model': 'deepseek-chat',
            'api_key': 'sk-test123456789'
        }
        manager._validate_config(valid_config)
        print("✓ 有效配置验证通过")
        
        # 无效配置 - 缺少字段
        try:
            invalid_config = {'provider': 'deepseek'}
            manager._validate_config(invalid_config)
            print("✗ 应该拒绝无效配置")
            return False
        except Exception:
            print("✓ 正确拒绝无效配置")
        
        return True
    except Exception as e:
        print(f"✗ 配置验证失败: {e}")
        return False

def test_mask_api_key():
    """测试 API Key 遮蔽"""
    print("\n测试 4: API Key 遮蔽...")
    try:
        test_cases = [
            ("sk-test123456789", "sk-tes...6789"),
            ("short", "***"),
            ("", "***"),
            (None, "***")
        ]
        
        for api_key, expected in test_cases:
            result = mask_api_key(api_key)
            if result != expected:
                print(f"✗ 遮蔽失败: {api_key} -> {result} (期望: {expected})")
                return False
        
        print("✓ API Key 遮蔽测试通过")
        return True
    except Exception as e:
        print(f"✗ API Key 遮蔽失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("配置管理器验证")
    print("=" * 60)
    
    tests = [
        test_initialization,
        test_encryption_roundtrip,
        test_validation,
        test_mask_api_key
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)
    
    if all(results):
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
