"""
SQL 标识符引用处理的单元测试

测试达梦和人大金仓数据库的标识符引用规则。
"""

import pytest
from api.sql_utils.sql_sanitizer import DatabaseSpecificQuoter


class TestDatabaseSpecificQuoter:
    """测试 DatabaseSpecificQuoter 类的功能"""

    def test_get_quote_char_dm(self):
        """测试达梦数据库使用双引号"""
        quote_char = DatabaseSpecificQuoter.get_quote_char('dm')
        assert quote_char == '"'

    def test_get_quote_char_kingbase(self):
        """测试人大金仓数据库使用双引号"""
        quote_char = DatabaseSpecificQuoter.get_quote_char('kingbase')
        assert quote_char == '"'

    def test_get_quote_char_postgresql(self):
        """测试 PostgreSQL 使用双引号"""
        quote_char = DatabaseSpecificQuoter.get_quote_char('postgresql')
        assert quote_char == '"'

    def test_get_quote_char_mysql(self):
        """测试 MySQL 使用反引号"""
        quote_char = DatabaseSpecificQuoter.get_quote_char('mysql')
        assert quote_char == '`'

    def test_needs_quoting_special_chars(self):
        """测试包含特殊字符的标识符需要引用"""
        # 包含连字符
        assert DatabaseSpecificQuoter.needs_quoting('user-data', 'dm') is True
        
        # 包含空格
        assert DatabaseSpecificQuoter.needs_quoting('user data', 'dm') is True
        
        # 包含点号
        assert DatabaseSpecificQuoter.needs_quoting('user.data', 'dm') is True

    def test_needs_quoting_reserved_words(self):
        """测试 SQL 保留字需要引用"""
        assert DatabaseSpecificQuoter.needs_quoting('SELECT', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('TABLE', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('USER', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('order', 'kingbase') is True

    def test_needs_quoting_starts_with_digit(self):
        """测试以数字开头的标识符需要引用"""
        assert DatabaseSpecificQuoter.needs_quoting('123table', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('2users', 'kingbase') is True

    def test_needs_quoting_uppercase_letters(self):
        """测试包含大写字母的标识符需要引用（达梦和人大金仓）"""
        # 达梦数据库
        assert DatabaseSpecificQuoter.needs_quoting('UserData', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('USERS', 'dm') is True
        
        # 人大金仓数据库
        assert DatabaseSpecificQuoter.needs_quoting('UserData', 'kingbase') is True
        assert DatabaseSpecificQuoter.needs_quoting('USERS', 'kingbase') is True

    def test_needs_quoting_normal_identifier(self):
        """测试普通标识符不需要引用"""
        assert DatabaseSpecificQuoter.needs_quoting('users', 'dm') is False
        assert DatabaseSpecificQuoter.needs_quoting('orders', 'kingbase') is False
        assert DatabaseSpecificQuoter.needs_quoting('user_id', 'dm') is False

    def test_needs_quoting_already_quoted(self):
        """测试已经引用的标识符不需要再次引用"""
        assert DatabaseSpecificQuoter.needs_quoting('"users"', 'dm') is False
        assert DatabaseSpecificQuoter.needs_quoting('"user-data"', 'kingbase') is False

    def test_quote_identifier_dm(self):
        """测试达梦数据库的标识符引用"""
        # 普通标识符
        result = DatabaseSpecificQuoter.quote_identifier('users', 'dm')
        assert result == '"users"'
        
        # 包含特殊字符
        result = DatabaseSpecificQuoter.quote_identifier('user-data', 'dm')
        assert result == '"user-data"'
        
        # 包含空格
        result = DatabaseSpecificQuoter.quote_identifier('user data', 'dm')
        assert result == '"user data"'

    def test_quote_identifier_kingbase(self):
        """测试人大金仓数据库的标识符引用"""
        # 普通标识符
        result = DatabaseSpecificQuoter.quote_identifier('orders', 'kingbase')
        assert result == '"orders"'
        
        # 包含特殊字符
        result = DatabaseSpecificQuoter.quote_identifier('order-items', 'kingbase')
        assert result == '"order-items"'

    def test_quote_identifier_with_quotes(self):
        """测试包含引号的标识符的转义"""
        # 达梦数据库 - 双引号转义为两个双引号
        result = DatabaseSpecificQuoter.quote_identifier('user"data', 'dm')
        assert result == '"user""data"'
        
        # 人大金仓数据库 - 双引号转义为两个双引号
        result = DatabaseSpecificQuoter.quote_identifier('order"items', 'kingbase')
        assert result == '"order""items"'
        
        # MySQL - 反引号转义为两个反引号
        result = DatabaseSpecificQuoter.quote_identifier('user`data', 'mysql')
        assert result == '`user``data`'

    def test_quote_identifier_already_quoted(self):
        """测试已经引用的标识符不会重复引用"""
        # 达梦数据库
        result = DatabaseSpecificQuoter.quote_identifier('"users"', 'dm')
        assert result == '"users"'
        
        # 人大金仓数据库
        result = DatabaseSpecificQuoter.quote_identifier('"orders"', 'kingbase')
        assert result == '"orders"'

    def test_quote_identifier_empty(self):
        """测试空标识符"""
        result = DatabaseSpecificQuoter.quote_identifier('', 'dm')
        assert result == ''
        
        result = DatabaseSpecificQuoter.quote_identifier('   ', 'kingbase')
        assert result == '   '

    def test_escape_identifier_dm(self):
        """测试达梦数据库的标识符转义"""
        # 包含双引号
        result = DatabaseSpecificQuoter.escape_identifier('user"data', 'dm')
        assert result == 'user""data'
        
        # 包含多个双引号
        result = DatabaseSpecificQuoter.escape_identifier('user"data"table', 'dm')
        assert result == 'user""data""table'

    def test_escape_identifier_kingbase(self):
        """测试人大金仓数据库的标识符转义"""
        # 包含双引号
        result = DatabaseSpecificQuoter.escape_identifier('order"items', 'kingbase')
        assert result == 'order""items'

    def test_escape_identifier_mysql(self):
        """测试 MySQL 的标识符转义"""
        # 包含反引号
        result = DatabaseSpecificQuoter.escape_identifier('user`data', 'mysql')
        assert result == 'user``data'

    def test_auto_quote_identifiers_dm(self):
        """测试达梦数据库的自动引用"""
        sql = "SELECT * FROM user-data WHERE id = 1"
        known_tables = {'user-data'}
        
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, known_tables, 'dm'
        )
        
        assert modified is True
        assert '"user-data"' in result

    def test_auto_quote_identifiers_kingbase(self):
        """测试人大金仓数据库的自动引用"""
        sql = "SELECT * FROM order-items WHERE id = 1"
        known_tables = {'order-items'}
        
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, known_tables, 'kingbase'
        )
        
        assert modified is True
        assert '"order-items"' in result

    def test_auto_quote_identifiers_with_join(self):
        """测试包含 JOIN 的查询的自动引用"""
        sql = "SELECT * FROM user-data JOIN order-items ON user-data.id = order-items.user_id"
        known_tables = {'user-data', 'order-items'}
        
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, known_tables, 'dm'
        )
        
        assert modified is True
        assert '"user-data"' in result
        assert '"order-items"' in result

    def test_auto_quote_identifiers_no_modification(self):
        """测试不需要引用的查询不会被修改"""
        sql = "SELECT * FROM users WHERE id = 1"
        known_tables = {'users'}
        
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, known_tables, 'dm'
        )
        
        assert modified is False
        assert result == sql

    def test_auto_quote_identifiers_unknown_table(self):
        """测试未知表名不会被引用"""
        sql = "SELECT * FROM unknown-table WHERE id = 1"
        known_tables = {'users', 'orders'}
        
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, known_tables, 'dm'
        )
        
        assert modified is False
        assert result == sql


class TestSQLReservedWords:
    """测试 SQL 保留字检测"""

    def test_reserved_words_detection(self):
        """测试常见 SQL 保留字的检测"""
        reserved_words = [
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'TABLE', 'USER',
            'ORDER', 'GROUP', 'INDEX', 'KEY', 'DATABASE', 'SCHEMA'
        ]
        
        for word in reserved_words:
            assert DatabaseSpecificQuoter.needs_quoting(word, 'dm') is True
            assert DatabaseSpecificQuoter.needs_quoting(word.lower(), 'kingbase') is True

    def test_reserved_words_quoting(self):
        """测试保留字的引用"""
        # 达梦数据库
        result = DatabaseSpecificQuoter.quote_identifier('USER', 'dm')
        assert result == '"USER"'
        
        result = DatabaseSpecificQuoter.quote_identifier('order', 'dm')
        assert result == '"order"'
        
        # 人大金仓数据库
        result = DatabaseSpecificQuoter.quote_identifier('TABLE', 'kingbase')
        assert result == '"TABLE"'
        
        result = DatabaseSpecificQuoter.quote_identifier('index', 'kingbase')
        assert result == '"index"'


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_identifier(self):
        """测试空标识符"""
        assert DatabaseSpecificQuoter.needs_quoting('', 'dm') is False
        assert DatabaseSpecificQuoter.quote_identifier('', 'dm') == ''

    def test_whitespace_identifier(self):
        """测试只包含空格的标识符"""
        assert DatabaseSpecificQuoter.needs_quoting('   ', 'dm') is False

    def test_unicode_identifier(self):
        """测试 Unicode 字符标识符"""
        # 中文标识符
        result = DatabaseSpecificQuoter.quote_identifier('用户表', 'dm')
        assert result == '"用户表"'
        
        result = DatabaseSpecificQuoter.quote_identifier('订单表', 'kingbase')
        assert result == '"订单表"'

    def test_mixed_case_identifier(self):
        """测试混合大小写标识符"""
        # 达梦和人大金仓对大小写敏感，需要引用
        result = DatabaseSpecificQuoter.quote_identifier('UserData', 'dm')
        assert result == '"UserData"'
        
        result = DatabaseSpecificQuoter.quote_identifier('OrderItems', 'kingbase')
        assert result == '"OrderItems"'

    def test_identifier_with_underscore(self):
        """测试包含下划线的标识符"""
        # 下划线是合法字符，不需要引用
        assert DatabaseSpecificQuoter.needs_quoting('user_data', 'dm') is False
        assert DatabaseSpecificQuoter.needs_quoting('order_items', 'kingbase') is False

    def test_identifier_with_numbers(self):
        """测试包含数字的标识符"""
        # 以字母开头，包含数字，不需要引用
        assert DatabaseSpecificQuoter.needs_quoting('user123', 'dm') is False
        assert DatabaseSpecificQuoter.needs_quoting('table2', 'kingbase') is False
        
        # 以数字开头，需要引用
        assert DatabaseSpecificQuoter.needs_quoting('123user', 'dm') is True
        assert DatabaseSpecificQuoter.needs_quoting('2table', 'kingbase') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
