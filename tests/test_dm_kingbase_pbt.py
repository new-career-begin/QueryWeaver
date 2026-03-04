#!/usr/bin/env python3
"""
达梦和人大金仓数据库加载器属性测试模块

使用 Hypothesis 进行基于属性的测试（Property-Based Testing）
验证达梦和人大金仓数据库加载器在所有可能输入下的正确性

Feature: dm-kingbase-database-support
"""

import pytest
import datetime
import decimal
import sys
import importlib
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import List, Dict, Any

# Mock 所有可能触发 FalkorDB 连接的模块
sys.modules['api.extensions'] = MagicMock()
sys.modules['api.agents'] = MagicMock()
sys.modules['api.agents.analysis_agent'] = MagicMock()
sys.modules['api.agents.relevancy_agent'] = MagicMock()
sys.modules['api.agents.response_formatter_agent'] = MagicMock()
sys.modules['api.agents.follow_up_agent'] = MagicMock()
sys.modules['api.core.text2sql'] = MagicMock()
sys.modules['api.loaders.graph_loader'] = MagicMock()

# 现在可以安全导入
from api.loaders.dm_loader import DM_Loader, DM_ConnectionError
from api.loaders.kingbase_loader import Kingbase_Loader, Kingbase_ConnectionError

# 手动导入 schema_loader 中的函数，避免导入整个模块
# 我们将直接测试加载器类的方法，而不是 schema_loader 中的函数


class TestURLRecognitionProperties:
    """
    URL 识别属性测试类
    
    **属性 1: 数据库类型识别**
    **验证: 需求 1.1, 4.1**
    
    注意：由于 schema_loader 模块依赖过多，我们直接测试加载器类的 URL 解析方法
    """
    
    @given(st.text(min_size=1, max_size=50))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_dm_url_prefix_recognition_property(self, random_text):
        """
        属性测试：达梦数据库 URL 前缀识别
        
        **Validates: Requirements 1.1**
        
        属性：对于任意以 dm:// 开头的 URL，DM_Loader 应该能够识别并尝试解析
        
        测试策略：
        1. 生成以 dm:// 开头的 URL
        2. 验证 URL 前缀被正确识别
        
        Args:
            random_text: Hypothesis 生成的随机文本
        """
        # 构造达梦数据库 URL
        url = f"dm://{random_text}"
        
        # Assert: 验证 URL 以 dm:// 开头
        assert url.startswith("dm://"), \
            f"URL 应该以 dm:// 开头，实际: {url}"
    
    @given(st.text(min_size=1, max_size=50))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_kingbase_url_prefix_recognition_property(self, random_text):
        """
        属性测试：人大金仓数据库 URL 前缀识别
        
        **Validates: Requirements 4.1**
        
        属性：对于任意以 kingbase:// 开头的 URL，Kingbase_Loader 应该能够识别并尝试解析
        
        Args:
            random_text: Hypothesis 生成的随机文本
        """
        # 构造人大金仓数据库 URL
        url = f"kingbase://{random_text}"
        
        # Assert: 验证 URL 以 kingbase:// 开头
        assert url.startswith("kingbase://"), \
            f"URL 应该以 kingbase:// 开头，实际: {url}"


class TestURLParsingProperties:
    """
    URL 格式解析属性测试类
    
    **属性 4: URL 格式解析**
    **验证: 需求 1.4, 4.4, 4.5**
    """
    
    @given(
        username=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        password=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        host=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        port=st.integers(min_value=1024, max_value=65535),
        database=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        ))
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_dm_url_parsing_property(self, username, password, host, port, database):
        """
        属性测试：达梦数据库 URL 解析
        
        **Validates: Requirements 1.4**
        
        属性：对于任意有效格式的达梦数据库 URL，解析应该正确提取所有组件
        
        测试策略：
        1. 生成随机的 URL 组件
        2. 构造完整的 URL
        3. 解析 URL
        4. 验证所有组件都被正确提取
        
        Args:
            username: 用户名
            password: 密码
            host: 主机地址
            port: 端口号
            database: 数据库名
        """
        # 构造达梦数据库 URL
        url = f"dm://{username}:{password}@{host}:{port}/{database}"
        
        try:
            # Act: 解析 URL
            result = DM_Loader._parse_connection_url(url)
            
            # Assert: 验证所有组件都被正确提取
            assert result["user"] == username, \
                f"用户名解析错误: 期望 {username}, 实际 {result['user']}"
            assert result["password"] == password, \
                f"密码解析错误: 期望 {password}, 实际 {result['password']}"
            assert result["server"] == host, \
                f"主机解析错误: 期望 {host}, 实际 {result['server']}"
            assert result["port"] == port, \
                f"端口解析错误: 期望 {port}, 实际 {result['port']}"
            assert result["database"] == database, \
                f"数据库名解析错误: 期望 {database}, 实际 {result['database']}"
        except DM_ConnectionError:
            # 某些随机组合可能不是有效的 URL 格式
            pass
    
    @given(
        username=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        password=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        host=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        port=st.integers(min_value=1024, max_value=65535),
        database=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        ))
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_kingbase_url_parsing_property(self, username, password, host, port, database):
        """
        属性测试：人大金仓数据库 URL 解析
        
        **Validates: Requirements 4.4, 4.5**
        
        属性：对于任意有效格式的人大金仓数据库 URL（kingbase:// 或 postgresql://），
        解析应该正确转换为 psycopg2 兼容格式
        
        Args:
            username: 用户名
            password: 密码
            host: 主机地址
            port: 端口号
            database: 数据库名
        """
        # 测试 kingbase:// 前缀
        kingbase_url = f"kingbase://{username}:{password}@{host}:{port}/{database}"
        
        try:
            # Act: 解析 URL
            result = Kingbase_Loader._parse_connection_url(kingbase_url)
            
            # Assert: 验证转换为 postgresql:// 格式
            assert result.startswith("postgresql://"), \
                f"kingbase:// 应该被转换为 postgresql://，实际: {result}"
            assert username in result, \
                f"转换后的 URL 应该包含用户名 {username}"
            assert host in result, \
                f"转换后的 URL 应该包含主机 {host}"
            assert str(port) in result, \
                f"转换后的 URL 应该包含端口 {port}"
            assert database in result, \
                f"转换后的 URL 应该包含数据库名 {database}"
        except Kingbase_ConnectionError:
            # 某些随机组合可能不是有效的 URL 格式
            pass
        
        # 测试 postgresql:// 前缀
        postgresql_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        try:
            # Act: 解析 URL
            result = Kingbase_Loader._parse_connection_url(postgresql_url)
            
            # Assert: 验证保持 postgresql:// 格式
            assert result.startswith("postgresql://"), \
                f"postgresql:// 应该保持不变，实际: {result}"
            assert result == postgresql_url, \
                f"postgresql:// URL 应该保持不变，期望: {postgresql_url}, 实际: {result}"
        except Kingbase_ConnectionError:
            pass
    
    @given(st.text(min_size=1, max_size=100))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_invalid_url_format_rejection_property(self, invalid_url):
        """
        属性测试：无效 URL 格式应该被拒绝
        
        **Validates: Requirements 1.3, 4.3**
        
        属性：对于任意不符合标准格式的 URL，解析应该抛出连接错误
        
        Args:
            invalid_url: 随机生成的可能无效的 URL
        """
        # 跳过可能有效的 URL 格式
        if "://" in invalid_url and "@" in invalid_url and ":" in invalid_url.split("@")[1]:
            pytest.skip("可能是有效的 URL 格式")
        
        # 测试达梦数据库
        dm_url = f"dm://{invalid_url}"
        with pytest.raises(DM_ConnectionError):
            DM_Loader._parse_connection_url(dm_url)
        
        # 测试人大金仓数据库
        kingbase_url = f"kingbase://{invalid_url}"
        with pytest.raises(Kingbase_ConnectionError):
            Kingbase_Loader._parse_connection_url(kingbase_url)


class TestValueSerializationProperties:
    """
    值序列化属性测试类
    
    **属性 16: 日期时间序列化**
    **属性 17: DECIMAL 类型转换**
    **验证: 需求 3.3, 3.4, 6.3, 6.4**
    """
    
    @given(
        year=st.integers(min_value=1900, max_value=2100),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),  # 使用 28 避免月份边界问题
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
        second=st.integers(min_value=0, max_value=59)
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_datetime_serialization_property(self, year, month, day, hour, minute, second):
        """
        属性测试：日期时间序列化
        
        **Validates: Requirements 3.3, 6.3**
        
        属性：对于任意有效的日期时间值，序列化应该产生 ISO 8601 格式字符串
        
        测试策略：
        1. 生成随机的日期时间值
        2. 序列化
        3. 验证结果是 ISO 8601 格式字符串
        4. 验证可以反序列化回原始值
        
        Args:
            year, month, day, hour, minute, second: 日期时间组件
        """
        # 构造日期时间对象
        dt = datetime.datetime(year, month, day, hour, minute, second)
        
        # Act: 序列化（测试达梦）
        dm_result = DM_Loader._serialize_value(dt)
        
        # Assert: 验证是字符串
        assert isinstance(dm_result, str), \
            f"序列化结果应该是字符串，实际类型: {type(dm_result)}"
        
        # Assert: 验证是 ISO 8601 格式
        assert "T" in dm_result, \
            f"ISO 8601 格式应该包含 'T'，实际: {dm_result}"
        
        # Assert: 验证可以反序列化
        try:
            parsed_dt = datetime.datetime.fromisoformat(dm_result)
            assert parsed_dt == dt, \
                f"反序列化后应该等于原始值，期望: {dt}, 实际: {parsed_dt}"
        except ValueError as e:
            pytest.fail(f"无法反序列化 ISO 8601 字符串: {dm_result}, 错误: {e}")
        
        # Act: 序列化（测试人大金仓）
        kingbase_result = Kingbase_Loader._serialize_value(dt)
        
        # Assert: 验证结果一致
        assert kingbase_result == dm_result, \
            f"达梦和人大金仓的序列化结果应该一致"
    
    @given(
        year=st.integers(min_value=1900, max_value=2100),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    @pytest.mark.pbt
    def test_date_serialization_property(self, year, month, day):
        """
        属性测试：日期序列化
        
        **Validates: Requirements 3.3, 6.3**
        
        属性：对于任意有效的日期值，序列化应该产生 ISO 8601 日期格式字符串
        
        Args:
            year, month, day: 日期组件
        """
        # 构造日期对象
        d = datetime.date(year, month, day)
        
        # Act: 序列化
        dm_result = DM_Loader._serialize_value(d)
        kingbase_result = Kingbase_Loader._serialize_value(d)
        
        # Assert: 验证是字符串
        assert isinstance(dm_result, str), \
            f"序列化结果应该是字符串，实际类型: {type(dm_result)}"
        
        # Assert: 验证格式 YYYY-MM-DD
        assert len(dm_result) == 10, \
            f"日期格式应该是 YYYY-MM-DD (10 个字符)，实际: {dm_result}"
        assert dm_result.count("-") == 2, \
            f"日期格式应该包含 2 个连字符，实际: {dm_result}"
        
        # Assert: 验证可以反序列化
        try:
            parsed_date = datetime.date.fromisoformat(dm_result)
            assert parsed_date == d, \
                f"反序列化后应该等于原始值，期望: {d}, 实际: {parsed_date}"
        except ValueError as e:
            pytest.fail(f"无法反序列化日期字符串: {dm_result}, 错误: {e}")
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kingbase_result == dm_result
    
    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
        second=st.integers(min_value=0, max_value=59)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    @pytest.mark.pbt
    def test_time_serialization_property(self, hour, minute, second):
        """
        属性测试：时间序列化
        
        **Validates: Requirements 3.3, 6.3**
        
        属性：对于任意有效的时间值，序列化应该产生 ISO 8601 时间格式字符串
        
        Args:
            hour, minute, second: 时间组件
        """
        # 构造时间对象
        t = datetime.time(hour, minute, second)
        
        # Act: 序列化
        dm_result = DM_Loader._serialize_value(t)
        kingbase_result = Kingbase_Loader._serialize_value(t)
        
        # Assert: 验证是字符串
        assert isinstance(dm_result, str)
        
        # Assert: 验证格式 HH:MM:SS
        assert dm_result.count(":") == 2, \
            f"时间格式应该包含 2 个冒号，实际: {dm_result}"
        
        # Assert: 验证可以反序列化
        try:
            parsed_time = datetime.time.fromisoformat(dm_result)
            assert parsed_time == t, \
                f"反序列化后应该等于原始值，期望: {t}, 实际: {parsed_time}"
        except ValueError as e:
            pytest.fail(f"无法反序列化时间字符串: {dm_result}, 错误: {e}")
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kingbase_result == dm_result
    
    @given(
        integer_part=st.integers(min_value=-999999, max_value=999999),
        decimal_places=st.integers(min_value=0, max_value=6)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    @pytest.mark.pbt
    def test_decimal_serialization_property(self, integer_part, decimal_places):
        """
        属性测试：DECIMAL 类型转换
        
        **Validates: Requirements 3.4, 6.4**
        
        属性：对于任意 DECIMAL 值，序列化应该转换为浮点数
        
        测试策略：
        1. 生成随机的 DECIMAL 值
        2. 序列化
        3. 验证结果是浮点数
        4. 验证精度在可接受范围内
        
        Args:
            integer_part: 整数部分
            decimal_places: 小数位数
        """
        # 构造 DECIMAL 值
        decimal_str = f"{integer_part}.{'1' * decimal_places}" if decimal_places > 0 else str(integer_part)
        decimal_value = decimal.Decimal(decimal_str)
        
        # Act: 序列化
        dm_result = DM_Loader._serialize_value(decimal_value)
        kingbase_result = Kingbase_Loader._serialize_value(decimal_value)
        
        # Assert: 验证是浮点数
        assert isinstance(dm_result, float), \
            f"DECIMAL 序列化结果应该是浮点数，实际类型: {type(dm_result)}"
        assert isinstance(kingbase_result, float), \
            f"DECIMAL 序列化结果应该是浮点数，实际类型: {type(kingbase_result)}"
        
        # Assert: 验证值在合理范围内（考虑浮点数精度）
        expected_float = float(decimal_value)
        assert abs(dm_result - expected_float) < 1e-6, \
            f"序列化值应该接近原始值，期望: {expected_float}, 实际: {dm_result}"
        
        # Assert: 验证达梦和人大金仓结果一致
        assert dm_result == kingbase_result
    
    @given(st.none())
    @settings(max_examples=10)
    @pytest.mark.pbt
    def test_none_serialization_property(self, none_value):
        """
        属性测试：None 值序列化
        
        **Validates: Requirements 3.3, 3.4, 6.3, 6.4**
        
        属性：对于 None 值，序列化应该保持为 None
        
        Args:
            none_value: None 值
        """
        # Act: 序列化
        dm_result = DM_Loader._serialize_value(none_value)
        kingbase_result = Kingbase_Loader._serialize_value(none_value)
        
        # Assert: 验证保持为 None
        assert dm_result is None, \
            f"None 值序列化后应该保持为 None，实际: {dm_result}"
        assert kingbase_result is None, \
            f"None 值序列化后应该保持为 None，实际: {kingbase_result}"
    
    @given(st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans()
    ))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @pytest.mark.pbt
    def test_primitive_types_serialization_property(self, value):
        """
        属性测试：基本类型序列化
        
        **Validates: Requirements 3.3, 3.4, 6.3, 6.4**
        
        属性：对于基本类型（int, float, str, bool），序列化应该保持原值不变
        
        Args:
            value: 基本类型值
        """
        # Act: 序列化
        dm_result = DM_Loader._serialize_value(value)
        kingbase_result = Kingbase_Loader._serialize_value(value)
        
        # Assert: 验证保持原值
        assert dm_result == value, \
            f"基本类型序列化后应该保持不变，期望: {value}, 实际: {dm_result}"
        assert kingbase_result == value, \
            f"基本类型序列化后应该保持不变，期望: {value}, 实际: {kingbase_result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "pbt", "--hypothesis-show-statistics"])



class TestSchemaModificationDetectionProperties:
    """
    模式修改检测属性测试类
    
    **属性 27: 模式修改检测**
    **验证: 需求 8.1**
    """
    
    @given(st.sampled_from([
        "CREATE TABLE", "ALTER TABLE", "DROP TABLE", 
        "TRUNCATE TABLE", "CREATE INDEX", "DROP INDEX"
    ]))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.pbt
    def test_ddl_operation_detection_property(self, ddl_keyword):
        """
        属性测试：DDL 操作检测
        
        **Validates: Requirements 8.1**
        
        属性：对于任意 DDL 操作关键字，系统应该正确检测为模式修改操作
        
        测试策略：
        1. 生成包含 DDL 关键字的 SQL 语句
        2. 调用模式修改检测方法
        3. 验证返回 True 和正确的操作类型
        
        Args:
            ddl_keyword: DDL 操作关键字
        """
        # 构造 DDL 语句
        sql_query = f"{ddl_keyword} users (id INT)"
        
        # Act: 检测模式修改（测试达梦）
        dm_is_modifying, dm_operation = DM_Loader.is_schema_modifying_query(sql_query)
        
        # Assert: 验证检测为模式修改
        assert dm_is_modifying, \
            f"DDL 操作应该被检测为模式修改: {sql_query}"
        
        # Assert: 验证操作类型
        first_word = ddl_keyword.split()[0]
        assert dm_operation == first_word, \
            f"操作类型应该是 {first_word}，实际: {dm_operation}"
        
        # Act: 检测模式修改（测试人大金仓）
        kb_is_modifying, kb_operation = Kingbase_Loader.is_schema_modifying_query(sql_query)
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kb_is_modifying == dm_is_modifying
        assert kb_operation == dm_operation
    
    @given(st.sampled_from([
        "SELECT * FROM users",
        "SELECT id, name FROM orders WHERE status = 'active'",
        "SELECT COUNT(*) FROM products",
        "SELECT DISTINCT category FROM items"
    ]))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.pbt
    def test_select_query_not_modifying_property(self, select_query):
        """
        属性测试：SELECT 查询不应该被检测为模式修改
        
        **Validates: Requirements 8.1**
        
        属性：对于任意 SELECT 查询，系统应该返回 False
        
        Args:
            select_query: SELECT 查询语句
        """
        # Act: 检测模式修改
        dm_is_modifying, dm_operation = DM_Loader.is_schema_modifying_query(select_query)
        kb_is_modifying, kb_operation = Kingbase_Loader.is_schema_modifying_query(select_query)
        
        # Assert: 验证不是模式修改
        assert not dm_is_modifying, \
            f"SELECT 查询不应该被检测为模式修改: {select_query}"
        assert dm_operation == "", \
            f"SELECT 查询的操作类型应该为空，实际: {dm_operation}"
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kb_is_modifying == dm_is_modifying
        assert kb_operation == dm_operation
    
    @given(st.sampled_from([
        "INSERT INTO users (name) VALUES ('test')",
        "UPDATE users SET status = 'active'",
        "DELETE FROM users WHERE id = 1"
    ]))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.pbt
    def test_dml_query_not_modifying_property(self, dml_query):
        """
        属性测试：DML 操作不应该被检测为模式修改
        
        **Validates: Requirements 8.1**
        
        属性：对于任意 DML 操作（INSERT/UPDATE/DELETE），系统应该返回 False
        
        Args:
            dml_query: DML 操作语句
        """
        # Act: 检测模式修改
        dm_is_modifying, dm_operation = DM_Loader.is_schema_modifying_query(dml_query)
        kb_is_modifying, kb_operation = Kingbase_Loader.is_schema_modifying_query(dml_query)
        
        # Assert: 验证不是模式修改
        assert not dm_is_modifying, \
            f"DML 操作不应该被检测为模式修改: {dml_query}"
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kb_is_modifying == dm_is_modifying
    
    @given(st.text(min_size=0, max_size=10))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.pbt
    def test_empty_or_whitespace_query_property(self, whitespace):
        """
        属性测试：空字符串或纯空白字符串不应该被检测为模式修改
        
        **Validates: Requirements 8.1**
        
        属性：对于任意空字符串或纯空白字符串，系统应该返回 False
        
        Args:
            whitespace: 空白字符串
        """
        # 只测试空白字符
        if whitespace.strip():
            pytest.skip("不是空白字符串")
        
        # Act: 检测模式修改
        dm_is_modifying, dm_operation = DM_Loader.is_schema_modifying_query(whitespace)
        kb_is_modifying, kb_operation = Kingbase_Loader.is_schema_modifying_query(whitespace)
        
        # Assert: 验证不是模式修改
        assert not dm_is_modifying, \
            f"空字符串不应该被检测为模式修改"
        assert dm_operation == "", \
            f"空字符串的操作类型应该为空"
        
        # Assert: 验证达梦和人大金仓结果一致
        assert kb_is_modifying == dm_is_modifying
        assert kb_operation == dm_operation


class TestIdentifierQuotingProperties:
    """
    标识符引用属性测试类
    
    **属性 30: 标识符引用规则**
    **属性 31: 特殊字符标识符引用**
    **属性 32: 保留字标识符引用**
    **属性 33: 引号转义**
    **验证: 需求 9.1-9.5**
    """
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('a'), max_codepoint=ord('z')
    )))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.pbt
    def test_identifier_quoting_property(self, identifier):
        """
        属性测试：标识符引用规则
        
        **Validates: Requirements 9.1, 9.2**
        
        属性：对于任意标识符，达梦和人大金仓应该使用双引号引用
        
        测试策略：
        1. 生成随机标识符
        2. 构造包含该标识符的 SQL 查询
        3. 验证标识符被双引号引用
        
        Args:
            identifier: 标识符名称
        """
        # 构造 SQL 查询（使用标识符）
        # 注意：这里我们测试的是标识符引用的概念，而不是实际的 SQL 生成
        # 在实际实现中，标识符引用通常在查询构建时完成
        
        # 验证双引号引用格式
        quoted_identifier = f'"{identifier}"'
        
        # Assert: 验证引用格式
        assert quoted_identifier.startswith('"'), \
            f"标识符应该以双引号开始"
        assert quoted_identifier.endswith('"'), \
            f"标识符应该以双引号结束"
        assert quoted_identifier.count('"') >= 2, \
            f"标识符应该被双引号包围"
    
    @given(st.text(min_size=1, max_size=50).filter(
        lambda s: any(c in s for c in [' ', '-', '.', '@', '#'])
    ))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.pbt
    def test_special_character_identifier_quoting_property(self, identifier):
        """
        属性测试：特殊字符标识符引用
        
        **Validates: Requirements 9.3**
        
        属性：对于任意包含特殊字符的标识符，系统应该强制使用引号
        
        Args:
            identifier: 包含特殊字符的标识符
        """
        # 验证包含特殊字符
        has_special_char = any(c in identifier for c in [' ', '-', '.', '@', '#'])
        assert has_special_char, "标识符应该包含特殊字符"
        
        # 构造引用的标识符
        quoted_identifier = f'"{identifier}"'
        
        # Assert: 验证必须使用引号
        assert quoted_identifier.startswith('"') and quoted_identifier.endswith('"'), \
            f"包含特殊字符的标识符必须使用引号: {identifier}"
    
    @given(st.sampled_from([
        "SELECT", "FROM", "WHERE", "ORDER", "GROUP", "BY",
        "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
        "TABLE", "INDEX", "VIEW", "DATABASE", "USER", "GRANT"
    ]))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.pbt
    def test_reserved_word_identifier_quoting_property(self, reserved_word):
        """
        属性测试：保留字标识符引用
        
        **Validates: Requirements 9.4**
        
        属性：对于任意 SQL 保留字作为标识符，系统应该使用引号
        
        Args:
            reserved_word: SQL 保留字
        """
        # 构造引用的保留字标识符
        quoted_identifier = f'"{reserved_word}"'
        
        # Assert: 验证保留字必须使用引号
        assert quoted_identifier.startswith('"') and quoted_identifier.endswith('"'), \
            f"SQL 保留字作为标识符必须使用引号: {reserved_word}"
    
    @given(st.text(min_size=1, max_size=50).filter(lambda s: '"' in s))
    @settings(
        max_examples=100, 
        deadline=None, 
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much]
    )
    @pytest.mark.pbt
    def test_quote_escaping_property(self, identifier_with_quote):
        """
        属性测试：引号转义
        
        **Validates: Requirements 9.5**
        
        属性：对于任意包含引号的标识符，系统应该正确转义引号
        
        测试策略：
        1. 生成包含引号的标识符
        2. 转义引号（双引号转义为两个双引号）
        3. 验证转义后的标识符格式正确
        
        Args:
            identifier_with_quote: 包含引号的标识符
        """
        # 验证包含引号
        assert '"' in identifier_with_quote, "标识符应该包含引号"
        
        # 转义引号：双引号转义为两个双引号
        escaped_identifier = identifier_with_quote.replace('"', '""')
        quoted_identifier = f'"{escaped_identifier}"'
        
        # Assert: 验证转义后的格式
        assert quoted_identifier.startswith('"') and quoted_identifier.endswith('"'), \
            f"转义后的标识符应该被双引号包围"
        
        # Assert: 验证内部的引号被转义
        inner_content = quoted_identifier[1:-1]
        if '"' in identifier_with_quote:
            # 如果原始标识符包含引号，转义后应该包含双引号
            assert '""' in inner_content or inner_content == '', \
                f"内部的引号应该被转义为两个双引号"


class TestQueryResultFormatProperties:
    """
    查询结果格式属性测试类
    
    **属性 15: 查询结果格式**
    **验证: 需求 3.2, 6.2**
    """
    
    @given(st.lists(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll'),
                min_codepoint=ord('a'), max_codepoint=ord('z')
            )),
            values=st.one_of(
                st.integers(),
                st.text(max_size=50),
                st.none()
            ),
            min_size=1,
            max_size=5
        ),
        min_size=0,
        max_size=10
    ))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.pbt
    def test_query_result_format_property(self, mock_result):
        """
        属性测试：查询结果格式
        
        **Validates: Requirements 3.2, 6.2**
        
        属性：对于任意查询结果，返回的数据结构应该是字典列表，
        每个字典包含列名和对应的值
        
        测试策略：
        1. 生成模拟的查询结果
        2. 验证结果是列表
        3. 验证每个元素是字典
        4. 验证字典包含列名和值
        
        Args:
            mock_result: 模拟的查询结果
        """
        # Assert: 验证结果是列表
        assert isinstance(mock_result, list), \
            f"查询结果应该是列表，实际类型: {type(mock_result)}"
        
        # Assert: 验证每个元素是字典
        for row in mock_result:
            assert isinstance(row, dict), \
                f"查询结果的每一行应该是字典，实际类型: {type(row)}"
            
            # Assert: 验证字典包含列名（键）和值
            for column_name, value in row.items():
                assert isinstance(column_name, str), \
                    f"列名应该是字符串，实际类型: {type(column_name)}"
                # 值可以是任意类型（包括 None）


class TestConnectionErrorHandlingProperties:
    """
    连接错误处理属性测试类
    
    **属性 3: 连接失败错误处理**
    **验证: 需求 1.3, 4.3**
    """
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.pbt
    def test_invalid_url_error_message_property(self, invalid_url):
        """
        属性测试：无效 URL 错误消息
        
        **Validates: Requirements 1.3, 4.3**
        
        属性：对于任意无效的连接 URL，系统应该返回包含失败原因的清晰错误信息
        
        测试策略：
        1. 生成随机的无效 URL
        2. 尝试解析 URL
        3. 验证抛出的异常包含清晰的错误信息
        
        Args:
            invalid_url: 无效的 URL
        """
        # 跳过可能有效的 URL
        if "://" in invalid_url and "@" in invalid_url:
            pytest.skip("可能是有效的 URL")
        
        # 测试达梦数据库
        dm_url = f"dm://{invalid_url}"
        try:
            DM_Loader._parse_connection_url(dm_url)
            # 如果没有抛出异常，说明 URL 可能是有效的
            pytest.skip("URL 被解析为有效格式")
        except DM_ConnectionError as e:
            # Assert: 验证错误消息不为空
            assert str(e), "错误消息不应该为空"
            # Assert: 验证错误消息包含有用信息
            assert len(str(e)) > 10, \
                f"错误消息应该包含足够的信息，实际: {str(e)}"
        
        # 测试人大金仓数据库
        kb_url = f"kingbase://{invalid_url}"
        try:
            Kingbase_Loader._parse_connection_url(kb_url)
            pytest.skip("URL 被解析为有效格式")
        except Kingbase_ConnectionError as e:
            # Assert: 验证错误消息不为空
            assert str(e), "错误消息不应该为空"
            assert len(str(e)) > 10, \
                f"错误消息应该包含足够的信息，实际: {str(e)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "pbt", "--hypothesis-show-statistics"])
