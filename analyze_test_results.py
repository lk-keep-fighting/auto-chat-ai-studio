#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析测试结果，检查步骤23和25的输出
"""

import sys
from pathlib import Path
import pandas as pd

def analyze_step23_output(folder):
    """分析步骤23的输出"""
    print("\n" + "=" * 60)
    print("📄 步骤23：SRT文件分析")
    print("=" * 60)
    
    # 查找SRT文件
    srt_files = list(folder.glob("step_23_output_*.srt"))
    txt_files = list(folder.glob("step_23_output.txt"))
    
    if srt_files:
        print(f"\n✅ 找到 {len(srt_files)} 个SRT文件:")
        for srt_file in srt_files:
            with open(srt_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否包含UI元素
            ui_keywords = ['code', 'Srt', 'download', 'content_copy', 'expand_less', 'expand_more', 'Google Search']
            found_ui = [kw for kw in ui_keywords if kw in content]
            
            # 检查是否以序号1开始
            starts_with_1 = content.strip().startswith('1\n') or content.strip().startswith('1 ')
            
            # 统计时间戳数量
            import re
            timestamps = re.findall(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->', content)
            
            print(f"\n  📝 {srt_file.name}")
            print(f"    大小: {len(content)} 字符")
            print(f"    时间戳数量: {len(timestamps)}")
            print(f"    以序号1开始: {'✅' if starts_with_1 else '❌'}")
            print(f"    包含UI元素: {'❌ ' + ', '.join(found_ui) if found_ui else '✅ 无'}")
            
            # 显示前5行
            lines = content.split('\n')[:5]
            print(f"    前5行:")
            for line in lines:
                print(f"      {line}")
    
    if txt_files:
        print(f"\n⚠️ 找到 {len(txt_files)} 个文本文件（应该是SRT文件）:")
        for txt_file in txt_files:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"  📝 {txt_file.name}")
            print(f"    大小: {len(content)} 字符")
            print(f"    预览: {content[:200]}...")
    
    if not srt_files and not txt_files:
        print("\n❌ 未找到任何输出文件")
    
    # 查找调试文件
    debug_folder = folder / "debug"
    if debug_folder.exists():
        html_files = list(debug_folder.glob("step_23_response_*.html"))
        text_files = list(debug_folder.glob("step_23_text_*.txt"))
        
        if html_files or text_files:
            print(f"\n💾 调试文件:")
            print(f"  HTML文件: {len(html_files)}")
            print(f"  文本文件: {len(text_files)}")
            
            if html_files:
                latest_html = max(html_files, key=lambda f: f.stat().st_mtime)
                print(f"  最新HTML: {latest_html.name}")
                print(f"  💡 运行 'python analyze_step23_html.py' 分析HTML结构")

def analyze_step25_output(folder):
    """分析步骤25的输出"""
    print("\n" + "=" * 60)
    print("📊 步骤25：表格数据分析")
    print("=" * 60)
    
    # 查找Excel文件
    excel_files = list(folder.glob("step_25_output.xlsx"))
    
    if excel_files:
        print(f"\n✅ 找到 {len(excel_files)} 个Excel文件:")
        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file)
                
                print(f"\n  📝 {excel_file.name}")
                print(f"    行数: {len(df)}")
                print(f"    列数: {len(df.columns)}")
                print(f"    列名: {', '.join(df.columns.tolist())}")
                
                # 显示每列的统计
                print(f"\n    列统计:")
                for col in df.columns:
                    non_empty = df[col].astype(str).str.strip().ne('').sum()
                    print(f"      {col}: {non_empty}/{len(df)} 行有数据")
                
                # 显示前3行
                print(f"\n    前3行数据:")
                print(df.head(3).to_string(index=False))
                
            except Exception as e:
                print(f"  ❌ 读取Excel失败: {e}")
    else:
        print("\n❌ 未找到Excel文件")
    
    # 查找调试文件
    debug_folder = folder / "debug"
    if debug_folder.exists():
        html_files = list(debug_folder.glob("step_25_response_*.html"))
        text_files = list(debug_folder.glob("step_25_text_*.txt"))
        
        if html_files or text_files:
            print(f"\n💾 调试文件:")
            print(f"  HTML文件: {len(html_files)}")
            print(f"  文本文件: {len(text_files)}")
            
            if html_files:
                latest_html = max(html_files, key=lambda f: f.stat().st_mtime)
                print(f"  最新HTML: {latest_html.name}")
                print(f"  💡 运行 'python analyze_step25_html.py' 分析HTML结构")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 测试结果分析工具")
    print("=" * 60)
    
    process_folder = Path("assets/Process_Folder")
    
    # 查找测试文件夹
    step23_folders = list(process_folder.glob("test_步骤23*"))
    step25_folders = list(process_folder.glob("test_步骤25*"))
    
    if not step23_folders and not step25_folders:
        print("\n❌ 未找到测试输出文件夹")
        print("💡 请先运行测试脚本:")
        print("  bash test/test_step23_25.sh")
        return
    
    # 分析步骤23
    if step23_folders:
        for folder in step23_folders:
            print(f"\n📁 分析文件夹: {folder.name}")
            analyze_step23_output(folder)
    
    # 分析步骤25
    if step25_folders:
        for folder in step25_folders:
            print(f"\n📁 分析文件夹: {folder.name}")
            analyze_step25_output(folder)
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)
    
    print("\n💡 后续操作:")
    print("  1. 如果步骤23有问题，运行: python analyze_step23_html.py")
    print("  2. 如果步骤25有问题，运行: python analyze_step25_html.py")
    print("  3. 查看调试HTML文件，了解页面结构")
    print("  4. 根据分析结果调整提取策略")

if __name__ == "__main__":
    # 检查依赖
    try:
        import pandas as pd
    except ImportError:
        print("❌ 需要安装 pandas")
        print("运行: pip install pandas openpyxl")
        sys.exit(1)
    
    main()
