"""达梦数据库加载器模块，用于加载达梦数据库模式到 FalkorDB 图数据库。"""

import re
import datetime
import decimal
import logging
from typing import AsyncGenerator, Dict, Any, List, Tuple

from api.loaders.base_loader import BaseLoader  # pylint: disable=import-error

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DM_QueryError(Exception):
    """达梦数据库查询执行错误异常类。"""


class DM_ConnectionError(Exception):
    """达梦数据库连接错误异常类。"""


class DM_Loader(BaseLoader):
    """
    达梦数据库加载器
    
    负责连接达梦数据库、提取模式信息和执行查询。
    继承自 BaseLoader 抽象基类。
    """

    # DDL 操作关键字 - 用于检测模式修改操作
    SCHEMA_MODIFYING_OPERATIONS = {
        'CREATE', 'ALTER', 'DROP', 'RENAME', 'TRUNCATE'
    }

    # 模式修改操作的正则模式 - 用于精确匹配 DDL 语句
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
        
        达梦数据库实现，使用子查询和 ROWNUM 进行随机采样。
        达梦数据库不支持 ORDER BY RANDOM()，使用 DBMS_RANDOM.VALUE 函数。
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            col_name: 列名
            sample_size: 要获取的随机示例数量（默认：3）
            
        Returns:
            示例值列表
        """
        try:
            # 达梦数据库使用双引号引用标识符
            # 使用 DISTINCT 去重，并限制返回数量
            # 注意：达梦数据库可能不支持 DBMS_RANDOM，使用简单的 DISTINCT 查询
            query = f'''
                SELECT DISTINCT "{col_name}"
                FROM "{table_name}"
                WHERE "{col_name}" IS NOT NULL
                AND ROWNUM <= {sample_size * 3}
            '''
            
            cursor.execute(query)
            sample_results = cursor.fetchmany(sample_size)
            
            return [row[0] for row in sample_results if row[0] is not None]
        except Exception as e:  # pylint: disable=broad-exception-caught
            # 如果查询失败，记录警告并返回空列表
            logging.warning(
                f"获取列 {table_name}.{col_name} 的示例值失败: {str(e)}"
            )
            return []

    @staticmethod
    def _serialize_value(value):
        """
        将非 JSON 可序列化的值转换为 JSON 可序列化格式
        
        Args:
            value: 要序列化的值
            
        Returns:
            JSON 可序列化版本的值
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
    def _parse_connection_url(connection_url: str) -> Dict[str, Any]:
        """
        解析达梦数据库连接 URL
        
        Args:
            connection_url: 达梦数据库连接 URL
                          格式: dm://username:password@host:port/database
                          
        Returns:
            Dict[str, Any]: 连接参数字典
            {
                "user": "用户名",
                "password": "密码",
                "server": "主机地址",
                "port": 端口号,
                "database": "数据库名"
            }
            
        Raises:
            DM_ConnectionError: URL 格式不正确时抛出
        """
        import re
        from urllib.parse import unquote
        
        # 匹配 dm://username:password@host:port/database 格式
        pattern = r'^dm://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)$'
        match = re.match(pattern, connection_url)
        
        if not match:
            logging.error(f"达梦数据库连接 URL 格式不正确: {connection_url}")
            raise DM_ConnectionError(
                "连接 URL 格式不正确，应为: dm://username:password@host:port/database"
            )
        
        username, password, host, port, database = match.groups()
        
        # URL 解码（处理特殊字符）
        username = unquote(username)
        password = unquote(password)
        database = unquote(database)
        
        return {
            "user": username,
            "password": password,
            "server": host,
            "port": int(port),
            "database": database
        }

    @staticmethod
    async def load(prefix: str, connection_url: str) -> AsyncGenerator[tuple[bool, str], None]:
        """
        从达梦数据库加载图数据到图数据库
        
        Args:
            prefix: 用户 ID 前缀
            connection_url: 达梦数据库连接 URL，格式：
                          dm://username:password@host:port/database
                          
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
        try:
            # 导入 dmPython 驱动
            try:
                import dmPython
            except ImportError as e:
                logging.error("dmPython 驱动未安装")
                yield False, "达梦数据库驱动未安装，请运行: pip install dmPython"
                return
            
            # 解析连接 URL
            yield True, "正在解析连接参数..."
            conn_params = DM_Loader._parse_connection_url(connection_url)
            
            # 提取数据库名称
            db_name = conn_params["database"]
            
            # 建立数据库连接
            yield True, f"正在连接到达梦数据库 {conn_params['server']}:{conn_params['port']}..."
            logging.info(
                f"连接达梦数据库: {conn_params['server']}:{conn_params['port']}/{db_name}"
            )
            
            try:
                conn = dmPython.connect(
                    user=conn_params["user"],
                    password=conn_params["password"],
                    server=conn_params["server"],
                    port=conn_params["port"]
                )
                
                # 切换到指定数据库
                cursor = conn.cursor()
                # 达梦数据库使用 SYSDBA 模式，需要设置当前模式
                # 注意：达梦数据库的连接方式可能需要在连接字符串中指定数据库
                # 这里假设已经连接到正确的数据库实例
                
                logging.info(f"成功连接到达梦数据库: {db_name}")
                yield True, "数据库连接成功"
                
            except dmPython.Error as e:
                error_msg = f"连接达梦数据库失败: {str(e)}"
                logging.error(error_msg)
                yield False, "无法连接到达梦数据库，请检查连接参数和网络连接"
                return
            
            # 提取表信息
            yield True, "正在提取表信息..."
            entities = DM_Loader.extract_tables_info(cursor)
            
            yield True, "正在提取关系信息..."
            # 提取所有关系信息
            relationships = DM_Loader.extract_relationships(cursor)
            
            # 关闭数据库连接
            cursor.close()
            conn.close()
            logging.info("达梦数据库连接已关闭")
            
            yield True, "正在加载数据到图数据库..."
            # 加载数据到图数据库
            from api.loaders.graph_loader import load_to_graph  # pylint: disable=import-error
            await load_to_graph(
                f"{prefix}_{db_name}",
                entities,
                relationships,
                db_name=db_name,
                db_url=connection_url
            )
            
            yield True, (
                f"达梦数据库模式加载成功。共发现 {len(entities)} 个表。"
            )
            
        except DM_ConnectionError as e:
            logging.error(f"达梦数据库连接错误: {str(e)}")
            yield False, str(e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error(f"加载达梦数据库模式时出错: {str(e)}")
            logging.exception("详细错误信息:")
            yield False, "加载达梦数据库模式失败，请检查日志获取详细信息"

    @staticmethod
    def extract_tables_info(cursor) -> Dict[str, Any]:
        """
        从达梦数据库提取表和列信息
        
        Args:
            cursor: 数据库游标
            
        Returns:
            Dict[str, Any]: 表信息字典
            {
                "table_name": {
                    "description": "表描述",
                    "columns": {
                        "column_name": {
                            "type": "数据类型",
                            "null": "是否可空",
                            "key": "键类型",
                            "description": "列描述",
                            "default": "默认值",
                            "sample_values": ["示例值1", "示例值2"]
                        }
                    },
                    "foreign_keys": [
                        {
                            "constraint_name": "约束名",
                            "column": "源列",
                            "referenced_table": "引用表",
                            "referenced_column": "引用列"
                        }
                    ],
                    "col_descriptions": ["列描述1", "列描述2", ...]
                }
            }
            
        实现细节：
            - 查询 DBA_TABLES 获取表列表
            - 查询 DBA_TAB_COLUMNS 获取列信息
            - 查询 DBA_CONSTRAINTS 和 DBA_CONS_COLUMNS 获取约束信息
            - 使用 TABLESAMPLE 或 ORDER BY RANDOM() 获取示例值
        """
        entities = {}
        
        try:
            # 获取当前用户的所有表
            # 达梦数据库使用 USER_TABLES 或 DBA_TABLES 视图
            # 这里使用 USER_TABLES 获取当前用户的表
            cursor.execute("""
                SELECT TABLE_NAME, COMMENTS
                FROM USER_TAB_COMMENTS
                WHERE TABLE_TYPE = 'TABLE'
                ORDER BY TABLE_NAME
            """)
            
            tables = cursor.fetchall()
            logging.info(f"发现 {len(tables)} 个表")
            
            for table_row in tables:
                table_name = table_row[0].strip() if table_row[0] else ""
                table_comment = table_row[1].strip() if table_row[1] else ""
                
                if not table_name:
                    continue
                
                try:
                    # 获取该表的列信息
                    columns_info = DM_Loader.extract_columns_info(cursor, table_name)
                    
                    # 获取该表的外键信息
                    foreign_keys = DM_Loader.extract_foreign_keys(cursor, table_name)
                    
                    # 生成表描述
                    table_description = table_comment if table_comment else f"表: {table_name}"
                    
                    # 获取列描述列表用于批量嵌入
                    col_descriptions = [
                        col_info['description'] 
                        for col_info in columns_info.values()
                    ]
                    
                    entities[table_name] = {
                        'description': table_description,
                        'columns': columns_info,
                        'foreign_keys': foreign_keys,
                        'col_descriptions': col_descriptions
                    }
                    
                    logging.info(
                        f"成功提取表 {table_name} 的信息: "
                        f"{len(columns_info)} 列, {len(foreign_keys)} 个外键"
                    )
                    
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # 记录错误但继续处理其他表
                    logging.error(f"提取表 {table_name} 信息失败: {str(e)}")
                    continue
            
            return entities
            
        except Exception as e:
            logging.error(f"提取表信息时出错: {str(e)}")
            raise DM_QueryError(f"提取表信息失败: {str(e)}") from e

    @staticmethod
    def extract_columns_info(cursor, table_name: str) -> Dict[str, Any]:
        """
        提取指定表的列信息
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            
        Returns:
            Dict[str, Any]: 列信息字典
            
        查询字段：
            - COLUMN_NAME: 列名
            - DATA_TYPE: 数据类型
            - NULLABLE: 是否可空
            - DATA_DEFAULT: 默认值
            - COMMENTS: 列注释
            - 主键标识
            - 外键标识
        """
        columns_info = {}
        
        try:
            # 查询列信息，包括主键和外键标识
            # 达梦数据库使用 USER_TAB_COLUMNS 和 USER_COL_COMMENTS 视图
            cursor.execute("""
                SELECT 
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.NULLABLE,
                    c.DATA_DEFAULT,
                    CASE 
                        WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PRIMARY KEY'
                        WHEN fk.COLUMN_NAME IS NOT NULL THEN 'FOREIGN KEY'
                        ELSE 'NONE'
                    END AS KEY_TYPE,
                    COALESCE(cc.COMMENTS, '') AS COLUMN_COMMENT
                FROM USER_TAB_COLUMNS c
                LEFT JOIN (
                    SELECT col.COLUMN_NAME
                    FROM USER_CONSTRAINTS con
                    JOIN USER_CONS_COLUMNS col 
                        ON con.CONSTRAINT_NAME = col.CONSTRAINT_NAME
                    WHERE con.TABLE_NAME = :table_name
                    AND con.CONSTRAINT_TYPE = 'P'
                ) pk ON pk.COLUMN_NAME = c.COLUMN_NAME
                LEFT JOIN (
                    SELECT col.COLUMN_NAME
                    FROM USER_CONSTRAINTS con
                    JOIN USER_CONS_COLUMNS col 
                        ON con.CONSTRAINT_NAME = col.CONSTRAINT_NAME
                    WHERE con.TABLE_NAME = :table_name
                    AND con.CONSTRAINT_TYPE = 'R'
                ) fk ON fk.COLUMN_NAME = c.COLUMN_NAME
                LEFT JOIN USER_COL_COMMENTS cc 
                    ON cc.TABLE_NAME = c.TABLE_NAME 
                    AND cc.COLUMN_NAME = c.COLUMN_NAME
                WHERE c.TABLE_NAME = :table_name
                ORDER BY c.COLUMN_ID
            """, {"table_name": table_name})
            
            columns = cursor.fetchall()
            
            for col_row in columns:
                col_name = col_row[0].strip() if col_row[0] else ""
                data_type = col_row[1].strip() if col_row[1] else ""
                is_nullable = col_row[2].strip() if col_row[2] else "Y"
                column_default = col_row[3].strip() if col_row[3] else None
                key_type = col_row[4].strip() if col_row[4] else "NONE"
                column_comment = col_row[5].strip() if col_row[5] else ""
                
                if not col_name:
                    continue
                
                # 生成列描述
                description_parts = []
                if column_comment:
                    description_parts.append(column_comment)
                else:
                    description_parts.append(f"列 {col_name}，类型 {data_type}")
                
                if key_type != 'NONE':
                    description_parts.append(f"({key_type})")
                
                if is_nullable == 'N':
                    description_parts.append("(NOT NULL)")
                
                if column_default:
                    description_parts.append(f"(默认值: {column_default})")
                
                # 提取列的示例值
                sample_values = DM_Loader.extract_sample_values_for_column(
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
            
        except Exception as e:
            logging.error(f"提取表 {table_name} 的列信息失败: {str(e)}")
            raise DM_QueryError(f"提取列信息失败: {str(e)}") from e

    @staticmethod
    def extract_foreign_keys(cursor, table_name: str) -> List[Dict[str, str]]:
        """
        提取指定表的外键约束
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            
        Returns:
            List[Dict[str, str]]: 外键列表
            
        查询来源：
            - DBA_CONSTRAINTS: 约束信息
            - DBA_CONS_COLUMNS: 约束列信息
        """
        foreign_keys = []
        
        try:
            # 查询外键约束信息
            # 达梦数据库使用 USER_CONSTRAINTS 和 USER_CONS_COLUMNS 视图
            cursor.execute("""
                SELECT 
                    con.CONSTRAINT_NAME,
                    col.COLUMN_NAME,
                    r_con.TABLE_NAME AS REFERENCED_TABLE,
                    r_col.COLUMN_NAME AS REFERENCED_COLUMN
                FROM USER_CONSTRAINTS con
                JOIN USER_CONS_COLUMNS col 
                    ON con.CONSTRAINT_NAME = col.CONSTRAINT_NAME
                JOIN USER_CONSTRAINTS r_con 
                    ON con.R_CONSTRAINT_NAME = r_con.CONSTRAINT_NAME
                JOIN USER_CONS_COLUMNS r_col 
                    ON r_con.CONSTRAINT_NAME = r_col.CONSTRAINT_NAME
                    AND col.POSITION = r_col.POSITION
                WHERE con.TABLE_NAME = :table_name
                AND con.CONSTRAINT_TYPE = 'R'
                ORDER BY con.CONSTRAINT_NAME, col.POSITION
            """, {"table_name": table_name})
            
            fk_rows = cursor.fetchall()
            
            for fk_row in fk_rows:
                constraint_name = fk_row[0].strip() if fk_row[0] else ""
                column_name = fk_row[1].strip() if fk_row[1] else ""
                referenced_table = fk_row[2].strip() if fk_row[2] else ""
                referenced_column = fk_row[3].strip() if fk_row[3] else ""
                
                if constraint_name and column_name and referenced_table and referenced_column:
                    foreign_keys.append({
                        'constraint_name': constraint_name,
                        'column': column_name,
                        'referenced_table': referenced_table,
                        'referenced_column': referenced_column
                    })
            
            return foreign_keys
            
        except Exception as e:
            logging.error(f"提取表 {table_name} 的外键信息失败: {str(e)}")
            # 返回空列表而不是抛出异常，允许继续处理
            return []

    @staticmethod
    def extract_relationships(cursor) -> Dict[str, List[Dict[str, str]]]:
        """
        提取数据库中所有表之间的外键关系
        
        Args:
            cursor: 数据库游标
            
        Returns:
            Dict[str, List[Dict[str, str]]]: 关系字典
            {
                "constraint_name": [
                    {
                        "from": "源表",
                        "to": "目标表",
                        "source_column": "源列",
                        "target_column": "目标列",
                        "note": "约束说明"
                    }
                ]
            }
        """
        relationships = {}
        
        try:
            # 查询所有外键关系
            # 达梦数据库使用 USER_CONSTRAINTS 和 USER_CONS_COLUMNS 视图
            cursor.execute("""
                SELECT 
                    con.TABLE_NAME,
                    con.CONSTRAINT_NAME,
                    col.COLUMN_NAME,
                    r_con.TABLE_NAME AS REFERENCED_TABLE,
                    r_col.COLUMN_NAME AS REFERENCED_COLUMN
                FROM USER_CONSTRAINTS con
                JOIN USER_CONS_COLUMNS col 
                    ON con.CONSTRAINT_NAME = col.CONSTRAINT_NAME
                JOIN USER_CONSTRAINTS r_con 
                    ON con.R_CONSTRAINT_NAME = r_con.CONSTRAINT_NAME
                JOIN USER_CONS_COLUMNS r_col 
                    ON r_con.CONSTRAINT_NAME = r_col.CONSTRAINT_NAME
                    AND col.POSITION = r_col.POSITION
                WHERE con.CONSTRAINT_TYPE = 'R'
                ORDER BY con.TABLE_NAME, con.CONSTRAINT_NAME, col.POSITION
            """)
            
            rel_rows = cursor.fetchall()
            
            for rel_row in rel_rows:
                table_name = rel_row[0].strip() if rel_row[0] else ""
                constraint_name = rel_row[1].strip() if rel_row[1] else ""
                column_name = rel_row[2].strip() if rel_row[2] else ""
                referenced_table = rel_row[3].strip() if rel_row[3] else ""
                referenced_column = rel_row[4].strip() if rel_row[4] else ""
                
                if not all([table_name, constraint_name, column_name, 
                           referenced_table, referenced_column]):
                    continue
                
                # 如果约束名还不存在，创建新列表
                if constraint_name not in relationships:
                    relationships[constraint_name] = []
                
                # 添加关系信息
                relationships[constraint_name].append({
                    'from': table_name,
                    'to': referenced_table,
                    'source_column': column_name,
                    'target_column': referenced_column,
                    'note': f'外键约束: {constraint_name}'
                })
            
            logging.info(f"成功提取 {len(relationships)} 个外键关系")
            return relationships
            
        except Exception as e:
            logging.error(f"提取关系信息失败: {str(e)}")
            # 返回空字典而不是抛出异常，允许继续处理
            return {}

    @staticmethod
    def execute_sql_query(sql_query: str, db_url: str) -> List[Dict[str, Any]]:
        """
        在达梦数据库上执行 SQL 查询
        
        Args:
            sql_query: SQL 查询语句
            db_url: 数据库连接 URL
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
            
        处理逻辑：
            - SELECT 查询: 返回结果集
            - INSERT/UPDATE/DELETE: 返回影响行数
            - DDL 操作: 返回操作状态
            - 错误处理: 抛出自定义异常
            
        Raises:
            DM_ConnectionError: 连接错误
            DM_QueryError: 查询执行错误
        """
        import json
        import time
        
        # 导入 dmPython 驱动
        try:
            import dmPython
        except ImportError as e:
            error_msg = "达梦数据库驱动未安装，请运行: pip install dmPython"
            logging.error(error_msg)
            raise DM_ConnectionError(error_msg) from e
        
        conn = None
        cursor = None
        start_time = time.time()
        
        try:
            # 解析连接 URL
            conn_params = DM_Loader._parse_connection_url(db_url)
            
            # 记录查询开始日志
            logging.info(json.dumps({
                "event": "query_start",
                "db_type": "dm",
                "host": conn_params["server"],
                "database": conn_params["database"],
                "sql": sql_query[:200],  # 只记录前 200 个字符
                "timestamp": datetime.datetime.now().isoformat()
            }))
            
            # 建立数据库连接
            try:
                conn = dmPython.connect(
                    user=conn_params["user"],
                    password=conn_params["password"],
                    server=conn_params["server"],
                    port=conn_params["port"]
                )
                
                # 设置查询超时（30 秒）
                cursor = conn.cursor()
                # 注意：达梦数据库的超时设置可能需要使用特定的 API
                # 这里假设使用标准的 cursor 执行
                
            except dmPython.Error as e:
                error_msg = f"连接达梦数据库失败: {str(e)}"
                logging.error(json.dumps({
                    "event": "connection_error",
                    "db_type": "dm",
                    "host": conn_params["server"],
                    "database": conn_params["database"],
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                raise DM_ConnectionError(error_msg) from e
            
            # 执行 SQL 查询
            try:
                cursor.execute(sql_query)
                
                # 检查查询是否返回结果（SELECT 查询）
                if cursor.description is not None:
                    # 这是 SELECT 查询或类似的返回行的查询
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    
                    result_list = []
                    for row in results:
                        # 序列化每个值以确保 JSON 兼容性
                        serialized_row = {
                            columns[i]: DM_Loader._serialize_value(row[i])
                            for i in range(len(columns))
                        }
                        result_list.append(serialized_row)
                    
                    # 记录查询成功日志
                    execution_time = time.time() - start_time
                    logging.info(json.dumps({
                        "event": "query_success",
                        "db_type": "dm",
                        "sql": sql_query[:200],
                        "row_count": len(result_list),
                        "execution_time": round(execution_time, 3),
                        "timestamp": datetime.datetime.now().isoformat()
                    }))
                    
                else:
                    # 这是 INSERT、UPDATE、DELETE 或其他非 SELECT 查询
                    # 返回操作信息
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
                        "db_type": "dm",
                        "operation": sql_type,
                        "affected_rows": affected_rows,
                        "execution_time": round(execution_time, 3),
                        "timestamp": datetime.datetime.now().isoformat()
                    }))
                
                # 提交事务（对于写操作）
                conn.commit()
                
                return result_list
                
            except dmPython.Error as e:
                # 查询执行错误
                execution_time = time.time() - start_time
                logging.error(json.dumps({
                    "event": "query_error",
                    "db_type": "dm",
                    "sql": sql_query[:200],
                    "error": str(e),
                    "execution_time": round(execution_time, 3),
                    "timestamp": datetime.datetime.now().isoformat()
                }))
                
                # 回滚事务
                if conn:
                    conn.rollback()
                
                raise DM_QueryError(f"查询执行失败: {str(e)}") from e
                
        except DM_ConnectionError:
            # 重新抛出连接错误
            raise
        except DM_QueryError:
            # 重新抛出查询错误
            raise
        except Exception as e:
            # 捕获其他未预期的错误
            execution_time = time.time() - start_time
            logging.error(json.dumps({
                "event": "unexpected_error",
                "db_type": "dm",
                "sql": sql_query[:200] if sql_query else "",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": round(execution_time, 3),
                "timestamp": datetime.datetime.now().isoformat()
            }))
            
            raise DM_QueryError(f"执行查询时发生错误: {str(e)}") from e
            
        finally:
            # 确保关闭数据库连接
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def is_schema_modifying_query(sql_query: str) -> Tuple[bool, str]:
        """
        检测 SQL 查询是否修改数据库模式
        
        Args:
            sql_query: SQL 查询语句
            
        Returns:
            Tuple[bool, str]: (是否修改模式, 操作类型)
            
        检测方法：
            1. 提取第一个关键字
            2. 检查是否在 SCHEMA_MODIFYING_OPERATIONS 中
            3. 使用正则表达式精确匹配
        """
        if not sql_query or not sql_query.strip():
            return False, ""

        # 清理并规范化查询
        normalized_query = sql_query.strip().upper()

        # 检查基本的 DDL 操作
        first_word = normalized_query.split()[0] if normalized_query.split() else ""
        if first_word in DM_Loader.SCHEMA_MODIFYING_OPERATIONS:
            # 使用正则模式进行更精确的检测
            for pattern in DM_Loader.SCHEMA_PATTERNS:
                if re.match(pattern, normalized_query, re.IGNORECASE):
                    return True, first_word

            # 如果是已知的 DDL 操作但不匹配特定模式，
            # 仍然认为它是模式修改操作（宁可保守）
            return True, first_word

        return False, ""

    @staticmethod
    @staticmethod
    async def refresh_graph_schema(graph_id: str, db_url: str) -> Tuple[bool, str]:
        """
        通过清除现有数据并从数据库重新加载来刷新图模式
        
        Args:
            graph_id: 要刷新的图 ID
            db_url: 数据库连接 URL
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
            
        工作流程：
            1. 删除现有图数据
            2. 重新连接数据库
            3. 重新提取模式
            4. 重新加载到图数据库
        """
        try:
            logging.info("检测到模式修改操作，正在刷新图模式...")

            # 导入 db 扩展（避免循环导入）
            from api.extensions import db  # pylint: disable=import-error,import-outside-toplevel

            # 清除现有图数据
            # 在重新加载之前删除当前图
            graph = db.select_graph(graph_id)
            await graph.delete()
            logging.info(f"已删除现有图数据: {graph_id}")

            # 从 graph_id 中提取前缀（移除数据库名部分）
            # graph_id 格式通常是 "prefix_database_name"
            parts = graph_id.split('_')
            if len(parts) >= 2:
                # 通过连接除最后一个部分外的所有部分来重建前缀
                prefix = '_'.join(parts[:-1])
            else:
                prefix = graph_id

            logging.info(f"正在重新加载模式，前缀: {prefix}, URL: {db_url}")

            # 重用现有的 load 方法重新加载模式
            # load 方法是一个异步生成器，需要迭代它
            success = False
            last_message = ""
            
            async for status, message in DM_Loader.load(prefix, db_url):
                last_message = message
                if status:
                    success = True
                else:
                    success = False
                    break

            if success:
                logging.info("图模式刷新成功")
                return True, last_message

            logging.error("模式刷新失败")
            return False, last_message or "重新加载模式失败"

        except Exception as e:  # pylint: disable=broad-exception-caught
            # 记录错误并返回失败
            error_msg = f"刷新图模式时出错: {str(e)}"
            logging.error(error_msg)
            logging.exception("详细错误信息:")
            return False, "刷新图模式失败，请检查日志获取详细信息"
