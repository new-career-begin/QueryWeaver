#!/usr/bin/env python3
"""
运行达梦和人大金仓数据库支持的所有单元测试

任务 8：检查点 - 确保所有单元测试通过
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock 所有外部依赖
from unittest.mock import MagicMock

# Mock 数据库驱动
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.sql'] = MagicMock()
sys.modules['dmPython'] = MagicMock()

# Mock 图数据库
sys.modules['falkordb'] = MagicMock()
sys.modules['falkordb.asyncio'] = MagicMock()

# Mock Redis
sys.modules['redis'] = MagicMock()
sys.modules['redis.asyncio'] = MagicMock()

# Mock 其他依赖
sys.modules['tqdm'] = MagicMock()
sys.modules['litellm'] = MagicMock()

# 现在可以安全导入测试模块
import pytest

def main():
    """运行所有相关测试"""
    print("=" * 80)
    print("任务 8：检查点 - 运行达梦和人大金仓数据库支持的单元测试")
    print("=" * 80)
    print()
    
    # 测试文件列表
    test_files = [
        'tests/test_dm_loader.py',
        'tests/test_kingbase_loader_schema.py',
        'tests/test_sql_identifier_quoting.py',
    ]
    
    # 运行测试
    exit_code = pytest.main([
        *test_files,
        '-v',                    # 详细输出
        '--tb=short',            # 简短的错误回溯
        '--color=yes',           # 彩色输出
        '-x',                    # 遇到第一个失败就停止
        '--disable-warnings',    # 禁用警告
    ])
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上面的错误信息")
    print("=" * 80)
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
