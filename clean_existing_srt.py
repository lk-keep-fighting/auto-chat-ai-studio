#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量清理现有的SRT文件
移除UI元素（如 expand_less 之前的内容）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from video_automation import VideoProcessor

def clean_all_srt_files():
    """批量清理所有SRT文件"""
    
    print("=" * 60)
    print("🧹 批量清理SRT文件")
    print("=" * 60)
    
    # 查找所有SRT文件
    process_folder = Path("assets/Process_Folder")
    srt_files = list(process_folder.glob("**/step_23_output_*.srt"))
    
    if not srt_files:
        print("❌ 未找到任何SRT文件")
        return
    
    print(f"\n📋 找到 {len(srt_files)} 个SRT文件")
    
    processor = VideoProcessor()
    cleaned_count = 0
    
    for srt_file in srt_files:
        print(f"\n📄 处理: {srt_file.relative_to(process_folder)}")
        
        try:
            # 读取原始内容
            with open(srt_file, "r", encoding="utf-8") as f:
                original_content = f.read()
            
            # 检查是否需要清理
            if 'expand_less' in original_content or 'expand_more' in original_content:
                print(f"  🔍 检测到UI元素，需要清理")
                
                # 清理内容
                cleaned_content = processor._clean_srt_content(original_content)
                
                # 备份原文件
                backup_file = srt_file.with_suffix('.srt.bak')
                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(original_content)
                print(f"  💾 已备份到: {backup_file.name}")
                
                # 保存清理后的内容
                with open(srt_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                
                print(f"  ✅ 已清理: {len(original_content)} → {len(cleaned_content)} 字符")
                print(f"  📉 减少了: {len(original_content) - len(cleaned_content)} 字符")
                cleaned_count += 1
            else:
                # 检查是否以序号1开始
                if original_content.strip().startswith('1\n') or original_content.strip().startswith('1 '):
                    print(f"  ✅ 内容正常，无需清理")
                else:
                    print(f"  ⚠️ 内容格式可能有问题，但未检测到UI元素")
                    print(f"  开头内容: {original_content[:50]}")
        
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ 清理完成: {cleaned_count}/{len(srt_files)} 个文件")
    print("=" * 60)
    
    if cleaned_count > 0:
        print("\n💡 提示:")
        print("  - 原文件已备份为 .srt.bak")
        print("  - 如需恢复，可以删除清理后的文件并重命名备份文件")

if __name__ == "__main__":
    clean_all_srt_files()
