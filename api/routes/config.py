"""
LLM 配置管理 API 路由

提供用户 LLM 配置的 CRUD 操作和连接测试功能。
支持 DeepSeek、OpenAI、Azure 等多种模型提供商。
"""

from typing import Optional, Dict, Any
import logging

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.auth.user_management import token_required
from api.config_manager import LLMConfigManager, ConfigurationError, EncryptionError, mask_api_key

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/config", tags=["config"])

# 初始化配置管理器
config_manager = LLMConfigManager()


# ---- 数据模型 ----

class LLMConfigRequest(BaseModel):
    """
    LLM 配置请求模型
    
    用于保存用户的 LLM 配置，支持多种模型提供商。
    """
    
    provider: str = Field(
        ...,
        description="模型提供商：deepseek（推荐，高性价比）, openai, azure",
        example="deepseek"
    )
    completion_model: str = Field(
        ...,
        description="对话模型名称，用于 Text2SQL 生成",
        example="deepseek-chat"
    )
    embedding_model: str = Field(
        ...,
        description="嵌入模型名称，用于向量化表和列描述",
        example="text-embedding-ada-002"
    )
    api_key: str = Field(
        ...,
        description="API Key，将被加密存储",
        example="sk-xxxxxxxxxxxxx"
    )
    base_url: Optional[str] = Field(
        None,
        description="自定义 API 端点（可选）",
        example="https://api.deepseek.com"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="额外参数（temperature, max_tokens 等）",
        example={
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "deepseek",
                "completion_model": "deepseek-chat",
                "embedding_model": "text-embedding-ada-002",
                "api_key": "sk-xxxxxxxxxxxxx",
                "base_url": "https://api.deepseek.com",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }


class LLMConfigResponse(BaseModel):
    """LLM 配置响应模型"""
    
    provider: str = Field(..., description="模型提供商")
    completion_model: str = Field(..., description="对话模型名称")
    embedding_model: str = Field(..., description="嵌入模型名称")
    api_key: str = Field(..., description="遮蔽后的 API Key")
    base_url: Optional[str] = Field(None, description="API 端点")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "deepseek",
                "completion_model": "deepseek-chat",
                "embedding_model": "text-embedding-ada-002",
                "api_key": "sk-abc...xyz",
                "base_url": "https://api.deepseek.com",
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }


class TestConnectionRequest(BaseModel):
    """
    测试连接请求模型
    
    用于验证 LLM 提供商的 API Key 和端点配置是否正确。
    """
    
    provider: str = Field(
        ...,
        description="模型提供商：deepseek, openai, azure",
        example="deepseek"
    )
    api_key: str = Field(
        ...,
        description="API Key",
        example="sk-xxxxxxxxxxxxx"
    )
    base_url: Optional[str] = Field(
        None,
        description="自定义 API 端点（可选）",
        example="https://api.deepseek.com"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "deepseek",
                "api_key": "sk-xxxxxxxxxxxxx",
                "base_url": "https://api.deepseek.com"
            }
        }


class TestConnectionResponse(BaseModel):
    """测试连接响应模型"""
    
    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    latency: Optional[float] = Field(None, description="响应延迟（毫秒）")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "连接成功",
                "latency": 234.5
            }
        }


# ---- API 路由 ----

@router.get(
    "/llm",
    summary="获取 LLM 配置",
    description="""
    获取当前用户的 LLM 配置。
    
    **功能说明**：
    - 返回用户通过 Web 界面保存的自定义配置
    - 如果用户没有自定义配置，返回 null 并提示使用默认配置
    - API Key 会被遮蔽，只显示前后几位（如：sk-abc...xyz）
    
    **配置优先级**：
    1. 用户配置（最高优先级）- 通过此 API 保存的配置
    2. 环境变量 - 系统管理员配置的默认值
    3. 系统默认值（最低优先级）
    
    **使用场景**：
    - 在设置页面显示当前配置
    - 验证用户是否已配置 LLM
    - 获取配置用于编辑
    
    **认证要求**：需要有效的用户认证 Token
    """,
    responses={
        200: {
            "description": "成功获取配置",
            "content": {
                "application/json": {
                    "examples": {
                        "with_config": {
                            "summary": "用户已配置",
                            "value": {
                                "success": True,
                                "config": {
                                    "provider": "deepseek",
                                    "completion_model": "deepseek-chat",
                                    "embedding_model": "text-embedding-ada-002",
                                    "api_key": "sk-abc...xyz",
                                    "base_url": "https://api.deepseek.com",
                                    "parameters": {
                                        "temperature": 0.7,
                                        "max_tokens": 2000
                                    }
                                }
                            }
                        },
                        "no_config": {
                            "summary": "用户未配置",
                            "value": {
                                "success": True,
                                "config": None,
                                "message": "使用默认配置"
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "未认证或 Token 无效"},
        500: {"description": "服务器内部错误"}
    }
)
@token_required
async def get_llm_config(request: Request) -> JSONResponse:
    """
    获取当前用户的 LLM 配置
    
    需要用户认证。返回用户自定义配置或提示使用默认配置。
    API Key 会被遮蔽，只显示前后几位。
    
    Args:
        request: FastAPI 请求对象（包含用户信息）
        
    Returns:
        JSONResponse: 包含配置信息的响应
        
    Raises:
        HTTPException: 当获取配置失败时抛出 500 错误
    """
    try:
        user_email = request.state.user_email
        logger.info(f"用户 {user_email} 请求获取 LLM 配置")
        
        # 获取用户配置
        config = await config_manager.get_user_config(user_email)
        
        if config:
            # 遮蔽 API Key
            if 'api_key' in config:
                config['api_key'] = mask_api_key(config['api_key'])
            
            logger.info(f"成功返回用户 {user_email} 的 LLM 配置")
            return JSONResponse({
                "success": True,
                "config": config
            })
        else:
            logger.info(f"用户 {user_email} 没有自定义配置，使用默认配置")
            return JSONResponse({
                "success": True,
                "config": None,
                "message": "使用默认配置"
            })
            
    except Exception as e:
        logger.error(f"获取用户配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败，请稍后重试"
        )


@router.post(
    "/llm",
    summary="保存 LLM 配置",
    description="""
    保存用户的 LLM 配置到数据库。
    
    **功能说明**：
    - 验证配置的有效性（提供商、模型名称等）
    - 加密存储 API Key
    - 保存到 FalkorDB 的用户节点
    - 配置立即生效，无需重启服务
    
    **支持的提供商**：
    - **deepseek**：高性价比的国产 LLM，推荐使用
    - **openai**：OpenAI 官方 API
    - **azure**：Azure OpenAI 服务
    
    **配置示例**：
    
    DeepSeek 配置：
    ```json
    {
      "provider": "deepseek",
      "completion_model": "deepseek-chat",
      "embedding_model": "text-embedding-ada-002",
      "api_key": "sk-xxxxxxxxxxxxx",
      "base_url": "https://api.deepseek.com",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    }
    ```
    
    **使用场景**：
    - 首次登录时配置 LLM
    - 在设置页面修改配置
    - 切换不同的模型提供商
    
    **认证要求**：需要有效的用户认证 Token
    """,
    responses={
        200: {
            "description": "配置保存成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "配置保存成功"
                    }
                }
            }
        },
        400: {
            "description": "配置无效",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_provider": {
                            "summary": "不支持的提供商",
                            "value": {
                                "detail": "不支持的模型提供商。支持的提供商: deepseek, openai, azure"
                            }
                        },
                        "invalid_config": {
                            "summary": "配置验证失败",
                            "value": {
                                "detail": "API Key 格式无效"
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "未认证或 Token 无效"},
        500: {"description": "服务器内部错误"}
    }
)
@token_required
async def save_llm_config(
    request: Request,
    config_req: LLMConfigRequest
) -> JSONResponse:
    """
    保存用户的 LLM 配置
    
    需要用户认证。验证配置有效性后保存到数据库。
    API Key 会被加密存储。
    
    Args:
        request: FastAPI 请求对象（包含用户信息）
        config_req: 配置请求对象
        
    Returns:
        JSONResponse: 保存结果
        
    Raises:
        HTTPException: 当配置无效或保存失败时抛出错误
    """
    try:
        user_email = request.state.user_email
        logger.info(f"用户 {user_email} 请求保存 LLM 配置")
        
        # 验证提供商
        valid_providers = ['deepseek', 'openai', 'azure']
        if config_req.provider not in valid_providers:
            logger.warning(
                f"用户 {user_email} 尝试使用不支持的提供商: {config_req.provider}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的模型提供商。支持的提供商: {', '.join(valid_providers)}"
            )
        
        # 转换为字典
        config_data = config_req.dict()
        
        # 保存配置
        success = await config_manager.save_user_config(user_email, config_data)
        
        if success:
            logger.info(f"用户 {user_email} 的 LLM 配置保存成功")
            return JSONResponse({
                "success": True,
                "message": "配置保存成功"
            })
        else:
            logger.error(f"用户 {user_email} 的 LLM 配置保存失败")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置保存失败，请稍后重试"
            )
            
    except ConfigurationError as e:
        # 配置验证错误
        logger.warning(f"配置验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EncryptionError as e:
        # 加密错误
        logger.error(f"配置加密失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置加密失败，请联系管理员"
        )
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"保存配置时发生未预期错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置保存失败"
        )


@router.delete(
    "/llm",
    summary="删除 LLM 配置",
    description="""
    删除用户的 LLM 配置，恢复使用系统默认配置。
    
    **功能说明**：
    - 从数据库中删除用户的自定义配置
    - 删除后用户将使用环境变量或系统默认配置
    - 不影响其他用户的配置
    
    **使用场景**：
    - 用户想要恢复使用系统默认配置
    - 清除错误的配置
    - 切换回环境变量配置
    
    **认证要求**：需要有效的用户认证 Token
    """,
    responses={
        200: {
            "description": "配置删除成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "配置已删除，恢复使用默认配置"
                    }
                }
            }
        },
        401: {"description": "未认证或 Token 无效"},
        500: {"description": "服务器内部错误"}
    }
)
@token_required
async def delete_llm_config(request: Request) -> JSONResponse:
    """
    删除用户的 LLM 配置
    
    需要用户认证。删除后用户将恢复使用系统默认配置。
    
    Args:
        request: FastAPI 请求对象（包含用户信息）
        
    Returns:
        JSONResponse: 删除结果
        
    Raises:
        HTTPException: 当删除失败时抛出 500 错误
    """
    try:
        user_email = request.state.user_email
        logger.info(f"用户 {user_email} 请求删除 LLM 配置")
        
        # 删除配置
        success = await config_manager.delete_user_config(user_email)
        
        if success:
            logger.info(f"用户 {user_email} 的 LLM 配置已删除")
            return JSONResponse({
                "success": True,
                "message": "配置已删除，恢复使用默认配置"
            })
        else:
            logger.error(f"用户 {user_email} 的 LLM 配置删除失败")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置删除失败，请稍后重试"
            )
            
    except Exception as e:
        logger.error(f"删除配置时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置删除失败"
        )


@router.post(
    "/llm/test",
    summary="测试 LLM 连接",
    description="""
    测试 LLM 提供商的连接和 API Key 有效性。
    
    **功能说明**：
    - 发送测试请求到指定的 LLM 提供商
    - 验证 API Key 是否有效
    - 测量响应延迟
    - 不会保存配置，仅用于验证
    
    **测试内容**：
    - API Key 认证
    - 网络连接
    - API 端点可用性
    - 响应时间
    
    **使用场景**：
    - 保存配置前验证 API Key
    - 排查连接问题
    - 测试不同的 API 端点
    
    **测试示例**：
    
    测试 DeepSeek：
    ```json
    {
      "provider": "deepseek",
      "api_key": "sk-xxxxxxxxxxxxx",
      "base_url": "https://api.deepseek.com"
    }
    ```
    
    测试 OpenAI：
    ```json
    {
      "provider": "openai",
      "api_key": "sk-xxxxxxxxxxxxx"
    }
    ```
    
    **认证要求**：需要有效的用户认证 Token
    """,
    responses={
        200: {
            "description": "测试完成（成功或失败）",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "连接成功",
                            "value": {
                                "success": True,
                                "message": "连接成功",
                                "latency": 234.5
                            }
                        },
                        "auth_failed": {
                            "summary": "认证失败",
                            "value": {
                                "success": False,
                                "message": "API Key 无效或已过期",
                                "latency": None
                            }
                        },
                        "timeout": {
                            "summary": "连接超时",
                            "value": {
                                "success": False,
                                "message": "连接超时，请检查网络或 API 端点",
                                "latency": None
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求参数无效",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "不支持的模型提供商。支持的提供商: deepseek, openai, azure"
                    }
                }
            }
        },
        401: {"description": "未认证或 Token 无效"},
        500: {"description": "服务器内部错误"}
    }
)
@token_required
async def test_llm_connection(
    request: Request,
    test_req: TestConnectionRequest
) -> JSONResponse:
    """
    测试 LLM 提供商连接
    
    需要用户认证。发送测试请求验证 API Key 和端点配置是否正确。
    不会保存配置，仅用于验证。
    
    Args:
        request: FastAPI 请求对象（包含用户信息）
        test_req: 测试请求对象
        
    Returns:
        JSONResponse: 测试结果
        
    Raises:
        HTTPException: 当测试请求失败时抛出错误
    """
    try:
        user_email = request.state.user_email
        logger.info(
            f"用户 {user_email} 请求测试 {test_req.provider} 连接"
        )
        
        # 验证提供商
        valid_providers = ['deepseek', 'openai', 'azure']
        if test_req.provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的模型提供商。支持的提供商: {', '.join(valid_providers)}"
            )
        
        # 测试连接
        result = await config_manager.test_connection(
            provider=test_req.provider,
            api_key=test_req.api_key,
            base_url=test_req.base_url
        )
        
        if result['success']:
            logger.info(
                f"用户 {user_email} 的 {test_req.provider} 连接测试成功，"
                f"延迟: {result['latency']}ms"
            )
        else:
            logger.warning(
                f"用户 {user_email} 的 {test_req.provider} 连接测试失败: "
                f"{result['message']}"
            )
        
        return JSONResponse(result)
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"连接测试时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="连接测试失败"
        )
