#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制清理所有SRT文件，移除末尾的UI元素和无关内容
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from video_automation import VideoProcessor

def force_clean_all_srt_files():
    """强制清理所有SRT文件"""
    
    print("=" * 60)
    print("🧹 强制清理所有SRT文件")
    print("=" * 60)
    
    # 查找所有SRT文件
    process_folder = Path("assets/Process_Folder")
    srt_files = list(process_folder.glob("**/step_23_output_*.srt"))
    
    # 排除已清理的文件
    srt_files = [f for f in srt_files if '_cleaned' not in f.name]
    
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
            
            original_len = len(original_content)
            
            # 清理内容
            cleaned_content = processor._clean_srt_content(original_content)
            cleaned_len = len(cleaned_content)
            
            # 如果内容有变化，则保存
            if cleaned_len != original_len:
                # 备份原文件
                backup_file = srt_file.with_suffix('.srt.bak2')
                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(original_content)
                print(f"  💾 已备份到: {backup_file.name}")
                
                # 保存清理后的内容
                with open(srt_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                
                print(f"  ✅ 已清理: {original_len} → {cleaned_len} 字符")
                print(f"  📉 减少了: {original_len - cleaned_len} 字符")
                cleaned_count += 1
            else:
                print(f"  ✅ 内容无变化，跳过")
        
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"✅ 清理完成: {cleaned_count}/{len(srt_files)} 个文件")
    print("=" * 60)
    
    if cleaned_count > 0:
        print("\n💡 提示:")
        print("  - 原文件已备份为 .srt.bak2")
        print("  - 如需恢复，可以删除清理后的文件并重命名备份文件")

if __name__ == "__main__":
    force_clean_all_srt_files()
