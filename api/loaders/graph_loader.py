"""Graph loader module for loading data into graph databases."""

import json

import tqdm

from api.config import Config
from api.extensions import db
from api.utils import generate_db_description, create_combined_description


async def load_to_graph(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    graph_id: str,
    entities: dict,
    relationships: dict,
    batch_size: int = 100,
    db_name: str = "TBD",
    db_url: str = "",
    user_email: str = None,
) -> None:
    """
    将数据加载到图数据库中
    
    从数据库模式提取的实体和关系加载到 FalkorDB 图数据库中。
    支持使用用户配置的嵌入模型生成向量表示。
    
    Args:
        graph_id: 图数据库标识符
        entities: 包含实体及其属性的字典
        relationships: 包含实体间关系的字典
        batch_size: 批量嵌入的大小
        db_name: 数据库名称
        db_url: 数据库连接 URL
        user_email: 可选的用户邮箱，用于加载用户配置的嵌入模型
    """
    graph = db.select_graph(graph_id)
    
    # 使用用户配置的嵌入模型（如果提供了用户邮箱）
    embedding_model = await Config.get_embedding_model(user_email)
    vec_len = embedding_model.get_vector_size()
    
    # 验证向量维度与 FalkorDB 配置一致
    # FalkorDB 默认向量维度通常是 1536 (OpenAI text-embedding-ada-002)
    # 如果使用其他模型，需要确保维度匹配
    import logging
    logger = logging.getLogger(__name__)
    
    # 记录嵌入模型信息
    logger.info(f"使用嵌入模型: {embedding_model.model_name}, 向量维度: {vec_len}")
    
    # 检查向量维度是否在合理范围内
    if vec_len < 128 or vec_len > 4096:
        logger.warning(
            f"向量维度 {vec_len} 超出常见范围 [128, 4096]，"
            f"请确认嵌入模型配置正确"
        )
    
    # 如果之前已经创建了向量索引，验证维度是否一致
    # 这里我们记录维度信息，供后续调试使用
    logger.debug(f"图数据库 {graph_id} 将使用向量维度: {vec_len}")

    create_combined_description(entities)

    try:
        # Create vector indices
        await graph.query(
            """
            CREATE VECTOR INDEX FOR (t:Table) ON (t.embedding)
            OPTIONS {dimension:$size, similarityFunction:'euclidean'}
        """,
            {"size": vec_len},
        )

        await graph.query(
            """
            CREATE VECTOR INDEX FOR (c:Column) ON (c.embedding)
            OPTIONS {dimension:$size, similarityFunction:'euclidean'}
        """,
            {"size": vec_len},
        )
        await graph.query("CREATE INDEX FOR (p:Table) ON (p.name)")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error creating vector indices: {str(e)}")

    db_des = generate_db_description(db_name=db_name, table_names=list(entities.keys()))
    await graph.query(
        """
        CREATE (d:Database {
            name: $db_name,
            description: $description,
            url: $url
        })
        """,
        {"db_name": db_name, "description": db_des, "url": db_url},
    )

    # 批量生成所有表的嵌入向量（优化性能）
    table_names = list(entities.keys())
    table_descriptions = [entities[name]["description"] for name in table_names]
    
    # 使用批量 API 一次性生成所有表的嵌入
    table_embeddings = embedding_model.embed(table_descriptions)
    
    # 创建表节点映射
    table_embedding_map = dict(zip(table_names, table_embeddings))

    for table_name, table_info in tqdm.tqdm(entities.items(), desc="Creating Graph Table Nodes"):
        table_desc = table_info["description"]
        # 使用预先批量生成的嵌入向量
        table_embedding = table_embedding_map[table_name]
        fk = json.dumps(table_info.get("foreign_keys", []))

        # Create table node
        await graph.query(
            """
            CREATE (t:Table {
                name: $table_name,
                description: $description,
                embedding: vecf32($embedding),
                foreign_keys: $foreign_keys
            })
            """,
            {
                "table_name": table_name,
                "description": table_desc,
                "embedding": table_embedding,
                "foreign_keys": fk,
            },
        )

        # Batch embeddings for table columns
        # TODO: Check if the embedding model and description are correct  # pylint: disable=fixme
        # (without 2 sources of truth)
        batch_flag = True
        col_descriptions = table_info.get("col_descriptions")
        if col_descriptions is None:
            batch_flag = False
        else:
            try:
                embed_columns = []
                for batch in tqdm.tqdm(
                    [
                        col_descriptions[i : i + batch_size]
                        for i in range(0, len(col_descriptions), batch_size)
                    ],
                    desc=f"Creating embeddings for {table_name} columns",
                ):

                    embedding_result = embedding_model.embed(batch)
                    embed_columns.extend(embedding_result)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error creating embeddings: {str(e)}")
                batch_flag = False

        # Create column nodes
        for idx, (col_name, col_info) in tqdm.tqdm(
            enumerate(table_info["columns"].items()),
            desc=f"Creating Graph Columns for {table_name}",
            total=len(table_info["columns"]),
        ):
            if not batch_flag:
                embed_columns = []
                embedding_result = embedding_model.embed(col_info["description"])
                embed_columns.extend(embedding_result)
                idx = 0

            # Combine description with sample values after embedding is created
            final_description = col_info["description"]
            sample_values = col_info.get("sample_values", [])
            if sample_values:
                sample_values_str = f"(Sample values: {', '.join(f'({v})' for v in sample_values)})"
                final_description = f"{final_description} {sample_values_str}"

            await graph.query(
                """
                MATCH (t:Table {name: $table_name})
                CREATE (c:Column {
                    name: $col_name,
                    type: $type,
                    nullable: $nullable,
                    key_type: $key,
                    description: $description,
                    embedding: vecf32($embedding)
                })-[:BELONGS_TO]->(t)
                """,
                {
                    "table_name": table_name,
                    "col_name": col_name,
                    "type": col_info.get("type", "unknown"),
                    "nullable": col_info.get("null", "unknown"),
                    "key": col_info.get("key", "unknown"),
                    "description": final_description,
                    "embedding": embed_columns[idx],
                },
            )

    # Create relationships
    for rel_name, table_info in tqdm.tqdm(
        relationships.items(), desc="Creating Graph Table Relationships"
    ):
        for rel in table_info:
            source_table = rel["from"]
            source_field = rel["source_column"]
            target_table = rel["to"]
            target_field = rel["target_column"]
            note = rel.get("note", "")

            # Create relationship if both tables and columns exist
            try:
                await graph.query(
                    """
                    MATCH (src:Column {name: $source_col})
                        -[:BELONGS_TO]->(source:Table {name: $source_table})
                    MATCH (tgt:Column {name: $target_col})
                        -[:BELONGS_TO]->(target:Table {name: $target_table})
                    CREATE (src)-[:REFERENCES {
                        rel_name: $rel_name,
                        note: $note
                    }]->(tgt)
                    """,
                    {
                        "source_col": source_field,
                        "target_col": target_field,
                        "source_table": source_table,
                        "target_table": target_table,
                        "rel_name": rel_name,
                        "note": note,
                    },
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Warning: Could not create relationship: {str(e)}")
                continue
