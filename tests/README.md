# 测试配置指南

## 环境配置

### 1. FalkorDB 连接配置

测试会自动从项目根目录的 `.env` 文件中读取 FalkorDB 连接配置。

#### 配置方式

在项目根目录的 `.env` 文件中配置：

```bash
# FalkorDB 连接地址（必需）
FALKORDB_URL=redis://192.168.31.202:36379/0
```

#### 配置说明

- `FALKORDB_URL`: FalkorDB 的完整连接 URL
  - 格式：`redis://host:port/db`
  - 示例：`redis://192.168.31.202:36379/0`
  - 默认值：`redis://localhost:6379/0`

### 2. 安装依赖

在运行测试前，请确保已安装所有依赖：

```bash
# 安装项目依赖（包括 python-dotenv）
pipenv install

# 安装开发依赖
pipenv install --dev
```

### 3. 运行测试

#### 运行所有测试

```bash
pipenv run pytest
```

#### 运行特定测试文件

```bash
# 运行单元测试
pipenv run pytest tests/test_config.py

# 运行属性测试
pipenv run pytest tests/test_vector_dimension_consistency_pbt.py

# 运行 E2E 测试
pipenv run pytest tests/e2e/
```

#### 运行特定测试用例

```bash
pipenv run pytest tests/test_config.py::test_deepseek_config_from_env
```

### 4. 测试环境变量优先级

测试环境变量的加载优先级如下：

1. `.env` 文件中的配置（最高优先级）
2. `conftest.py` 中的默认值（仅在 `.env` 未配置时使用）
3. 系统环境变量

### 5. 常见问题

#### Q: 测试连接不到 FalkorDB？

**A:** 请检查以下几点：

1. 确认 `.env` 文件中的 `FALKORDB_URL` 配置正确
2. 确认 FalkorDB 服务正在运行
3. 确认网络连接正常（如果是远程地址）
4. 确认端口没有被防火墙阻止

```bash
# 测试连接
redis-cli -h 192.168.31.202 -p 36379 ping
```

#### Q: 测试仍然使用 localhost:6379？

**A:** 请确保：

1. 已安装 `python-dotenv` 依赖：
   ```bash
   pipenv install python-dotenv
   ```

2. `.env` 文件在项目根目录
3. 重新运行测试

#### Q: 如何临时覆盖配置？

**A:** 可以通过环境变量临时覆盖：

```bash
# Windows CMD
set FALKORDB_URL=redis://other-host:6379/0 && pipenv run pytest

# Windows PowerShell
$env:FALKORDB_URL="redis://other-host:6379/0"; pipenv run pytest

# Linux/Mac
FALKORDB_URL=redis://other-host:6379/0 pipenv run pytest
```

### 6. 测试数据隔离

为了避免测试数据污染生产环境，建议：

1. 使用独立的 FalkorDB 实例进行测试
2. 使用不同的数据库编号（例如：`/1` 而不是 `/0`）
3. 测试后清理测试数据

### 7. CI/CD 配置

在 CI/CD 环境中，可以通过环境变量配置：

```yaml
# GitHub Actions 示例
env:
  FALKORDB_URL: redis://test-falkordb:6379/0
  FASTAPI_SECRET_KEY: test-secret-key
```

## 测试类型

### 单元测试

测试单个函数或类的功能，使用 Mock 隔离外部依赖。

```bash
pipenv run pytest tests/test_config.py -v
```

### 属性测试（PBT）

使用 Hypothesis 进行基于属性的测试，验证代码在各种输入下的正确性。

```bash
pipenv run pytest tests/test_*_pbt.py -v
```

### 集成测试

测试多个组件的集成，需要真实的 FalkorDB 连接。

```bash
pipenv run pytest tests/test_token_management.py -v
```

### E2E 测试

使用 Playwright 进行端到端测试，测试完整的用户流程。

```bash
pipenv run pytest tests/e2e/ -v
```

## 测试覆盖率

查看测试覆盖率报告：

```bash
# 生成覆盖率报告
pipenv run pytest --cov=api --cov-report=html

# 查看报告
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## 调试测试

### 使用 pytest 调试

```bash
# 显示详细输出
pipenv run pytest -v -s

# 在第一个失败处停止
pipenv run pytest -x

# 显示局部变量
pipenv run pytest -l

# 进入 pdb 调试器
pipenv run pytest --pdb
```

### 查看日志

```bash
# 显示日志输出
pipenv run pytest --log-cli-level=DEBUG
```

## 相关文档

- [Pytest 文档](https://docs.pytest.org/)
- [Hypothesis 文档](https://hypothesis.readthedocs.io/)
- [Playwright 文档](https://playwright.dev/python/)
- [FalkorDB 文档](https://docs.falkordb.com/)
