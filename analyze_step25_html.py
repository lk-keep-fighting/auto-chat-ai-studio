#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析步骤25保存的HTML文件，查找表格数据
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

def analyze_html_file(html_file):
    """分析HTML文件，查找表格数据"""
    
    print("=" * 60)
    print(f"📄 分析文件: {html_file.name}")
    print("=" * 60)
    
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 查找表格元素
        print("\n🔍 查找表格元素...")
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 个表格")
        
        for i, table in enumerate(tables):
            print(f"\n📊 表格 {i}:")
            
            # 查找表头
            headers = []
            thead = table.find('thead')
            if thead:
                header_cells = thead.find_all(['th', 'td'])
                headers = [cell.get_text().strip() for cell in header_cells]
                print(f"  表头（从thead）: {headers}")
            else:
                # 尝试从第一行获取表头
                first_row = table.find('tr')
                if first_row:
                    header_cells = first_row.find_all(['th', 'td'])
                    headers = [cell.get_text().strip() for cell in header_cells]
                    print(f"  表头（从第一行）: {headers}")
            
            # 查找数据行
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                rows = table.find_all('tr')[1:]  # 跳过表头行
            
            print(f"  数据行数: {len(rows)}")
            
            # 提取前3行数据作为示例
            if rows:
                print(f"  前3行数据:")
                for j, row in enumerate(rows[:3]):
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text().strip() for cell in cells]
                    print(f"    行 {j+1}: {row_data}")
            
            # 尝试提取完整表格数据
            try:
                table_data = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_dict = {}
                    for k, cell in enumerate(cells):
                        if k < len(headers):
                            row_dict[headers[k]] = cell.get_text().strip()
                        else:
                            row_dict[f"column_{k}"] = cell.get_text().strip()
                    if row_dict:
                        table_data.append(row_dict)
                
                if table_data:
                    print(f"\n  ✅ 成功提取 {len(table_data)} 行数据")
                    
                    # 保存为Excel
                    df = pd.DataFrame(table_data)
                    output_file = html_file.parent / f"{html_file.stem}_extracted.xlsx"
                    df.to_excel(output_file, index=False)
                    print(f"  💾 已保存到: {output_file.name}")
                    
                    # 显示列统计
                    print(f"\n  📊 列统计:")
                    for col in df.columns:
                        non_empty = df[col].astype(str).str.strip().ne('').sum()
                        print(f"    {col}: {non_empty}/{len(df)} 行有数据")
                    
            except Exception as e:
                print(f"  ❌ 提取表格数据失败: {e}")
        
        # 2. 查找Markdown表格
        print("\n🔍 查找Markdown表格...")
        text_content = soup.get_text()
        
        # 查找Markdown表格格式（|分隔）
        markdown_lines = [line for line in text_content.split('\n') if '|' in line]
        if markdown_lines:
            print(f"找到 {len(markdown_lines)} 行包含 | 的文本")
            print(f"前5行:")
            for line in markdown_lines[:5]:
                print(f"  {line.strip()}")
        
        # 3. 查找CSV格式
        print("\n🔍 查找CSV格式...")
        csv_lines = [line for line in text_content.split('\n') if ',' in line and len(line.split(',')) > 3]
        if csv_lines:
            print(f"找到 {len(csv_lines)} 行可能的CSV数据")
            print(f"前5行:")
            for line in csv_lines[:5]:
                print(f"  {line.strip()}")
        
        # 4. 查找代码块中的表格
        print("\n🔍 查找代码块中的表格...")
        code_blocks = soup.find_all(['pre', 'code'])
        print(f"找到 {len(code_blocks)} 个代码块")
        
        for i, block in enumerate(code_blocks):
            text = block.get_text()
            if '|' in text or ',' in text:
                print(f"\n  代码块 {i} 可能包含表格数据:")
                print(f"    长度: {len(text)} 字符")
                print(f"    预览: {text[:200]}...")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 步骤25 HTML分析工具")
    print("=" * 60)
    
    # 查找所有步骤25的HTML文件
    process_folder = Path("assets/Process_Folder")
    html_files = list(process_folder.glob("**/debug/step_25_response_*.html"))
    
    if not html_files:
        print("\n❌ 未找到步骤25的HTML文件")
        print("💡 请先运行 video_automation.py 或测试脚本，并确保 SAVE_DEBUG_HTML = True")
        return
    
    print(f"\n📋 找到 {len(html_files)} 个HTML文件")
    
    # 分析最新的文件
    latest_file = max(html_files, key=lambda f: f.stat().st_mtime)
    print(f"\n📄 分析最新的文件: {latest_file.relative_to(process_folder)}")
    
    analyze_html_file(latest_file)
    
    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)

if __name__ == "__main__":
    # 检查是否安装了依赖
    try:
        from bs4 import BeautifulSoup
        import pandas as pd
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("运行: pip install beautifulsoup4 pandas openpyxl")
        sys.exit(1)
    
    main()
