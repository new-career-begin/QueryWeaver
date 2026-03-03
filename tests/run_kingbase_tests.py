#!/usr/bin/env python3
"""运行人大金仓加载器测试的独立脚本"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock 所有外部依赖
from unittest.mock import MagicMock
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.sql'] = MagicMock()
sys.modules['falkordb'] = MagicMock()
sys.modules['falkordb.asyncio'] = MagicMock()
sys.modules['tqdm'] = MagicMock()

# 现在可以安全导入测试模块
import pytest

if __name__ == '__main__':
    # 运行测试
    exit_code = pytest.main([
        'tests/test_kingbase_loader_schema.py',
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    sys.exit(exit_code)
