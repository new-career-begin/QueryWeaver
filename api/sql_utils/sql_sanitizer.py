"""SQL sanitization utilities for handling identifiers with special characters."""

import re
from typing import Set, Tuple


class SQLIdentifierQuoter:
    """
    Utility class for automatically quoting SQL identifiers (table/column names)
    that contain special characters like dashes.
    """

    # Characters that require quoting in identifiers
    SPECIAL_CHARS = {'-', ' ', '.', '@', '#', '$', '%', '^', '&', '*', '(',
                     ')', '+', '=', '[', ']', '{', '}', '|', '\\', ':',
                     ';', '"', "'", '<', '>', ',', '?', '/'}
    # SQL keywords that should not be quoted
    SQL_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
        'AS', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'ORDER',
        'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT', 'UPDATE', 'DELETE',
        'CREATE', 'DROP', 'ALTER', 'TABLE', 'INTO', 'VALUES', 'SET', 'COUNT',
        'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'ALL', 'UNION', 'INTERSECT',
        'EXCEPT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'CAST', 'ASC', 'DESC'
    }

    @classmethod
    def needs_quoting(cls, identifier: str) -> bool:
        """
        Check if an identifier needs quoting based on special characters.
        
        Args:
            identifier: The table or column name to check
            
        Returns:
            True if the identifier needs quoting, False otherwise
        """
        # Already quoted
        if (identifier.startswith('"') and identifier.endswith('"')) or \
           (identifier.startswith('`') and identifier.endswith('`')):
            return False

        # Check if it's a SQL keyword
        if identifier.upper() in cls.SQL_KEYWORDS:
            return False

        # Check for special characters
        return any(char in cls.SPECIAL_CHARS for char in identifier)

    @staticmethod
    def quote_identifier(identifier: str, quote_char: str = '"') -> str:
        """
        Quote an identifier if not already quoted.
        
        Args:
            identifier: The identifier to quote
            quote_char: The quote character to use (default: " for PostgreSQL/standard SQL)
            
        Returns:
            Quoted identifier
        """
        identifier = identifier.strip()

        # Don't double-quote
        if (identifier.startswith('"') and identifier.endswith('"')) or \
           (identifier.startswith('`') and identifier.endswith('`')):
            return identifier

        return f'{quote_char}{identifier}{quote_char}'

    @classmethod
    def extract_table_names_from_query(cls, sql_query: str) -> Set[str]:
        """
        Extract potential table names from a SQL query.
        Looks for identifiers after FROM, JOIN, UPDATE, INSERT INTO, etc.
        
        Args:
            sql_query: The SQL query to parse
            
        Returns:
            Set of potential table names
        """
        table_names = set()

        # Pattern to match table names after FROM, JOIN, UPDATE, INSERT INTO, etc.
        # This is a heuristic approach - not perfect but handles common cases
        patterns = [
            r'\bFROM\s+([a-zA-Z0-9_\-]+)',
            r'\bJOIN\s+([a-zA-Z0-9_\-]+)',
            r'\bUPDATE\s+([a-zA-Z0-9_\-]+)',
            r'\bINSERT\s+INTO\s+([a-zA-Z0-9_\-]+)',
            r'\bTABLE\s+([a-zA-Z0-9_\-]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1).strip()
                # Skip if it's already quoted or an alias
                if not ((table_name.startswith('"') and table_name.endswith('"')) or
                       (table_name.startswith('`') and table_name.endswith('`'))):
                    table_names.add(table_name)

        return table_names

    @classmethod
    def auto_quote_identifiers(
        cls,
        sql_query: str,
        known_tables: Set[str],
        quote_char: str = '"'
    ) -> Tuple[str, bool]:
        """
        Automatically quote table names with special characters in a SQL query.
        
        Args:
            sql_query: The SQL query to process
            known_tables: Set of known table names from the database schema
            quote_char: Quote character to use (default: " for PostgreSQL, use ` for MySQL)
            
        Returns:
            Tuple of (modified_query, was_modified)
        """
        modified = False
        result_query = sql_query

        # Extract potential table names from query
        query_tables = cls.extract_table_names_from_query(sql_query)

        # For each table that needs quoting
        for table in query_tables:
            # Check if this table exists in known schema and needs quoting
            if table in known_tables and cls.needs_quoting(table):
                # Quote the table name
                quoted = cls.quote_identifier(table, quote_char)

                # Replace unquoted occurrences with quoted version
                # Use word boundaries to avoid partial replacements
                # Handle cases: FROM table, JOIN table, table.column, etc.
                patterns_to_replace = [
                    (rf'\b{re.escape(table)}\b(?!\s*\.)', quoted),
                    (rf'\b{re.escape(table)}\.', f'{quoted}.'),
                ]

                for pattern, replacement in patterns_to_replace:
                    new_query = re.sub(pattern, replacement, result_query, flags=re.IGNORECASE)
                    if new_query != result_query:
                        modified = True
                        result_query = new_query

        return result_query, modified


class DatabaseSpecificQuoter:  # pylint: disable=too-few-public-methods
    """
    数据库特定引用字符工厂类
    
    为不同数据库类型提供正确的标识符引用字符。
    """

    # SQL 保留字集合（常见的跨数据库保留字）
    SQL_RESERVED_WORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE', 'IS', 'NULL',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT', 'UPDATE',
        'DELETE', 'CREATE', 'DROP', 'ALTER', 'TABLE', 'INTO', 'VALUES', 'SET',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'ALL', 'UNION',
        'INTERSECT', 'EXCEPT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'CAST',
        'ASC', 'DESC', 'INDEX', 'KEY', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK',
        'DEFAULT', 'CONSTRAINT', 'REFERENCES', 'CASCADE', 'RESTRICT', 'VIEW',
        'TRIGGER', 'PROCEDURE', 'FUNCTION', 'SCHEMA', 'DATABASE', 'USER',
        'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'BEGIN'
    }

    @staticmethod
    def get_quote_char(db_type: str) -> str:
        """
        获取数据库类型对应的标识符引用字符
        
        Args:
            db_type: 数据库类型 ('postgresql', 'mysql', 'dm', 'kingbase' 等)
            
        Returns:
            引用字符
            
        引用规则：
            - MySQL/MariaDB: 使用反引号 `
            - PostgreSQL/SQLite/SQL Server/达梦/人大金仓: 使用双引号 "
        """
        if db_type.lower() in ['mysql', 'mariadb']:
            return '`'
        # PostgreSQL, SQLite, SQL Server, 达梦, 人大金仓 (标准 SQL) 使用双引号
        # 达梦和人大金仓都遵循标准 SQL 规范，使用双引号引用标识符
        return '"'

    @staticmethod
    def needs_quoting(identifier: str, db_type: str = 'postgresql') -> bool:
        """
        检查标识符是否需要引用
        
        Args:
            identifier: 表名或列名
            db_type: 数据库类型
            
        Returns:
            如果需要引用返回 True，否则返回 False
            
        需要引用的情况：
            1. 包含特殊字符（空格、连字符、点号等）
            2. 是 SQL 保留字
            3. 以数字开头
            4. 包含大写字母（某些数据库区分大小写）
        """
        if not identifier or not identifier.strip():
            return False
        
        # 已经被引用
        quote_char = DatabaseSpecificQuoter.get_quote_char(db_type)
        if identifier.startswith(quote_char) and identifier.endswith(quote_char):
            return False
        
        # 检查是否是 SQL 保留字
        if identifier.upper() in DatabaseSpecificQuoter.SQL_RESERVED_WORDS:
            return True
        
        # 检查是否包含特殊字符
        if any(char in SQLIdentifierQuoter.SPECIAL_CHARS for char in identifier):
            return True
        
        # 检查是否以数字开头
        if identifier[0].isdigit():
            return True
        
        # 检查是否包含大写字母（对于区分大小写的数据库）
        # 达梦和人大金仓默认不区分大小写，但如果标识符包含大写字母，
        # 为了保持原样，需要引用
        if db_type.lower() in ['dm', 'kingbase', 'postgresql']:
            if any(char.isupper() for char in identifier):
                return True
        
        return False

    @staticmethod
    def quote_identifier(identifier: str, db_type: str = 'postgresql') -> str:
        """
        引用标识符（如果需要）
        
        Args:
            identifier: 要引用的标识符
            db_type: 数据库类型
            
        Returns:
            引用后的标识符
            
        引用规则：
            - 达梦数据库: 使用双引号，内部双引号转义为两个双引号
            - 人大金仓数据库: 使用双引号，内部双引号转义为两个双引号
            - PostgreSQL: 使用双引号，内部双引号转义为两个双引号
            - MySQL: 使用反引号，内部反引号转义为两个反引号
        """
        if not identifier or not identifier.strip():
            return identifier
        
        identifier = identifier.strip()
        
        # 获取引用字符
        quote_char = DatabaseSpecificQuoter.get_quote_char(db_type)
        
        # 如果已经被引用，直接返回
        if identifier.startswith(quote_char) and identifier.endswith(quote_char):
            return identifier
        
        # 转义标识符中的引号字符
        # 对于双引号：" -> ""
        # 对于反引号：` -> ``
        escaped_identifier = identifier.replace(quote_char, quote_char + quote_char)
        
        # 返回引用后的标识符
        return f'{quote_char}{escaped_identifier}{quote_char}'

    @staticmethod
    def escape_identifier(identifier: str, db_type: str = 'postgresql') -> str:
        """
        转义标识符中的特殊字符
        
        Args:
            identifier: 要转义的标识符
            db_type: 数据库类型
            
        Returns:
            转义后的标识符
            
        转义规则：
            - 双引号 " 转义为 ""
            - 反引号 ` 转义为 ``
        """
        if not identifier:
            return identifier
        
        quote_char = DatabaseSpecificQuoter.get_quote_char(db_type)
        
        # 转义引号字符
        return identifier.replace(quote_char, quote_char + quote_char)

    @staticmethod
    def auto_quote_identifiers_for_db(
        sql_query: str,
        known_tables: Set[str],
        db_type: str = 'postgresql'
    ) -> Tuple[str, bool]:
        """
        根据数据库类型自动引用 SQL 查询中的标识符
        
        Args:
            sql_query: SQL 查询语句
            known_tables: 已知的表名集合
            db_type: 数据库类型 ('postgresql', 'mysql', 'dm', 'kingbase')
            
        Returns:
            (修改后的查询, 是否被修改) 的元组
            
        处理逻辑：
            1. 提取查询中的表名
            2. 检查每个表名是否需要引用
            3. 使用正确的引用字符引用标识符
            4. 处理表名.列名的情况
        """
        modified = False
        result_query = sql_query
        
        # 获取引用字符
        quote_char = DatabaseSpecificQuoter.get_quote_char(db_type)
        
        # 提取查询中的潜在表名
        query_tables = SQLIdentifierQuoter.extract_table_names_from_query(sql_query)
        
        # 对每个需要引用的表名进行处理
        for table in query_tables:
            # 检查表是否存在于已知模式中且需要引用
            if table in known_tables and DatabaseSpecificQuoter.needs_quoting(table, db_type):
                # 引用表名
                quoted = DatabaseSpecificQuoter.quote_identifier(table, db_type)
                
                # 替换未引用的出现为引用版本
                # 使用单词边界避免部分替换
                # 处理情况：FROM table, JOIN table, table.column 等
                patterns_to_replace = [
                    (rf'\b{re.escape(table)}\b(?!\s*\.)', quoted),
                    (rf'\b{re.escape(table)}\.', f'{quoted}.'),
                ]
                
                for pattern, replacement in patterns_to_replace:
                    new_query = re.sub(pattern, replacement, result_query, flags=re.IGNORECASE)
                    if new_query != result_query:
                        modified = True
                        result_query = new_query
        
        return result_query, modified
