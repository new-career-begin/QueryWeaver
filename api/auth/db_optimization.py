"""数据库优化模块

提供数据库索引创建和查询优化功能，用于提升 OAuth 认证相关的查询性能。
"""

import logging
from typing import List, Dict, Any
from api.extensions import db

logger = logging.getLogger(__name__)


async def create_identity_indexes() -> Dict[str, bool]:
    """
    为 Identity 节点创建索引，优化查询性能
    
    创建以下索引：
    1. provider + provider_user_id 复合索引（用于快速查找身份）
    2. email 索引（用于跨提供商账号关联）
    3. last_login 索引（用于查询活跃用户）
    
    Returns:
        包含索引创建结果的字典
    """
    results = {}
    
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # 1. 为 provider + provider_user_id 创建复合索引
        # 这是最常用的查询模式，用于身份验证
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (i:Identity) ON (i.provider, i.provider_user_id)
                """
            )
            results["provider_composite_index"] = True
            logger.info("成功创建 Identity 节点的 provider 复合索引")
        except Exception as e:
            # 索引可能已存在
            logger.warning("创建 provider 复合索引失败（可能已存在）: %s", str(e))
            results["provider_composite_index"] = False
        
        # 2. 为 email 创建索引
        # 用于跨提供商账号关联和邮箱查询
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (i:Identity) ON (i.email)
                """
            )
            results["email_index"] = True
            logger.info("成功创建 Identity 节点的 email 索引")
        except Exception as e:
            logger.warning("创建 email 索引失败（可能已存在）: %s", str(e))
            results["email_index"] = False
        
        # 3. 为 last_login 创建索引
        # 用于查询活跃用户和统计分析
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (i:Identity) ON (i.last_login)
                """
            )
            results["last_login_index"] = True
            logger.info("成功创建 Identity 节点的 last_login 索引")
        except Exception as e:
            logger.warning("创建 last_login 索引失败（可能已存在）: %s", str(e))
            results["last_login_index"] = False
        
        return results
        
    except Exception as e:
        logger.error("创建 Identity 索引时发生错误: %s", str(e))
        return {"error": str(e)}


async def create_token_indexes() -> Dict[str, bool]:
    """
    为 Token 节点创建索引，优化 Token 查询性能
    
    创建以下索引：
    1. id 索引（Token 主键）
    2. expires_at 索引（用于清理过期 Token）
    
    Returns:
        包含索引创建结果的字典
    """
    results = {}
    
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # 1. 为 Token id 创建索引
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (t:Token) ON (t.id)
                """
            )
            results["token_id_index"] = True
            logger.info("成功创建 Token 节点的 id 索引")
        except Exception as e:
            logger.warning("创建 Token id 索引失败（可能已存在）: %s", str(e))
            results["token_id_index"] = False
        
        # 2. 为 expires_at 创建索引
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (t:Token) ON (t.expires_at)
                """
            )
            results["expires_at_index"] = True
            logger.info("成功创建 Token 节点的 expires_at 索引")
        except Exception as e:
            logger.warning("创建 expires_at 索引失败（可能已存在）: %s", str(e))
            results["expires_at_index"] = False
        
        return results
        
    except Exception as e:
        logger.error("创建 Token 索引时发生错误: %s", str(e))
        return {"error": str(e)}


async def create_user_indexes() -> Dict[str, bool]:
    """
    为 User 节点创建索引，优化用户查询性能
    
    创建以下索引：
    1. email 索引（用户主键）
    
    Returns:
        包含索引创建结果的字典
    """
    results = {}
    
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # 为 User email 创建索引
        try:
            await organizations_graph.query(
                """
                CREATE INDEX FOR (u:User) ON (u.email)
                """
            )
            results["user_email_index"] = True
            logger.info("成功创建 User 节点的 email 索引")
        except Exception as e:
            logger.warning("创建 User email 索引失败（可能已存在）: %s", str(e))
            results["user_email_index"] = False
        
        return results
        
    except Exception as e:
        logger.error("创建 User 索引时发生错误: %s", str(e))
        return {"error": str(e)}


async def initialize_all_indexes() -> Dict[str, Any]:
    """
    初始化所有认证相关的数据库索引
    
    这个函数应该在应用启动时调用一次，确保所有必要的索引都已创建。
    
    Returns:
        包含所有索引创建结果的字典
    """
    logger.info("开始初始化数据库索引...")
    
    results = {
        "identity_indexes": await create_identity_indexes(),
        "token_indexes": await create_token_indexes(),
        "user_indexes": await create_user_indexes()
    }
    
    # 统计成功创建的索引数量
    total_success = sum(
        1 for category in results.values()
        if isinstance(category, dict)
        for value in category.values()
        if value is True
    )
    
    logger.info(f"数据库索引初始化完成，成功创建 {total_success} 个索引")
    
    return results


async def get_index_info() -> List[Dict[str, Any]]:
    """
    获取当前数据库中的所有索引信息
    
    Returns:
        索引信息列表
    """
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # FalkorDB 使用 CALL db.indexes() 查询索引
        result = await organizations_graph.query("CALL db.indexes()")
        
        indexes = []
        if result.result_set:
            for row in result.result_set:
                indexes.append({
                    "label": row[0] if len(row) > 0 else None,
                    "property": row[1] if len(row) > 1 else None,
                    "type": row[2] if len(row) > 2 else None
                })
        
        logger.info(f"当前数据库共有 {len(indexes)} 个索引")
        return indexes
        
    except Exception as e:
        logger.error("获取索引信息时发生错误: %s", str(e))
        return []


async def optimize_user_query(
    provider: str,
    provider_user_id: str
) -> Dict[str, Any]:
    """
    优化的用户查询函数
    
    使用索引加速查询，减少查询时间
    
    Args:
        provider: 认证提供商
        provider_user_id: 提供商用户ID
        
    Returns:
        用户信息字典，如果未找到返回 None
    """
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # 使用索引优化的查询
        # FalkorDB 会自动使用 (provider, provider_user_id) 复合索引
        query = """
        MATCH (identity:Identity {provider: $provider, provider_user_id: $provider_user_id})
        MATCH (identity)-[:AUTHENTICATES]->(user:User)
        RETURN identity, user
        """
        
        result = await organizations_graph.query(
            query,
            {
                "provider": provider,
                "provider_user_id": provider_user_id
            }
        )
        
        if result.result_set:
            identity = result.result_set[0][0]
            user = result.result_set[0][1]
            return {
                "identity": identity,
                "user": user
            }
        
        return None
        
    except Exception as e:
        logger.error(
            "优化查询用户信息时发生错误: provider=%s, provider_user_id=%s, error=%s",
            provider,
            provider_user_id,
            str(e)
        )
        return None


async def cleanup_expired_tokens() -> int:
    """
    清理过期的 Token
    
    使用 expires_at 索引快速查找并删除过期的 Token
    
    Returns:
        删除的 Token 数量
    """
    try:
        organizations_graph = db.select_graph("Organizations")
        
        # 使用索引查找过期 Token
        query = """
        MATCH (t:Token)
        WHERE t.expires_at < timestamp()
        DELETE t
        RETURN count(t) as deleted_count
        """
        
        result = await organizations_graph.query(query)
        
        if result.result_set:
            deleted_count = result.result_set[0][0]
            logger.info(f"已清理 {deleted_count} 个过期 Token")
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error("清理过期 Token 时发生错误: %s", str(e))
        return 0
