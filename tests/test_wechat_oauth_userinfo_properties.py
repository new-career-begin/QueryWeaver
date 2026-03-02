"""
微信和企业微信用户信息获取的属性测试

本测试文件使用 hypothesis 进行属性测试,验证用户信息解析的正确性属性。

测试的属性:
- 属性 5: 微信用户信息完整性
- 属性 6: 企业微信用户信息完整性

验证需求: 2.1.2.8, 2.2.2.8
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from api.auth.oauth_handlers import WeChatOAuthHandler, WeComOAuthHandler


# -----------------------------
# 测试配置
# -----------------------------

# 微信测试配置
WECHAT_TEST_CONFIG = {
    "app_id": "wx_test_app_id_12345",
    "app_secret": "test_secret_key",
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
    "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    "scope": "snsapi_userinfo"
}

# 企业微信测试配置
WECOM_TEST_CONFIG = {
    "corp_id": "ww_test_corp_id_12345",
    "agent_id": "1000001",
    "corp_secret": "test_corp_secret",
    "authorize_url": "https://open.weixin.qq.com/connect/oauth2/authorize",
    "access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
    "userinfo_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    "user_detail_url": "https://qyapi.weixin.qq.com/cgi-bin/user/get",
    "scope": "snsapi_base"
}


# -----------------------------
# Hypothesis 策略定义
# -----------------------------

# 生成有效的 OpenID (微信用户标识)
openid_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=20,
    max_size=50
)

# 生成有效的 UnionID (微信跨应用用户标识)
unionid_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=20,
    max_size=50
)

# 生成有效的用户昵称 (支持中文)
nickname_strategy = st.text(
    min_size=1,
    max_size=50
).filter(lambda s: len(s.strip()) > 0)

# 生成有效的头像 URL
avatar_url_strategy = st.builds(
    lambda: f"https://thirdwx.qlogo.cn/mmopen/{st.text(alphabet='abcdef0123456789', min_size=32, max_size=32).example()}/132",
)

# 生成有效的企业微信 UserID
wecom_userid_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        min_codepoint=48,
        max_codepoint=122
    ),
    min_size=1,
    max_size=64
)

# 生成有效的企业邮箱
email_strategy = st.builds(
    lambda name, domain: f"{name}@{domain}.com",
    name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
        min_size=3,
        max_size=20
    ),
    domain=st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122),
        min_size=3,
        max_size=15
    )
)

# 生成部门 ID 列表
department_strategy = st.lists(
    st.integers(min_value=1, max_value=1000),
    min_size=0,
    max_size=5
)


# -----------------------------
# 属性 5: 微信用户信息完整性
# -----------------------------

@given(
    openid=openid_strategy,
    nickname=nickname_strategy,
    headimgurl=avatar_url_strategy,
    unionid=st.one_of(st.none(), unionid_strategy)
)
@settings(max_examples=100, deadline=None)
def test_wechat_user_info_completeness(
    openid: str,
    nickname: str,
    headimgurl: str,
    unionid: str | None
):
    """
    属性测试: 微信用户信息解析必须包含所有必需字段
    
    对于任何有效的微信用户数据,解析后的用户信息必须包含:
    - id: 用户唯一标识 (OpenID)
    - email: 虚拟邮箱地址
    - name: 用户昵称
    - picture: 头像 URL
    - provider: 固定为 "wechat"
    - unionid: 可选的跨应用标识
    
    验证需求: 2.1.2.8
    
    Args:
        openid: 随机生成的 OpenID
        nickname: 随机生成的用户昵称
        headimgurl: 随机生成的头像 URL
        unionid: 可选的 UnionID
    """
    # Arrange - 准备微信原始用户数据
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    raw_user_data = {
        "openid": openid,
        "nickname": nickname,
        "headimgurl": headimgurl
    }
    
    if unionid is not None:
        raw_user_data["unionid"] = unionid
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证必需字段存在
    assert "id" in parsed_info, "缺少 id 字段"
    assert "email" in parsed_info, "缺少 email 字段"
    assert "name" in parsed_info, "缺少 name 字段"
    assert "picture" in parsed_info, "缺少 picture 字段"
    assert "provider" in parsed_info, "缺少 provider 字段"
    
    # 验证字段值正确
    assert parsed_info["id"] == openid, "id 应该等于 openid"
    assert parsed_info["name"] == nickname, "name 应该等于 nickname"
    assert parsed_info["picture"] == headimgurl, "picture 应该等于 headimgurl"
    assert parsed_info["provider"] == "wechat", "provider 必须为 'wechat'"
    
    # 验证虚拟邮箱格式
    assert "@wechat.queryweaver.local" in parsed_info["email"], \
        "email 必须使用 @wechat.queryweaver.local 域名"
    assert parsed_info["email"].startswith(openid), \
        "email 必须以 openid 开头"
    
    # 验证 unionid (如果提供)
    if unionid is not None:
        assert "unionid" in parsed_info, "提供了 unionid 时必须包含在解析结果中"
        assert parsed_info["unionid"] == unionid, "unionid 值应该保持不变"


@given(
    openid=openid_strategy,
    nickname=nickname_strategy
)
@settings(max_examples=100, deadline=None)
def test_wechat_user_info_without_optional_fields(
    openid: str,
    nickname: str
):
    """
    属性测试: 微信用户信息解析应该正确处理缺失的可选字段
    
    即使缺少可选字段 (如 headimgurl, unionid),解析也应该成功,
    并且必需字段仍然存在。
    
    验证需求: 2.1.2.8
    
    Args:
        openid: 随机生成的 OpenID
        nickname: 随机生成的用户昵称
    """
    # Arrange - 准备最小化的用户数据
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    raw_user_data = {
        "openid": openid,
        "nickname": nickname
        # 故意不包含 headimgurl 和 unionid
    }
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证必需字段仍然存在
    assert "id" in parsed_info
    assert "email" in parsed_info
    assert "name" in parsed_info
    assert "provider" in parsed_info
    
    # picture 字段应该存在,但可能为 None
    assert "picture" in parsed_info
    
    # 验证基本字段值
    assert parsed_info["id"] == openid
    assert parsed_info["name"] == nickname
    assert parsed_info["provider"] == "wechat"


@given(openid=openid_strategy)
@settings(max_examples=100, deadline=None)
def test_wechat_user_info_with_missing_nickname(openid: str):
    """
    属性测试: 微信用户信息解析应该为缺失的昵称提供默认值
    
    当用户数据中缺少昵称时,应该使用默认值 "微信用户"。
    
    验证需求: 2.1.2.8
    
    Args:
        openid: 随机生成的 OpenID
    """
    # Arrange - 准备缺少昵称的用户数据
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    raw_user_data = {
        "openid": openid
        # 故意不包含 nickname
    }
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证使用了默认昵称
    assert parsed_info["name"] == "微信用户", \
        "缺少昵称时应该使用默认值 '微信用户'"


# -----------------------------
# 属性 6: 企业微信用户信息完整性
# -----------------------------

@given(
    userid=wecom_userid_strategy,
    name=nickname_strategy,
    email=st.one_of(st.none(), email_strategy),
    avatar=st.one_of(st.none(), avatar_url_strategy),
    department=department_strategy
)
@settings(max_examples=100, deadline=None)
def test_wecom_user_info_completeness(
    userid: str,
    name: str,
    email: str | None,
    avatar: str | None,
    department: list[int]
):
    """
    属性测试: 企业微信用户信息解析必须包含所有必需字段
    
    对于任何有效的企业微信用户数据,解析后的用户信息必须包含:
    - id: 用户唯一标识 (UserID)
    - email: 企业邮箱或虚拟邮箱
    - name: 用户姓名
    - picture: 头像 URL (可选)
    - provider: 固定为 "wecom"
    - corp_id: 企业 ID
    - department: 部门 ID 列表
    
    验证需求: 2.2.2.8
    
    Args:
        userid: 随机生成的 UserID
        name: 随机生成的用户姓名
        email: 可选的企业邮箱
        avatar: 可选的头像 URL
        department: 部门 ID 列表
    """
    # Arrange - 准备企业微信原始用户数据
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    raw_user_data = {
        "userid": userid,
        "name": name,
        "department": department
    }
    
    if email is not None:
        raw_user_data["email"] = email
    
    if avatar is not None:
        raw_user_data["avatar"] = avatar
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证必需字段存在
    assert "id" in parsed_info, "缺少 id 字段"
    assert "email" in parsed_info, "缺少 email 字段"
    assert "name" in parsed_info, "缺少 name 字段"
    assert "provider" in parsed_info, "缺少 provider 字段"
    assert "corp_id" in parsed_info, "缺少 corp_id 字段"
    assert "department" in parsed_info, "缺少 department 字段"
    
    # 验证字段值正确
    assert parsed_info["id"] == userid, "id 应该等于 userid"
    assert parsed_info["name"] == name, "name 应该等于用户姓名"
    assert parsed_info["provider"] == "wecom", "provider 必须为 'wecom'"
    assert parsed_info["corp_id"] == WECOM_TEST_CONFIG["corp_id"], \
        "corp_id 应该等于配置中的企业 ID"
    assert parsed_info["department"] == department, \
        "department 应该等于原始部门列表"
    
    # 验证邮箱
    if email is not None:
        assert parsed_info["email"] == email, \
            "提供了企业邮箱时应该使用企业邮箱"
    else:
        # 没有企业邮箱时应该使用虚拟邮箱
        assert "@wecom.queryweaver.local" in parsed_info["email"], \
            "没有企业邮箱时应该使用虚拟邮箱"
        assert parsed_info["email"].startswith(userid), \
            "虚拟邮箱应该以 userid 开头"
    
    # 验证头像 (可选字段)
    if avatar is not None:
        assert "picture" in parsed_info
        assert parsed_info["picture"] == avatar


@given(
    userid=wecom_userid_strategy,
    name=nickname_strategy
)
@settings(max_examples=100, deadline=None)
def test_wecom_user_info_without_optional_fields(
    userid: str,
    name: str
):
    """
    属性测试: 企业微信用户信息解析应该正确处理缺失的可选字段
    
    即使缺少可选字段 (如 email, avatar, department),解析也应该成功,
    并且必需字段仍然存在。
    
    验证需求: 2.2.2.8
    
    Args:
        userid: 随机生成的 UserID
        name: 随机生成的用户姓名
    """
    # Arrange - 准备最小化的用户数据
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    raw_user_data = {
        "userid": userid,
        "name": name
        # 故意不包含 email, avatar, department
    }
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证必需字段仍然存在
    assert "id" in parsed_info
    assert "email" in parsed_info
    assert "name" in parsed_info
    assert "provider" in parsed_info
    assert "corp_id" in parsed_info
    assert "department" in parsed_info
    
    # 验证基本字段值
    assert parsed_info["id"] == userid
    assert parsed_info["name"] == name
    assert parsed_info["provider"] == "wecom"
    
    # 验证使用了虚拟邮箱
    assert "@wecom.queryweaver.local" in parsed_info["email"]
    
    # 验证部门列表为空列表
    assert parsed_info["department"] == []


@given(userid=wecom_userid_strategy)
@settings(max_examples=100, deadline=None)
def test_wecom_user_info_with_missing_name(userid: str):
    """
    属性测试: 企业微信用户信息解析应该为缺失的姓名提供默认值
    
    当用户数据中缺少姓名时,应该使用默认值 "企业微信用户"。
    
    验证需求: 2.2.2.8
    
    Args:
        userid: 随机生成的 UserID
    """
    # Arrange - 准备缺少姓名的用户数据
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    raw_user_data = {
        "userid": userid
        # 故意不包含 name
    }
    
    # Act - 执行解析
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # Assert - 验证使用了默认姓名
    assert parsed_info["name"] == "企业微信用户", \
        "缺少姓名时应该使用默认值 '企业微信用户'"


# -----------------------------
# 边界条件和特殊情况测试
# -----------------------------

def test_wechat_user_info_with_empty_nickname():
    """
    测试: 微信用户信息解析应该处理空昵称
    
    当昵称为空字符串时,应该使用默认值。
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    raw_user_data = {
        "openid": "test_openid_12345",
        "nickname": ""  # 空昵称
    }
    
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # 空昵称应该被替换为默认值
    assert parsed_info["name"] != ""
    assert len(parsed_info["name"]) > 0


def test_wecom_user_info_with_empty_name():
    """
    测试: 企业微信用户信息解析应该处理空姓名
    
    当姓名为空字符串时,应该使用默认值。
    """
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    raw_user_data = {
        "userid": "test_userid_12345",
        "name": ""  # 空姓名
    }
    
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # 空姓名应该被替换为默认值
    assert parsed_info["name"] != ""
    assert len(parsed_info["name"]) > 0


def test_wechat_user_info_with_special_characters():
    """
    测试: 微信用户信息解析应该正确处理特殊字符
    
    昵称可能包含表情符号、特殊字符等。
    """
    handler = WeChatOAuthHandler(WECHAT_TEST_CONFIG)
    
    raw_user_data = {
        "openid": "test_openid_12345",
        "nickname": "测试用户😀🎉"  # 包含中文和表情符号
    }
    
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # 应该保留原始昵称
    assert parsed_info["name"] == "测试用户😀🎉"


def test_wecom_user_info_with_multiple_departments():
    """
    测试: 企业微信用户信息解析应该正确处理多个部门
    
    用户可能属于多个部门。
    """
    handler = WeComOAuthHandler(WECOM_TEST_CONFIG)
    
    raw_user_data = {
        "userid": "test_userid_12345",
        "name": "张三",
        "department": [1, 2, 3, 10, 20]  # 多个部门
    }
    
    parsed_info = handler.parse_user_info(raw_user_data)
    
    # 应该保留所有部门
    assert parsed_info["department"] == [1, 2, 3, 10, 20]
    assert len(parsed_info["department"]) == 5
