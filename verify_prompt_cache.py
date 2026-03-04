"""
Prompt 缓存性能验证脚本

演示 Prompt 模板缓存的性能提升效果
"""

import time
from api.prompt_cache import get_prompt_cache, PromptCache, clear_prompt_cache


def simulate_prompt_building():
    """模拟构建复杂的 Prompt 模板"""
    # 模拟一些计算开销
    time.sleep(0.005)  # 5ms
    
    # 返回一个大型模板
    template = """
    You are a professional Text-to-SQL system.
    
    Database: {database_type}
    Schema: {schema}
    User Query: {user_query}
    Instructions: {instructions}
    
    """ + "Additional context and rules... " * 100
    
    return template


def benchmark_without_cache(iterations=10):
    """基准测试：不使用缓存"""
    print("=" * 60)
    print("基准测试：不使用缓存")
    print("=" * 60)
    
    total_time = 0
    
    for i in range(iterations):
        start = time.time()
        
        # 每次都重新构建 Prompt
        template = simulate_prompt_building()
        prompt = template.format(
            database_type="postgresql",
            schema="users, orders",
            user_query="查询所有用户",
            instructions="使用标准 SQL"
        )
        
        elapsed = time.time() - start
        total_time += elapsed
        
        if i == 0:
            print(f"第 {i+1} 次: {elapsed*1000:.2f}ms (首次)")
        elif i < 3:
            print(f"第 {i+1} 次: {elapsed*1000:.2f}ms")
    
    avg_time = total_time / iterations
    print(f"\n平均时间: {avg_time*1000:.2f}ms")
    print(f"总时间: {total_time*1000:.2f}ms")
    
    return avg_time


def benchmark_with_cache(iterations=10):
    """基准测试：使用缓存"""
    print("\n" + "=" * 60)
    print("基准测试：使用缓存")
    print("=" * 60)
    
    clear_prompt_cache()
    cache = get_prompt_cache()
    
    cache_key = PromptCache.generate_cache_key(
        template_type='analysis',
        database_type='postgresql',
        has_instructions=True
    )
    
    total_time = 0
    
    for i in range(iterations):
        start = time.time()
        
        # 尝试从缓存获取
        template = cache.get(cache_key)
        
        if template is None:
            # 缓存未命中，构建并缓存
            template = simulate_prompt_building()
            cache.set(cache_key, template)
        
        # 替换动态内容
        prompt = template.format(
            database_type="postgresql",
            schema="users, orders",
            user_query="查询所有用户",
            instructions="使用标准 SQL"
        )
        
        elapsed = time.time() - start
        total_time += elapsed
        
        if i == 0:
            print(f"第 {i+1} 次: {elapsed*1000:.2f}ms (首次，缓存未命中)")
        elif i < 3:
            print(f"第 {i+1} 次: {elapsed*1000:.2f}ms (缓存命中)")
    
    avg_time = total_time / iterations
    print(f"\n平均时间: {avg_time*1000:.2f}ms")
    print(f"总时间: {total_time*1000:.2f}ms")
    
    # 显示缓存统计
    stats = cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  命中率: {stats['hit_rate']:.2%}")
    print(f"  命中次数: {stats['hits']}")
    print(f"  未命中次数: {stats['misses']}")
    print(f"  缓存大小: {stats['cache_size']}")
    
    return avg_time


def demonstrate_cache_benefits():
    """演示缓存的性能优势"""
    print("\n" + "=" * 60)
    print("Prompt 模板缓存性能验证")
    print("=" * 60)
    print("\n测试场景：模拟 10 次 Prompt 构建请求")
    print("每次构建耗时约 5ms + 模板处理时间\n")
    
    # 运行基准测试
    time_without_cache = benchmark_without_cache(iterations=10)
    time_with_cache = benchmark_with_cache(iterations=10)
    
    # 计算性能提升
    improvement = time_without_cache / time_with_cache
    time_saved = (time_without_cache - time_with_cache) * 1000
    
    print("\n" + "=" * 60)
    print("性能对比总结")
    print("=" * 60)
    print(f"不使用缓存平均时间: {time_without_cache*1000:.2f}ms")
    print(f"使用缓存平均时间:   {time_with_cache*1000:.2f}ms")
    print(f"性能提升:           {improvement:.1f}x")
    print(f"每次请求节省:       {time_saved:.2f}ms")
    print("\n结论：使用 Prompt 缓存可以显著减少重复构建开销！")


def demonstrate_cache_scenarios():
    """演示不同场景下的缓存效果"""
    print("\n" + "=" * 60)
    print("多场景缓存测试")
    print("=" * 60)
    
    clear_prompt_cache()
    cache = get_prompt_cache()
    
    scenarios = [
        {'db': 'postgresql', 'has_memory': True, 'has_instructions': True},
        {'db': 'postgresql', 'has_memory': False, 'has_instructions': True},
        {'db': 'mysql', 'has_memory': True, 'has_instructions': True},
        {'db': 'postgresql', 'has_memory': True, 'has_instructions': True},  # 重复
    ]
    
    print("\n测试 4 个不同的场景（第 4 个与第 1 个相同）:\n")
    
    for i, scenario in enumerate(scenarios, 1):
        cache_key = PromptCache.generate_cache_key(
            template_type='analysis',
            database_type=scenario['db'],
            has_memory=scenario['has_memory'],
            has_instructions=scenario['has_instructions']
        )
        
        start = time.time()
        template = cache.get(cache_key)
        
        if template is None:
            template = simulate_prompt_building()
            cache.set(cache_key, template)
            status = "缓存未命中，已构建"
        else:
            status = "缓存命中"
        
        elapsed = time.time() - start
        
        print(f"场景 {i}: db={scenario['db']}, "
              f"memory={scenario['has_memory']}, "
              f"instructions={scenario['has_instructions']}")
        print(f"  状态: {status}")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print()
    
    stats = cache.get_stats()
    print(f"最终缓存统计:")
    print(f"  缓存大小: {stats['cache_size']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")


if __name__ == "__main__":
    # 运行性能验证
    demonstrate_cache_benefits()
    
    # 运行多场景测试
    demonstrate_cache_scenarios()
    
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
