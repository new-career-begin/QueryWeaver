"""人大金仓数据库加载器，用于将数据库模式加载到 FalkorDB 图数据库中。"""

import re
import datetime
import decimal
import logging
from typing import AsyncGenerator, Dict, Any, List, Tuple

import psycopg2
from psycopg2 import sql
import tqdm

from api.loaders.base_loader import BaseLoader  # pylint: disable=import-error
from api.loaders.graph_loader import load_to_graph  # pylint: disable=import-error

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Kingbase_QueryError(Exception):
    """人大金仓数据库查询执行失败时抛出的异常。"""


class Kingbase_ConnectionError(Exception):
    """人大金仓数据库连接失败时抛出的异常。"""


class Kingbase_Loader(BaseLoader):
    """
    人大金仓数据库加载器
    
    人大金仓基于 PostgreSQL，因此复用 PostgreSQL 的大部分实现。
    支持 kingbase:// 和 postgresql:// 连接 URL 格式。
    """

    # DDL 操作关键字，用于检测模式修改操作
    SCHEMA_MODIFYING_OPERATIONS = {
        'CREATE', 'ALTER', 'DROP', 'RENAME', 'TRUNCATE'
    }

    # 模式修改操作的正则模式
    SCHEMA_PATTERNS = [
        r'^\s*CREATE\s+TABLE',
        r'^\s*CREATE\s+INDEX',
        r'^\s*CREATE\s+UNIQUE\s+INDEX',
        r'^\s*ALTER\s+TABLE',
        r'^\s*DROP\s+TABLE',
        r'^\s*DROP\s+INDEX',
        r'^\s*RENAME\s+TABLE',
        r'^\s*TRUNCATE\s+TABLE',
        r'^\s*CREATE\s+VIEW',
        r'^\s*DROP\s+VIEW',
        r'^\s*CREATE\s+SCHEMA',
        r'^\s*DROP\s+SCHEMA',
    ]

    @staticmethod
    def _execute_sample_query(
        cursor, table_name: str, col_name: str, sample_size: int = 3
    ) -> List[Any]:
        """
        执行查询以获取列的随机示例值
        
        人大金仓实现使用 ORDER BY RANDOM() 进行随机采样。
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            col_name: 列名
            sample_size: 示例数量，默认为 3
            
        Returns:
            示例值列表
        """
        query = sql.SQL("""
            SELECT {col}
            FROM (
                SELECT DISTINCT {col}
                FROM {table}
                WHERE {col} IS NOT NULL
            ) AS distinct_vals
            ORDER BY RANDOM()
            LIMIT %s;
        """).format(
            col=sql.Identifier(col_name),
            table=sql.Identifier(table_name)
        )
        cursor.execute(query, (sample_size,))
        sample_results = cursor.fetchall()
        return [row[0] for row in sample_results if row[0] is not None]

    @staticmethod
    def _serialize_value(value):
        """
        将非 JSON 可序列化的值转换为 JSON 可序列化格式
        
        Args:
            value: 要序列化的值
            
        Returns:
            JSON 可序列化的值
        """
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()
        if isinstance(value, datetime.time):
            return value.isoformat()
        if isinstance(value, decimal.Decimal):
            return float(value)
        if value is None:
            return None
        return value

    @staticmethod
    async def load(prefix: str, connection_url: str) -> AsyncGenerator[tuple[bool, str], None]:
        """
        从人大金仓数据库加载模式数据到图数据库
        
        Args:
            prefix: 用户 ID 前缀
            connection_url: 人大金仓数据库连接 URL，格式：
                          kingbase://username:password@host:port/database
                          或 postgresql://username:password@host:port/database
                          
        Yields:
            tuple[bool, str]: (成功标志, 进度消息)
            
        工作流程：
            1. 解析连接 URL
            2. 建立数据库连接
            3. 提取表信息
            4. 提取关系信息
            5. 加载到图数据库
            6. 关闭连接
        """
        import json
        
        conn = None
        cursor = None
        
        try:
            # 解析连接 URL
            yield True, "正在解析连接参数..."
            db_url = Kingbase_Loader._parse_connection_url(connection_url)
            
            # 从连接 URL 提取数据库名和主机信息用于日志
            db_name = connection_url.split('/')[-1]
            if '?' in db_name:
                db_name = db_name.split('?')[0]
            
            # 提取主机和端口信息用于日志（不包含密码）
            import re
            url_pattern = r'(?:kingbase|postgresql)://([^:]+):([^@]+)@([^:]+):(\d+)/'
            match = re.match(url_pattern, connection_url)
            if match:
                username, _, host, port = match.groups()
                host_info = f"{host}:{port}"
            else:
                host_info = "未知主机"
            
            # 建立数据库连接
            yield True, f"正在连接到人大金仓数据库 {host_info}..."
            logging.info(
                f"连接人大金仓数据库: {host_info}/{db_name}"
            )
            
            try:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                
                # 记录连接成功日志
                logging.info(json.dumps({
                    "event": "connection_success",
                    "db_type": "kingbase",
                    "host": host_info,
                    "database": db_name,
                    "user_id": prefix,
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                
                logging.info(f"成功连接到人大金仓数据库: {db_name}")
                yield True, "数据库连接成功"
                
            except psycopg2.OperationalError as e:
                # 连接错误（主机不可达、端口错误、网络问题等）
                error_msg = f"连接人大金仓数据库失败: {str(e)}"
                logging.error(json.dumps({
                    "event": "connection_error",
                    "db_type": "kingbase",
                    "host": host_info,
                    "database": db_name,
                    "error_type": "OperationalError",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                yield False, "无法连接到人大金仓数据库，请检查主机地址、端口和网络连接"
                return
                
            except psycopg2.DatabaseError as e:
                # 数据库错误（认证失败、数据库不存在等）
                error_msg = f"人大金仓数据库认证失败: {str(e)}"
                logging.error(json.dumps({
                    "event": "connection_error",
                    "db_type": "kingbase",
                    "host": host_info,
                    "database": db_name,
                    "error_type": "DatabaseError",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                yield False, "数据库认证失败，请检查用户名、密码和数据库名称"
                return

            # 获取所有表信息
            yield True, "正在提取表信息..."
            entities = Kingbase_Loader.extract_tables_info(cursor)
            
            logging.info(f"成功提取 {len(entities)} 个表的信息")

            yield True, "正在提取关系信息..."
            # 获取所有关系信息
            relationships = Kingbase_Loader.extract_relationships(cursor)
            
            logging.info(f"成功提取 {len(relationships)} 个外键关系")

            # 关闭数据库连接
            cursor.close()
            conn.close()
            logging.info("人大金仓数据库连接已关闭")

            yield True, "正在加载数据到图数据库..."
            # 加载数据到图数据库
            # 从 base64 编码的 user_id 解码出 user_email
            import base64
            try:
                user_email = base64.b64decode(prefix).decode('utf-8')
            except Exception:  # pylint: disable=broad-exception-caught
                user_email = None
            
            await load_to_graph(
                f"{prefix}_{db_name}",
                entities,
                relationships,
                db_name=db_name,
                db_url=connection_url,
                user_email=user_email
            )

            yield True, (
                f"人大金仓数据库模式加载成功。共发现 {len(entities)} 个表。"
            )

        except Kingbase_ConnectionError as e:
            logging.error(f"人大金仓数据库连接错误: {str(e)}")
            yield False, str(e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error(f"加载人大金仓数据库模式时出错: {str(e)}")
            logging.exception("详细错误信息:")
            yield False, "加载人大金仓数据库模式失败，请检查日志获取详细信息"
        finally:
            # 确保关闭数据库连接
            if cursor:
                try:
                    cursor.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

    @staticmethod
    def _parse_connection_url(connection_url: str) -> str:
        """
        解析人大金仓连接 URL
        
        将 kingbase:// 前缀转换为 postgresql:// 以兼容 psycopg2 驱动。
        支持以下格式：
        - kingbase://username:password@host:port/database
        - postgresql://username:password@host:port/database
        
        Args:
            connection_url: 原始连接 URL
            
        Returns:
            psycopg2 兼容的连接 URL
            
        Raises:
            Kingbase_ConnectionError: URL 格式不正确时抛出
        """
        import re
        
        if not connection_url or not connection_url.strip():
            logging.error("连接 URL 为空")
            raise Kingbase_ConnectionError("连接 URL 不能为空")
        
        # 验证 URL 格式
        # 支持 kingbase:// 和 postgresql:// 前缀
        url_pattern = r'^(kingbase|postgresql)://[^:]+:[^@]+@[^:]+:\d+/.+'
        if not re.match(url_pattern, connection_url):
            logging.error(f"人大金仓数据库连接 URL 格式不正确: {connection_url}")
            raise Kingbase_ConnectionError(
                "连接 URL 格式不正确，应为: "
                "kingbase://username:password@host:port/database 或 "
                "postgresql://username:password@host:port/database"
            )
        
        # 将 kingbase:// 转换为 postgresql://
        if connection_url.startswith('kingbase://'):
            parsed_url = connection_url.replace('kingbase://', 'postgresql://', 1)
            logging.info("已将 kingbase:// URL 转换为 postgresql:// 格式")
            return parsed_url
        
        # 如果已经是 postgresql:// 格式，直接返回
        if connection_url.startswith('postgresql://'):
            logging.info("使用 postgresql:// URL 连接人大金仓数据库")
            return connection_url
        
        # 不应该到达这里，但为了安全起见
        logging.warning(f"未知的 URL 格式: {connection_url}")
        return connection_url

    @staticmethod
    def extract_tables_info(cursor) -> Dict[str, Any]:
        """
        从人大金仓数据库提取表和列信息
        
        Args:
            cursor: 数据库游标
            
        Returns:
            包含表信息的字典
        """
        entities = {}

        # 获取 public schema 中的所有表
        cursor.execute("""
            SELECT table_name, table_comment
            FROM information_schema.tables t
            LEFT JOIN (
                SELECT schemaname, tablename, description as table_comment
                FROM pg_tables pt
                JOIN pg_class pc ON pc.relname = pt.tablename
                JOIN pg_description pd ON pd.objoid = pc.oid AND pd.objsubid = 0
                WHERE pt.schemaname = 'public'
            ) tc ON tc.tablename = t.table_name
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name;
        """)

        tables = cursor.fetchall()

        for table_name, table_comment in tqdm.tqdm(tables, desc="正在提取表信息"):
            table_name = table_name.strip()

            # 获取该表的列信息
            columns_info = Kingbase_Loader.extract_columns_info(cursor, table_name)

            # 获取该表的外键
            foreign_keys = Kingbase_Loader.extract_foreign_keys(cursor, table_name)

            # 生成表描述
            table_description = table_comment if table_comment else f"表: {table_name}"

            # 获取列描述用于批量嵌入
            col_descriptions = [col_info['description'] for col_info in columns_info.values()]

            entities[table_name] = {
                'description': table_description,
                'columns': columns_info,
                'foreign_keys': foreign_keys,
                'col_descriptions': col_descriptions
            }

        return entities

    @staticmethod
    def extract_columns_info(cursor, table_name: str) -> Dict[str, Any]:
        """
        提取指定表的列信息
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            
        Returns:
            包含列信息的字典
        """
        cursor.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE
                    WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                    WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                    ELSE 'NONE'
                END as key_type,
                COALESCE(pgd.description, '') as column_comment
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
            ) pk ON pk.column_name = c.column_name
            LEFT JOIN (
                SELECT ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.table_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
            ) fk ON fk.column_name = c.column_name
            LEFT JOIN pg_class pc ON pc.relname = c.table_name
            LEFT JOIN pg_attribute pa ON pa.attrelid = pc.oid AND pa.attname = c.column_name
            LEFT JOIN pg_description pgd ON pgd.objoid = pc.oid AND pgd.objsubid = pa.attnum
            WHERE c.table_name = %s
            AND c.table_schema = 'public'
            ORDER BY c.ordinal_position;
        """, (table_name, table_name, table_name))

        columns = cursor.fetchall()
        columns_info = {}

        for col_name, data_type, is_nullable, column_default, key_type, column_comment in columns:
            col_name = col_name.strip()

            # 生成列描述
            description_parts = []
            if column_comment:
                description_parts.append(column_comment)
            else:
                description_parts.append(f"列 {col_name}，类型为 {data_type}")

            if key_type != 'NONE':
                description_parts.append(f"({key_type})")

            if is_nullable == 'NO':
                description_parts.append("(NOT NULL)")

            if column_default:
                description_parts.append(f"(默认值: {column_default})")

            # 提取列的示例值（单独存储，不包含在描述中）
            sample_values = Kingbase_Loader.extract_sample_values_for_column(
                cursor, table_name, col_name
            )

            columns_info[col_name] = {
                'type': data_type,
                'null': is_nullable,
                'key': key_type,
                'description': ' '.join(description_parts),
                'default': column_default,
                'sample_values': sample_values
            }

        return columns_info

    @staticmethod
    def extract_foreign_keys(cursor, table_name: str) -> List[Dict[str, str]]:
        """
        提取指定表的外键信息
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            
        Returns:
            外键字典列表
        """
        cursor.execute("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            AND tc.table_schema = 'public';
        """, (table_name,))

        foreign_keys = []
        for constraint_name, column_name, foreign_table, foreign_column in cursor.fetchall():
            foreign_keys.append({
                'constraint_name': constraint_name.strip(),
                'column': column_name.strip(),
                'referenced_table': foreign_table.strip(),
                'referenced_column': foreign_column.strip()
            })

        return foreign_keys

    @staticmethod
    def extract_relationships(cursor) -> Dict[str, List[Dict[str, str]]]:
        """
        从数据库提取所有关系信息
        
        Args:
            cursor: 数据库游标
            
        Returns:
            包含关系信息的字典
        """
        cursor.execute("""
            SELECT
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name, tc.constraint_name;
        """)

        relationships = {}
        for (table_name, constraint_name, column_name,
             foreign_table, foreign_column) in cursor.fetchall():
            table_name = table_name.strip()
            constraint_name = constraint_name.strip()

            if constraint_name not in relationships:
                relationships[constraint_name] = []

            relationships[constraint_name].append({
                'from': table_name,
                'to': foreign_table.strip(),
                'source_column': column_name.strip(),
                'target_column': foreign_column.strip(),
                'note': f'外键约束: {constraint_name}'
            })

        return relationships

    @staticmethod
    def is_schema_modifying_query(sql_query: str) -> Tuple[bool, str]:
        """
        检测 SQL 查询是否修改数据库模式
        
        Args:
            sql_query: 要检查的 SQL 查询
            
        Returns:
            (是否修改模式, 操作类型) 的元组
        """
        if not sql_query or not sql_query.strip():
            return False, ""

        # 清理和规范化查询
        normalized_query = sql_query.strip().upper()

        # 检查基本的 DDL 操作
        first_word = normalized_query.split()[0] if normalized_query.split() else ""
        if first_word in Kingbase_Loader.SCHEMA_MODIFYING_OPERATIONS:
            # 使用模式匹配进行更精确的检测
            for pattern in Kingbase_Loader.SCHEMA_PATTERNS:
                if re.match(pattern, normalized_query, re.IGNORECASE):
                    return True, first_word

            # 如果是已知的 DDL 操作但不匹配特定模式，
            # 仍然认为它是模式修改操作（宁可保守）
            return True, first_word

        return False, ""

    @staticmethod
    async def refresh_graph_schema(graph_id: str, db_url: str) -> Tuple[bool, str]:
        """
        通过清除现有数据并从数据库重新加载来刷新图模式
        
        Args:
            graph_id: 要刷新的图 ID
            db_url: 数据库连接 URL
            
        Returns:
            (成功标志, 消息) 的元组
        """
        try:
            logging.info("检测到模式修改。正在刷新图模式。")

            # 在此处导入以避免循环导入
            from api.extensions import db  # pylint: disable=import-error,import-outside-toplevel

            # 清除现有图数据
            # 在重新加载之前删除当前图
            graph = db.select_graph(graph_id)
            await graph.delete()

            # 从 graph_id 提取前缀（移除数据库名部分）
            # graph_id 格式通常为 "prefix_database_name"
            parts = graph_id.split('_')
            if len(parts) >= 2:
                # 通过连接除最后一个部分外的所有部分来重建前缀
                prefix = '_'.join(parts[:-1])
            else:
                prefix = graph_id

            # 复用现有的 load 方法重新加载模式
            success = False
            message = ""
            async for status, msg in Kingbase_Loader.load(prefix, db_url):
                success = status
                message = msg

            if success:
                logging.info("图模式刷新成功。")
                return True, message

            logging.error("模式刷新失败")
            return False, "重新加载模式失败"

        except Exception as e:  # pylint: disable=broad-exception-caught
            # 记录错误并返回失败
            logging.error("刷新图模式时出错: %s", str(e))
            error_msg = "刷新图模式时出错"
            logging.error(error_msg)
            return False, error_msg

    @staticmethod
    def execute_sql_query(sql_query: str, db_url: str) -> List[Dict[str, Any]]:
        """
        在人大金仓数据库上执行 SQL 查询并返回结果
        
        Args:
            sql_query: 要执行的 SQL 查询
            db_url: 人大金仓连接 URL，格式：
                    kingbase://username:password@host:port/database
                    或 postgresql://username:password@host:port/database
                    
        Returns:
            包含查询结果的字典列表
            
        Raises:
            Kingbase_ConnectionError: 连接错误
            Kingbase_QueryError: 查询执行错误
        """
        import json
        import time
        
        conn = None
        cursor = None
        start_time = time.time()
        
        try:
            # 将 kingbase:// URL 转换为 postgresql:// 以兼容 psycopg2
            parsed_url = Kingbase_Loader._parse_connection_url(db_url)
            
            # 提取数据库信息用于日志（不包含密码）
            import re
            url_pattern = r'(?:kingbase|postgresql)://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(url_pattern, db_url)
            if match:
                username, _, host, port, database = match.groups()
                host_info = f"{host}:{port}"
                db_name = database.split('?')[0] if '?' in database else database
            else:
                host_info = "未知主机"
                db_name = "未知数据库"
            
            # 记录查询开始日志
            logging.info(json.dumps({
                "event": "query_start",
                "db_type": "kingbase",
                "host": host_info,
                "database": db_name,
                "sql": sql_query[:200],  # 只记录前 200 个字符
                "timestamp": datetime.datetime.now().isoformat()
            }))
            
            # 连接到人大金仓数据库
            try:
                conn = psycopg2.connect(parsed_url)
                cursor = conn.cursor()
                
            except psycopg2.OperationalError as e:
                error_msg = f"连接人大金仓数据库失败: {str(e)}"
                logging.error(json.dumps({
                    "event": "connection_error",
                    "db_type": "kingbase",
                    "host": host_info,
                    "database": db_name,
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                raise Kingbase_ConnectionError(error_msg) from e
                
            except psycopg2.DatabaseError as e:
                error_msg = f"人大金仓数据库认证失败: {str(e)}"
                logging.error(json.dumps({
                    "event": "connection_error",
                    "db_type": "kingbase",
                    "host": host_info,
                    "database": db_name,
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                raise Kingbase_ConnectionError(error_msg) from e

            # 执行 SQL 查询
            try:
                cursor.execute(sql_query)

                # 检查查询是否返回结果（SELECT 查询）
                if cursor.description is not None:
                    # 这是返回行的 SELECT 查询或类似查询
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    result_list = []
                    for row in results:
                        # 序列化每个值以确保 JSON 兼容性
                        serialized_row = {
                            columns[i]: Kingbase_Loader._serialize_value(row[i])
                            for i in range(len(columns))
                        }
                        result_list.append(serialized_row)
                    
                    # 记录查询成功日志
                    execution_time = time.time() - start_time
                    logging.info(json.dumps({
                        "event": "query_success",
                        "db_type": "kingbase",
                        "sql": sql_query[:200],
                        "row_count": len(result_list),
                        "execution_time": round(execution_time, 3),
                        "timestamp": datetime.datetime.now().isoformat()
                    }))
                    
                else:
                    # 这是 INSERT、UPDATE、DELETE 或其他非 SELECT 查询
                    # 返回有关操作的信息
                    affected_rows = cursor.rowcount
                    sql_type = sql_query.strip().split()[0].upper()

                    if sql_type in ['INSERT', 'UPDATE', 'DELETE']:
                        result_list = [{
                            "operation": sql_type,
                            "affected_rows": affected_rows,
                            "status": "success"
                        }]
                    else:
                        # 对于其他类型的查询（CREATE、DROP 等）
                        result_list = [{
                            "operation": sql_type,
                            "status": "success"
                        }]
                    
                    # 记录操作成功日志
                    execution_time = time.time() - start_time
                    logging.info(json.dumps({
                        "event": "query_success",
                        "db_type": "kingbase",
                        "operation": sql_type,
                        "affected_rows": affected_rows,
                        "execution_time": round(execution_time, 3),
                        "timestamp": datetime.datetime.now().isoformat()
                    }))

                # 提交写操作的事务
                conn.commit()

                return result_list
                
            except psycopg2.Error as e:
                # 查询执行错误
                execution_time = time.time() - start_time
                logging.error(json.dumps({
                    "event": "query_error",
                    "db_type": "kingbase",
                    "sql": sql_query[:200],
                    "error": str(e),
                    "execution_time": round(execution_time, 3),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                
                # 回滚事务
                if conn:
                    conn.rollback()
                
                raise Kingbase_QueryError(f"查询执行失败: {str(e)}") from e

        except Kingbase_ConnectionError:
            # 重新抛出连接错误
            raise
        except Kingbase_QueryError:
            # 重新抛出查询错误
            raise
        except Exception as e:
            # 捕获其他未预期的错误
            execution_time = time.time() - start_time
            logging.error(json.dumps({
                "event": "unexpected_error",
                "db_type": "kingbase",
                "sql": sql_query[:200] if sql_query else "",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": round(execution_time, 3),
                "timestamp": datetime.datetime.now().isoformat()
            }))
            
            raise Kingbase_QueryError(f"执行查询时发生错误: {str(e)}") from e
            
        finally:
            # 确保关闭数据库连接
            if cursor:
                try:
                    cursor.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
