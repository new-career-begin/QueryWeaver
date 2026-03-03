"""
SQL 标识符引用功能验证脚本

演示达梦和人大金仓数据库的标识符引用功能。
"""

from api.sql_utils.sql_sanitizer import DatabaseSpecificQuoter


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_quote_char():
    """测试不同数据库的引用字符"""
    print_section("1. 测试引用字符")
    
    databases = ['dm', 'kingbase', 'postgresql', 'mysql']
    for db in databases:
        quote_char = DatabaseSpecificQuoter.get_quote_char(db)
        print(f"{db:15} -> 引用字符: {quote_char}")


def test_needs_quoting():
    """测试标识符是否需要引用"""
    print_section("2. 测试标识符引用需求")
    
    test_cases = [
        ('users', 'dm', '普通标识符'),
        ('user-data', 'dm', '包含连字符'),
        ('user data', 'kingbase', '包含空格'),
        ('SELECT', 'dm', 'SQL保留字'),
        ('UserData', 'kingbase', '包含大写字母'),
        ('123table', 'dm', '以数字开头'),
        ('user_id', 'kingbase', '包含下划线'),
    ]
    
    for identifier, db_type, description in test_cases:
        needs = DatabaseSpecificQuoter.needs_quoting(identifier, db_type)
        status = "需要引用" if needs else "不需要引用"
        print(f"{description:20} | {identifier:15} | {db_type:10} -> {status}")


def test_quote_identifier():
    """测试标识符引用"""
    print_section("3. 测试标识符引用")
    
    test_cases = [
        ('users', 'dm'),
        ('user-data', 'dm'),
        ('order items', 'kingbase'),
        ('user"data', 'dm'),
        ('TABLE', 'kingbase'),
        ('用户表', 'dm'),
    ]
    
    for identifier, db_type in test_cases:
        quoted = DatabaseSpecificQuoter.quote_identifier(identifier, db_type)
        print(f"{db_type:10} | {identifier:20} -> {quoted}")


def test_escape_identifier():
    """测试标识符转义"""
    print_section("4. 测试标识符转义")
    
    test_cases = [
        ('user"data', 'dm', '包含双引号'),
        ('user"data"table', 'kingbase', '包含多个双引号'),
        ('user`data', 'mysql', '包含反引号'),
    ]
    
    for identifier, db_type, description in test_cases:
        escaped = DatabaseSpecificQuoter.escape_identifier(identifier, db_type)
        print(f"{description:20} | {identifier:20} -> {escaped}")


def test_auto_quote():
    """测试自动引用SQL查询"""
    print_section("5. 测试自动引用SQL查询")
    
    test_cases = [
        (
            "SELECT * FROM user-data WHERE id = 1",
            {'user-data'},
            'dm',
            '达梦数据库 - 包含连字符的表名'
        ),
        (
            "SELECT * FROM order-items JOIN user-data ON order-items.user_id = user-data.id",
            {'order-items', 'user-data'},
            'kingbase',
            '人大金仓 - 多表JOIN'
        ),
        (
            "SELECT * FROM users WHERE id = 1",
            {'users'},
            'dm',
            '达梦数据库 - 普通表名（不需要引用）'
        ),
    ]
    
    for sql, tables, db_type, description in test_cases:
        result, modified = DatabaseSpecificQuoter.auto_quote_identifiers_for_db(
            sql, tables, db_type
        )
        status = "已修改" if modified else "未修改"
        print(f"\n{description}")
        print(f"  原始SQL: {sql}")
        print(f"  结果SQL: {result}")
        print(f"  状态: {status}")


def test_reserved_words():
    """测试SQL保留字"""
    print_section("6. 测试SQL保留字引用")
    
    reserved_words = ['SELECT', 'TABLE', 'USER', 'ORDER', 'INDEX']
    
    for word in reserved_words:
        needs = DatabaseSpecificQuoter.needs_quoting(word, 'dm')
        quoted = DatabaseSpecificQuoter.quote_identifier(word, 'dm')
        print(f"{word:10} -> 需要引用: {needs:5} -> {quoted}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  SQL 标识符引用功能验证")
    print("  达梦数据库 (DM) 和人大金仓数据库 (Kingbase)")
    print("=" * 60)
    
    test_quote_char()
    test_needs_quoting()
    test_quote_identifier()
    test_escape_identifier()
    test_auto_quote()
    test_reserved_words()
    
    print("\n" + "=" * 60)
    print("  验证完成！")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
