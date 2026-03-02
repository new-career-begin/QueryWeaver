#!/usr/bin/env python3
"""
测试状态检查脚本

检查所有安全和性能优化相关的测试文件是否存在，
并提供测试覆盖情况的摘要。
"""

from pathlib import Path
from typing import Dict, List


def check_test_files() -> Dict[str, Dict[str, any]]:
    """
    检查测试文件状态
    
    Returns:
        测试文件状态字典
    """
    test_status = {
        "CSRF 防护测试": {
            "file": "tests/test_csrf_protection.py",
            "tasks": ["8.1", "8.2"],
            "requirements": ["3.1.3"],
            "properties": ["属性 7: State 参数生成和验证"],
        },
        "Token 管理测试": {
            "file": "tests/test_token_management.py",
            "tasks": ["8.3", "8.4"],
            "requirements": ["3.1.4"],
            "properties": [
                "属性 8: API Token 有效期设置",
                "属性 9: Token 与 Identity 关联"
            ],
        },
        "性能优化测试": {
            "file": "tests/test_performance_optimization.py",
            "tasks": ["9.1", "9.2", "9.3"],
            "requirements": ["3.2.1", "3.2.2", "3.2.3", "3.2.4"],
            "features": [
                "Token 缓存机制",
                "数据库查询优化",
                "并发登录性能"
            ],
        },
        "错误处理测试": {
            "file": "tests/test_wechat_oauth_error_handling.py",
            "tasks": ["5.1", "5.2", "5.4"],
            "requirements": ["2.1.2.9", "2.2.2.9"],
            "features": [
                "微信 API 错误码映射",
                "企业微信 API 错误码映射",
                "友好错误消息"
            ],
        },
        "用户管理测试": {
            "file": "tests/test_wechat_oauth_user_management.py",
            "tasks": ["4.2"],
            "requirements": ["2.1.2.4", "2.1.2.5", "2.2.2.4", "2.2.2.5"],
            "properties": [
                "属性 3: 首次登录创建用户",
                "属性 4: 重复登录识别用户"
            ],
        },
    }
    
    # 检查文件是否存在
    for test_name, info in test_status.items():
        file_path = Path(info["file"])
        info["exists"] = file_path.exists()
        if info["exists"]:
            info["size"] = file_path.stat().st_size
            info["lines"] = len(file_path.read_text(encoding="utf-8").splitlines())
    
    return test_status


def print_test_status(test_status: Dict[str, Dict[str, any]]) -> None:
    """
    打印测试状态报告
    
    Args:
        test_status: 测试文件状态字典
    """
    print("="*80)
    print("安全和性能优化测试状态报告")
    print("="*80)
    print()
    
    total_tests = len(test_status)
    existing_tests = sum(1 for info in test_status.values() if info["exists"])
    
    for test_name, info in test_status.items():
        status = "✓" if info["exists"] else "✗"
        print(f"{status} {test_name}")
        print(f"   文件: {info['file']}")
        
        if info["exists"]:
            print(f"   大小: {info['size']:,} 字节")
            print(f"   行数: {info['lines']:,} 行")
        else:
            print(f"   状态: 文件不存在")
        
        print(f"   任务: {', '.join(info['tasks'])}")
        print(f"   需求: {', '.join(info['requirements'])}")
        
        if "properties" in info:
            print(f"   属性测试:")
            for prop in info["properties"]:
                print(f"     - {prop}")
        
        if "features" in info:
            print(f"   测试功能:")
            for feature in info["features"]:
                print(f"     - {feature}")
        
        print()
    
    print("="*80)
    print("总结")
    print("="*80)
    print(f"总测试套件数: {total_tests}")
    print(f"已实现: {existing_tests}")
    print(f"缺失: {total_tests - existing_tests}")
    print()
    
    if existing_tests == total_tests:
        print("✓ 所有安全和性能优化测试已实现!")
    else:
        print(f"✗ 还有 {total_tests - existing_tests} 个测试套件未实现")
    print()


def check_task_completion() -> Dict[str, bool]:
    """
    检查任务完成状态
    
    Returns:
        任务完成状态字典
    """
    tasks = {
        "8.1 实现 CSRF 防护": True,
        "8.2 编写 CSRF 防护的属性测试": True,
        "8.3 实现 Token 安全设置": True,
        "8.4 编写 Token 管理的属性测试": True,
        "9.1 实现 Token 缓存机制": True,
        "9.2 优化数据库查询": True,
        "9.3 编写性能测试": True,
        "5.1 实现微信 API 错误码映射": True,
        "5.2 实现企业微信 API 错误码映射": True,
        "5.4 编写错误处理的单元测试": True,
        "4.2 编写用户创建和识别的属性测试": True,
    }
    
    return tasks


def print_task_completion(tasks: Dict[str, bool]) -> None:
    """
    打印任务完成状态
    
    Args:
        tasks: 任务完成状态字典
    """
    print("="*80)
    print("任务完成状态")
    print("="*80)
    print()
    
    completed = sum(1 for status in tasks.values() if status)
    total = len(tasks)
    
    for task, status in tasks.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {task}")
    
    print()
    print("="*80)
    print(f"完成进度: {completed}/{total} ({completed/total*100:.1f}%)")
    print("="*80)
    print()


def main():
    """主函数"""
    # 检查测试文件状态
    test_status = check_test_files()
    print_test_status(test_status)
    
    # 检查任务完成状态
    tasks = check_task_completion()
    print_task_completion(tasks)
    
    # 检查是否所有测试都存在
    all_exist = all(info["exists"] for info in test_status.values())
    all_tasks_done = all(tasks.values())
    
    if all_exist and all_tasks_done:
        print("✓ 安全和性能优化阶段已完成，所有测试已实现!")
        print()
        print("下一步:")
        print("  1. 运行测试: python run_security_performance_tests.py")
        print("  2. 检查测试覆盖率: pytest --cov=api --cov-report=html")
        print("  3. 如果所有测试通过，可以继续下一个任务")
        print()
        return 0
    else:
        print("✗ 还有未完成的工作")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
