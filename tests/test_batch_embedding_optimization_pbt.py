"""
属性测试：批量嵌入优化

Feature: deepseek-llm-support
Property 17: 批量嵌入优化
验证需求: 7.4, 12.2

属性：对于任意包含多个文本的嵌入请求，系统应该使用批量 API 而不是多次单独调用
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, call
from api.config import EmbeddingsModel


# 策略：生成文本列表（2-10 个文本）
text_lists = st.lists(
    st.text(min_size=1, max_size=100),
    min_size=2,
    max_size=10
)


@given(texts=text_lists)
@settings(
    max_examples=20,  # 减少到 20 个示例以加快测试
    deadline=5000  # 5 秒超时
)
def test_batch_embedding_uses_single_api_call(texts):
    """
    属性测试：批量嵌入使用单次 API 调用
    
    Feature: deepseek-llm-support, Property 17: 批量嵌入优化
    
    属性：对于任意包含多个文本的嵌入请求，应该使用批量 API（单次调用）
    而不是多次单独调用
    
    验证：
    1. 嵌入模型的 embed 方法只被调用一次
    2. 传入的参数是完整的文本列表
    3. 返回的嵌入向量数量与输入文本数量一致
    """
    # 创建模拟的嵌入模型
    with patch('litellm.embedding') as mock_embedding:
        # 模拟返回结果：每个文本返回一个 1536 维的向量
        mock_embedding.return_value = Mock(
            data=[
                {'embedding': [0.1] * 1536} 
                for _ in texts
            ]
        )
        
        # 创建嵌入模型实例
        embedding_model = EmbeddingsModel(model_name="openai/text-embedding-ada-002")
        
        # 调用 embed 方法
        embeddings = embedding_model.embed(texts)
        
        # 验证 1：litellm.embedding 只被调用一次（批量调用）
        assert mock_embedding.call_count == 1, \
            f"应该只调用一次批量 API，实际调用了 {mock_embedding.call_count} 次"
        
        # 验证 2：传入的参数是完整的文本列表
        call_args = mock_embedding.call_args
        assert call_args is not None, "应该有调用参数"
        
        # 检查传入的 input 参数
        if 'input' in call_args[1]:
            input_param = call_args[1]['input']
        else:
            input_param = call_args[0][0] if len(call_args[0]) > 0 else None
        
        assert isinstance(input_param, list), \
            f"传入的参数应该是列表，实际是 {type(input_param)}"
        assert len(input_param) == len(texts), \
            f"传入的文本数量应该是 {len(texts)}，实际是 {len(input_param)}"
        
        # 验证 3：返回的嵌入向量数量与输入文本数量一致
        assert len(embeddings) == len(texts), \
            f"返回的嵌入向量数量应该是 {len(texts)}，实际是 {len(embeddings)}"
        
        # 验证每个嵌入向量的维度
        for i, emb in enumerate(embeddings):
            assert isinstance(emb, list), \
                f"第 {i} 个嵌入向量应该是列表"
            assert len(emb) == 1536, \
                f"第 {i} 个嵌入向量维度应该是 1536，实际是 {len(emb)}"


@given(
    batch_size=st.integers(min_value=2, max_value=5),
    num_batches=st.integers(min_value=1, max_value=3)
)
@settings(
    max_examples=10,  # 减少到 10 个示例
    deadline=5000
)
def test_multiple_batches_optimization(batch_size, num_batches):
    """
    属性测试：多批次嵌入优化
    
    Feature: deepseek-llm-support, Property 17: 批量嵌入优化
    
    属性：当需要处理多批次文本时，每批次应该使用一次批量 API 调用，
    而不是对每个文本单独调用
    
    验证：
    1. API 调用次数等于批次数量（而不是文本总数）
    2. 每次调用传入的是一批文本列表
    """
    total_texts = batch_size * num_batches
    texts = [f"text_{i}" for i in range(total_texts)]
    
    with patch('litellm.embedding') as mock_embedding:
        # 模拟返回结果
        mock_embedding.return_value = Mock(
            data=[
                {'embedding': [0.1] * 1536} 
                for _ in range(batch_size)
            ]
        )
        
        embedding_model = EmbeddingsModel(model_name="openai/text-embedding-ada-002")
        
        # 模拟分批处理
        all_embeddings = []
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            embeddings = embedding_model.embed(batch)
            all_embeddings.extend(embeddings)
        
        # 验证：API 调用次数等于批次数量
        assert mock_embedding.call_count == num_batches, \
            f"应该调用 {num_batches} 次批量 API，实际调用了 {mock_embedding.call_count} 次"
        
        # 验证：每次调用传入的是批量文本
        for call_obj in mock_embedding.call_args_list:
            if 'input' in call_obj[1]:
                input_param = call_obj[1]['input']
            else:
                input_param = call_obj[0][0] if len(call_obj[0]) > 0 else None
            
            assert isinstance(input_param, list), \
                "每次调用应该传入列表"
            assert len(input_param) <= batch_size, \
                f"每批次大小不应超过 {batch_size}"
        
        # 验证：返回的总嵌入向量数量正确
        assert len(all_embeddings) == total_texts, \
            f"返回的嵌入向量总数应该是 {total_texts}，实际是 {len(all_embeddings)}"


@given(texts=text_lists)
@settings(
    max_examples=10,  # 减少到 10 个示例
    deadline=5000
)
def test_batch_embedding_preserves_order(texts):
    """
    属性测试：批量嵌入保持顺序
    
    Feature: deepseek-llm-support, Property 17: 批量嵌入优化
    
    属性：批量嵌入返回的向量顺序应该与输入文本顺序一致
    
    验证：
    1. 返回的嵌入向量顺序与输入文本顺序对应
    2. 可以通过索引正确访问对应的嵌入向量
    """
    with patch('litellm.embedding') as mock_embedding:
        # 为每个文本生成唯一的嵌入向量（使用索引作为第一个元素）
        mock_embedding.return_value = Mock(
            data=[
                {'embedding': [float(i)] + [0.1] * 1535} 
                for i in range(len(texts))
            ]
        )
        
        embedding_model = EmbeddingsModel(model_name="openai/text-embedding-ada-002")
        embeddings = embedding_model.embed(texts)
        
        # 验证：返回的嵌入向量数量正确
        assert len(embeddings) == len(texts), \
            "嵌入向量数量应该与输入文本数量一致"
        
        # 验证：顺序保持一致（通过第一个元素的值判断）
        for i, emb in enumerate(embeddings):
            assert emb[0] == float(i), \
                f"第 {i} 个嵌入向量的顺序不正确，期望 {float(i)}，实际 {emb[0]}"


@given(
    texts=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=1
    )
)
@settings(
    max_examples=5,  # 减少到 5 个示例
    deadline=5000
)
def test_single_text_still_uses_batch_api(texts):
    """
    属性测试：单个文本也使用批量 API
    
    Feature: deepseek-llm-support, Property 17: 批量嵌入优化
    
    属性：即使只有一个文本，也应该使用批量 API 接口（传入列表）
    保持接口一致性
    
    验证：
    1. 传入的参数是列表格式
    2. API 只被调用一次
    """
    with patch('litellm.embedding') as mock_embedding:
        mock_embedding.return_value = Mock(
            data=[{'embedding': [0.1] * 1536}]
        )
        
        embedding_model = EmbeddingsModel(model_name="openai/text-embedding-ada-002")
        embeddings = embedding_model.embed(texts)
        
        # 验证：只调用一次
        assert mock_embedding.call_count == 1, \
            "应该只调用一次 API"
        
        # 验证：传入的是列表
        call_args = mock_embedding.call_args
        if 'input' in call_args[1]:
            input_param = call_args[1]['input']
        else:
            input_param = call_args[0][0] if len(call_args[0]) > 0 else None
        
        assert isinstance(input_param, list), \
            "即使单个文本，也应该传入列表格式"
        
        # 验证：返回结果正确
        assert len(embeddings) == 1, \
            "应该返回一个嵌入向量"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
