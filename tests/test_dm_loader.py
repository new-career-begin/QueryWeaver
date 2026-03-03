#!/usr/bin/env python3
"""
达梦数据库加载器单元测试模块

测试达梦数据库加载器的所有功能，包括：
- URL 解析
- 连接管理
- 模式提取
- 查询执行
- 值序列化
- 模式修改检测
- 错误处理
"""

import datetime
import decimal
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any

from api.loaders.dm_loader import (
    DM_Loader,
    DM_QueryError,
    DM_ConnectionError
)


class TestDMLoaderURLParsing(unittest.TestCase):
    """达梦数据库 URL 解析测试套件"""

    def test_parse_connection_url_valid(self):
        """
        测试：解析有效的达梦数据库连接 URL
        
        验证需求 1.4：系统应该支持标准的达梦数据库连接 URL 格式
        """
        # Arrange
        url = "dm://testuser:testpass@192.168.1.100:5236/testdb"

        # Act
        result = DM_Loader._parse_connection_url(url)

        # Assert
        self.assertEqual(result["user"], "testuser")
        self.assertEqual(result["password"], "testpass")
        self.assertEqual(result["server"], "192.168.1.100")
        self.assertEqual(result["port"], 5236)
        self.assertEqual(result["database"], "testdb")

    def test_parse_connection_url_with_special_characters(self):
        """
        测试：解析包含特殊字符的 URL
        
        验证 URL 解码功能
        """
        # Arrange - URL 编码的特殊字符
        url = "dm://user%40name:pass%23word@localhost:5236/test%20db"

        # Act
        result = DM_Loader._parse_connection_url(url)

        # Assert
        self.assertEqual(result["user"], "user@name")
        self.assertEqual(result["password"], "pass#word")
        self.assertEqual(result["database"], "test db")

    def test_parse_connection_url_invalid_format(self):
        """
        测试：解析无效格式的 URL 应该抛出异常
        
        验证需求 1.3：连接失败时应该返回清晰的错误信息
        """
        # Arrange
        invalid_urls = [
            "postgresql://user:pass@host:5432/db",  # 错误的协议
            "dm://user@host:5236/db",  # 缺少密码
            "dm://user:pass@host/db",  # 缺少端口
            "dm://host:5236/db",  # 缺少用户名和密码
        ]

        # Act & Assert
        for url in invalid_urls:
            with self.assertRaises(DM_ConnectionError):
                DM_Loader._parse_connection_url(url)


class TestDMLoaderValueSerialization(unittest.TestCase):
    """达梦数据库值序列化测试套件"""

    def test_serialize_value_datetime(self):
        """
        测试：datetime 类型应该被序列化为 ISO 8601 格式字符串
        
        验证需求 3.3：查询结果包含日期时间类型时，应该将其序列化为 ISO 8601 格式字符串
        """
        # Arrange
        test_datetime = datetime.datetime(2025, 1, 15, 10, 30, 45)
        test_date = datetime.date(2025, 1, 15)
        test_time = datetime.time(10, 30, 45)

        # Act
        result_datetime = DM_Loader._serialize_value(test_datetime)
        result_date = DM_Loader._serialize_value(test_date)
        result_time = DM_Loader._serialize_value(test_time)

        # Assert
        self.assertEqual(result_datetime, "2025-01-15T10:30:45")
        self.assertEqual(result_date, "2025-01-15")
        self.assertEqual(result_time, "10:30:45")

    def test_serialize_value_decimal(self):
        """
        测试：Decimal 类型应该被转换为浮点数
        
        验证需求 3.4：查询结果包含 DECIMAL 类型时，应该将其转换为浮点数
        """
        # Arrange
        test_decimal = decimal.Decimal("123.45")

        # Act
        result = DM_Loader._serialize_value(test_decimal)

        # Assert
        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

    def test_serialize_value_none(self):
        """测试：None 值应该保持为 None"""
        result = DM_Loader._serialize_value(None)
        self.assertIsNone(result)

    def test_serialize_value_primitive_types(self):
        """测试：基本类型应该保持不变"""
        test_values = [
            ("test_string", "test_string"),
            (123, 123),
            (45.67, 45.67),
            (True, True),
            (False, False)
        ]

        for input_value, expected_value in test_values:
            result = DM_Loader._serialize_value(input_value)
            self.assertEqual(result, expected_value)


class TestDMLoaderQueryExecution(unittest.TestCase):
    """达梦数据库查询执行测试套件"""

    def setUp(self):
        """设置测试环境"""
        self.test_db_url = "dm://test_user:test_pass@localhost:5236/test_db"
        self.test_select_query = "SELECT * FROM users LIMIT 10"
        self.test_insert_query = "INSERT INTO users (name, email) VALUES ('test', 'test@example.com')"
        
        # 创建 mock dmPython 模块
        self.mock_dmpython = MagicMock()
        self.mock_dmpython.Error = Exception
        sys.modules['dmPython'] = self.mock_dmpython

    def tearDown(self):
        """清理测试环境"""
        if 'dmPython' in sys.modules:
            del sys.modules['dmPython']

    def test_execute_sql_query_select_success(self):
        """
        测试：SELECT 查询应该成功执行并返回结果集
        
        验证需求 3.1, 3.2：系统应该使用达梦数据库驱动执行查询并返回结果
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com")
        ]

        # Act
        result = DM_Loader.execute_sql_query(self.test_select_query, self.test_db_url)

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["name"], "Alice")
        self.assertEqual(result[1]["id"], 2)
        self.assertEqual(result[1]["email"], "bob@example.com")

    def test_execute_sql_query_insert_success(self):
        """
        测试：INSERT 查询应该返回影响行数
        
        验证需求 3.1：系统应该处理 INSERT/UPDATE/DELETE 操作
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = None
        mock_cursor.rowcount = 1

        # Act
        result = DM_Loader.execute_sql_query(self.test_insert_query, self.test_db_url)

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operation"], "INSERT")
        self.assertEqual(result[0]["affected_rows"], 1)
        self.assertEqual(result[0]["status"], "success")

    def test_execute_sql_query_update_success(self):
        """
        测试：UPDATE 查询应该返回影响行数
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = None
        mock_cursor.rowcount = 5

        # Act
        result = DM_Loader.execute_sql_query(
            "UPDATE users SET status = 'active'", 
            self.test_db_url
        )

        # Assert
        self.assertEqual(result[0]["operation"], "UPDATE")
        self.assertEqual(result[0]["affected_rows"], 5)

    def test_execute_sql_query_connection_error(self):
        """
        测试：连接失败应该抛出 DM_ConnectionError
        
        验证需求 1.3, 3.6：连接失败时应该返回清晰的错误信息
        """
        # Arrange
        self.mock_dmpython.connect.side_effect = Exception("连接超时")

        # Act & Assert
        with self.assertRaises(DM_ConnectionError) as context:
            DM_Loader.execute_sql_query(self.test_select_query, self.test_db_url)

        self.assertIn("连接达梦数据库失败", str(context.exception))

    def test_execute_sql_query_execution_error(self):
        """
        测试：查询执行失败应该抛出 DM_QueryError
        
        验证需求 3.6：查询执行失败时应该返回数据库错误信息
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("表不存在")

        # Act & Assert
        with self.assertRaises(DM_QueryError) as context:
            DM_Loader.execute_sql_query("SELECT * FROM nonexistent_table", self.test_db_url)

        self.assertIn("查询执行失败", str(context.exception))

    def test_execute_sql_query_closes_connection(self):
        """
        测试：查询完成后应该关闭连接
        
        验证资源管理：确保连接被正确关闭
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = [(1,)]

        # Act
        DM_Loader.execute_sql_query(self.test_select_query, self.test_db_url)

        # Assert
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_execute_sql_query_with_datetime_values(self):
        """
        测试：查询结果包含日期时间值时应该正确序列化
        
        验证需求 3.3：日期时间序列化
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        test_datetime = datetime.datetime(2025, 1, 15, 10, 30, 45)
        mock_cursor.description = [("id",), ("created_at",)]
        mock_cursor.fetchall.return_value = [(1, test_datetime)]

        # Act
        result = DM_Loader.execute_sql_query(self.test_select_query, self.test_db_url)

        # Assert
        self.assertEqual(result[0]["created_at"], "2025-01-15T10:30:45")

    def test_execute_sql_query_with_decimal_values(self):
        """
        测试：查询结果包含 DECIMAL 值时应该转换为浮点数
        
        验证需求 3.4：DECIMAL 类型转换
        """
        # Arrange
        mock_conn = Mock()
        mock_cursor = Mock()
        self.mock_dmpython.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        test_decimal = decimal.Decimal("99.99")
        mock_cursor.description = [("id",), ("price",)]
        mock_cursor.fetchall.return_value = [(1, test_decimal)]

        # Act
        result = DM_Loader.execute_sql_query(self.test_select_query, self.test_db_url)

        # Assert
        self.assertEqual(result[0]["price"], 99.99)
        self.assertIsInstance(result[0]["price"], float)


class TestDMLoaderSchemaExtraction(unittest.TestCase):
    """达梦数据库模式提取测试套件"""

    def setUp(self):
        """设置测试环境"""
        self.mock_cursor = Mock()

    def test_extract_tables_info_success(self):
        """
        测试：成功提取表信息
        
        验证需求 2.1：系统应该提取所有用户表的名称和注释
        """
        # Arrange
        self.mock_cursor.fetchall.return_value = [
            ("USERS", "用户信息表"),
            ("ORDERS", "订单表")
        ]

        # Mock extract_columns_info 和 extract_foreign_keys
        with patch.object(DM_Loader, 'extract_columns_info') as mock_columns, \
             patch.object(DM_Loader, 'extract_foreign_keys') as mock_fks:
            
            mock_columns.return_value = {
                "ID": {"type": "INTEGER", "null": "N", "key": "PRIMARY KEY", 
                       "description": "用户ID", "default": None, "sample_values": [1, 2, 3]}
            }
            mock_fks.return_value = []

            # Act
            result = DM_Loader.extract_tables_info(self.mock_cursor)

            # Assert
            self.assertEqual(len(result), 2)
            self.assertIn("USERS", result)
            self.assertIn("ORDERS", result)
            self.assertEqual(result["USERS"]["description"], "用户信息表")

    def test_extract_columns_info_success(self):
        """
        测试：成功提取列信息
        
        验证需求 2.2：系统应该获取每个表的所有列信息
        """
        # Arrange
        self.mock_cursor.fetchall.return_value = [
            ("ID", "INTEGER", "N", None, "PRIMARY KEY", "用户ID"),
            ("NAME", "VARCHAR", "N", None, "NONE", "用户名"),
            ("EMAIL", "VARCHAR", "Y", None, "NONE", "邮箱地址")
        ]

        # Mock _execute_sample_query
        with patch.object(DM_Loader, '_execute_sample_query') as mock_sample:
            mock_sample.return_value = ["sample1", "sample2"]

            # Act
            result = DM_Loader.extract_columns_info(self.mock_cursor, "USERS")

            # Assert
            self.assertEqual(len(result), 3)
            self.assertIn("ID", result)
            self.assertIn("NAME", result)
            self.assertIn("EMAIL", result)
            
            # 验证主键标识
            self.assertEqual(result["ID"]["key"], "PRIMARY KEY")
            self.assertEqual(result["NAME"]["key"], "NONE")
            
            # 验证可空性
            self.assertEqual(result["ID"]["null"], "N")
            self.assertEqual(result["EMAIL"]["null"], "Y")

    def test_extract_foreign_keys_success(self):
        """
        测试：成功提取外键信息
        
        验证需求 2.5：系统应该记录外键约束名称、源列、引用表和引用列
        """
        # Arrange
        self.mock_cursor.fetchall.return_value = [
            ("FK_USER_ID", "USER_ID", "USERS", "ID"),
            ("FK_PRODUCT_ID", "PRODUCT_ID", "PRODUCTS", "ID")
        ]

        # Act
        result = DM_Loader.extract_foreign_keys(self.mock_cursor, "ORDERS")

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["constraint_name"], "FK_USER_ID")
        self.assertEqual(result[0]["column"], "USER_ID")
        self.assertEqual(result[0]["referenced_table"], "USERS")
        self.assertEqual(result[0]["referenced_column"], "ID")

    def test_extract_relationships_success(self):
        """
        测试：成功提取表之间的关系
        
        验证需求 2.5：系统应该提取所有外键关系
        """
        # Arrange
        self.mock_cursor.fetchall.return_value = [
            ("ORDERS", "FK_USER_ID", "USER_ID", "USERS", "ID"),
            ("ORDERS", "FK_PRODUCT_ID", "PRODUCT_ID", "PRODUCTS", "ID"),
            ("ORDER_ITEMS", "FK_ORDER_ID", "ORDER_ID", "ORDERS", "ID")
        ]

        # Act
        result = DM_Loader.extract_relationships(self.mock_cursor)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIn("FK_USER_ID", result)
        self.assertIn("FK_PRODUCT_ID", result)
        self.assertIn("FK_ORDER_ID", result)
        
        # 验证关系详情
        user_rel = result["FK_USER_ID"][0]
        self.assertEqual(user_rel["from"], "ORDERS")
        self.assertEqual(user_rel["to"], "USERS")
        self.assertEqual(user_rel["source_column"], "USER_ID")
        self.assertEqual(user_rel["target_column"], "ID")

    def test_execute_sample_query_success(self):
        """
        测试：成功获取列的示例值
        
        验证需求 2.7：系统应该为每个列提取最多 3 个示例值
        """
        # Arrange
        self.mock_cursor.fetchmany.return_value = [
            ("Alice",),
            ("Bob",),
            ("Charlie",)
        ]

        # Act
        result = DM_Loader._execute_sample_query(self.mock_cursor, "USERS", "NAME", 3)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Alice")
        self.assertEqual(result[1], "Bob")
        self.assertEqual(result[2], "Charlie")

    def test_execute_sample_query_with_null_values(self):
        """
        测试：示例查询应该过滤 NULL 值
        """
        # Arrange
        self.mock_cursor.fetchmany.return_value = [
            ("Alice",),
            (None,),
            ("Bob",)
        ]

        # Act
        result = DM_Loader._execute_sample_query(self.mock_cursor, "USERS", "NAME", 3)

        # Assert
        # 应该只包含非 NULL 值
        self.assertEqual(len(result), 2)
        self.assertNotIn(None, result)

    def test_extract_tables_info_handles_error(self):
        """
        测试：提取表信息时遇到错误应该继续处理其他表
        
        验证需求 2.8：提取过程中发生错误时应该记录日志并继续处理其他表
        """
        # Arrange
        self.mock_cursor.fetchall.return_value = [
            ("USERS", "用户表"),
            ("ORDERS", "订单表")
        ]

        # Mock extract_columns_info - 第一次调用失败，第二次成功
        with patch.object(DM_Loader, 'extract_columns_info') as mock_columns, \
             patch.object(DM_Loader, 'extract_foreign_keys') as mock_fks:
            
            mock_columns.side_effect = [
                Exception("提取失败"),  # USERS 表失败
                {"ID": {"type": "INTEGER", "null": "N", "key": "PRIMARY KEY",
                       "description": "订单ID", "default": None, "sample_values": []}}  # ORDERS 表成功
            ]
            mock_fks.return_value = []

            # Act
            result = DM_Loader.extract_tables_info(self.mock_cursor)

            # Assert
            # 应该只包含成功提取的表
            self.assertEqual(len(result), 1)
            self.assertIn("ORDERS", result)
            self.assertNotIn("USERS", result)


class TestDMLoaderSchemaModification(unittest.TestCase):
    """达梦数据库模式修改检测测试套件"""

    def test_is_schema_modifying_query_create_table(self):
        """
        测试：检测 CREATE TABLE 语句
        
        验证需求 8.1：系统应该检测模式修改操作
        """
        # Arrange
        queries = [
            "CREATE TABLE users (id INT PRIMARY KEY)",
            "  CREATE TABLE orders (id INT)",
            "create table products (id int)"
        ]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertTrue(is_modifying)
            self.assertEqual(operation, "CREATE")

    def test_is_schema_modifying_query_alter_table(self):
        """测试：检测 ALTER TABLE 语句"""
        # Arrange
        queries = [
            "ALTER TABLE users ADD COLUMN age INT",
            "  ALTER TABLE users DROP COLUMN email",
            "alter table users modify column name varchar(100)"
        ]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertTrue(is_modifying)
            self.assertEqual(operation, "ALTER")

    def test_is_schema_modifying_query_drop_table(self):
        """测试：检测 DROP TABLE 语句"""
        # Arrange
        queries = [
            "DROP TABLE users",
            "  DROP TABLE IF EXISTS orders",
            "drop table products"
        ]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertTrue(is_modifying)
            self.assertEqual(operation, "DROP")

    def test_is_schema_modifying_query_truncate_table(self):
        """测试：检测 TRUNCATE TABLE 语句"""
        # Arrange
        query = "TRUNCATE TABLE users"

        # Act
        is_modifying, operation = DM_Loader.is_schema_modifying_query(query)

        # Assert
        self.assertTrue(is_modifying)
        self.assertEqual(operation, "TRUNCATE")

    def test_is_schema_modifying_query_select(self):
        """测试：SELECT 语句不应该被识别为模式修改"""
        # Arrange
        queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM orders WHERE status = 'active'",
            "select count(*) from products"
        ]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertFalse(is_modifying)
            self.assertEqual(operation, "")

    def test_is_schema_modifying_query_insert_update_delete(self):
        """测试：DML 语句不应该被识别为模式修改"""
        # Arrange
        queries = [
            "INSERT INTO users (name) VALUES ('Alice')",
            "UPDATE users SET status = 'active'",
            "DELETE FROM users WHERE id = 1"
        ]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertFalse(is_modifying)

    def test_is_schema_modifying_query_empty_string(self):
        """测试：空字符串应该返回 False"""
        # Arrange
        queries = ["", "   ", "\n\t"]

        # Act & Assert
        for query in queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            self.assertFalse(is_modifying)
            self.assertEqual(operation, "")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("运行达梦数据库加载器单元测试")
    print("=" * 70)
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
