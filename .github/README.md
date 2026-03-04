# GitHub Actions 工作流说明

本目录包含 QueryWeaver 项目的所有 GitHub Actions 持续集成工作流配置。

## 工作流列表

### 1. 数据库测试工作流 (`database-tests.yml`)

**用途**：运行所有数据库相关的测试，包括单元测试、集成测试和属性测试。

**触发条件**：
- Push 到 `main`、`staging`、`develop` 分支
- Pull Request 到 `main`、`staging` 分支

**包含的任务**：
- ✅ 单元测试（Unit Tests）
- ✅ 数据库集成测试（PostgreSQL、MySQL、Kingbase）
- ✅ 属性测试（Property-Based Tests）
- ✅ 代码质量检查（Lint）
- ✅ 测试摘要（Test Summary）

**预计执行时间**：10-15 分钟

### 2. 达梦数据库专项测试 (`dm-database-tests.yml`)

**用途**：专门测试达梦数据库加载器的功能。

**触发条件**：
- 修改达梦相关文件时触发
- 提交消息包含 `[dm-integration]` 时运行集成测试

**包含的任务**：
- ✅ 达梦加载器单元测试
- ✅ 达梦属性测试
- ⚠️ 达梦集成测试（需要自托管 runner）

**预计执行时间**：5-8 分钟

### 3. 代码覆盖率报告 (`coverage-report.yml`)

**用途**：生成详细的代码覆盖率报告并上传到 Codecov。

**触发条件**：
- Push 到 `main`、`staging` 分支
- Pull Request 到 `main`、`staging` 分支

**包含的任务**：
- ✅ 生成覆盖率报告（XML、HTML、JSON）
- ✅ 上传到 Codecov
- ✅ 覆盖率阈值检查（最低 70%）
- ✅ PR 覆盖率差异分析

**预计执行时间**：12-18 分钟

## 配置要求

### GitHub Secrets

需要在仓库设置中配置以下密钥：

| 密钥名称 | 用途 | 必需性 |
|---------|------|--------|
| `CODECOV_TOKEN` | 上传覆盖率到 Codecov | 可选 |
| `DM_TEST_URL` | 达梦数据库测试连接 | 仅集成测试 |

### 配置步骤

1. 进入仓库的 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加上述密钥

## 本地测试

在提交代码前，建议在本地运行测试：

```bash
# 启动测试数据库
docker-compose -f docker-compose.test.yml up -d

# 运行单元测试
make test-unit

# 运行覆盖率测试
pipenv run pytest tests/ -k "not e2e" --cov=api --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html

# 清理测试环境
docker-compose -f docker-compose.test.yml down
```

## 工作流状态徽章

在 README.md 中添加以下徽章显示 CI 状态：

```markdown
![Database Tests](https://github.com/YOUR_ORG/QueryWeaver/workflows/Database%20Tests/badge.svg)
![Coverage](https://codecov.io/gh/YOUR_ORG/QueryWeaver/branch/main/graph/badge.svg)
```

## 故障排查

### 测试失败

1. 查看 Actions 标签页中的详细日志
2. 检查是否是环境问题（数据库连接、依赖版本）
3. 在本地复现问题
4. 修复后重新提交

### 覆盖率下降

1. 检查 PR 中的覆盖率差异报告
2. 为新代码添加测试
3. 确保覆盖率不低于 70%

### 工作流超时

1. 检查是否有慢速测试
2. 考虑使用 `pytest-xdist` 并行执行
3. 优化测试数据库初始化

## 最佳实践

### 提交代码前

- ✅ 在本地运行测试
- ✅ 确保代码通过 lint 检查
- ✅ 添加必要的测试用例
- ✅ 更新相关文档

### Pull Request

- ✅ 等待所有 CI 检查通过
- ✅ 关注覆盖率变化
- ✅ 及时修复失败的测试
- ✅ 回应代码审查意见

### 维护工作流

- 🔄 定期更新依赖版本
- 🔄 监控测试执行时间
- 🔄 优化慢速测试
- 🔄 清理过时的工作流

## 性能优化

### 缓存策略

工作流已配置以下缓存：
- Python 依赖缓存
- npm 包缓存
- Hypothesis 数据库缓存

### 并行执行

使用矩阵策略并行测试多个数据库：
- PostgreSQL
- MySQL
- Kingbase

### 选择性测试

仅运行受影响的测试：
```bash
pytest tests/loaders/ --verbose  # 仅测试加载器
pytest tests/ -m "not slow"      # 跳过慢速测试
```

## 监控指标

### 关键指标

- 测试通过率：目标 > 95%
- 代码覆盖率：目标 > 70%
- 平均执行时间：目标 < 15 分钟
- 失败率：目标 < 5%

### 查看指标

1. GitHub Actions 标签页
2. Codecov 仪表板
3. 工作流运行历史

## 相关文档

- [CI 配置文档](../docs/CI_CONFIGURATION.md)
- [测试指南](../docs/TESTING.md)
- [贡献指南](../CONTRIBUTING.md)

## 联系方式

如有问题或建议：
- 提交 GitHub Issue
- 在 Discord 社区讨论
- 联系维护团队
