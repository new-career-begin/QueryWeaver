"""人大金仓数据库加载器完整单元测试"""

import pytest
import sys
import asyncio
import datetime
import decimal
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Mock 所有外部依赖模块以避免导入错误
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.sql'] = MagicMock()
sys.modules['falkordb'] = MagicMock()
sys.modules['falkordb.asyncio'] = MagicMock()
sys.modules['tqdm'] = MagicMock()

from api.loaders.kingbase_loader import (
    Kingbase_Loader,
    Kingbase_QueryError,
    Kingbase_ConnectionError
)


async def _consume_loader(loader_gen):
    """消费异步生成器加载器并返回最终结果"""
    last_success, last_message = False, ""
    async for success, message in loader_gen:
        last_success, last_message = success, message
    return last_success, last_message


class TestKingbaseLoaderURLParsing:
    """测试人大金仓加载器的 URL 解析功能"""

    def test_parse_kingbase_url_valid(self):
        """测试解析有效的 kingbase:// URL"""
        url = "kingbase://testuser:testpass@localhost:54321/testdb"
        result = Kingbase_Loader._parse_connection_url(url)
        
        # 应该转换为 postgresql:// 格式
        assert result == "postgresql://testuser:testpass@localhost:54321/testdb"

    def test_parse_postgresql_url_valid(self):
        """测试解析有效的 postgresql:// URL（人大金仓兼容）"""
        url = "postgresql://testuser:testpass@localhost:54321/testdb"
        result = Kingbase_Loader._parse_connection_url(url)
        
        # 应该保持 postgresql:// 格式
        assert result == "postgresql://testuser:testpass@localhost:54321/testdb"

    def test_parse_url_with_default_port(self):
        """测试解析带默认端口的 URL"""
        url = "kingbase://testuser:testpass@localhost:54321/testdb"
        result = Kingbase_Loader._parse_connection_url(url)
        
        assert "54321" in result
        assert "postgresql://" in result

    def test_parse_url_with_query_params(self):
        """测试解析带查询参数的 URL"""
        url = "kingbase://testuser:testpass@localhost:54321/testdb?sslmode=require"
        result = Kingbase_Loader._parse_connection_url(url)
        
        # 应该保留查询参数
        assert "postgresql://" in result
        assert "testdb" in result

    def test_parse_url_empty(self):
        """测试解析空 URL"""
        with pytest.raises(Kingbase_ConnectionError, match="连接 URL 不能为空"):
            Kingbase_Loader._parse_connection_url("")

    def test_parse_url_invalid_format(self):
        """测试解析无效格式的 URL"""
        with pytest.raises(Kingbase_ConnectionError, match="连接 URL 格式不正确"):
            Kingbase_Loader._parse_connection_url("mysql://user@host/db")

    def test_parse_url_missing_host(self):
        """测试解析缺少主机的 URL"""
        with pytest.raises(Kingbase_ConnectionError, match="连接 URL 格式不正确"):
            Kingbase_Loader._parse_connection_url("kingbase://")

    def test_parse_url_missing_database(self):
        """测试解析缺少数据库名的 URL"""
        with pytest.raises(Kingbase_ConnectionError, match="连接 URL 格式不正确"):
            Kingbase_Loader._parse_connection_url("kingbase://user:pass@host:54321/")


class TestKingbaseLoaderConnection:
    """测试人大金仓加载器的连接管理功能"""

    @pytest.mark.asyncio
    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    @patch('api.loaders.kingbase_loader.load_to_graph')
    async def test_successful_connection(self, mock_load_to_graph, mock_connect):
        """测试成功建立连接"""
        # 模拟数据库连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟表查询结果
        mock_cursor.fetchall.return_value = [
            ('users', '用户表'),
        ]
        
        # 模拟子方法
        with patch.object(Kingbase_Loader, 'extract_columns_info', return_value={}), \
             patch.object(Kingbase_Loader, 'extract_foreign_keys', return_value=[]), \
             patch.object(Kingbase_Loader, 'extract_relationships', return_value={}):
            
            success, message = await _consume_loader(
                Kingbase_Loader.load("test_prefix", "kingbase://user:pass@localhost:54321/testdb")
            )
        
        # 验证连接成功
        assert success is True
        assert "成功" in message
        mock_connect.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    async def test_connection_operational_error(self, mock_connect):
        """测试连接操作错误（主机不可达、端口错误等）"""
        import psycopg2
        
        # 模拟连接操作错误
        mock_connect.side_effect = psycopg2.OperationalError("无法连接到主机")
        
        success, message = await _consume_loader(
            Kingbase_Loader.load("test_prefix", "kingbase://user:pass@invalid:54321/testdb")
        )
        
        # 验证错误处理
        assert success is False
        assert "无法连接" in message or "请检查" in message

    @pytest.mark.asyncio
    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    async def test_connection_database_error(self, mock_connect):
        """测试数据库认证错误"""
        import psycopg2
        
        # 模拟数据库认证错误
        mock_connect.side_effect = psycopg2.DatabaseError("认证失败")
        
        success, message = await _consume_loader(
            Kingbase_Loader.load("test_prefix", "kingbase://wrong:wrong@localhost:54321/testdb")
        )
        
        # 验证错误处理
        assert success is False
        assert "认证失败" in message or "用户名" in message or "密码" in message


class TestKingbaseLoaderSchemaExtraction:
    """测试人大金仓加载器的模式提取方法"""

    def test_execute_sample_query(self):
        """测试 _execute_sample_query 方法"""
        # 创建模拟游标
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('value1',),
            ('value2',),
            ('value3',)
        ]
        
        # 执行方法
        result = Kingbase_Loader._execute_sample_query(
            mock_cursor, 'test_table', 'test_column', 3
        )
        
        # 验证结果
        assert result == ['value1', 'value2', 'value3']
        assert mock_cursor.execute.called
        
        # 验证 SQL 查询被正确构造
        call_args = mock_cursor.execute.call_args
        assert call_args is not None
        # 验证传递了正确的参数
        assert call_args[0][1] == (3,)

    def test_execute_sample_query_with_nulls(self):
        """测试 _execute_sample_query 方法过滤 NULL 值"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('value1',),
            (None,),
            ('value2',),
        ]
        
        result = Kingbase_Loader._execute_sample_query(
            mock_cursor, 'test_table', 'test_column', 3
        )
        
        # NULL 值应该被过滤掉
        assert result == ['value1', 'value2']

    def test_serialize_value_datetime(self):
        """测试日期时间值的序列化"""
        import datetime
        
        # 测试 datetime
        dt = datetime.datetime(2025, 1, 15, 10, 30, 0)
        result = Kingbase_Loader._serialize_value(dt)
        assert result == '2025-01-15T10:30:00'
        
        # 测试 date
        d = datetime.date(2025, 1, 15)
        result = Kingbase_Loader._serialize_value(d)
        assert result == '2025-01-15'
        
        # 测试 time
        t = datetime.time(10, 30, 0)
        result = Kingbase_Loader._serialize_value(t)
        assert result == '10:30:00'

    def test_serialize_value_decimal(self):
        """测试 Decimal 值的序列化"""
        import decimal
        
        dec = decimal.Decimal('123.45')
        result = Kingbase_Loader._serialize_value(dec)
        assert result == 123.45
        assert isinstance(result, float)

    def test_serialize_value_none(self):
        """测试 None 值的序列化"""
        result = Kingbase_Loader._serialize_value(None)
        assert result is None

    def test_serialize_value_regular_types(self):
        """测试常规类型的序列化"""
        # 字符串
        assert Kingbase_Loader._serialize_value('test') == 'test'
        
        # 整数
        assert Kingbase_Loader._serialize_value(42) == 42
        
        # 浮点数
        assert Kingbase_Loader._serialize_value(3.14) == 3.14

    def test_extract_tables_info(self):
        """测试 extract_tables_info 方法"""
        mock_cursor = Mock()
        
        # 模拟表查询结果
        mock_cursor.fetchall.return_value = [
            ('users', '用户表'),
            ('orders', '订单表'),
        ]
        
        # 模拟 extract_columns_info 和 extract_foreign_keys
        with patch.object(Kingbase_Loader, 'extract_columns_info') as mock_columns, \
             patch.object(Kingbase_Loader, 'extract_foreign_keys') as mock_fks:
            
            mock_columns.return_value = {
                'id': {
                    'type': 'integer',
                    'null': 'NO',
                    'key': 'PRIMARY KEY',
                    'description': '用户ID',
                    'default': None,
                    'sample_values': ['1', '2', '3']
                }
            }
            
            mock_fks.return_value = []
            
            # 执行方法
            result = Kingbase_Loader.extract_tables_info(mock_cursor)
            
            # 验证结果
            assert 'users' in result
            assert 'orders' in result
            assert result['users']['description'] == '用户表'
            assert 'columns' in result['users']
            assert 'foreign_keys' in result['users']
            assert 'col_descriptions' in result['users']

    def test_extract_columns_info(self):
        """测试 extract_columns_info 方法"""
        mock_cursor = Mock()
        
        # 模拟列查询结果
        mock_cursor.fetchall.return_value = [
            ('id', 'integer', 'NO', None, 'PRIMARY KEY', '用户ID'),
            ('username', 'varchar', 'NO', None, 'NONE', '用户名'),
            ('email', 'varchar', 'YES', None, 'NONE', '邮箱地址'),
        ]
        
        # 模拟 extract_sample_values_for_column
        with patch.object(Kingbase_Loader, 'extract_sample_values_for_column') as mock_samples:
            mock_samples.return_value = ['sample1', 'sample2']
            
            # 执行方法
            result = Kingbase_Loader.extract_columns_info(mock_cursor, 'users')
            
            # 验证结果
            assert 'id' in result
            assert 'username' in result
            assert 'email' in result
            
            # 验证列信息
            assert result['id']['type'] == 'integer'
            assert result['id']['key'] == 'PRIMARY KEY'
            assert result['id']['null'] == 'NO'
            assert result['id']['sample_values'] == ['sample1', 'sample2']
            
            # 验证描述包含关键信息
            assert 'PRIMARY KEY' in result['id']['description']
            assert 'NOT NULL' in result['username']['description']

    def test_extract_foreign_keys(self):
        """测试 extract_foreign_keys 方法"""
        mock_cursor = Mock()
        
        # 模拟外键查询结果
        mock_cursor.fetchall.return_value = [
            ('fk_user_id', 'user_id', 'users', 'id'),
            ('fk_product_id', 'product_id', 'products', 'id'),
        ]
        
        # 执行方法
        result = Kingbase_Loader.extract_foreign_keys(mock_cursor, 'orders')
        
        # 验证结果
        assert len(result) == 2
        assert result[0]['constraint_name'] == 'fk_user_id'
        assert result[0]['column'] == 'user_id'
        assert result[0]['referenced_table'] == 'users'
        assert result[0]['referenced_column'] == 'id'

    def test_extract_relationships(self):
        """测试 extract_relationships 方法"""
        mock_cursor = Mock()
        
        # 模拟关系查询结果
        mock_cursor.fetchall.return_value = [
            ('orders', 'fk_user_id', 'user_id', 'users', 'id'),
            ('orders', 'fk_product_id', 'product_id', 'products', 'id'),
        ]
        
        # 执行方法
        result = Kingbase_Loader.extract_relationships(mock_cursor)
        
        # 验证结果
        assert 'fk_user_id' in result
        assert 'fk_product_id' in result
        
        # 验证关系信息
        assert result['fk_user_id'][0]['from'] == 'orders'
        assert result['fk_user_id'][0]['to'] == 'users'
        assert result['fk_user_id'][0]['source_column'] == 'user_id'
        assert result['fk_user_id'][0]['target_column'] == 'id'
        assert '外键约束' in result['fk_user_id'][0]['note']

    def test_extract_sample_values_for_column(self):
        """测试 extract_sample_values_for_column 方法（继承自基类）"""
        mock_cursor = Mock()
        
        # 模拟 _execute_sample_query 返回值
        with patch.object(Kingbase_Loader, '_execute_sample_query') as mock_execute:
            mock_execute.return_value = [123, 456, 789]
            
            # 执行方法
            result = Kingbase_Loader.extract_sample_values_for_column(
                mock_cursor, 'users', 'id', 3
            )
            
            # 验证结果
            assert result == ['123', '456', '789']
            mock_execute.assert_called_once_with(mock_cursor, 'users', 'id', 3)

    def test_extract_sample_values_for_column_with_strings(self):
        """测试字符串类型的示例值提取"""
        mock_cursor = Mock()
        
        with patch.object(Kingbase_Loader, '_execute_sample_query') as mock_execute:
            mock_execute.return_value = ['alice', 'bob', 'charlie']
            
            result = Kingbase_Loader.extract_sample_values_for_column(
                mock_cursor, 'users', 'username', 3
            )
            
            assert result == ['alice', 'bob', 'charlie']

    def test_extract_sample_values_for_column_empty(self):
        """测试空示例值的情况"""
        mock_cursor = Mock()
        
        with patch.object(Kingbase_Loader, '_execute_sample_query') as mock_execute:
            mock_execute.return_value = []
            
            result = Kingbase_Loader.extract_sample_values_for_column(
                mock_cursor, 'users', 'id', 3
            )
            
            assert result == []

    def test_extract_columns_info_with_defaults(self):
        """测试带默认值的列信息提取"""
        mock_cursor = Mock()
        
        # 模拟带默认值的列
        mock_cursor.fetchall.return_value = [
            ('created_at', 'timestamp', 'NO', 'CURRENT_TIMESTAMP', 'NONE', '创建时间'),
            ('status', 'varchar', 'NO', "'active'", 'NONE', '状态'),
        ]
        
        with patch.object(Kingbase_Loader, 'extract_sample_values_for_column') as mock_samples:
            mock_samples.return_value = []
            
            result = Kingbase_Loader.extract_columns_info(mock_cursor, 'users')
            
            # 验证默认值在描述中
            assert '默认值: CURRENT_TIMESTAMP' in result['created_at']['description']
            assert "默认值: 'active'" in result['status']['description']

    def test_extract_tables_info_integration(self):
        """集成测试：完整的表信息提取流程"""
        mock_cursor = Mock()
        
        # 模拟完整的查询流程
        mock_cursor.fetchall.side_effect = [
            # 第一次调用：获取表列表
            [('users', '用户表')],
        ]
        
        # 模拟子方法
        with patch.object(Kingbase_Loader, 'extract_columns_info') as mock_columns, \
             patch.object(Kingbase_Loader, 'extract_foreign_keys') as mock_fks:
            
            mock_columns.return_value = {
                'id': {
                    'type': 'integer',
                    'null': 'NO',
                    'key': 'PRIMARY KEY',
                    'description': '用户ID (PRIMARY KEY) (NOT NULL)',
                    'default': None,
                    'sample_values': ['1', '2', '3']
                },
                'username': {
                    'type': 'varchar',
                    'null': 'NO',
                    'key': 'NONE',
                    'description': '用户名 (NOT NULL)',
                    'default': None,
                    'sample_values': ['alice', 'bob']
                }
            }
            
            mock_fks.return_value = []
            
            result = Kingbase_Loader.extract_tables_info(mock_cursor)
            
            # 验证完整结构
            assert len(result) == 1
            assert 'users' in result
            
            users_table = result['users']
            assert users_table['description'] == '用户表'
            assert len(users_table['columns']) == 2
            assert len(users_table['col_descriptions']) == 2
            assert users_table['foreign_keys'] == []
            
            # 验证列描述列表
            assert '用户ID (PRIMARY KEY) (NOT NULL)' in users_table['col_descriptions']
            assert '用户名 (NOT NULL)' in users_table['col_descriptions']


class TestKingbaseLoaderQueryExecution:
    """测试人大金仓加载器的查询执行功能"""

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_select_query(self, mock_connect):
        """测试执行 SELECT 查询"""
        # 模拟数据库连接和游标
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟查询结果
        mock_cursor.description = [('id',), ('name',), ('email',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', 'alice@example.com'),
            (2, 'Bob', 'bob@example.com'),
        ]
        
        # 执行查询
        result = Kingbase_Loader.execute_sql_query(
            "SELECT * FROM users LIMIT 2",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['name'] == 'Alice'
        assert result[1]['email'] == 'bob@example.com'

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_insert_query(self, mock_connect):
        """测试执行 INSERT 查询"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟 INSERT 操作
        mock_cursor.description = None
        mock_cursor.rowcount = 1
        
        result = Kingbase_Loader.execute_sql_query(
            "INSERT INTO users (name, email) VALUES ('Charlie', 'charlie@example.com')",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['operation'] == 'INSERT'
        assert result[0]['affected_rows'] == 1
        assert result[0]['status'] == 'success'

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_update_query(self, mock_connect):
        """测试执行 UPDATE 查询"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟 UPDATE 操作
        mock_cursor.description = None
        mock_cursor.rowcount = 3
        
        result = Kingbase_Loader.execute_sql_query(
            "UPDATE users SET status = 'active' WHERE id > 10",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证结果
        assert result[0]['operation'] == 'UPDATE'
        assert result[0]['affected_rows'] == 3

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_delete_query(self, mock_connect):
        """测试执行 DELETE 查询"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟 DELETE 操作
        mock_cursor.description = None
        mock_cursor.rowcount = 2
        
        result = Kingbase_Loader.execute_sql_query(
            "DELETE FROM users WHERE status = 'inactive'",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证结果
        assert result[0]['operation'] == 'DELETE'
        assert result[0]['affected_rows'] == 2

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_ddl_query(self, mock_connect):
        """测试执行 DDL 查询（CREATE、DROP 等）"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟 CREATE TABLE 操作
        mock_cursor.description = None
        mock_cursor.rowcount = 0
        
        result = Kingbase_Loader.execute_sql_query(
            "CREATE TABLE test_table (id INT PRIMARY KEY)",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证结果
        assert result[0]['operation'] == 'CREATE'
        assert result[0]['status'] == 'success'

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_query_with_datetime_serialization(self, mock_connect):
        """测试查询结果中日期时间类型的序列化"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟包含日期时间的查询结果
        mock_cursor.description = [('id',), ('created_at',), ('updated_at',)]
        mock_cursor.fetchall.return_value = [
            (1, datetime.datetime(2025, 1, 15, 10, 30, 0), datetime.date(2025, 1, 15)),
        ]
        
        result = Kingbase_Loader.execute_sql_query(
            "SELECT * FROM logs",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证日期时间被序列化为 ISO 8601 格式
        assert result[0]['created_at'] == '2025-01-15T10:30:00'
        assert result[0]['updated_at'] == '2025-01-15'

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_query_with_decimal_serialization(self, mock_connect):
        """测试查询结果中 Decimal 类型的序列化"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟包含 Decimal 的查询结果
        mock_cursor.description = [('id',), ('price',), ('balance',)]
        mock_cursor.fetchall.return_value = [
            (1, decimal.Decimal('99.99'), decimal.Decimal('1234.56')),
        ]
        
        result = Kingbase_Loader.execute_sql_query(
            "SELECT * FROM products",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证 Decimal 被转换为浮点数
        assert result[0]['price'] == 99.99
        assert result[0]['balance'] == 1234.56
        assert isinstance(result[0]['price'], float)

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_query_connection_error(self, mock_connect):
        """测试查询执行时的连接错误"""
        import psycopg2
        
        # 模拟连接错误
        mock_connect.side_effect = psycopg2.OperationalError("连接失败")
        
        with pytest.raises(Kingbase_ConnectionError, match="连接人大金仓数据库失败"):
            Kingbase_Loader.execute_sql_query(
                "SELECT * FROM users",
                "kingbase://user:pass@invalid:54321/testdb"
            )

    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    def test_execute_query_syntax_error(self, mock_connect):
        """测试查询执行时的 SQL 语法错误"""
        import psycopg2
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 模拟 SQL 语法错误
        mock_cursor.execute.side_effect = psycopg2.Error("语法错误")
        
        with pytest.raises(Kingbase_QueryError, match="查询执行失败"):
            Kingbase_Loader.execute_sql_query(
                "SELCT * FROM users",  # 故意拼写错误
                "kingbase://user:pass@localhost:54321/testdb"
            )


class TestKingbaseLoaderSchemaModification:
    """测试人大金仓加载器的模式修改检测功能"""

    def test_detect_create_table(self):
        """测试检测 CREATE TABLE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "CREATE TABLE users (id INT PRIMARY KEY)"
        )
        
        assert is_modifying is True
        assert operation == 'CREATE'

    def test_detect_alter_table(self):
        """测试检测 ALTER TABLE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "ALTER TABLE users ADD COLUMN email VARCHAR(100)"
        )
        
        assert is_modifying is True
        assert operation == 'ALTER'

    def test_detect_drop_table(self):
        """测试检测 DROP TABLE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "DROP TABLE users"
        )
        
        assert is_modifying is True
        assert operation == 'DROP'

    def test_detect_truncate_table(self):
        """测试检测 TRUNCATE TABLE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "TRUNCATE TABLE users"
        )
        
        assert is_modifying is True
        assert operation == 'TRUNCATE'

    def test_detect_create_index(self):
        """测试检测 CREATE INDEX 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "CREATE INDEX idx_email ON users(email)"
        )
        
        assert is_modifying is True
        assert operation == 'CREATE'

    def test_detect_drop_index(self):
        """测试检测 DROP INDEX 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "DROP INDEX idx_email"
        )
        
        assert is_modifying is True
        assert operation == 'DROP'

    def test_detect_create_view(self):
        """测试检测 CREATE VIEW 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active'"
        )
        
        assert is_modifying is True
        assert operation == 'CREATE'

    def test_detect_with_leading_whitespace(self):
        """测试检测带前导空格的 DDL 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "  CREATE TABLE test (id INT)"
        )
        
        assert is_modifying is True
        assert operation == 'CREATE'

    def test_detect_with_lowercase(self):
        """测试检测小写的 DDL 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "create table test (id int)"
        )
        
        assert is_modifying is True
        assert operation == 'CREATE'

    def test_not_detect_select(self):
        """测试不检测 SELECT 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "SELECT * FROM users"
        )
        
        assert is_modifying is False
        assert operation == ''

    def test_not_detect_insert(self):
        """测试不检测 INSERT 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "INSERT INTO users (name) VALUES ('Alice')"
        )
        
        assert is_modifying is False

    def test_not_detect_update(self):
        """测试不检测 UPDATE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "UPDATE users SET status = 'active'"
        )
        
        assert is_modifying is False

    def test_not_detect_delete(self):
        """测试不检测 DELETE 语句"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(
            "DELETE FROM users WHERE id = 1"
        )
        
        assert is_modifying is False

    def test_detect_empty_query(self):
        """测试检测空查询"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query("")
        
        assert is_modifying is False
        assert operation == ''

    def test_detect_whitespace_only_query(self):
        """测试检测只有空格的查询"""
        is_modifying, operation = Kingbase_Loader.is_schema_modifying_query("   ")
        
        assert is_modifying is False


class TestKingbaseLoaderRefreshSchema:
    """测试人大金仓加载器的模式刷新功能"""

    @pytest.mark.asyncio
    @patch('api.loaders.kingbase_loader.db')
    @patch('api.loaders.kingbase_loader.psycopg2.connect')
    @patch('api.loaders.kingbase_loader.load_to_graph')
    async def test_refresh_graph_schema_success(self, mock_load_to_graph, mock_connect, mock_db):
        """测试成功刷新图模式"""
        # 模拟图数据库
        mock_graph = AsyncMock()
        mock_db.select_graph.return_value = mock_graph
        
        # 模拟数据库连接
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('users', '用户表')]
        
        # 模拟子方法
        with patch.object(Kingbase_Loader, 'extract_columns_info', return_value={}), \
             patch.object(Kingbase_Loader, 'extract_foreign_keys', return_value=[]), \
             patch.object(Kingbase_Loader, 'extract_relationships', return_value={}):
            
            success, message = await Kingbase_Loader.refresh_graph_schema(
                "test_prefix_testdb",
                "kingbase://user:pass@localhost:54321/testdb"
            )
        
        # 验证刷新成功
        assert success is True
        mock_graph.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.loaders.kingbase_loader.db')
    async def test_refresh_graph_schema_failure(self, mock_db):
        """测试刷新图模式失败"""
        # 模拟图删除失败
        mock_graph = AsyncMock()
        mock_graph.delete.side_effect = Exception("删除失败")
        mock_db.select_graph.return_value = mock_graph
        
        success, message = await Kingbase_Loader.refresh_graph_schema(
            "test_prefix_testdb",
            "kingbase://user:pass@localhost:54321/testdb"
        )
        
        # 验证刷新失败
        assert success is False
        assert "错误" in message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
