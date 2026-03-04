"""
兼容性集成测试

测试多提供商配置、配置切换和默认配置回退功能。
确保 DeepSeek 支持不会破坏现有的 OpenAI/Azure 配置。

验证需求：10.1, 10.2, 10.3
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from api.config import Config, UserConfig, EmbeddingsModel

# 配置 pytest-asyncio
pytestmark = pytest.mark.asyncio


class TestBackwardCompatibility:
    """测试向后兼容性"""
    
    @pytest.mark.asyncio
    async def test_existing_azure_config_still_works(self):
        """
        测试：现有 Azure 配置仍然正常工作
        
        验证需求 10.1：保持现有 OpenAI/Azure 配置工作
        """
        # 清空所有环境变量，只保留 Azure 配置
        with patch.dict(os.environ, {}, clear=True):
            # 模拟没有用户配置
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                # 获取模型
                model = await Config.get_completion_model()
                
                # 应该返回默认的 Azure 模型
                assert model == "azure/gpt-4.1"
                
                # 获取嵌入模型
                embedding_model = await Config.get_embedding_model()
                assert isinstance(embedding_model, EmbeddingsModel)
                assert embedding_model.model_name == "azure/text-embedding-ada-002"
    
    @pytest.mark.asyncio
    async def test_existing_openai_config_still_works(self):
        """
        测试：现有 OpenAI 配置仍然正常工作
        
        验证需求 10.1：保持现有 OpenAI/Azure 配置工作
        """
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                # 获取模型
                model = await Config.get_completion_model()
                
                # 应该返回 OpenAI 模型
                assert model.startswith("openai/")
                
                # 获取嵌入模型
                embedding_model = await Config.get_embedding_model()
                assert isinstance(embedding_model, EmbeddingsModel)
                assert embedding_model.model_name.startswith("openai/")
    
    @pytest.mark.asyncio
    async def test_deepseek_does_not_break_azure(self):
        """
        测试：添加 DeepSeek 配置不会破坏 Azure 配置
        
        验证需求 10.1：保持现有 OpenAI/Azure 配置工作
        """
        # 同时配置 DeepSeek 和 Azure（通过环境变量）
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'sk-deepseek-test123',
            'AZURE_API_KEY': 'azure-test123'
        }, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                # 获取模型（应该优先使用 DeepSeek）
                model = await Config.get_completion_model()
                
                # 应该返回 DeepSeek 模型（因为环境变量优先级）
                assert model.startswith("deepseek/")


class TestMultiProviderCoexistence:
    """测试多提供商并存"""
    
    @pytest.mark.asyncio
    async def test_user_can_use_deepseek_while_others_use_azure(self):
        """
        测试：用户可以使用 DeepSeek，而其他用户使用 Azure
        
        验证需求 10.2：支持多提供商并存
        """
        # 用户 A 配置了 DeepSeek
        user_a_config = UserConfig("user_a@example.com", {
            'provider': 'deepseek',
            'completion_model': 'deepseek-chat',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'sk-deepseek-a'
        })
        
        # 用户 B 没有配置（使用默认 Azure）
        with patch.dict(os.environ, {}, clear=True):
            # 模拟用户 A 的配置加载
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(return_value=user_a_config)
            ):
                model_a = await Config.get_completion_model("user_a@example.com")
                assert model_a == "deepseek/deepseek-chat"
            
            # 模拟用户 B 没有配置
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(return_value=None)
            ):
                model_b = await Config.get_completion_model("user_b@example.com")
                assert model_b == "azure/gpt-4.1"
    
    @pytest.mark.asyncio
    async def test_different_users_different_providers(self):
        """
        测试：不同用户可以使用不同的提供商
        
        验证需求 10.2：支持多提供商并存
        """
        # 用户 1: DeepSeek
        user1_config = UserConfig("user1@example.com", {
            'provider': 'deepseek',
            'completion_model': 'deepseek-chat',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'sk-deepseek-1'
        })
        
        # 用户 2: OpenAI
        user2_config = UserConfig("user2@example.com", {
            'provider': 'openai',
            'completion_model': 'gpt-4',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'sk-openai-2'
        })
        
        # 用户 3: Azure
        user3_config = UserConfig("user3@example.com", {
            'provider': 'azure',
            'completion_model': 'gpt-4.1',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'azure-3'
        })
        
        # 测试每个用户的配置
        configs = [
            ("user1@example.com", user1_config, "deepseek/deepseek-chat"),
            ("user2@example.com", user2_config, "openai/gpt-4"),
            ("user3@example.com", user3_config, "azure/gpt-4.1")
        ]
        
        for email, config, expected_model in configs:
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(return_value=config)
            ):
                model = await Config.get_completion_model(email)
                assert model == expected_model


class TestDefaultFallback:
    """测试默认配置回退"""
    
    @pytest.mark.asyncio
    async def test_fallback_to_env_when_user_config_fails(self):
        """
        测试：用户配置加载失败时回退到环境变量
        
        验证需求 10.3：未配置时使用默认提供商
        """
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'sk-deepseek-test123'
        }, clear=True):
            # 模拟用户配置加载失败
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(side_effect=Exception("数据库连接失败"))
            ):
                # 应该回退到环境变量配置
                model = await Config.get_completion_model("user@example.com")
                assert model.startswith("deepseek/")
    
    @pytest.mark.asyncio
    async def test_fallback_to_default_when_no_config(self):
        """
        测试：没有任何配置时使用默认值
        
        验证需求 10.3：未配置时使用默认提供商
        """
        # 清空所有环境变量
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                # 应该使用默认的 Azure 配置
                model = await Config.get_completion_model()
                assert model == "azure/gpt-4.1"
    
    @pytest.mark.asyncio
    async def test_fallback_chain_user_to_env_to_default(self):
        """
        测试：完整的回退链：用户配置 -> 环境变量 -> 默认值
        
        验证需求 10.3：未配置时使用默认提供商
        """
        # 场景 1：有用户配置
        user_config = UserConfig("user@example.com", {
            'provider': 'deepseek',
            'completion_model': 'deepseek-chat',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'sk-deepseek-user'
        })
        
        with patch.object(
            Config, 
            'load_user_config', 
            new=AsyncMock(return_value=user_config)
        ):
            model = await Config.get_completion_model("user@example.com")
            assert model == "deepseek/deepseek-chat"
        
        # 场景 2：没有用户配置，但有环境变量
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                model = await Config.get_completion_model("user@example.com")
                assert model.startswith("openai/")
        
        # 场景 3：没有用户配置，也没有环境变量
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                model = await Config.get_completion_model("user@example.com")
                assert model == "azure/gpt-4.1"


class TestConfigurationPriority:
    """测试配置优先级"""
    
    @pytest.mark.asyncio
    async def test_user_config_overrides_env_var(self):
        """
        测试：用户配置优先于环境变量
        
        验证需求 10.4：配置优先级正确
        """
        # 设置环境变量为 OpenAI
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            # 用户配置为 DeepSeek
            user_config = UserConfig("user@example.com", {
                'provider': 'deepseek',
                'completion_model': 'deepseek-chat',
                'embedding_model': 'text-embedding-ada-002',
                'api_key': 'sk-deepseek-user'
            })
            
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(return_value=user_config)
            ):
                model = await Config.get_completion_model("user@example.com")
                # 应该使用用户配置的 DeepSeek，而不是环境变量的 OpenAI
                assert model == "deepseek/deepseek-chat"
    
    @pytest.mark.asyncio
    async def test_env_var_overrides_default(self):
        """
        测试：环境变量优先于默认值
        
        验证需求 10.4：配置优先级正确
        """
        # 设置 DeepSeek 环境变量
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'sk-deepseek-test123'
        }, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                model = await Config.get_completion_model()
                # 应该使用环境变量的 DeepSeek，而不是默认的 Azure
                assert model.startswith("deepseek/")
    
    @pytest.mark.asyncio
    async def test_no_user_email_skips_user_config(self):
        """
        测试：没有提供用户邮箱时跳过用户配置加载
        
        验证需求 10.4：配置优先级正确
        """
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            # 不提供用户邮箱
            model = await Config.get_completion_model(user_email=None)
            
            # 应该直接使用环境变量，不尝试加载用户配置
            assert model.startswith("openai/")


class TestEmbeddingModelCompatibility:
    """测试嵌入模型兼容性"""
    
    @pytest.mark.asyncio
    async def test_azure_embedding_model_still_works(self):
        """
        测试：Azure 嵌入模型仍然正常工作
        
        验证需求 10.1：保持现有配置工作
        """
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                embedding_model = await Config.get_embedding_model()
                
                assert isinstance(embedding_model, EmbeddingsModel)
                assert embedding_model.model_name == "azure/text-embedding-ada-002"
    
    @pytest.mark.asyncio
    async def test_openai_embedding_model_still_works(self):
        """
        测试：OpenAI 嵌入模型仍然正常工作
        
        验证需求 10.1：保持现有配置工作
        """
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            with patch.object(Config, 'load_user_config', new=AsyncMock(return_value=None)):
                embedding_model = await Config.get_embedding_model()
                
                assert isinstance(embedding_model, EmbeddingsModel)
                assert embedding_model.model_name.startswith("openai/")
    
    @pytest.mark.asyncio
    async def test_deepseek_embedding_uses_openai(self):
        """
        测试：DeepSeek 嵌入模型使用 OpenAI（因为 DeepSeek 暂无嵌入模型）
        
        验证需求 10.2：支持多提供商并存
        """
        user_config = UserConfig("user@example.com", {
            'provider': 'deepseek',
            'completion_model': 'deepseek-chat',
            'embedding_model': 'text-embedding-ada-002',
            'api_key': 'sk-deepseek-test'
        })
        
        with patch.object(
            Config, 
            'load_user_config', 
            new=AsyncMock(return_value=user_config)
        ):
            embedding_model = await Config.get_embedding_model("user@example.com")
            
            assert isinstance(embedding_model, EmbeddingsModel)
            # DeepSeek 应该使用 OpenAI 的嵌入模型
            assert embedding_model.model_name == "openai/text-embedding-ada-002"


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_config_error(self):
        """
        测试：配置加载错误时优雅降级
        
        验证需求 10.3：未配置时使用默认提供商
        """
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'sk-deepseek-test123'
        }, clear=True):
            # 模拟配置加载抛出异常
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(side_effect=Exception("配置加载失败"))
            ):
                # 应该捕获异常并回退到环境变量
                model = await Config.get_completion_model("user@example.com")
                assert model.startswith("deepseek/")
    
    @pytest.mark.asyncio
    async def test_invalid_user_config_falls_back(self):
        """
        测试：无效的用户配置时回退到环境变量
        
        验证需求 10.3：未配置时使用默认提供商
        """
        # 返回一个无效的配置（缺少必要字段）
        invalid_config = UserConfig("user@example.com", {
            'provider': 'deepseek',
            # 缺少 completion_model
            'embedding_model': 'text-embedding-ada-002'
        })
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-openai-test123'
        }, clear=True):
            with patch.object(
                Config, 
                'load_user_config', 
                new=AsyncMock(return_value=invalid_config)
            ):
                # 由于配置无效（completion_model 为 None），应该回退
                model = await Config.get_completion_model("user@example.com")
                # 应该回退到环境变量
                assert model.startswith("openai/")
