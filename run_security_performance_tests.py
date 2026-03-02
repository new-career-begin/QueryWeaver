#!/usr/bin/env python3
"""
安全和性能优化测试运行脚本

此脚本运行所有与安全和性能优化相关的测试，包括：
- CSRF 防护测试
- Token 管理测试
- 性能优化测试
- 错误处理测试
- 用户管理测试
"""

import subprocess
import sys
from pathlib import Path


def run_tests(test_files: list[str]) -> tuple[int, int]:
    """
    运行指定的测试文件
    
    Args:
        test_files: 测试文件路径列表
        
    Returns:
        (成功数, 失败数)
    """
    success_count = 0
    failure_count = 0
    
    for test_file in test_files:
        print(f"\n{'='*80}")
        print(f"运行测试: {test_file}")
        print(f"{'='*80}\n")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=False,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"\n✓ {test_file} 测试通过")
                success_count += 1
            else:
                print(f"\n✗ {test_file} 测试失败")
                failure_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"\n✗ {test_file} 测试超时")
            failure_count += 1
        except Exception as e:
            print(f"\n✗ {test_file} 运行出错: {str(e)}")
            failure_count += 1
    
    return success_count, failure_count


def main():
    """主函数"""
    print("="*80)
    print("安全和性能优化测试套件")
    print("="*80)
    
    # 定义测试文件列表
    test_files = [
        "tests/test_csrf_protection.py",           # 任务 8.1, 8.2: CSRF 防护
        "tests/test_token_management.py",          # 任务 8.3, 8.4: Token 管理
        "tests/test_performance_optimization.py",  # 任务 9.1, 9.2, 9.3: 性能优化
        "tests/test_wechat_oauth_error_handling.py",  # 任务 5.1, 5.2, 5.4: 错误处理
        "tests/test_wechat_oauth_user_management.py", # 任务 4.2: 用户管理
    ]
    
    # 检查测试文件是否存在
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print("\n警告: 以下测试文件不存在:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n将只运行存在的测试文件...\n")
        test_files = [f for f in test_files if f not in missing_files]
    
    if not test_files:
        print("\n错误: 没有找到任何测试文件!")
        return 1
    
    # 运行测试
    success_count, failure_count = run_tests(test_files)
    
    # 输出总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"总测试文件数: {len(test_files)}")
    print(f"通过: {success_count}")
    print(f"失败: {failure_count}")
    
    if failure_count == 0:
        print("\n✓ 所有安全和性能优化测试通过!")
        return 0
    else:
        print(f"\n✗ 有 {failure_count} 个测试文件失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
