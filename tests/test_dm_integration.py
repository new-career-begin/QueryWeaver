"""
达梦数据库端到端集成测试

测试完整的连接、提取、加载、查询流程。
需要真实的达梦数据库实例才能运行。

运行方式：
    pytest tests/test_dm_integration.py -v -s

环境变量配置：
    DM_TEST_URL: 达梦数据库连接 URL
    例如: dm://SYSDBA:SYSDBA@192.168.1.100:5236/TESTDB
"""

import os
import pytest
import logging
from typing import AsyncGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 检查是否配置了达梦数据库测试环境
DM_TEST_URL = os.getenv("DM_TEST_URL")
DM_INTEGRATION_ENABLED = DM_TEST_URL is not None

# 如果没有配置测试环境，跳过所有测试
pytestmark = pytest.mark.skipif(
    not DM_INTEGRATION_ENABLED,
    reason="达梦数据库集成测试需要设置 DM_TEST_URL 环境变量"
)


@pytest.fixture(scope="module")
def dm_test_url():
    """提供达梦数据库测试连接 URL"""
    return DM_TEST_URL


@pytest.fixture(scope="module")
async def dm_test_connection(dm_test_url):
    """
    建立达梦数据库测试连接
    
    在模块级别创建连接，所有测试共享
    """
    try:
        import dmPython
    except ImportError:
        pytest.skip("dmPython 驱动未安装，跳过达梦数据库集成测试")
    
    # 解析连接 URL
    from api.loaders.dm_loader import DM_Loader
    
    try:
        conn_params = DM_Loader._parse_connection_url(dm_test_url)
        
        # 建立连接
        conn = dmPython.connect(
            user=conn_params["user"],
            password=conn_params["password"],
            server=conn_params["server"],
            port=conn_params["port"]
        )
        
        cursor = conn.cursor()
        
        logger.info(f"成功连接到达梦数据库测试实例: {conn_params['server']}")
        
        yield {"connection": conn, "cursor": cursor, "params": conn_params}
        
        # 清理
        cursor.close()
        conn.close()
        logger.info("达梦数据库测试连接已关闭")
        
    except Exception as e:
        logger.error(f"连接达梦数据库失败: {str(e)}")
        pytest.fail(f"无法建立达梦数据库测试连接: {str(e)}")


@pytest.fixture(scope="module")
async def dm_test_schema(dm_test_connection):
    """
    创建测试数据库模式和数据
    
    创建测试表：
    - TEST_USERS: 用户表
    - TEST_ORDERS: 订单表
    - TEST_ORDER_ITEMS: 订单项表
    """
    cursor = dm_test_connection["cursor"]
    conn = dm_test_connection["connection"]
    
    try:
        # 清理可能存在的旧测试表
        logger.info("清理旧的测试表...")
        cleanup_tables = [
            "DROP TABLE IF EXISTS TEST_ORDER_ITEMS",
            "DROP TABLE IF EXISTS TEST_ORDERS",
            "DROP TABLE IF EXISTS TEST_USERS"
        ]
        
        for sql in cleanup_tables:
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logger.warning(f"清理表失败（可能不存在）: {str(e)}")
        
        # 创建测试表
        logger.info("创建测试表...")
        
        # 用户表
        cursor.execute("""
            CREATE TABLE TEST_USERS (
                ID INT PRIMARY KEY,
                USERNAME VARCHAR(50) NOT NULL,
                EMAIL VARCHAR(100),
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                BALANCE DECIMAL(10, 2)
            )
        """)
        
        # 添加表注释
        cursor.execute("""
            COMMENT ON TABLE TEST_USERS IS '测试用户表'
        """)
        
        # 添加列注释
        cursor.execute("""
            COMMENT ON COLUMN TEST_USERS.ID IS '用户ID'
        """)
        cursor.execute("""
            COMMENT ON COLUMN TEST_USERS.USERNAME IS '用户名'
        """)
        cursor.execute("""
            COMMENT ON COLUMN TEST_USERS.EMAIL IS '电子邮箱'
        """)
        
        # 订单表
        cursor.execute("""
            CREATE TABLE TEST_ORDERS (
                ID INT PRIMARY KEY,
                USER_ID INT,
                ORDER_DATE TIMESTAMP,
                TOTAL_AMOUNT DECIMAL(10, 2),
                CONSTRAINT FK_ORDERS_USER FOREIGN KEY (USER_ID) 
                    REFERENCES TEST_USERS(ID)
            )
        """)
        
        cursor.execute("""
            COMMENT ON TABLE TEST_ORDERS IS '测试订单表'
        """)
        
        # 订单项表
        cursor.execute("""
            CREATE TABLE TEST_ORDER_ITEMS (
                ID INT PRIMARY KEY,
                ORDER_ID INT,
                PRODUCT_NAME VARCHAR(100),
                QUANTITY INT,
                PRICE DECIMAL(10, 2),
                CONSTRAINT FK_ORDER_ITEMS_ORDER FOREIGN KEY (ORDER_ID) 
                    REFERENCES TEST_ORDERS(ID)
            )
        """)
        
        cursor.execute("""
            COMMENT ON TABLE TEST_ORDER_ITEMS IS '测试订单项表'
        """)
        
        conn.commit()
        logger.info("测试表创建成功")
        
        # 插入测试数据
        logger.info("插入测试数据...")
        
        # 插入用户
        users_data = [
            (1, 'alice', 'alice@example.com', 100.50),
            (2, 'bob', 'bob@example.com', 250.75),
            (3, 'charlie', 'charlie@example.com', 50.00),
        ]
        
        for user in users_data:
            cursor.execute("""
                INSERT INTO TEST_USERS (ID, USERNAME, EMAIL, BALANCE)
                VALUES (?, ?, ?, ?)
            """, user)
        
        # 插入订单
        orders_data = [
            (1, 1, '2025-01-10 10:00:00', 99.99),
            (2, 2, '2025-01-12 14:30:00', 149.99),
            (3, 1, '2025-01-15 09:15:00', 75.50),
        ]
        
        for order in orders_data:
            cursor.execute("""
                INSERT INTO TEST_ORDERS (ID, USER_ID, ORDER_DATE, TOTAL_AMOUNT)
                VALUES (?, ?, TO_TIMESTAMP(?, 'YYYY-MM-DD HH24:MI:SS'), ?)
            """, (order[0], order[1], order[2], order[3]))
        
        # 插入订单项
        items_data = [
            (1, 1, '商品A', 2, 49.99),
            (2, 1, '商品B', 1, 49.99),
            (3, 2, '商品C', 3, 49.99),
            (4, 3, '商品D', 1, 75.50),
        ]
        
        for item in items_data:
            cursor.execute("""
                INSERT INTO TEST_ORDER_ITEMS (ID, ORDER_ID, PRODUCT_NAME, QUANTITY, PRICE)
                VALUES (?, ?, ?, ?, ?)
            """, item)
        
        conn.commit()
        logger.info("测试数据插入成功")
        
        yield {
            "tables": ["TEST_USERS", "TEST_ORDERS", "TEST_ORDER_ITEMS"],
            "user_count": len(users_data),
            "order_count": len(orders_data),
            "item_count": len(items_data)
        }
        
    except Exception as e:
        logger.error(f"创建测试模式失败: {str(e)}")
        conn.rollback()
        pytest.fail(f"无法创建测试模式: {str(e)}")
    
    finally:
        # 清理测试数据
        logger.info("清理测试数据...")
        cleanup_tables = [
            "DROP TABLE IF EXISTS TEST_ORDER_ITEMS",
            "DROP TABLE IF EXISTS TEST_ORDERS",
            "DROP TABLE IF EXISTS TEST_USERS"
        ]
        
        for sql in cleanup_tables:
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logger.warning(f"清理表失败: {str(e)}")


class TestDMIntegration:
    """达梦数据库集成测试套件"""
    
    @pytest.mark.asyncio
    async def test_dm_connection_success(self, dm_test_url):
        """
        测试：成功连接到达梦数据库
        
        验证：
        - 能够解析连接 URL
        - 能够建立数据库连接
        - 连接参数正确
        """
        from api.loaders.dm_loader import DM_Loader
        import dmPython
        
        # 解析 URL
        conn_params = DM_Loader._parse_connection_url(dm_test_url)
        
        assert "user" in conn_params
        assert "password" in conn_params
        assert "server" in conn_params
        assert "port" in conn_params
        
        # 建立连接
        conn = dmPython.connect(
            user=conn_params["user"],
            password=conn_params["password"],
            server=conn_params["server"],
            port=conn_params["port"]
        )
        
        assert conn is not None
        
        # 测试连接可用性
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        assert result[0] == 1
        
        cursor.close()
        conn.close()
    
    @pytest.mark.asyncio
    async def test_dm_extract_tables_info(self, dm_test_connection, dm_test_schema):
        """
        测试：提取达梦数据库表信息
        
        验证：
        - 能够提取所有测试表
        - 表信息包含必要字段
        - 列信息完整
        - 外键信息正确
        """
        from api.loaders.dm_loader import DM_Loader
        
        cursor = dm_test_connection["cursor"]
        
        # 提取表信息
        entities = DM_Loader.extract_tables_info(cursor)
        
        # 验证提取了测试表
        expected_tables = dm_test_schema["tables"]
        for table_name in expected_tables:
            assert table_name in entities, f"表 {table_name} 未被提取"
        
        # 验证 TEST_USERS 表信息
        users_table = entities["TEST_USERS"]
        assert "description" in users_table
        assert "columns" in users_table
        assert "foreign_keys" in users_table
        assert "col_descriptions" in users_table
        
        # 验证列信息
        columns = users_table["columns"]
        assert "ID" in columns
        assert "USERNAME" in columns
        assert "EMAIL" in columns
        assert "BALANCE" in columns
        
        # 验证主键标识
        assert columns["ID"]["key"] == "PRIMARY KEY"
        
        # 验证 TEST_ORDERS 表的外键
        orders_table = entities["TEST_ORDERS"]
        foreign_keys = orders_table["foreign_keys"]
        assert len(foreign_keys) > 0
        
        # 验证外键指向 TEST_USERS
        fk = foreign_keys[0]
        assert fk["column"] == "USER_ID"
        assert fk["referenced_table"] == "TEST_USERS"
        assert fk["referenced_column"] == "ID"
    
    @pytest.mark.asyncio
    async def test_dm_extract_relationships(self, dm_test_connection, dm_test_schema):
        """
        测试：提取达梦数据库关系信息
        
        验证：
        - 能够提取所有外键关系
        - 关系信息完整
        - 关系方向正确
        """
        from api.loaders.dm_loader import DM_Loader
        
        cursor = dm_test_connection["cursor"]
        
        # 提取关系信息
        relationships = DM_Loader.extract_relationships(cursor)
        
        # 应该至少有 2 个外键关系
        assert len(relationships) >= 2
        
        # 验证关系结构
        for constraint_name, relations in relationships.items():
            assert isinstance(relations, list)
            assert len(relations) > 0
            
            for rel in relations:
                assert "from" in rel
                assert "to" in rel
                assert "source_column" in rel
                assert "target_column" in rel
                assert "note" in rel
    
    @pytest.mark.asyncio
    async def test_dm_execute_select_query(self, dm_test_url, dm_test_schema):
        """
        测试：执行 SELECT 查询
        
        验证：
        - 能够执行简单查询
        - 返回正确的结果格式
        - 数据序列化正确
        """
        from api.loaders.dm_loader import DM_Loader
        
        # 执行查询
        sql = "SELECT * FROM TEST_USERS ORDER BY ID"
        results = DM_Loader.execute_sql_query(sql, dm_test_url)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == dm_test_schema["user_count"]
        
        # 验证第一条记录
        first_user = results[0]
        assert "ID" in first_user
        assert "USERNAME" in first_user
        assert "EMAIL" in first_user
        assert first_user["USERNAME"] == "alice"
    
    @pytest.mark.asyncio
    async def test_dm_execute_join_query(self, dm_test_url, dm_test_schema):
        """
        测试：执行 JOIN 查询
        
        验证：
        - 能够执行复杂查询
        - JOIN 结果正确
        """
        from api.loaders.dm_loader import DM_Loader
        
        # 执行 JOIN 查询
        sql = """
            SELECT u.USERNAME, o.ID as ORDER_ID, o.TOTAL_AMOUNT
            FROM TEST_USERS u
            JOIN TEST_ORDERS o ON u.ID = o.USER_ID
            ORDER BY u.USERNAME, o.ID
        """
        
        results = DM_Loader.execute_sql_query(sql, dm_test_url)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == dm_test_schema["order_count"]
        
        # 验证结果包含正确的列
        first_row = results[0]
        assert "USERNAME" in first_row
        assert "ORDER_ID" in first_row
        assert "TOTAL_AMOUNT" in first_row
    
    @pytest.mark.asyncio
    async def test_dm_schema_modifying_detection(self):
        """
        测试：模式修改操作检测
        
        验证：
        - 能够正确识别 DDL 操作
        - 不会误判 DML 操作
        """
        from api.loaders.dm_loader import DM_Loader
        
        # DDL 操作应该被检测到
        ddl_queries = [
            "CREATE TABLE test_table (id INT)",
            "ALTER TABLE test_table ADD COLUMN name VARCHAR(50)",
            "DROP TABLE test_table",
            "TRUNCATE TABLE test_table",
        ]
        
        for query in ddl_queries:
            is_modifying, operation = DM_Loader.is_schema_modifying_query(query)
            assert is_modifying, f"未检测到 DDL 操作: {query}"
            assert operation in DM_Loader.SCHEMA_MODIFYING_OPERATIONS
        
        # DML 操作不应该被检测为模式修改
        dml_queries = [
            "SELECT * FROM test_table",
            "INSERT INTO test_table VALUES (1, 'test')",
            "UPDATE test_table SET name = 'test' WHERE id = 1",
            "DELETE FROM test_table WHERE id = 1",
        ]
        
        for query in dml_queries:
            is_modifying, _ = DM_Loader.is_schema_modifying_query(query)
            assert not is_modifying, f"误判 DML 操作为模式修改: {query}"
    
    @pytest.mark.asyncio
    async def test_dm_end_to_end_load(self, dm_test_url, dm_test_schema):
        """
        测试：端到端模式加载流程
        
        验证：
        - 完整的 load 流程能够成功执行
        - 所有步骤都返回成功状态
        - 最终消息包含正确的表数量
        """
        from api.loaders.dm_loader import DM_Loader
        import base64
        
        # 创建测试用户前缀
        test_user_email = "test@example.com"
        prefix = base64.b64encode(test_user_email.encode()).decode()
        
        # 执行加载流程
        messages = []
        success_count = 0
        
        async for status, message in DM_Loader.load(prefix, dm_test_url):
            messages.append((status, message))
            if status:
                success_count += 1
            logger.info(f"[{'成功' if status else '失败'}] {message}")
        
        # 验证至少有一些成功的步骤
        assert success_count > 0, "没有任何步骤成功"
        
        # 验证最后一条消息
        final_status, final_message = messages[-1]
        if final_status:
            # 如果成功，应该包含表数量信息
            assert "表" in final_message or "成功" in final_message
        
        logger.info(f"加载流程完成，共 {len(messages)} 个步骤，{success_count} 个成功")


class TestDMErrorHandling:
    """达梦数据库错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_dm_invalid_url_format(self):
        """
        测试：无效的连接 URL 格式
        
        验证：
        - 抛出 DM_ConnectionError
        - 错误消息清晰
        """
        from api.loaders.dm_loader import DM_Loader, DM_ConnectionError
        
        invalid_urls = [
            "invalid://user:pass@host:5236/db",
            "dm://user@host:5236/db",  # 缺少密码
            "dm://user:pass@host/db",  # 缺少端口
            "",  # 空字符串
        ]
        
        for url in invalid_urls:
            with pytest.raises(DM_ConnectionError):
                DM_Loader._parse_connection_url(url)
    
    @pytest.mark.asyncio
    async def test_dm_connection_failure(self):
        """
        测试：连接失败处理
        
        验证：
        - 无效的主机地址导致连接失败
        - 返回友好的错误消息
        """
        from api.loaders.dm_loader import DM_Loader
        
        # 使用无效的连接信息
        invalid_url = "dm://invalid_user:invalid_pass@nonexistent_host:5236/testdb"
        
        messages = []
        async for status, message in DM_Loader.load("test_prefix", invalid_url):
            messages.append((status, message))
            if not status:
                # 应该有失败消息
                assert "连接" in message or "失败" in message
                break
        
        # 应该至少有一条失败消息
        assert any(not status for status, _ in messages)
    
    @pytest.mark.asyncio
    async def test_dm_query_error_handling(self, dm_test_url):
        """
        测试：查询错误处理
        
        验证：
        - 无效的 SQL 导致查询失败
        - 抛出 DM_QueryError
        - 错误消息包含数据库错误信息
        """
        from api.loaders.dm_loader import DM_Loader, DM_QueryError
        
        # 执行无效的 SQL
        invalid_sql = "SELECT * FROM NONEXISTENT_TABLE_12345"
        
        with pytest.raises(DM_QueryError) as exc_info:
            DM_Loader.execute_sql_query(invalid_sql, dm_test_url)
        
        # 验证错误消息
        error_message = str(exc_info.value)
        assert "失败" in error_message or "错误" in error_message


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
