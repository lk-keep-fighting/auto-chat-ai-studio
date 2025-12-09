#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试test_步骤23_SRT文件的清理功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from video_automation import VideoProcessor

def test_srt_cleaning():
    """测试SRT内容清理"""
    
    # 读取有问题的SRT文件
    srt_file = Path("assets/Process_Folder/test_步骤23_SRT文件/step_23_output_1.srt")
    
    if not srt_file.exists():
        print(f"❌ 文件不存在: {srt_file}")
        return
    
    print("=" * 60)
    print("🧪 测试test_步骤23_SRT文件的清理功能")
    print("=" * 60)
    
    # 读取原始内容
    with open(srt_file, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    print(f"\n📄 原始文件: {srt_file}")
    print(f"📏 原始长度: {len(original_content)} 字符")
    print(f"\n原始内容:")
    print("-" * 60)
    print(original_content)
    print("-" * 60)
    
    # 创建VideoProcessor实例并清理内容
    processor = VideoProcessor()
    cleaned_content = processor._clean_srt_content(original_content)
    
    print(f"\n✨ 清理后长度: {len(cleaned_content)} 字符")
    print(f"📉 减少了: {len(original_content) - len(cleaned_content)} 字符")
    print(f"\n清理后内容:")
    print("-" * 60)
    print(cleaned_content)
    print("-" * 60)
    
    # 保存清理后的内容
    cleaned_file = srt_file.parent / f"{srt_file.stem}_cleaned.srt"
    with open(cleaned_file, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    print(f"\n✅ 清理后的内容已保存到: {cleaned_file}")
    
    # 验证清理效果
    print("\n🔍 验证清理效果:")
    ui_keywords = ['code', 'Srt', 'download', 'content_copy', 'expand_less', 'expand_more', 'SRT 文件 B']
    found_keywords = [kw for kw in ui_keywords if kw in cleaned_content]
    
    if found_keywords:
        print(f"⚠️ 仍然包含UI关键词: {', '.join(found_keywords)}")
    else:
        print("✅ 已移除所有UI关键词")
    
    # 检查是否以序号1开始
    if cleaned_content.strip().startswith('1\n') or cleaned_content.strip().startswith('1 '):
        print("✅ 内容以序号1开始")
    else:
        print(f"⚠️ 内容不是以序号1开始，而是: {cleaned_content[:20]}")
    
    # 检查末尾是否干净
    last_lines = cleaned_content.strip().split('\n')[-5:]
    print(f"\n📋 最后5行:")
    for i, line in enumerate(last_lines, 1):
        print(f"  {i}. {repr(line)}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_srt_cleaning()
