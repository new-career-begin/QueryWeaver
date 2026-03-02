# 设计文档：DeepSeek 大模型支持

## 概述

本设计文档描述了为 QueryWeaver 项目添加 DeepSeek 大语言模型支持的技术实现方案。DeepSeek 是一个国产高性价比的大语言模型服务提供商，提供与 OpenAI 兼容的 API 接口。通过集成 DeepSeek，QueryWeaver 将为用户提供更多的模型选择，降低使用成本，并支持国产化部署需求。

### 设计目标

1. **无缝集成**：通过 LiteLLM 统一接口集成 DeepSeek，保持代码一致性
2. **用户友好**：提供可视化配置界面，降低配置门槛
3. **安全可靠**：加密存储敏感信息，提供完善的错误处理
4. **高性能**：优化 API 调用，支持批量请求和缓存
5. **可扩展**：设计灵活的配置架构，便于未来添加更多模型提供商

### 技术选型

- **LiteLLM**：统一的多模型接口库，已支持 DeepSeek
- **FalkorDB**：存储用户配置信息（Organizations 图）
- **FastAPI**：后端 API 框架
- **React + TypeScript**：前端配置界面
- **cryptography**：Python 加密库，用于敏感信息加密

### DeepSeek API 概述

DeepSeek 提供与 OpenAI 兼容的 API 接口：

- **API 端点**：https://api.deepseek.com
- **认证方式**：Bearer Token（API Key）
- **对话模型**：deepseek-chat、deepseek-coder
- **嵌入模型**：deepseek-embedding（暂未公开，使用第三方）
- **定价**：比 OpenAI 便宜约 90%

## 架构

### 系统架构图

```
用户界面层
    ↓
┌─────────────────────────────────────────┐
│  React 前端                              │
│  ├─ AI 配置页面 (AIConfigModal)         │
│  ├─ 设置菜单 (Settings)                 │
│  └─ 模型选择器 (ModelSelector)          │
└─────────────────────────────────────────┘
    ↓ HTTP/REST API
┌─────────────────────────────────────────┐
│  FastAPI 后端                            │
│  ├─ 配置管理路由 (/api/config)          │
│  ├─ 用户认证中间件                       │
│  └─ 配置加密/解密服务                    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  LLM 配置管理层                          │
│  ├─ Config 类扩展                        │
│  ├─ 用户配置加载器                       │
│  └─ 模型提供商选择器                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  LiteLLM 统一接口                        │
│  ├─ completion() - 对话生成              │
│  ├─ embedding() - 向量嵌入               │
│  └─ batch_completion() - 批量请求        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  模型提供商                              │
│  ├─ DeepSeek API                         │
│  ├─ OpenAI API                           │
│  └─ Azure OpenAI API                     │
└─────────────────────────────────────────┘

存储层：
┌─────────────────────────────────────────┐
│  FalkorDB Organizations 图               │
│  ├─ User 节点 (llm_config 属性)         │
│  ├─ Identity 节点                        │
│  └─ Token 节点                           │
└─────────────────────────────────────────┘
```

### 配置优先级

系统按以下优先级加载 LLM 配置：

1. **用户配置**（最高优先级）：存储在 FalkorDB User 节点的 llm_config 属性
2. **环境变量**：.env 文件或系统环境变量
3. **系统默认值**（最低优先级）：api/config.py 中的默认配置


## 组件和接口

### 1. 后端组件

#### 1.1 配置管理服务 (api/config_manager.py)

新增配置管理模块，负责用户 LLM 配置的 CRUD 操作。

```python
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import json
import os

class LLMConfigManager:
    """
    LLM 配置管理器
    
    负责用户 LLM 配置的加载、保存、加密和解密
    """
    
    def __init__(self):
        """初始化配置管理器，加载加密密钥"""
        self.encryption_key = self._load_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    async def get_user_config(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的 LLM 配置
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            用户配置字典，如果不存在则返回 None
        """
        pass
    
    async def save_user_config(
        self, 
        user_email: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        保存用户的 LLM 配置
        
        Args:
            user_email: 用户邮箱
            config: 配置字典
            
        Returns:
            保存是否成功
        """
        pass
    
    async def delete_user_config(self, user_email: str) -> bool:
        """
        删除用户的 LLM 配置
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            删除是否成功
        """
        pass
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        加密 API Key
        
        Args:
            api_key: 明文 API Key
            
        Returns:
            加密后的 API Key（Base64 编码）
        """
        pass
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        解密 API Key
        
        Args:
            encrypted_key: 加密的 API Key
            
        Returns:
            明文 API Key
        """
        pass
    
    async def test_connection(
        self, 
        provider: str, 
        api_key: str, 
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        测试 LLM 提供商连接
        
        Args:
            provider: 提供商名称（deepseek, openai, azure）
            api_key: API Key
            base_url: 可选的自定义 API 端点
            
        Returns:
            测试结果字典 {success: bool, message: str, latency: float}
        """
        pass
```


#### 1.2 Config 类扩展 (api/config.py)

扩展现有的 Config 类，支持动态加载用户配置。

```python
@dataclasses.dataclass
class Config:
    """
    配置类（扩展版）
    
    支持从多个来源加载配置：用户配置 > 环境变量 > 默认值
    """
    
    # 默认配置（保持向后兼容）
    AZURE_FLAG = True
    if not os.getenv("OPENAI_API_KEY"):
        EMBEDDING_MODEL_NAME = "azure/text-embedding-ada-002"
        COMPLETION_MODEL = "azure/gpt-4.1"
    else:
        AZURE_FLAG = False
        EMBEDDING_MODEL_NAME = "openai/text-embedding-ada-002"
        COMPLETION_MODEL = "openai/gpt-4.1"
    
    # DeepSeek 默认配置
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_COMPLETION_MODEL = "deepseek/deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL = "openai/text-embedding-ada-002"  # 暂用 OpenAI
    
    @classmethod
    def load_user_config(cls, user_email: str) -> 'UserConfig':
        """
        加载用户特定的配置
        
        Args:
            user_email: 用户邮箱
            
        Returns:
            UserConfig 实例
        """
        pass
    
    @classmethod
    def get_completion_model(cls, user_email: Optional[str] = None) -> str:
        """
        获取对话模型名称
        
        Args:
            user_email: 可选的用户邮箱，用于加载用户配置
            
        Returns:
            模型名称（格式：provider/model-name）
        """
        pass
    
    @classmethod
    def get_embedding_model(cls, user_email: Optional[str] = None) -> EmbeddingsModel:
        """
        获取嵌入模型实例
        
        Args:
            user_email: 可选的用户邮箱
            
        Returns:
            EmbeddingsModel 实例
        """
        pass


class UserConfig:
    """
    用户特定的 LLM 配置
    
    从 FalkorDB 加载并缓存用户配置
    """
    
    def __init__(self, user_email: str, config_data: Dict[str, Any]):
        """
        初始化用户配置
        
        Args:
            user_email: 用户邮箱
            config_data: 配置数据字典
        """
        self.user_email = user_email
        self.provider = config_data.get('provider', 'azure')
        self.completion_model = config_data.get('completion_model')
        self.embedding_model = config_data.get('embedding_model')
        self.api_key = config_data.get('api_key')  # 已解密
        self.base_url = config_data.get('base_url')
        self.parameters = config_data.get('parameters', {})
    
    def get_completion_model_name(self) -> str:
        """获取完整的对话模型名称"""
        return f"{self.provider}/{self.completion_model}"
    
    def get_embedding_model_instance(self) -> EmbeddingsModel:
        """获取嵌入模型实例"""
        model_name = f"{self.provider}/{self.embedding_model}"
        return EmbeddingsModel(model_name=model_name)
    
    def to_litellm_params(self) -> Dict[str, Any]:
        """
        转换为 LiteLLM 调用参数
        
        Returns:
            LiteLLM 参数字典
        """
        params = {
            'model': self.get_completion_model_name(),
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        if self.base_url:
            params['api_base'] = self.base_url
        
        # 添加用户自定义参数
        params.update(self.parameters)
        
        return params
```


#### 1.3 配置 API 路由 (api/routes/config.py)

新增 REST API 端点，用于前端配置管理。

```python
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from api.auth.user_management import token_required
from api.config_manager import LLMConfigManager

router = APIRouter(prefix="/api/config", tags=["config"])
config_manager = LLMConfigManager()


class LLMConfigRequest(BaseModel):
    """LLM 配置请求模型"""
    provider: str = Field(..., description="模型提供商：deepseek, openai, azure")
    completion_model: str = Field(..., description="对话模型名称")
    embedding_model: str = Field(..., description="嵌入模型名称")
    api_key: str = Field(..., description="API Key")
    base_url: Optional[str] = Field(None, description="自定义 API 端点")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="额外参数（temperature, max_tokens 等）"
    )


class TestConnectionRequest(BaseModel):
    """测试连接请求模型"""
    provider: str
    api_key: str
    base_url: Optional[str] = None


@router.get("/llm")
@token_required
async def get_llm_config(request: Request):
    """
    获取当前用户的 LLM 配置
    
    Returns:
        用户配置或默认配置
    """
    user_email = request.state.user_email
    config = await config_manager.get_user_config(user_email)
    
    if config:
        # 不返回完整的 API Key，只返回前后几位
        config['api_key'] = mask_api_key(config['api_key'])
        return {"success": True, "config": config}
    else:
        return {"success": True, "config": None, "message": "使用默认配置"}


@router.post("/llm")
@token_required
async def save_llm_config(request: Request, config_req: LLMConfigRequest):
    """
    保存用户的 LLM 配置
    
    Args:
        config_req: 配置请求对象
        
    Returns:
        保存结果
    """
    user_email = request.state.user_email
    
    # 验证配置
    if config_req.provider not in ['deepseek', 'openai', 'azure']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的模型提供商"
        )
    
    # 保存配置
    config_data = config_req.dict()
    success = await config_manager.save_user_config(user_email, config_data)
    
    if success:
        return {"success": True, "message": "配置保存成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置保存失败"
        )


@router.delete("/llm")
@token_required
async def delete_llm_config(request: Request):
    """
    删除用户的 LLM 配置，恢复使用默认配置
    
    Returns:
        删除结果
    """
    user_email = request.state.user_email
    success = await config_manager.delete_user_config(user_email)
    
    if success:
        return {"success": True, "message": "配置已删除，恢复使用默认配置"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置删除失败"
        )


@router.post("/llm/test")
@token_required
async def test_llm_connection(request: Request, test_req: TestConnectionRequest):
    """
    测试 LLM 提供商连接
    
    Args:
        test_req: 测试请求对象
        
    Returns:
        测试结果
    """
    result = await config_manager.test_connection(
        provider=test_req.provider,
        api_key=test_req.api_key,
        base_url=test_req.base_url
    )
    
    return result


def mask_api_key(api_key: str) -> str:
    """
    遮蔽 API Key，只显示前后几位
    
    Args:
        api_key: 完整的 API Key
        
    Returns:
        遮蔽后的 API Key（如：sk-abc...xyz）
    """
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:6]}...{api_key[-4:]}"
```


### 2. 前端组件

#### 2.1 AI 配置模态框 (app/src/components/AIConfigModal.tsx)

用户登录后显示的配置界面。

```typescript
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AIConfigModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (config: LLMConfig) => Promise<void>;
  allowSkip?: boolean;
}

interface LLMConfig {
  provider: 'deepseek' | 'openai' | 'azure';
  completion_model: string;
  embedding_model: string;
  api_key: string;
  base_url?: string;
  parameters?: Record<string, any>;
}

export const AIConfigModal: React.FC<AIConfigModalProps> = ({
  open,
  onClose,
  onSave,
  allowSkip = true
}) => {
  const [config, setConfig] = useState<LLMConfig>({
    provider: 'deepseek',
    completion_model: 'deepseek-chat',
    embedding_model: 'text-embedding-ada-002',
    api_key: '',
    base_url: 'https://api.deepseek.com',
  });
  
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null);
  const [saving, setSaving] = useState(false);
  
  // 模型选项配置
  const modelOptions = {
    deepseek: {
      completion: ['deepseek-chat', 'deepseek-coder'],
      embedding: ['text-embedding-ada-002'],  // 暂用 OpenAI
      baseUrl: 'https://api.deepseek.com'
    },
    openai: {
      completion: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
      embedding: ['text-embedding-ada-002', 'text-embedding-3-small'],
      baseUrl: 'https://api.openai.com/v1'
    },
    azure: {
      completion: ['gpt-4', 'gpt-35-turbo'],
      embedding: ['text-embedding-ada-002'],
      baseUrl: ''  // 需要用户提供
    }
  };
  
  // 当提供商改变时，更新默认值
  useEffect(() => {
    const options = modelOptions[config.provider];
    setConfig(prev => ({
      ...prev,
      completion_model: options.completion[0],
      embedding_model: options.embedding[0],
      base_url: options.baseUrl
    }));
  }, [config.provider]);
  
  // 测试连接
  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    
    try {
      const response = await fetch('/api/config/llm/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: config.provider,
          api_key: config.api_key,
          base_url: config.base_url
        })
      });
      
      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: '连接测试失败：' + error.message
      });
    } finally {
      setTesting(false);
    }
  };
  
  // 保存配置
  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(config);
      onClose();
    } catch (error) {
      setTestResult({
        success: false,
        message: '保存失败：' + error.message
      });
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>配置 AI 模型</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* 提供商选择 */}
          <div>
            <Label>模型提供商</Label>
            <Select
              value={config.provider}
              onValueChange={(value) => setConfig({...config, provider: value as any})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="deepseek">DeepSeek（推荐，高性价比）</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="azure">Azure OpenAI</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* API Key */}
          <div>
            <Label>API Key</Label>
            <Input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({...config, api_key: e.target.value})}
              placeholder="输入您的 API Key"
            />
          </div>
          
          {/* API 端点 */}
          <div>
            <Label>API 端点</Label>
            <Input
              value={config.base_url}
              onChange={(e) => setConfig({...config, base_url: e.target.value})}
              placeholder="API 基础 URL"
            />
          </div>
          
          {/* 对话模型 */}
          <div>
            <Label>对话模型</Label>
            <Select
              value={config.completion_model}
              onValueChange={(value) => setConfig({...config, completion_model: value})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {modelOptions[config.provider].completion.map(model => (
                  <SelectItem key={model} value={model}>{model}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* 嵌入模型 */}
          <div>
            <Label>嵌入模型</Label>
            <Select
              value={config.embedding_model}
              onValueChange={(value) => setConfig({...config, embedding_model: value})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {modelOptions[config.provider].embedding.map(model => (
                  <SelectItem key={model} value={model}>{model}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* 测试结果 */}
          {testResult && (
            <Alert variant={testResult.success ? 'default' : 'destructive'}>
              <AlertDescription>{testResult.message}</AlertDescription>
            </Alert>
          )}
          
          {/* 操作按钮 */}
          <div className="flex justify-between pt-4">
            <div>
              {allowSkip && (
                <Button variant="ghost" onClick={onClose}>
                  跳过配置
                </Button>
              )}
            </div>
            <div className="space-x-2">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={!config.api_key || testing}
              >
                {testing ? '测试中...' : '测试连接'}
              </Button>
              <Button
                onClick={handleSave}
                disabled={!config.api_key || saving}
              >
                {saving ? '保存中...' : '保存配置'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
```


#### 2.2 设置页面集成

在现有的设置页面中添加 AI 配置入口。

```typescript
// app/src/pages/Settings.tsx

import { AIConfigModal } from '@/components/AIConfigModal';

export const Settings: React.FC = () => {
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<LLMConfig | null>(null);
  
  // 加载当前配置
  useEffect(() => {
    loadCurrentConfig();
  }, []);
  
  const loadCurrentConfig = async () => {
    const response = await fetch('/api/config/llm');
    const data = await response.json();
    if (data.success && data.config) {
      setCurrentConfig(data.config);
    }
  };
  
  const handleSaveConfig = async (config: LLMConfig) => {
    await fetch('/api/config/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    await loadCurrentConfig();
  };
  
  return (
    <div className="settings-page">
      {/* 其他设置项 */}
      
      <div className="setting-section">
        <h3>AI 模型配置</h3>
        <p className="text-sm text-gray-600">
          配置用于 Text2SQL 的 AI 模型提供商和参数
        </p>
        
        {currentConfig ? (
          <div className="current-config">
            <p>当前提供商：{currentConfig.provider}</p>
            <p>对话模型：{currentConfig.completion_model}</p>
            <Button onClick={() => setShowAIConfig(true)}>
              修改配置
            </Button>
          </div>
        ) : (
          <Button onClick={() => setShowAIConfig(true)}>
            配置 AI 模型
          </Button>
        )}
      </div>
      
      <AIConfigModal
        open={showAIConfig}
        onClose={() => setShowAIConfig(false)}
        onSave={handleSaveConfig}
        allowSkip={false}
      />
    </div>
  );
};
```

#### 2.3 登录后配置引导

在用户首次登录时显示配置引导。

```typescript
// app/src/hooks/useFirstLoginGuide.ts

import { useEffect, useState } from 'react';

export const useFirstLoginGuide = () => {
  const [showConfigGuide, setShowConfigGuide] = useState(false);
  
  useEffect(() => {
    checkFirstLogin();
  }, []);
  
  const checkFirstLogin = async () => {
    // 检查用户是否已配置 LLM
    const response = await fetch('/api/config/llm');
    const data = await response.json();
    
    // 如果没有配置，显示引导
    if (data.success && !data.config) {
      setShowConfigGuide(true);
    }
  };
  
  return { showConfigGuide, setShowConfigGuide };
};

// 在主应用中使用
// app/src/App.tsx

export const App: React.FC = () => {
  const { showConfigGuide, setShowConfigGuide } = useFirstLoginGuide();
  
  return (
    <>
      {/* 应用主体 */}
      
      <AIConfigModal
        open={showConfigGuide}
        onClose={() => setShowConfigGuide(false)}
        onSave={handleSaveConfig}
        allowSkip={true}
      />
    </>
  );
};
```


## 数据模型

### 1. 用户配置数据模型

#### FalkorDB 图数据库模型

```cypher
// User 节点扩展
(:User {
    email: string,                    // 用户邮箱（主键）
    first_name: string,               // 名
    last_name: string,                // 姓
    created_at: timestamp,            // 创建时间
    llm_config: string                // LLM 配置（JSON 字符串，加密）
})

// llm_config JSON 结构
{
    "provider": "deepseek",           // 提供商：deepseek, openai, azure
    "completion_model": "deepseek-chat",  // 对话模型
    "embedding_model": "text-embedding-ada-002",  // 嵌入模型
    "api_key_encrypted": "...",       // 加密的 API Key
    "base_url": "https://api.deepseek.com",  // API 端点
    "parameters": {                   // 额外参数
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    "created_at": "2025-01-15T10:00:00Z",  // 配置创建时间
    "updated_at": "2025-01-15T10:00:00Z"   // 配置更新时间
}
```

### 2. API 请求/响应模型

#### 保存配置请求

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

#### 获取配置响应

```json
{
    "success": true,
    "config": {
        "provider": "deepseek",
        "completion_model": "deepseek-chat",
        "embedding_model": "text-embedding-ada-002",
        "api_key": "sk-abc...xyz",  // 遮蔽后的 API Key
        "base_url": "https://api.deepseek.com",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
}
```

#### 测试连接请求

```json
{
    "provider": "deepseek",
    "api_key": "sk-xxxxxxxxxxxxx",
    "base_url": "https://api.deepseek.com"
}
```

#### 测试连接响应

```json
{
    "success": true,
    "message": "连接成功",
    "latency": 234.5,  // 毫秒
    "model_info": {
        "available_models": ["deepseek-chat", "deepseek-coder"]
    }
}
```

### 3. LiteLLM 调用参数

#### Completion 调用

```python
from litellm import completion

# DeepSeek 调用示例
response = completion(
    model="deepseek/deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    api_key="sk-xxxxxxxxxxxxx",
    api_base="https://api.deepseek.com",
    temperature=0.7,
    max_tokens=2000
)
```

#### Embedding 调用

```python
from litellm import embedding

# 嵌入生成示例
response = embedding(
    model="openai/text-embedding-ada-002",  # DeepSeek 暂无嵌入模型
    input=["表描述文本1", "表描述文本2"],
    api_key="sk-xxxxxxxxxxxxx"
)
```

### 4. 环境变量配置

```bash
# .env 文件示例

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_COMPLETION_MODEL=deepseek-chat
DEEPSEEK_EMBEDDING_MODEL=text-embedding-ada-002

# 加密密钥（用于加密存储的 API Key）
LLM_CONFIG_ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# 默认模型提供商（可选）
DEFAULT_LLM_PROVIDER=deepseek
```

### 5. 配置优先级示例

```python
# 配置加载逻辑示例

def get_completion_model(user_email: Optional[str] = None) -> str:
    """
    按优先级获取对话模型
    
    优先级：用户配置 > 环境变量 > 默认值
    """
    # 1. 尝试加载用户配置（最高优先级）
    if user_email:
        user_config = load_user_config(user_email)
        if user_config and user_config.completion_model:
            return f"{user_config.provider}/{user_config.completion_model}"
    
    # 2. 尝试从环境变量加载
    if os.getenv("DEEPSEEK_API_KEY"):
        model = os.getenv("DEEPSEEK_COMPLETION_MODEL", "deepseek-chat")
        return f"deepseek/{model}"
    
    if os.getenv("OPENAI_API_KEY"):
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        return f"openai/{model}"
    
    # 3. 使用默认值（最低优先级）
    if os.getenv("AZURE_API_KEY"):
        return "azure/gpt-4.1"
    
    raise ValueError("未配置任何 LLM 提供商")
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1：环境变量配置加载

*对于任意*有效的环境变量配置组合，系统启动时应该正确读取并解析 DeepSeek 配置参数

**验证：需求 1.1**

### 属性 2：提供商识别

*对于任意*设置了 DEEPSEEK_API_KEY 的环境，系统应该将 DeepSeek 识别为可用的模型提供商

**验证：需求 1.2**

### 属性 3：自定义端点配置

*对于任意*有效的 DEEPSEEK_BASE_URL 环境变量，系统应该使用该 URL 作为 API 端点而不是默认值

**验证：需求 1.3**

### 属性 4：无效配置处理

*对于任意*无效或空的 API Key，系统应该记录警告日志并禁用 DeepSeek 提供商

**验证：需求 1.6**

### 属性 5：配置持久化往返

*对于任意*有效的用户配置，保存到 FalkorDB 后再读取应该得到等价的配置对象

**验证：需求 2.9, 2.10**

### 属性 6：API Key 加密往返

*对于任意*API Key 字符串，加密后存储再解密应该得到原始值

**验证：需求 2.14**

### 属性 7：LiteLLM 统一接口调用

*对于任意*有效的 completion 请求，系统应该通过 LiteLLM 接口调用 DeepSeek API

**验证：需求 3.1**

### 属性 8：流式响应支持

*对于任意*启用流式模式的请求，系统应该能够处理和返回流式响应

**验证：需求 3.4**

### 属性 9：指数退避重试

*对于任意*速率限制错误，系统应该使用指数退避策略进行重试，每次重试延迟应该是前一次的倍数

**验证：需求 4.2**

### 属性 10：Token 使用量记录

*对于任意*DeepSeek API 调用，日志中应该包含请求和响应的 token 使用量统计

**验证：需求 5.1**

### 属性 11：Token 限额控制

*对于任意*达到 token 限额的用户，新的 API 请求应该被拒绝并返回限额错误

**验证：需求 5.5**

### 属性 12：嵌入向量生成

*对于任意*表或列描述文本，系统应该使用配置的嵌入模型生成向量表示

**验证：需求 7.1**

### 属性 13：向量维度一致性

*对于任意*生成的嵌入向量，其维度应该等于 FalkorDB 向量索引配置的维度

**验证：需求 7.3**

### 属性 14：结构化日志完整性

*对于任意*DeepSeek API 调用，日志应该包含模型名称、请求参数、响应时间和 token 使用量等必需字段

**验证：需求 8.1**

### 属性 15：日志安全性

*对于任意*日志条目，不应该包含完整的 API Key（应该被遮蔽或省略）

**验证：需求 8.7, 11.2**

### 属性 16：响应时间性能

*对于任意*SQL 生成请求，95% 的请求应该在 5 秒内返回结果

**验证：需求 12.1**

### 属性 17：批量嵌入优化

*对于任意*包含多个文本的嵌入请求，系统应该使用批量 API 而不是多次单独调用

**验证：需求 12.2**


## 错误处理

### 错误类型和处理策略

#### 1. 配置错误

**错误场景**：
- API Key 缺失或格式无效
- Base URL 格式错误
- 模型名称不存在
- 配置参数类型错误

**处理策略**：
```python
class ConfigurationError(Exception):
    """配置错误异常"""
    pass

def validate_deepseek_config(config: Dict[str, Any]) -> None:
    """
    验证 DeepSeek 配置
    
    Args:
        config: 配置字典
        
    Raises:
        ConfigurationError: 配置无效时抛出
    """
    if not config.get('api_key'):
        logger.warning("DeepSeek API Key 未配置，禁用 DeepSeek 提供商")
        raise ConfigurationError("API Key 不能为空")
    
    if not config['api_key'].startswith('sk-'):
        logger.error(f"DeepSeek API Key 格式无效")
        raise ConfigurationError("API Key 格式无效")
    
    if config.get('base_url') and not config['base_url'].startswith('http'):
        logger.error(f"Base URL 格式无效: {config['base_url']}")
        raise ConfigurationError("Base URL 必须以 http:// 或 https:// 开头")
```

**用户消息**："配置无效，请检查 API Key 和端点设置"

#### 2. API 调用错误

**错误场景**：
- 认证失败（401）
- 速率限制（429）
- 服务不可用（503）
- 请求超时
- 网络错误

**处理策略**：
```python
import asyncio
from typing import Callable, Any

async def call_with_retry(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    带重试的 API 调用
    
    Args:
        func: 要调用的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff_factor: 退避因子
        
    Returns:
        函数执行结果
        
    Raises:
        最后一次尝试的异常
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except RateLimitError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"速率限制，{delay}秒后重试 (尝试 {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error("达到最大重试次数，放弃请求")
        except ServiceUnavailableError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"服务不可用，{delay}秒后重试 (尝试 {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error("服务持续不可用，放弃请求")
        except AuthenticationError as e:
            # 认证错误不重试
            logger.error(f"DeepSeek API 认证失败: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"API 调用失败: {str(e)}")
            raise
    
    raise last_exception
```

**用户消息**：
- 认证失败："API Key 无效，请检查配置"
- 速率限制："请求过于频繁，请稍后再试"
- 服务不可用："DeepSeek 服务暂时不可用，请稍后再试"

#### 3. 数据库错误

**错误场景**：
- FalkorDB 连接失败
- 配置保存失败
- 配置读取失败
- 加密/解密失败

**处理策略**：
```python
async def save_user_config_safe(
    user_email: str, 
    config: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    安全地保存用户配置
    
    Args:
        user_email: 用户邮箱
        config: 配置字典
        
    Returns:
        (成功标志, 错误消息)
    """
    try:
        # 加密敏感信息
        encrypted_config = encrypt_config(config)
        
        # 保存到数据库
        graph = db.select_graph("Organizations")
        query = """
        MATCH (u:User {email: $email})
        SET u.llm_config = $config,
            u.llm_config_updated_at = timestamp()
        RETURN u
        """
        result = await graph.query(
            query,
            {"email": user_email, "config": json.dumps(encrypted_config)}
        )
        
        if not result.result_set:
            logger.error(f"用户不存在: {user_email}")
            return False, "用户不存在"
        
        logger.info(f"用户配置保存成功: {user_email}")
        return True, None
        
    except EncryptionError as e:
        logger.error(f"配置加密失败: {str(e)}")
        return False, "配置加密失败"
    except ConnectionError as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False, "数据库连接失败，请稍后重试"
    except Exception as e:
        logger.exception(f"配置保存失败: {str(e)}")
        return False, "配置保存失败"
```

**用户消息**："配置保存失败，请稍后重试"

#### 4. 加密错误

**错误场景**：
- 加密密钥缺失
- 加密密钥格式错误
- 加密/解密失败

**处理策略**：
```python
from cryptography.fernet import Fernet, InvalidToken

class EncryptionError(Exception):
    """加密错误异常"""
    pass

def _load_encryption_key(self) -> bytes:
    """
    加载加密密钥
    
    Returns:
        加密密钥（bytes）
        
    Raises:
        EncryptionError: 密钥加载失败时抛出
    """
    key = os.getenv('LLM_CONFIG_ENCRYPTION_KEY')
    
    if not key:
        logger.error("加密密钥未配置")
        raise EncryptionError("LLM_CONFIG_ENCRYPTION_KEY 环境变量未设置")
    
    try:
        return base64.urlsafe_b64decode(key)
    except Exception as e:
        logger.error(f"加密密钥格式无效: {str(e)}")
        raise EncryptionError("加密密钥格式无效")

def encrypt_api_key(self, api_key: str) -> str:
    """加密 API Key"""
    try:
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"API Key 加密失败: {str(e)}")
        raise EncryptionError("加密失败")

def decrypt_api_key(self, encrypted_key: str) -> str:
    """解密 API Key"""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_key)
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    except InvalidToken:
        logger.error("API Key 解密失败：密钥无效或数据损坏")
        raise EncryptionError("解密失败：数据可能已损坏")
    except Exception as e:
        logger.error(f"API Key 解密失败: {str(e)}")
        raise EncryptionError("解密失败")
```

**用户消息**："配置加密失败，请联系管理员"

### 错误日志格式

所有错误日志使用统一的 JSON 格式：

```json
{
    "event": "deepseek_api_error",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "level": "ERROR",
    "user_email": "user@example.com",
    "provider": "deepseek",
    "error_type": "RateLimitError",
    "error_message": "Rate limit exceeded",
    "retry_attempt": 2,
    "max_retries": 3,
    "context": {
        "model": "deepseek-chat",
        "request_id": "req_123456"
    }
}
```


## 测试策略

### 双重测试方法

本功能采用单元测试和属性测试相结合的方式，确保全面的测试覆盖：

- **单元测试**：验证具体示例、边缘情况和错误条件
- **属性测试**：验证跨所有输入的通用属性
- 两者互补，共同保证代码质量

### 单元测试

#### 测试框架
- **pytest**：Python 测试框架
- **pytest-asyncio**：异步测试支持
- **unittest.mock**：模拟对象
- **pytest-cov**：代码覆盖率

#### 测试用例

##### 1. 配置管理测试

```python
import pytest
from api.config_manager import LLMConfigManager

@pytest.mark.asyncio
async def test_save_and_load_config():
    """测试配置保存和加载"""
    manager = LLMConfigManager()
    
    config = {
        'provider': 'deepseek',
        'completion_model': 'deepseek-chat',
        'api_key': 'sk-test123456'
    }
    
    # 保存配置
    success = await manager.save_user_config('test@example.com', config)
    assert success
    
    # 加载配置
    loaded_config = await manager.get_user_config('test@example.com')
    assert loaded_config['provider'] == 'deepseek'
    assert loaded_config['completion_model'] == 'deepseek-chat'

@pytest.mark.asyncio
async def test_api_key_encryption():
    """测试 API Key 加密和解密"""
    manager = LLMConfigManager()
    
    original_key = 'sk-test123456789'
    
    # 加密
    encrypted = manager.encrypt_api_key(original_key)
    assert encrypted != original_key
    
    # 解密
    decrypted = manager.decrypt_api_key(encrypted)
    assert decrypted == original_key

def test_invalid_api_key_format():
    """测试无效的 API Key 格式"""
    from api.config_manager import validate_deepseek_config, ConfigurationError
    
    config = {'api_key': 'invalid-key'}
    
    with pytest.raises(ConfigurationError):
        validate_deepseek_config(config)
```

##### 2. API 调用测试

```python
from unittest.mock import patch, MagicMock
import pytest

@pytest.mark.asyncio
@patch('litellm.completion')
async def test_deepseek_completion_call(mock_completion):
    """测试 DeepSeek completion 调用"""
    # 模拟 LiteLLM 响应
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message={'content': 'SELECT * FROM users'})]
    )
    
    from api.config import Config
    
    response = completion(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "查询所有用户"}],
        api_key="sk-test123"
    )
    
    assert response.choices[0].message['content'] == 'SELECT * FROM users'
    mock_completion.assert_called_once()

@pytest.mark.asyncio
async def test_retry_on_rate_limit():
    """测试速率限制重试"""
    from api.config_manager import call_with_retry, RateLimitError
    
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    result = await call_with_retry(failing_func, max_retries=3)
    
    assert result == "success"
    assert call_count == 3
```

##### 3. 前端组件测试

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AIConfigModal } from '@/components/AIConfigModal';

describe('AIConfigModal', () => {
  it('应该显示配置表单', () => {
    render(
      <AIConfigModal 
        open={true} 
        onClose={() => {}} 
        onSave={async () => {}} 
      />
    );
    
    expect(screen.getByText('配置 AI 模型')).toBeInTheDocument();
    expect(screen.getByLabelText('模型提供商')).toBeInTheDocument();
    expect(screen.getByLabelText('API Key')).toBeInTheDocument();
  });
  
  it('应该在选择 DeepSeek 时更新默认值', async () => {
    render(
      <AIConfigModal 
        open={true} 
        onClose={() => {}} 
        onSave={async () => {}} 
      />
    );
    
    const providerSelect = screen.getByLabelText('模型提供商');
    fireEvent.change(providerSelect, { target: { value: 'deepseek' } });
    
    await waitFor(() => {
      const baseUrlInput = screen.getByLabelText('API 端点') as HTMLInputElement;
      expect(baseUrlInput.value).toBe('https://api.deepseek.com');
    });
  });
  
  it('应该在测试连接成功时显示成功消息', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ success: true, message: '连接成功' })
      })
    ) as jest.Mock;
    
    render(
      <AIConfigModal 
        open={true} 
        onClose={() => {}} 
        onSave={async () => {}} 
      />
    );
    
    const testButton = screen.getByText('测试连接');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText('连接成功')).toBeInTheDocument();
    });
  });
});
```

### 属性测试

使用 Hypothesis 进行属性测试，验证通用属性。

#### 配置最小 100 次迭代

```python
# pytest.ini 或 pyproject.toml
[tool.pytest.ini_options]
hypothesis_profile = "default"

[tool.hypothesis]
max_examples = 100
```

#### 属性测试用例

```python
from hypothesis import given, strategies as st
import pytest

@given(st.text(min_size=10, max_size=100))
def test_api_key_encryption_roundtrip(api_key):
    """
    属性测试：API Key 加密往返
    
    Feature: deepseek-llm-support, Property 6: API Key 加密往返
    
    属性：对于任意 API Key 字符串，加密后再解密应该得到原始值
    """
    manager = LLMConfigManager()
    
    encrypted = manager.encrypt_api_key(api_key)
    decrypted = manager.decrypt_api_key(encrypted)
    
    assert decrypted == api_key
    assert encrypted != api_key  # 确保已加密

@given(
    st.dictionaries(
        keys=st.sampled_from(['provider', 'completion_model', 'api_key']),
        values=st.text(min_size=1, max_size=50)
    )
)
@pytest.mark.asyncio
async def test_config_persistence_roundtrip(config):
    """
    属性测试：配置持久化往返
    
    Feature: deepseek-llm-support, Property 5: 配置持久化往返
    
    属性：对于任意有效的配置，保存后再读取应该得到等价的配置
    """
    manager = LLMConfigManager()
    user_email = "test@example.com"
    
    # 保存配置
    await manager.save_user_config(user_email, config)
    
    # 读取配置
    loaded_config = await manager.get_user_config(user_email)
    
    # 验证关键字段相等
    for key in config:
        assert loaded_config.get(key) == config[key]

@given(st.lists(st.text(min_size=1, max_size=100), min_size=2, max_size=10))
def test_batch_embedding_optimization(texts):
    """
    属性测试：批量嵌入优化
    
    Feature: deepseek-llm-support, Property 17: 批量嵌入优化
    
    属性：对于任意包含多个文本的嵌入请求，应该使用批量 API
    """
    from unittest.mock import patch, call
    
    with patch('litellm.embedding') as mock_embedding:
        mock_embedding.return_value = MagicMock(
            data=[{'embedding': [0.1] * 1536} for _ in texts]
        )
        
        # 调用嵌入函数
        embeddings = Config.EMBEDDING_MODEL.embed(texts)
        
        # 验证只调用了一次（批量）
        assert mock_embedding.call_count == 1
        
        # 验证传入的是列表
        call_args = mock_embedding.call_args
        assert isinstance(call_args[1]['input'], list)
        assert len(call_args[1]['input']) == len(texts)

@given(st.integers(min_value=1, max_value=1000))
def test_vector_dimension_consistency(dimension):
    """
    属性测试：向量维度一致性
    
    Feature: deepseek-llm-support, Property 13: 向量维度一致性
    
    属性：对于任意生成的嵌入向量，其维度应该等于配置的维度
    """
    from unittest.mock import patch
    
    with patch('litellm.embedding') as mock_embedding:
        mock_embedding.return_value = MagicMock(
            data=[{'embedding': [0.1] * dimension}]
        )
        
        embeddings = Config.EMBEDDING_MODEL.embed(["test text"])
        
        assert len(embeddings[0]) == dimension
```

### 集成测试

#### 端到端测试流程

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_deepseek_end_to_end():
    """
    DeepSeek 端到端集成测试
    
    测试流程：
    1. 配置 DeepSeek
    2. 保存用户配置
    3. 生成 SQL 查询
    4. 生成向量嵌入
    5. 验证日志记录
    """
    # 1. 配置
    config = {
        'provider': 'deepseek',
        'completion_model': 'deepseek-chat',
        'embedding_model': 'text-embedding-ada-002',
        'api_key': os.getenv('DEEPSEEK_API_KEY_TEST'),
        'base_url': 'https://api.deepseek.com'
    }
    
    manager = LLMConfigManager()
    user_email = "integration_test@example.com"
    
    # 2. 保存配置
    success = await manager.save_user_config(user_email, config)
    assert success
    
    # 3. 生成 SQL
    user_config = Config.load_user_config(user_email)
    response = completion(
        model=user_config.get_completion_model_name(),
        messages=[
            {"role": "user", "content": "查询所有用户"}
        ],
        **user_config.to_litellm_params()
    )
    
    assert response.choices[0].message['content']
    
    # 4. 生成嵌入
    embeddings = user_config.get_embedding_model_instance().embed(
        ["users table", "orders table"]
    )
    
    assert len(embeddings) == 2
    assert all(isinstance(emb, list) for emb in embeddings)
    
    # 5. 验证日志（检查日志文件或日志捕获）
    # 这里简化处理，实际应该检查日志内容
```

### 测试覆盖率目标

- **代码覆盖率**：≥ 80%
- **分支覆盖率**：≥ 70%
- **核心功能覆盖率**：100%（配置管理、加密、API 调用）

### 持续集成

```yaml
# .github/workflows/test.yml
name: DeepSeek Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv install --dev
      
      - name: Run unit tests
        run: pipenv run pytest tests/ -m "not integration"
      
      - name: Run property tests
        run: pipenv run pytest tests/ -m property --hypothesis-show-statistics
      
      - name: Run integration tests
        env:
          DEEPSEEK_API_KEY_TEST: ${{ secrets.DEEPSEEK_API_KEY_TEST }}
        run: pipenv run pytest tests/ -m integration
      
      - name: Generate coverage report
        run: pipenv run pytest --cov=api --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

