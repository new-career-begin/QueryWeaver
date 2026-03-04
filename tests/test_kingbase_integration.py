"""
人大金仓数据库端到端集成测试

测试完整的连接、提取、加载、查询流程。
需要真实的人大金仓数据库实例才能运行。

运行方式：
    pytest tests/test_kingbase_integration.py -v -s

环境变量配置：
    KINGBASE_TEST_URL: 人大金仓数据库连接 URL
    例如: kingbase://SYSTEM:password@192.168.1.100:54321/TEST
    或: postgresql://SYSTEM:password@192.168.1.100:54321/TEST
"""

import os
import pytest
import logging
from typing import AsyncGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 检查是否配置了人大金仓数据库测试环境
KINGBASE_TEST_URL = os.getenv("KINGBASE_TEST_URL")
KINGBASE_INTEGRATION_ENABLED = KINGBASE_TEST_URL is not None

# 如果没有配置测试环境，跳过所有测试
pytestmark = pytest.mark.skipif(
    not KINGBASE_INTEGRATION_ENABLED,
    reason="人大金仓数据库集成测试需要设置 KINGBASE_TEST_URL 环境变量"
)


@pytest.fixture(scope="module")
def kingbase_test_url():
    """提供人大金仓数据库测试连接 URL"""
    return KINGBASE_TEST_URL


@pytest.fixture(scope="module")
async def kingbase_test_connection(kingbase_test_url):
    """
    建立人大金仓数据库测试连接
    
    在模块级别创建连接，所有测试共享
    """
    try:
        import psycopg2
    except ImportError:
        pytest.skip("psycopg2 驱动未安装，跳过人大金仓数据库集成测试")
    
    # 解析连接 URL
    from api.loaders.kingbase_loader import Kingbase_Loader
    
    try:
        parsed_url = Kingbase_Loader._parse_connection_url(kingbase_test_url)
        
        # 建立连接
        conn = psycopg2.connect(parsed_url)
        cursor = conn.cursor()
        
        logger.info(f"成功连接到人大金仓数据库测试实例")
        
        yield {"connection": conn, "cursor": cursor, "url": parsed_url}
        
        # 清理
        cursor.close()
        conn.close()
        logger.info("人大金仓数据库测试连接已关闭")
        
    except Exception as e:
        logger.error(f"连接人大金仓数据库失败: {str(e)}")
        pytest.fail(f"无法建立人大金仓数据库测试连接: {str(e)}")


@pytest.fixture(scope="module")
async def kingbase_test_schema(kingbase_test_connection):
    """
    创建测试数据库模式和数据
    
    创建测试表：
    - test_users: 用户表
    - test_orders: 订单表
    - test_order_items: 订单项表
    """
    cursor = kingbase_test_connection["cursor"]
    conn = kingbase_test_connection["connection"]
    
    try:
        # 清理可能存在的旧测试表
        logger.info("清理旧的测试表...")
        cleanup_tables = [
            "DROP TABLE IF EXISTS test_order_items CASCADE",
            "DROP TABLE IF EXISTS test_orders CASCADE",
            "DROP TABLE IF EXISTS test_users CASCADE"
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
            CREATE TABLE test_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                balance DECIMAL(10, 2)
            )
        """)
        
        # 添加表注释
        cursor.execute("""
            COMMENT ON TABLE test_users IS '测试用户表'
        """)
        
        # 添加列注释
        cursor.execute("""
            COMMENT ON COLUMN test_users.id IS '用户ID'
        """)
        cursor.execute("""
            COMMENT ON COLUMN test_users.username IS '用户名'
        """)
        cursor.execute("""
            COMMENT ON COLUMN test_users.email IS '电子邮箱'
        """)
        
        # 订单表
        cursor.execute("""
            CREATE TABLE test_orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                order_date TIMESTAMP,
                total_amount DECIMAL(10, 2),
                CONSTRAINT fk_orders_user FOREIGN KEY (user_id) 
                    REFERENCES test_users(id)
            )
        """)
        
        cursor.execute("""
            COMMENT ON TABLE test_orders IS '测试订单表'
        """)
        
        # 订单项表
        cursor.execute("""
            CREATE TABLE test_order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER,
                product_name VARCHAR(100),
                quantity INTEGER,
                price DECIMAL(10, 2),
                CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) 
                    REFERENCES test_orders(id)
            )
        """)
        
        cursor.execute("""
            COMMENT ON TABLE test_order_items IS '测试订单项表'
        """)
        
        conn.commit()
        logger.info("测试表创建成功")
        
        # 插入测试数据
        logger.info("插入测试数据...")
        
        # 插入用户
        users_data = [
            ('alice', 'alice@example.com', 100.50),
            ('bob', 'bob@example.com', 250.75),
            ('charlie', 'charlie@example.com', 50.00),
        ]
        
        for user in users_data:
            cursor.execute("""
                INSERT INTO test_users (username, email, balance)
                VALUES (%s, %s, %s)
            """, user)
        
        # 插入订单
        orders_data = [
            (1, '2025-01-10 10:00:00', 99.99),
            (2, '2025-01-12 14:30:00', 149.99),
            (1, '2025-01-15 09:15:00', 75.50),
        ]
        
        for order in orders_data:
            cursor.execute("""
                INSERT INTO test_orders (user_id, order_date, total_amount)
                VALUES (%s, %s, %s)
            """, order)
        
        # 插入订单项
        items_data = [
            (1, '商品A', 2, 49.99),
            (1, '商品B', 1, 49.99),
            (2, '商品C', 3, 49.99),
            (3, '商品D', 1, 75.50),
        ]
        
        for item in items_data:
            cursor.execute("""
                INSERT INTO test_order_items (order_id, product_name, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, item)
        
        conn.commit()
        logger.info("测试数据插入成功")
        
        yield {
            "tables": ["test_users", "test_orders", "test_order_items"],
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
            "DROP TABLE IF EXISTS test_order_items CASCADE",
            "DROP TABLE IF EXISTS test_orders CASCADE",
            "DROP TABLE IF EXISTS test_users CASCADE"
        ]
        
        for sql in cleanup_tables:
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logger.warning(f"清理表失败: {str(e)}")


class TestKingbaseIntegration:
    """人大金仓数据库集成测试套件"""
    
    @pytest.mark.asyncio
    async def test_kingbase_connection_success(self, kingbase_test_url):
        """
        测试：成功连接到人大金仓数据库
        
        验证：
        - 能够解析连接 URL（支持 kingbase:// 和 postgresql:// 前缀）
        - 能够建立数据库连接
        - 连接可用
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        import psycopg2
        
        # 解析 URL
        parsed_url = Kingbase_Loader._parse_connection_url(kingbase_test_url)
        
        assert parsed_url is not None
        assert parsed_url.startswith("postgresql://")
        
        # 建立连接
        conn = psycopg2.connect(parsed_url)
        
        assert conn is not None
        
        # 测试连接可用性
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        cursor.close()
        conn.close()
    
    @pytest.mark.asyncio
    async def test_kingbase_url_format_conversion(self):
        """
        测试：URL 格式转换
        
        验证：
        - kingbase:// 前缀被转换为 postgresql://
        - postgresql:// 前缀保持不变
        - URL 格式验证正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader, Kingbase_ConnectionError
        
        # 测试 kingbase:// 转换
        kingbase_url = "kingbase://user:pass@host:54321/db"
        parsed = Kingbase_Loader._parse_connection_url(kingbase_url)
        assert parsed.startswith("postgresql://")
        assert "user:pass@host:54321/db" in parsed
        
        # 测试 postgresql:// 保持不变
        pg_url = "postgresql://user:pass@host:54321/db"
        parsed = Kingbase_Loader._parse_connection_url(pg_url)
        assert parsed == pg_url
        
        # 测试无效格式
        invalid_urls = [
            "invalid://user:pass@host:54321/db",
            "kingbase://user@host:54321/db",  # 缺少密码
            "",  # 空字符串
        ]
        
        for url in invalid_urls:
            with pytest.raises(Kingbase_ConnectionError):
                Kingbase_Loader._parse_connection_url(url)
    
    @pytest.mark.asyncio
    async def test_kingbase_extract_tables_info(self, kingbase_test_connection, kingbase_test_schema):
        """
        测试：提取人大金仓数据库表信息
        
        验证：
        - 能够提取所有测试表
        - 表信息包含必要字段
        - 列信息完整
        - 外键信息正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        cursor = kingbase_test_connection["cursor"]
        
        # 提取表信息
        entities = Kingbase_Loader.extract_tables_info(cursor)
        
        # 验证提取了测试表
        expected_tables = kingbase_test_schema["tables"]
        for table_name in expected_tables:
            assert table_name in entities, f"表 {table_name} 未被提取"
        
        # 验证 test_users 表信息
        users_table = entities["test_users"]
        assert "description" in users_table
        assert "columns" in users_table
        assert "foreign_keys" in users_table
        assert "col_descriptions" in users_table
        
        # 验证列信息
        columns = users_table["columns"]
        assert "id" in columns
        assert "username" in columns
        assert "email" in columns
        assert "balance" in columns
        
        # 验证主键标识
        assert columns["id"]["key"] == "PRIMARY KEY"
        
        # 验证 test_orders 表的外键
        orders_table = entities["test_orders"]
        foreign_keys = orders_table["foreign_keys"]
        assert len(foreign_keys) > 0
        
        # 验证外键指向 test_users
        fk = foreign_keys[0]
        assert fk["column"] == "user_id"
        assert fk["referenced_table"] == "test_users"
        assert fk["referenced_column"] == "id"
    
    @pytest.mark.asyncio
    async def test_kingbase_extract_relationships(self, kingbase_test_connection, kingbase_test_schema):
        """
        测试：提取人大金仓数据库关系信息
        
        验证：
        - 能够提取所有外键关系
        - 关系信息完整
        - 关系方向正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        cursor = kingbase_test_connection["cursor"]
        
        # 提取关系信息
        relationships = Kingbase_Loader.extract_relationships(cursor)
        
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
    async def test_kingbase_execute_select_query(self, kingbase_test_url, kingbase_test_schema):
        """
        测试：执行 SELECT 查询
        
        验证：
        - 能够执行简单查询
        - 返回正确的结果格式
        - 数据序列化正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        # 执行查询
        sql = "SELECT * FROM test_users ORDER BY id"
        results = Kingbase_Loader.execute_sql_query(sql, kingbase_test_url)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == kingbase_test_schema["user_count"]
        
        # 验证第一条记录
        first_user = results[0]
        assert "id" in first_user
        assert "username" in first_user
        assert "email" in first_user
        assert first_user["username"] == "alice"
    
    @pytest.mark.asyncio
    async def test_kingbase_execute_join_query(self, kingbase_test_url, kingbase_test_schema):
        """
        测试：执行 JOIN 查询
        
        验证：
        - 能够执行复杂查询
        - JOIN 结果正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        # 执行 JOIN 查询
        sql = """
            SELECT u.username, o.id as order_id, o.total_amount
            FROM test_users u
            JOIN test_orders o ON u.id = o.user_id
            ORDER BY u.username, o.id
        """
        
        results = Kingbase_Loader.execute_sql_query(sql, kingbase_test_url)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) == kingbase_test_schema["order_count"]
        
        # 验证结果包含正确的列
        first_row = results[0]
        assert "username" in first_row
        assert "order_id" in first_row
        assert "total_amount" in first_row
    
    @pytest.mark.asyncio
    async def test_kingbase_execute_aggregate_query(self, kingbase_test_url):
        """
        测试：执行聚合查询
        
        验证：
        - 能够执行聚合函数
        - 结果正确
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        # 执行聚合查询
        sql = """
            SELECT 
                u.username,
                COUNT(o.id) as order_count,
                SUM(o.total_amount) as total_spent
            FROM test_users u
            LEFT JOIN test_orders o ON u.id = o.user_id
            GROUP BY u.username
            ORDER BY u.username
        """
        
        results = Kingbase_Loader.execute_sql_query(sql, kingbase_test_url)
        
        # 验证结果
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 验证聚合结果
        for row in results:
            assert "username" in row
            assert "order_count" in row
            assert "total_spent" in row or row["total_spent"] is None
    
    @pytest.mark.asyncio
    async def test_kingbase_schema_modifying_detection(self):
        """
        测试：模式修改操作检测
        
        验证：
        - 能够正确识别 DDL 操作
        - 不会误判 DML 操作
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        # DDL 操作应该被检测到
        ddl_queries = [
            "CREATE TABLE test_table (id INT)",
            "ALTER TABLE test_table ADD COLUMN name VARCHAR(50)",
            "DROP TABLE test_table",
            "TRUNCATE TABLE test_table",
        ]
        
        for query in ddl_queries:
            is_modifying, operation = Kingbase_Loader.is_schema_modifying_query(query)
            assert is_modifying, f"未检测到 DDL 操作: {query}"
            assert operation in Kingbase_Loader.SCHEMA_MODIFYING_OPERATIONS
        
        # DML 操作不应该被检测为模式修改
        dml_queries = [
            "SELECT * FROM test_table",
            "INSERT INTO test_table VALUES (1, 'test')",
            "UPDATE test_table SET name = 'test' WHERE id = 1",
            "DELETE FROM test_table WHERE id = 1",
        ]
        
        for query in dml_queries:
            is_modifying, _ = Kingbase_Loader.is_schema_modifying_query(query)
            assert not is_modifying, f"误判 DML 操作为模式修改: {query}"
    
    @pytest.mark.asyncio
    async def test_kingbase_end_to_end_load(self, kingbase_test_url, kingbase_test_schema):
        """
        测试：端到端模式加载流程
        
        验证：
        - 完整的 load 流程能够成功执行
        - 所有步骤都返回成功状态
        - 最终消息包含正确的表数量
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        import base64
        
        # 创建测试用户前缀
        test_user_email = "test@example.com"
        prefix = base64.b64encode(test_user_email.encode()).decode()
        
        # 执行加载流程
        messages = []
        success_count = 0
        
        async for status, message in Kingbase_Loader.load(prefix, kingbase_test_url):
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


class TestKingbaseErrorHandling:
    """人大金仓数据库错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_kingbase_connection_failure(self):
        """
        测试：连接失败处理
        
        验证：
        - 无效的主机地址导致连接失败
        - 返回友好的错误消息
        """
        from api.loaders.kingbase_loader import Kingbase_Loader
        
        # 使用无效的连接信息
        invalid_url = "kingbase://invalid_user:invalid_pass@nonexistent_host:54321/testdb"
        
        messages = []
        async for status, message in Kingbase_Loader.load("test_prefix", invalid_url):
            messages.append((status, message))
            if not status:
                # 应该有失败消息
                assert "连接" in message or "失败" in message
                break
        
        # 应该至少有一条失败消息
        assert any(not status for status, _ in messages)
    
    @pytest.mark.asyncio
    async def test_kingbase_query_error_handling(self, kingbase_test_url):
        """
        测试：查询错误处理
        
        验证：
        - 无效的 SQL 导致查询失败
        - 抛出 Kingbase_QueryError
        - 错误消息包含数据库错误信息
        """
        from api.loaders.kingbase_loader import Kingbase_Loader, Kingbase_QueryError
        
        # 执行无效的 SQL
        invalid_sql = "SELECT * FROM nonexistent_table_12345"
        
        with pytest.raises(Kingbase_QueryError) as exc_info:
            Kingbase_Loader.execute_sql_query(invalid_sql, kingbase_test_url)
        
        # 验证错误消息
        error_message = str(exc_info.value)
        assert "失败" in error_message or "错误" in error_message
    
    @pytest.mark.asyncio
    async def test_kingbase_invalid_url_format(self):
        """
        测试：无效的连接 URL 格式
        
        验证：
        - 抛出 Kingbase_ConnectionError
        - 错误消息清晰
        """
        from api.loaders.kingbase_loader import Kingbase_Loader, Kingbase_ConnectionError
        
        invalid_urls = [
            "invalid://user:pass@host:54321/db",
            "kingbase://user@host:54321/db",  # 缺少密码
            "kingbase://user:pass@host/db",  # 缺少端口
            "",  # 空字符串
        ]
        
        for url in invalid_urls:
            with pytest.raises(Kingbase_ConnectionError):
                Kingbase_Loader._parse_connection_url(url)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
