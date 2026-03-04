"""
LLM 配置管理模块

负责用户 LLM 配置的加载、保存、加密和解密操作。
支持 DeepSeek、OpenAI、Azure 等多种模型提供商的配置管理。
"""

from typing import Optional, Dict, Any, Tuple, List
from cryptography.fernet import Fernet, InvalidToken
import json
import os
import base64
import logging
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


class EncryptionError(Exception):
    """加密错误异常"""
    pass


class LLMConfigManager:
    """
    LLM 配置管理器
    
    负责用户 LLM 配置的加载、保存、加密和解密。
    使用 Fernet 对称加密保护敏感信息（如 API Key）。
    配置存储在 FalkorDB Organizations 图数据库的 User 节点中。
    """
    
    def __init__(self):
        """
        初始化配置管理器
        
        加载加密密钥并创建 Fernet 加密器实例。
        
        Raises:
            EncryptionError: 加密密钥加载失败时抛出
        """
        self.encryption_key = self._load_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        logger.info("LLM 配置管理器初始化成功")
    
    def _load_encryption_key(self) -> bytes:
        """
        从环境变量加载加密密钥，如果未配置则生成默认密钥
        
        加密密钥应该是 Fernet.generate_key() 生成的 Base64 编码字符串。
        该字符串本身就是 URL 安全的 Base64 编码，可以直接用于 Fernet。
        
        安全警告：
        - 如果未配置加密密钥，系统将生成默认密钥
        - 默认密钥仅用于开发和测试环境
        - 生产环境必须配置自定义加密密钥
        
        Returns:
            bytes: 加密密钥（Fernet 格式）
            
        Raises:
            EncryptionError: 密钥格式无效时抛出
        """
        key = os.getenv('LLM_CONFIG_ENCRYPTION_KEY')
        
        if not key:
            # 生成默认加密密钥
            logger.warning(
                "⚠️  加密密钥未配置：LLM_CONFIG_ENCRYPTION_KEY 环境变量未设置"
            )
            logger.warning(
                "⚠️  系统将使用默认加密密钥，这在生产环境中是不安全的！"
            )
            logger.warning(
                "⚠️  请立即设置 LLM_CONFIG_ENCRYPTION_KEY 环境变量"
            )
            logger.warning(
                "⚠️  生成密钥命令: python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
            
            # 生成默认密钥（仅用于开发环境）
            default_key = Fernet.generate_key()
            logger.info("已生成默认加密密钥（仅用于开发环境）")
            
            return default_key
        
        try:
            # Fernet.generate_key() 返回的是 bytes，环境变量中存储的是字符串
            # 需要转换为 bytes
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            
            # 验证密钥格式（尝试创建 Fernet 实例）
            Fernet(key_bytes)
            
            logger.info("加密密钥加载成功")
            return key_bytes
            
        except Exception as e:
            logger.error(f"加密密钥格式无效: {str(e)}")
            raise EncryptionError(f"加密密钥格式无效: {str(e)}")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        加密 API Key
        
        使用 Fernet 对称加密算法加密 API Key。
        加密后的数据使用 Base64 编码以便存储。
        
        Args:
            api_key: 明文 API Key
            
        Returns:
            str: 加密后的 API Key（Base64 编码）
            
        Raises:
            EncryptionError: 加密失败时抛出
        """
        if not api_key:
            raise ValueError("API Key 不能为空")
        
        try:
            # 加密 API Key
            encrypted_bytes = self.cipher.encrypt(api_key.encode('utf-8'))
            
            # Base64 编码以便存储
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            logger.debug("API Key 加密成功")
            return encrypted_str
            
        except Exception as e:
            logger.error(f"API Key 加密失败: {str(e)}")
            raise EncryptionError(f"加密失败: {str(e)}")
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        解密 API Key
        
        解密使用 encrypt_api_key 方法加密的 API Key。
        
        Args:
            encrypted_key: 加密的 API Key（Base64 编码）
            
        Returns:
            str: 明文 API Key
            
        Raises:
            EncryptionError: 解密失败时抛出
        """
        if not encrypted_key:
            raise ValueError("加密的 API Key 不能为空")
        
        try:
            # Base64 解码
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode('utf-8'))
            
            # 解密
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            logger.debug("API Key 解密成功")
            return decrypted_str
            
        except InvalidToken:
            logger.error("API Key 解密失败：密钥无效或数据损坏")
            raise EncryptionError("解密失败：数据可能已损坏或使用了错误的加密密钥")
        except Exception as e:
            logger.error(f"API Key 解密失败: {str(e)}")
            raise EncryptionError(f"解密失败: {str(e)}")
    
    async def get_user_config(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的 LLM 配置
        
        从 FalkorDB Organizations 图数据库中读取用户配置。
        自动解密敏感信息（如 API Key）。
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            Optional[Dict[str, Any]]: 用户配置字典，如果不存在则返回 None
            
        配置字典结构：
        {
            'provider': str,              # 提供商：deepseek, openai, azure
            'completion_model': str,      # 对话模型名称
            'embedding_model': str,       # 嵌入模型名称
            'api_key': str,              # API Key（已解密）
            'base_url': Optional[str],   # 自定义 API 端点
            'parameters': Dict[str, Any], # 额外参数
            'created_at': str,           # 创建时间
            'updated_at': str            # 更新时间
        }
        """
        try:
            # 导入数据库连接（延迟导入避免循环依赖）
            from api.extensions import db
            
            # 查询用户配置
            graph = db.select_graph("Organizations")
            query = """
            MATCH (u:User {email: $email})
            RETURN u.llm_config AS config
            """
            
            result = graph.query(query, {"email": user_email})
            
            if not result.result_set or not result.result_set[0][0]:
                logger.info(f"用户 {user_email} 没有自定义 LLM 配置")
                return None
            
            # 解析配置 JSON
            config_json = result.result_set[0][0]
            config = json.loads(config_json)
            
            # 解密 API Key
            if 'api_key_encrypted' in config:
                config['api_key'] = self.decrypt_api_key(config['api_key_encrypted'])
                del config['api_key_encrypted']
            
            logger.info(f"成功加载用户 {user_email} 的 LLM 配置")
            return config
            
        except EncryptionError:
            # 重新抛出加密错误
            raise
        except Exception as e:
            logger.error(f"加载用户配置失败: {str(e)}")
            return None
    
    async def save_user_config(
        self, 
        user_email: str, 
        config: Dict[str, Any],
        validate_api_key: bool = True
    ) -> bool:
        """
        保存用户的 LLM 配置
        
        将配置保存到 FalkorDB Organizations 图数据库。
        自动加密敏感信息（如 API Key）。
        
        Args:
            user_email: 用户邮箱
            config: 配置字典
            validate_api_key: 是否验证 API Key 有效性（默认 True）
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            ConfigurationError: 配置验证失败时抛出
            EncryptionError: 加密失败时抛出
        """
        try:
            # 验证配置
            self._validate_config(config)
            
            # 验证 API Key 格式
            if 'api_key' in config:
                format_valid, format_error = self.validate_api_key_format(
                    config['api_key'],
                    config['provider']
                )
                if not format_valid:
                    raise ConfigurationError(f"API Key 格式无效: {format_error}")
                
                # 可选：验证 API Key 有效性
                if validate_api_key:
                    logger.info(f"验证用户 {user_email} 的 API Key 有效性...")
                    active_valid, active_error = await self.validate_api_key_active(
                        config['api_key'],
                        config['provider'],
                        config.get('base_url')
                    )
                    if not active_valid:
                        raise ConfigurationError(
                            f"API Key 验证失败: {active_error}"
                        )
                    logger.info("API Key 验证通过")
            
            # 复制配置以避免修改原始对象
            config_to_save = config.copy()
            
            # 加密 API Key
            if 'api_key' in config_to_save:
                config_to_save['api_key_encrypted'] = self.encrypt_api_key(
                    config_to_save['api_key']
                )
                del config_to_save['api_key']
            
            # 添加时间戳
            now = datetime.utcnow().isoformat() + 'Z'
            if 'created_at' not in config_to_save:
                config_to_save['created_at'] = now
            config_to_save['updated_at'] = now
            
            # 导入数据库连接
            from api.extensions import db
            
            # 保存到数据库
            graph = db.select_graph("Organizations")
            query = """
            MATCH (u:User {email: $email})
            SET u.llm_config = $config,
                u.llm_config_updated_at = timestamp()
            RETURN u
            """
            
            result = graph.query(
                query,
                {
                    "email": user_email,
                    "config": json.dumps(config_to_save)
                }
            )
            
            if not result.result_set:
                logger.error(f"用户不存在: {user_email}")
                return False
            
            logger.info(f"用户 {user_email} 的 LLM 配置保存成功")
            return True
            
        except (ConfigurationError, EncryptionError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            logger.error(f"保存用户配置失败: {str(e)}")
            return False
    
    async def delete_user_config(self, user_email: str) -> bool:
        """
        删除用户的 LLM 配置
        
        删除后用户将使用系统默认配置。
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 导入数据库连接
            from api.extensions import db
            
            # 删除配置
            graph = db.select_graph("Organizations")
            query = """
            MATCH (u:User {email: $email})
            REMOVE u.llm_config, u.llm_config_updated_at
            RETURN u
            """
            
            result = graph.query(query, {"email": user_email})
            
            if not result.result_set:
                logger.error(f"用户不存在: {user_email}")
                return False
            
            logger.info(f"用户 {user_email} 的 LLM 配置已删除")
            return True
            
        except Exception as e:
            logger.error(f"删除用户配置失败: {str(e)}")
            return False
    
    async def test_connection(
        self, 
        provider: str, 
        api_key: str, 
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        测试 LLM 提供商连接
        
        发送一个简单的测试请求验证 API Key 和端点配置是否正确。
        
        Args:
            provider: 提供商名称（deepseek, openai, azure）
            api_key: API Key
            base_url: 可选的自定义 API 端点
            
        Returns:
            Dict[str, Any]: 测试结果字典
            {
                'success': bool,      # 测试是否成功
                'message': str,       # 结果消息
                'latency': float,     # 响应延迟（毫秒）
                'model_info': dict    # 可选的模型信息
            }
        """
        import time
        
        try:
            # 导入 LiteLLM（直接使用，因为这是测试连接）
            from litellm import completion
            
            # 构建模型名称
            if provider == 'deepseek':
                model = 'deepseek/deepseek-chat'
            elif provider == 'openai':
                model = 'openai/gpt-3.5-turbo'
            elif provider == 'azure':
                model = 'azure/gpt-35-turbo'
            else:
                return {
                    'success': False,
                    'message': f'不支持的提供商: {provider}',
                    'latency': 0
                }
            
            # 记录开始时间
            start_time = time.time()
            
            # 发送测试请求（不使用重试机制，快速失败）
            params = {
                'model': model,
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'api_key': api_key,
                'max_tokens': 10
            }
            
            if base_url:
                params['api_base'] = base_url
            
            response = completion(**params)
            
            # 计算延迟
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            
            logger.info(f"{provider} 连接测试成功，延迟: {latency:.2f}ms")
            
            return {
                'success': True,
                'message': '连接成功',
                'latency': round(latency, 2)
            }
            
        except Exception as e:
            logger.error(f"{provider} 连接测试失败: {str(e)}")
            
            # 解析错误类型
            error_message = str(e)
            if 'authentication' in error_message.lower() or '401' in error_message:
                message = 'API Key 无效，请检查配置'
            elif 'rate limit' in error_message.lower() or '429' in error_message:
                message = '请求过于频繁，请稍后再试'
            elif 'timeout' in error_message.lower():
                message = '连接超时，请检查网络或 API 端点'
            else:
                message = f'连接失败: {error_message}'
            
            return {
                'success': False,
                'message': message,
                'latency': 0
            }
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        验证配置的有效性
        
        Args:
            config: 配置字典
            
        Raises:
            ConfigurationError: 配置无效时抛出
        """
        # 验证必需字段
        required_fields = ['provider', 'completion_model', 'api_key']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"缺少必需字段: {field}")
        
        # 验证提供商
        valid_providers = ['deepseek', 'openai', 'azure']
        if config['provider'] not in valid_providers:
            raise ConfigurationError(
                f"不支持的提供商: {config['provider']}。"
                f"支持的提供商: {', '.join(valid_providers)}"
            )
        
        # 验证 API Key 格式（基本检查）
        api_key = config['api_key']
        if not api_key or len(api_key) < 10:
            raise ConfigurationError("API Key 格式无效")
        
        # DeepSeek 和 OpenAI 的 API Key 通常以 'sk-' 开头
        if config['provider'] in ['deepseek', 'openai']:
            if not api_key.startswith('sk-'):
                logger.warning(
                    f"{config['provider']} API Key 通常以 'sk-' 开头，"
                    "请确认 API Key 是否正确"
                )
        
        # 验证 Base URL 格式
        if 'base_url' in config and config['base_url']:
            base_url = config['base_url']
            if not base_url.startswith('http://') and not base_url.startswith('https://'):
                raise ConfigurationError(
                    "Base URL 必须以 http:// 或 https:// 开头"
                )
        
        logger.debug("配置验证通过")
    
    async def rotate_encryption_key(
        self,
        new_key: bytes,
        user_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        轮换加密密钥
        
        使用新密钥重新加密所有用户的配置。
        这是一个敏感操作，应该在维护窗口期间执行。
        
        Args:
            new_key: 新的加密密钥（Fernet 格式）
            user_emails: 可选的用户邮箱列表，如果为 None 则处理所有用户
            
        Returns:
            Dict[str, Any]: 轮换结果
            {
                'success': bool,
                'total': int,        # 总用户数
                'updated': int,      # 成功更新的用户数
                'failed': int,       # 失败的用户数
                'errors': List[str]  # 错误信息列表
            }
        """
        logger.info("开始密钥轮换操作")
        
        try:
            # 验证新密钥格式
            new_cipher = Fernet(new_key)
            
            # 导入数据库连接
            from api.extensions import db
            
            # 获取需要更新的用户列表
            graph = db.select_graph("Organizations")
            
            if user_emails:
                # 处理指定用户
                query = """
                MATCH (u:User)
                WHERE u.email IN $emails AND u.llm_config IS NOT NULL
                RETURN u.email AS email, u.llm_config AS config
                """
                result = graph.query(query, {"emails": user_emails})
            else:
                # 处理所有有配置的用户
                query = """
                MATCH (u:User)
                WHERE u.llm_config IS NOT NULL
                RETURN u.email AS email, u.llm_config AS config
                """
                result = graph.query(query)
            
            total = len(result.result_set)
            updated = 0
            failed = 0
            errors = []
            
            logger.info(f"找到 {total} 个用户需要更新加密密钥")
            
            # 遍历每个用户，重新加密配置
            for row in result.result_set:
                user_email = row[0]
                config_json = row[1]
                
                try:
                    # 解析配置
                    config = json.loads(config_json)
                    
                    # 使用旧密钥解密 API Key
                    if 'api_key_encrypted' in config:
                        old_api_key = self.decrypt_api_key(config['api_key_encrypted'])
                        
                        # 使用新密钥重新加密
                        encrypted_bytes = new_cipher.encrypt(old_api_key.encode('utf-8'))
                        new_encrypted = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
                        
                        # 更新配置
                        config['api_key_encrypted'] = new_encrypted
                        config['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                        
                        # 保存到数据库
                        update_query = """
                        MATCH (u:User {email: $email})
                        SET u.llm_config = $config,
                            u.llm_config_updated_at = timestamp()
                        RETURN u
                        """
                        
                        graph.query(
                            update_query,
                            {
                                "email": user_email,
                                "config": json.dumps(config)
                            }
                        )
                        
                        updated += 1
                        logger.debug(f"用户 {user_email} 的配置已使用新密钥重新加密")
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"用户 {user_email} 更新失败: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # 更新实例的加密器
            self.encryption_key = new_key
            self.cipher = new_cipher
            
            logger.info(
                f"密钥轮换完成：总计 {total}，成功 {updated}，失败 {failed}"
            )
            
            return {
                'success': failed == 0,
                'total': total,
                'updated': updated,
                'failed': failed,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"密钥轮换失败: {str(e)}")
            return {
                'success': False,
                'total': 0,
                'updated': 0,
                'failed': 0,
                'errors': [f"密钥轮换失败: {str(e)}"]
            }
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        生成新的加密密钥
        
        生成一个新的 Fernet 加密密钥，可用于配置或密钥轮换。
        
        Returns:
            str: Base64 编码的加密密钥字符串
            
        Example:
            >>> key = LLMConfigManager.generate_encryption_key()
            >>> print(f"LLM_CONFIG_ENCRYPTION_KEY={key}")
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')
    
    @staticmethod
    def validate_api_key_format(api_key: str, provider: str) -> Tuple[bool, Optional[str]]:
        """
        验证 API Key 格式
        
        根据不同的提供商验证 API Key 的格式是否正确。
        这是一个静态检查，不会实际调用 API。
        
        Args:
            api_key: API Key 字符串
            provider: 提供商名称（deepseek, openai, azure）
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
            
        Example:
            >>> valid, error = LLMConfigManager.validate_api_key_format(
            ...     "sk-abc123", "deepseek"
            ... )
            >>> if not valid:
            ...     print(f"API Key 无效: {error}")
        """
        # 基本检查
        if not api_key:
            return False, "API Key 不能为空"
        
        if not isinstance(api_key, str):
            return False, "API Key 必须是字符串"
        
        # 去除首尾空格
        api_key = api_key.strip()
        
        # 长度检查
        if len(api_key) < 10:
            return False, "API Key 长度过短，至少需要 10 个字符"
        
        if len(api_key) > 500:
            return False, "API Key 长度过长，最多 500 个字符"
        
        # 根据提供商进行特定检查
        if provider in ['deepseek', 'openai']:
            # DeepSeek 和 OpenAI 的 API Key 格式
            if not api_key.startswith('sk-'):
                return False, f"{provider} 的 API Key 必须以 'sk-' 开头"
            
            # 检查是否包含非法字符
            import re
            if not re.match(r'^sk-[A-Za-z0-9_-]+$', api_key):
                return False, "API Key 包含非法字符，只能包含字母、数字、下划线和连字符"
        
        elif provider == 'azure':
            # Azure 的 API Key 格式（32 个十六进制字符）
            import re
            if not re.match(r'^[a-fA-F0-9]{32}$', api_key):
                logger.warning(
                    "Azure API Key 通常是 32 位十六进制字符串，"
                    "当前格式可能不正确"
                )
        
        return True, None
    
    async def validate_api_key_active(
        self,
        api_key: str,
        provider: str,
        base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        验证 API Key 有效性
        
        通过实际调用 API 验证 API Key 是否有效且可用。
        这会发送一个轻量级的测试请求。
        
        Args:
            api_key: API Key 字符串
            provider: 提供商名称（deepseek, openai, azure）
            base_url: 可选的自定义 API 端点
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
            
        Example:
            >>> valid, error = await manager.validate_api_key_active(
            ...     "sk-abc123", "deepseek"
            ... )
            >>> if not valid:
            ...     print(f"API Key 无效: {error}")
        """
        # 先进行格式验证
        format_valid, format_error = self.validate_api_key_format(api_key, provider)
        if not format_valid:
            return False, format_error
        
        # 调用测试连接方法
        result = await self.test_connection(provider, api_key, base_url)
        
        if result['success']:
            return True, None
        else:
            return False, result['message']


def mask_api_key(api_key: str) -> str:
    """
    遮蔽 API Key，只显示前后几位
    
    用于在日志和用户界面中安全地显示 API Key。
    
    Args:
        api_key: 完整的 API Key
        
    Returns:
        str: 遮蔽后的 API Key（如：sk-abc...xyz）
    """
    if not api_key:
        return "***"
    
    if len(api_key) <= 10:
        return "***"
    
    return f"{api_key[:6]}...{api_key[-4:]}"
