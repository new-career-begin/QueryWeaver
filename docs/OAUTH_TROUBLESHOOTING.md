# OAuth 登录故障排查指南

本文档提供微信和企业微信 OAuth 登录的常见问题和解决方案,帮助快速定位和解决登录问题。

---

## 目录

1. [配置问题](#配置问题)
2. [授权流程问题](#授权流程问题)
3. [回调问题](#回调问题)
4. [用户信息问题](#用户信息问题)
5. [网络和环境问题](#网络和环境问题)
6. [错误码速查](#错误码速查)
7. [调试技巧](#调试技巧)

---

## 配置问题

### 问题 1: 登录按钮不显示

**症状**: 前端页面没有显示微信或企业微信登录按钮

**可能原因**:
1. 环境变量未配置
2. 配置不完整
3. 前端未正确读取配置

**解决方案**:

1. 检查环境变量是否设置:

```bash
# 微信登录
echo $WECHAT_APP_ID
echo $WECHAT_APP_SECRET

# 企业微信登录
echo $WECOM_CORP_ID
echo $WECOM_AGENT_ID
echo $WECOM_CORP_SECRET
```

2. 确保 `.env` 文件包含必需配置:

```bash
# 微信
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_secret_here

# 企业微信
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=your_secret_here
```

3. 重启应用使配置生效:

```bash
# Docker
docker restart <container_id>

# 本地开发
pipenv run uvicorn api.index:app --reload
```

4. 验证配置是否生效:

```bash
curl http://localhost:5000/auth/config
```

应该返回:

```json
{
  "wechat": true,
  "wecom": true,
  ...
}
```

---

### 问题 2: 点击登录按钮返回 503 错误

**症状**: 点击登录按钮后,页面显示"微信登录功能未启用,请联系管理员配置"

**错误信息**:

```json
{
  "detail": "微信登录功能未启用,请联系管理员配置"
}
```

**可能原因**:
1. AppID 或 AppSecret 未设置
2. 环境变量名称错误
3. 配置值为空字符串

**解决方案**:

1. 检查配置是否正确:

```python
# 在 Python 中验证
import os
print(f"WECHAT_APP_ID: {os.getenv('WECHAT_APP_ID')}")
print(f"WECHAT_APP_SECRET: {os.getenv('WECHAT_APP_SECRET')}")
```

2. 确保没有多余的空格或引号:

```bash
# 错误示例
WECHAT_APP_ID=" wx123456 "  # 有空格
WECHAT_APP_ID='wx123456'    # 有引号

# 正确示例
WECHAT_APP_ID=wx123456
```

3. 检查日志中的警告信息:

```bash
# 查看应用日志
docker logs <container_id> | grep -i wechat
```

---

### 问题 3: AppID 或 AppSecret 错误

**症状**: 授权后返回"系统配置错误,请联系管理员"

**错误日志**:

```
微信 API 错误: invalid appid, errcode: 40013
```

**可能原因**:
1. AppID 输入错误
2. AppSecret 输入错误
3. 使用了测试号的凭证但未正确配置

**解决方案**:

1. 登录微信开放平台验证凭证:
   - 网址: https://open.weixin.qq.com/
   - 进入"管理中心" > "网站应用"
   - 查看 AppID 和 AppSecret

2. 重新复制粘贴凭证,避免手动输入错误

3. 企业微信用户检查:
   - 登录企业微信管理后台: https://work.weixin.qq.com/
   - 进入"应用管理" > "自建应用"
   - 查看 CorpID、AgentID 和 Secret

4. 确保使用正确的凭证类型:
   - 微信: AppID + AppSecret
   - 企业微信: CorpID + AgentID + CorpSecret

---

## 授权流程问题

### 问题 4: 重定向到微信授权页面失败

**症状**: 点击登录按钮后,浏览器显示"无法访问此网站"或"ERR_NAME_NOT_RESOLVED"

**可能原因**:
1. 网络无法访问微信服务器
2. DNS 解析失败
3. 防火墙阻止访问

**解决方案**:

1. 测试网络连接:

```bash
# 测试微信 API 连通性
curl -I https://open.weixin.qq.com/

# 测试企业微信 API 连通性
curl -I https://qyapi.weixin.qq.com/
```

2. 检查 DNS 解析:

```bash
nslookup open.weixin.qq.com
nslookup qyapi.weixin.qq.com
```

3. 如果在中国大陆以外,可能需要配置代理

4. 检查防火墙规则,确保允许访问微信域名

---

### 问题 5: 授权页面显示"redirect_uri 参数错误"

**症状**: 微信授权页面显示错误提示

**错误信息**:

```
redirect_uri 参数错误
```

**可能原因**:
1. 回调 URL 未在微信后台配置
2. 回调域名与配置不匹配
3. 协议不匹配 (HTTP vs HTTPS)

**解决方案**:

1. 登录微信开放平台,检查授权回调域:
   - 进入"管理中心" > "网站应用" > "修改"
   - 查看"授权回调域"配置
   - 确保域名与实际回调 URL 的域名一致

2. 回调域名配置规则:
   - 只需要填写域名,不包含协议和路径
   - 例如: `example.com` 或 `app.example.com`
   - 不要填写: `https://example.com/login/wechat/authorized`

3. 企业微信用户检查"可信域名":
   - 进入"应用管理" > "自建应用" > "网页授权及JS-SDK"
   - 配置"可信域名"

4. 本地开发时的特殊处理:
   - 微信不支持 `localhost` 或 `127.0.0.1`
   - 需要使用内网穿透工具 (如 ngrok, frp)
   - 或者配置本地域名映射

---

### 问题 6: 扫码后显示"网页授权失败"

**症状**: PC 端扫码后,微信显示"网页授权失败"

**可能原因**:
1. 应用未审核通过
2. 应用已被封禁
3. 用户未关注公众号 (公众号网页授权)

**解决方案**:

1. 检查应用状态:
   - 登录微信开放平台
   - 查看应用审核状态
   - 确保应用已通过审核

2. 企业微信检查应用可见范围:
   - 进入"应用管理" > "自建应用"
   - 查看"可见范围"
   - 确保用户在可见范围内

3. 检查应用是否被限制:
   - 查看是否有违规记录
   - 联系微信客服确认状态

---

## 回调问题

### 问题 7: 回调时提示"State 验证失败"

**症状**: 授权后返回应用,显示"授权失败：安全验证失败,请重试"

**错误日志**:

```
State 验证失败: stored=xxx, received=yyy
```

**可能原因**:
1. Cookie 未正确传递
2. 浏览器禁用了 Cookie
3. 跨域问题
4. 时间不同步

**解决方案**:

1. 检查浏览器 Cookie 设置:
   - 确保浏览器允许 Cookie
   - 检查是否有隐私插件阻止 Cookie

2. 检查 `APP_ENV` 配置:

```bash
# 开发环境
APP_ENV=development

# 生产环境
APP_ENV=production
```

3. 确保使用正确的协议:
   - 开发环境: HTTP 可以
   - 生产环境: 必须 HTTPS

4. 检查服务器时间:

```bash
# 查看服务器时间
date

# 如果时间不准确,同步时间
ntpdate -u pool.ntp.org
```

5. 清除浏览器 Cookie 后重试

---

### 问题 8: 回调时提示"验证令牌已过期"

**症状**: 授权后返回应用,显示"授权失败：验证令牌已过期,请重新登录"

**错误日志**:

```
State 解析失败: Signature expired
```

**可能原因**:
1. 授权流程超过 10 分钟
2. 用户在授权页面停留时间过长

**解决方案**:

1. 重新发起登录流程

2. 如果经常遇到此问题,可以调整超时时间:

```python
# api/routes/auth.py
# 将 max_age 从 600 秒 (10 分钟) 调整为更长时间
serializer.loads(state, max_age=1800)  # 30 分钟
```

3. 检查是否有网络延迟导致回调缓慢

---

### 问题 9: 回调时提示"code 无效"或"code 已使用"

**症状**: 授权后返回应用,显示"登录失败: 微信 API 错误: invalid code"

**错误码**: 40029 或 40163

**可能原因**:
1. 授权码已过期 (5 分钟有效期)
2. 授权码已被使用过
3. 重复提交回调请求

**解决方案**:

1. 重新发起登录流程,不要重复使用旧的授权码

2. 检查是否有重复请求:
   - 查看浏览器网络面板
   - 确保回调 URL 只被请求一次

3. 避免浏览器刷新回调页面

4. 检查是否有自动重试逻辑导致重复请求

---

## 用户信息问题

### 问题 10: 获取用户信息失败

**症状**: 授权成功但无法获取用户信息

**错误日志**:

```
获取用户信息失败: invalid access_token
```

**错误码**: 41001 或 42001

**可能原因**:
1. access_token 无效
2. access_token 已过期
3. OpenID 不匹配

**解决方案**:

1. 检查 access_token 获取是否成功:

```python
# 在日志中查找
logger.info(f"access_token: {access_token}")
```

2. 确保使用正确的 OpenID:

```python
# 微信返回的 token_data 应包含 openid
{
  "access_token": "xxx",
  "expires_in": 7200,
  "refresh_token": "xxx",
  "openid": "xxx",
  "scope": "snsapi_userinfo"
}
```

3. 检查 scope 是否正确:
   - 获取用户信息需要 `snsapi_userinfo`
   - 如果只用 `snsapi_base`,无法获取详细信息

4. 企业微信用户检查应用权限:
   - 确保应用有"获取成员信息"权限

---

### 问题 11: 用户没有邮箱

**症状**: 用户登录成功,但邮箱显示为虚拟邮箱

**示例**: `o6_bmjrPTlm6_2sgVt7hMZOPfL2M@wechat.queryweaver.local`

**说明**: 这是正常行为,不是错误

**原因**:
- 微信 OAuth 不一定返回用户邮箱
- 系统自动生成虚拟邮箱作为用户标识

**如果需要真实邮箱**:

1. 引导用户在个人设置中绑定邮箱

2. 或者使用其他 OAuth 提供商 (Google, GitHub) 登录

3. 企业微信用户通常有企业邮箱,会自动使用

---

### 问题 12: 用户信息显示乱码

**症状**: 用户昵称或其他信息显示为乱码

**可能原因**:
1. 字符编码问题
2. 数据库编码配置错误

**解决方案**:

1. 确保 HTTP 请求使用 UTF-8 编码:

```python
response = await client.get(url, params=params)
response.encoding = 'utf-8'
data = response.json()
```

2. 检查数据库编码:

```cypher
// FalkorDB 默认支持 UTF-8
// 确保存储时没有编码转换
```

3. 检查日志输出编码:

```python
import sys
print(sys.getdefaultencoding())  # 应该是 'utf-8'
```

---

## 网络和环境问题

### 问题 13: 生产环境 HTTPS 问题

**症状**: 生产环境回调失败,提示"不安全的连接"

**可能原因**:
1. 未使用 HTTPS
2. SSL 证书无效
3. 证书过期

**解决方案**:

1. 确保使用 HTTPS:

```bash
# 检查 APP_ENV
echo $APP_ENV  # 应该是 production 或 staging
```

2. 验证 SSL 证书:

```bash
# 测试 HTTPS 连接
curl -I https://your-domain.com/

# 检查证书有效期
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

3. 使用 Let's Encrypt 免费证书:

```bash
# 安装 certbot
apt-get install certbot

# 获取证书
certbot certonly --standalone -d your-domain.com
```

4. 配置 Nginx 或其他反向代理使用 HTTPS

---

### 问题 14: 域名备案问题 (中国大陆)

**症状**: 微信提示"域名未备案"或"非法域名"

**说明**: 在中国大陆使用微信 OAuth 必须完成 ICP 备案

**解决方案**:

1. 完成域名 ICP 备案:
   - 联系域名服务商或云服务商
   - 提交备案申请
   - 等待审核 (通常 1-2 周)

2. 备案完成后,在微信后台配置域名

3. 海外部署不需要备案,但可能影响中国用户访问速度

---

### 问题 15: Docker 容器网络问题

**症状**: Docker 容器内无法访问微信 API

**可能原因**:
1. 容器网络配置错误
2. DNS 解析失败
3. 防火墙规则

**解决方案**:

1. 测试容器内网络:

```bash
# 进入容器
docker exec -it <container_id> bash

# 测试网络连接
curl -I https://open.weixin.qq.com/
```

2. 配置 DNS:

```bash
# 在 docker-compose.yml 中配置
services:
  app:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

3. 检查防火墙规则:

```bash
# 允许容器访问外网
iptables -A FORWARD -i docker0 -o eth0 -j ACCEPT
```

---

## 错误码速查

### 微信 OAuth 错误码

| 错误码 | 错误说明 | 解决方案 |
|--------|----------|----------|
| 40001 | AppSecret 错误 | 检查 WECHAT_APP_SECRET 配置 |
| 40013 | AppID 无效 | 检查 WECHAT_APP_ID 配置 |
| 40029 | code 无效 | 重新发起授权,不要重复使用 code |
| 40163 | code 已使用 | 重新发起授权,避免重复请求 |
| 41001 | 缺少 access_token | 检查 token 获取流程 |
| 41002 | 缺少 appid | 检查请求参数 |
| 41003 | 缺少 refresh_token | 检查 token 刷新流程 |
| 41004 | 缺少 secret | 检查配置 |
| 41005 | 缺少多媒体文件数据 | 不适用于登录场景 |
| 41006 | 缺少 media_id | 不适用于登录场景 |
| 42001 | access_token 超时 | 重新获取 access_token |
| 42002 | refresh_token 超时 | 重新发起授权 |
| 42003 | code 超时 | 重新发起授权 (code 有效期 5 分钟) |
| 50001 | 用户未授权该 API | 检查应用权限配置 |

### 企业微信 OAuth 错误码

| 错误码 | 错误说明 | 解决方案 |
|--------|----------|----------|
| 40001 | CorpSecret 错误 | 检查 WECOM_CORP_SECRET 配置 |
| 40013 | CorpID 无效 | 检查 WECOM_CORP_ID 配置 |
| 40029 | code 无效 | 重新发起授权 |
| 40163 | code 已使用 | 重新发起授权 |
| 41001 | 缺少 access_token | 检查 token 获取流程 |
| 42001 | access_token 超时 | 重新获取 access_token |
| 60011 | 部门不存在 | 检查用户部门配置 |
| 60102 | UserID 不存在 | 确认用户是企业成员 |
| 60103 | 手机号码不合法 | 检查用户信息 |
| 60104 | 邮箱不合法 | 检查用户信息 |
| 60105 | 用户已禁用 | 联系管理员启用用户 |
| 81013 | UserID、手机号、邮箱全部为空 | 至少提供一个标识 |
| 82001 | 指定的成员不在权限范围 | 调整应用可见范围 |

### HTTP 状态码

| 状态码 | 说明 | 常见场景 |
|--------|------|----------|
| 302 | 重定向 | 正常的授权流程 |
| 400 | 请求错误 | 参数缺失、验证失败 |
| 401 | 未授权 | Token 无效或过期 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 路由不存在 |
| 500 | 服务器错误 | 内部错误,查看日志 |
| 503 | 服务不可用 | OAuth 未配置 |

---

## 调试技巧

### 1. 启用详细日志

在 `.env` 文件中设置日志级别:

```bash
LOG_LEVEL=DEBUG
```

重启应用后,会输出详细的调试信息。

### 2. 查看应用日志

```bash
# Docker
docker logs -f <container_id>

# 本地开发
# 日志会直接输出到终端
```

### 3. 使用浏览器开发者工具

1. 打开浏览器开发者工具 (F12)
2. 切换到"网络"(Network) 标签
3. 点击登录按钮
4. 观察请求和响应:
   - 检查重定向 URL
   - 查看 Cookie 设置
   - 检查回调参数

### 4. 测试 OAuth 流程

使用 Postman 或 curl 测试各个端点:

```bash
# 1. 检查配置
curl http://localhost:5000/auth/config

# 2. 获取授权 URL (会重定向)
curl -L http://localhost:5000/login/wechat

# 3. 模拟回调 (需要有效的 code 和 state)
curl -v -b "oauth_state=xxx" \
  "http://localhost:5000/login/wechat/authorized?code=xxx&state=xxx"
```

### 5. 检查数据库状态

```cypher
// 查询所有 Identity 节点
MATCH (i:Identity) RETURN i LIMIT 10

// 查询特定用户
MATCH (i:Identity {provider: "wechat", provider_user_id: "xxx"})
RETURN i

// 查询用户关系
MATCH (i:Identity)-[:AUTHENTICATES]->(u:User)
WHERE i.provider = "wechat"
RETURN i, u
```

### 6. 使用微信开发者工具

微信提供了开发者工具用于调试:

1. 下载微信开发者工具
2. 使用"公众号网页调试"功能
3. 输入授权 URL 进行测试

### 7. 抓包分析

使用 Wireshark 或 Charles 抓包分析:

1. 启动抓包工具
2. 过滤微信相关域名
3. 分析请求和响应内容
4. 检查是否有异常

### 8. 单元测试

运行单元测试验证功能:

```bash
# 运行所有 OAuth 测试
pytest tests/test_wechat_oauth.py -v

# 运行特定测试
pytest tests/test_wechat_oauth.py::test_wechat_login -v
```

---

## 获取帮助

如果以上方法都无法解决问题,可以通过以下渠道获取帮助:

### 1. 查看官方文档

- [微信开放平台文档](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
- [企业微信 API 文档](https://developer.work.weixin.qq.com/document/path/91022)

### 2. 提交 Issue

在 GitHub 上提交 Issue:

1. 访问项目 GitHub 页面
2. 点击"Issues" > "New Issue"
3. 提供以下信息:
   - 问题描述
   - 错误日志
   - 环境信息 (操作系统、Python 版本等)
   - 复现步骤

### 3. 社区讨论

加入 Discord 社区讨论:

- 提问前先搜索是否有类似问题
- 提供详细的问题描述和日志
- 尊重社区规则

### 4. 联系微信客服

对于微信平台相关问题:

1. 登录微信开放平台
2. 进入"客服中心"
3. 提交工单或在线咨询

---

## 预防措施

### 1. 配置检查清单

在部署前检查:

- [ ] 所有必需的环境变量已设置
- [ ] AppID/CorpID 和 Secret 正确无误
- [ ] 回调 URL 在微信后台正确配置
- [ ] 域名已完成 ICP 备案 (中国大陆)
- [ ] 生产环境使用 HTTPS
- [ ] APP_ENV 设置正确
- [ ] 防火墙规则允许访问微信 API

### 2. 监控和告警

设置监控和告警:

```python
# 监控 OAuth 登录成功率
logger.info(json.dumps({
    "event": "oauth_login",
    "provider": "wechat",
    "success": True,
    "timestamp": datetime.now().isoformat()
}))

# 监控错误率
logger.error(json.dumps({
    "event": "oauth_error",
    "provider": "wechat",
    "error_code": error_code,
    "timestamp": datetime.now().isoformat()
}))
```

### 3. 定期测试

定期测试 OAuth 流程:

- 每周手动测试一次登录流程
- 运行自动化测试
- 检查日志中的异常

### 4. 文档更新

保持文档更新:

- 记录配置变更
- 更新故障排查经验
- 分享解决方案

---

## 附录

### A. 完整的配置示例

```bash
# .env 文件示例

# 应用环境
APP_ENV=production

# 密钥
FASTAPI_SECRET_KEY=your_super_secret_key_here_at_least_32_characters_long

# 微信 OAuth
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=1234567890abcdef1234567890abcdef

# 企业微信 OAuth
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=1234567890abcdef1234567890abcdef1234567890abcdef

# 可选: 自定义回调 URL
# WECHAT_REDIRECT_URI=https://your-domain.com/login/wechat/authorized
# WECOM_REDIRECT_URI=https://your-domain.com/login/wecom/authorized

# 日志级别
LOG_LEVEL=INFO
```

### B. 测试账号申请

微信测试号申请:

1. 访问: https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
2. 使用微信扫码登录
3. 获取测试号的 appID 和 appsecret
4. 配置接口配置信息

注意: 测试号功能有限,正式使用需要申请正式账号。

### C. 常用命令

```bash
# 查看环境变量
env | grep WECHAT
env | grep WECOM

# 测试网络连接
curl -I https://open.weixin.qq.com/
curl -I https://qyapi.weixin.qq.com/

# 查看应用日志
docker logs -f <container_id> | grep -i oauth

# 重启应用
docker restart <container_id>

# 清除浏览器 Cookie
# Chrome: F12 > Application > Cookies > 右键 > Clear

# 运行测试
pytest tests/test_wechat_oauth.py -v
```

---

**最后更新**: 2025-01-02

**版本**: 1.0.0

如有问题或建议,欢迎提交 Issue 或 Pull Request。
