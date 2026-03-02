#!/usr/bin/env python3
"""
自动保存 ASCII 设计稿到项目根目录的 ascii-ui-design/ 文件夹

使用方法:
    python scripts/save_design.py "设计内容" "页面名称" [版本号或时间戳]

示例:
    python scripts/save_design.py "$(cat design.txt)" "login_page" "v1"
    python scripts/save_design.py "$(cat design.txt)" "dashboard" "20250112"
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def find_project_root():
    """查找项目根目录（包含 .git 或 package.json 的目录）"""
    current = Path.cwd()
    
    # 检查当前目录
    if (current / '.git').exists() or (current / 'package.json').exists():
        return current
    
    # 向上查找
    for parent in current.parents:
        if (parent / '.git').exists() or (parent / 'package.json').exists():
            return parent
    
    # 如果找不到，使用当前目录
    return current


def save_design(design_content, page_name, version_or_timestamp=None):
    """
    保存设计稿到 ascii-ui-design/ 文件夹
    
    Args:
        design_content: ASCII 设计稿内容
        page_name: 页面名称
        version_or_timestamp: 版本号（如 "v1"）或时间戳（如 "20250112"），如果为 None 则使用当前时间戳
    """
    project_root = find_project_root()
    output_dir = project_root / 'ascii-ui-design'
    
    # 创建输出目录（如果不存在）
    output_dir.mkdir(exist_ok=True)
    
    # 确定文件名
    if version_or_timestamp:
        if version_or_timestamp.startswith('v'):
            filename = f"{page_name}_{version_or_timestamp}.txt"
        else:
            filename = f"{page_name}_{version_or_timestamp}.txt"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{page_name}_{timestamp}.txt"
    
    filepath = output_dir / filename
    
    # 保存文件
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(design_content)
        print(f"✅ 设计稿已保存到: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"❌ 保存失败: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("用法: python save_design.py <设计内容> <页面名称> [版本号或时间戳]", file=sys.stderr)
        print("示例: python save_design.py \"$(cat design.txt)\" \"login_page\" \"v1\"", file=sys.stderr)
        sys.exit(1)
    
    design_content = sys.argv[1]
    page_name = sys.argv[2]
    version_or_timestamp = sys.argv[3] if len(sys.argv) > 3 else None
    
    save_design(design_content, page_name, version_or_timestamp)


if __name__ == "__main__":
    main()
