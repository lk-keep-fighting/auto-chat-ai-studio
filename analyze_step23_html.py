#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析步骤23保存的HTML文件，查找SRT内容和下载按钮
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_html_file(html_file):
    """分析HTML文件，查找SRT相关内容"""
    
    print("=" * 60)
    print(f"📄 分析文件: {html_file.name}")
    print("=" * 60)
    
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 查找代码块
        print("\n🔍 查找代码块...")
        code_blocks = soup.find_all(['pre', 'code'])
        print(f"找到 {len(code_blocks)} 个代码块")
        
        for i, block in enumerate(code_blocks):
            text = block.get_text()
            if '-->' in text and re.search(r'\d{2}:\d{2}:\d{2},\d{3}', text):
                print(f"\n✅ 代码块 {i} 包含SRT内容:")
                print(f"  长度: {len(text)} 字符")
                print(f"  预览: {text[:200]}...")
        
        # 2. 查找下载按钮
        print("\n🔍 查找下载按钮...")
        download_buttons = soup.find_all('button', attrs={'aria-label': re.compile(r'download', re.I)})
        print(f"找到 {len(download_buttons)} 个下载按钮")
        
        for i, button in enumerate(download_buttons):
            print(f"\n按钮 {i}:")
            print(f"  aria-label: {button.get('aria-label')}")
            print(f"  class: {button.get('class')}")
            
            # 查找按钮附近的内容
            parent = button.parent
            if parent:
                parent_text = parent.get_text()
                if '-->' in parent_text:
                    print(f"  ✅ 父元素包含SRT内容")
                    print(f"  长度: {len(parent_text)} 字符")
        
        # 3. 查找所有包含SRT时间戳的元素
        print("\n🔍 查找包含SRT时间戳的元素...")
        all_text = soup.get_text()
        
        # 查找所有时间戳
        timestamps = re.findall(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}', all_text)
        print(f"找到 {len(timestamps)} 个时间戳")
        
        if timestamps:
            print(f"  第一个: {timestamps[0]}")
            print(f"  最后一个: {timestamps[-1]}")
        
        # 4. 查找包含class="code"或类似的元素
        print("\n🔍 查找包含'code'类名的元素...")
        code_elements = soup.find_all(class_=re.compile(r'code', re.I))
        print(f"找到 {len(code_elements)} 个元素")
        
        for i, elem in enumerate(code_elements[:5]):  # 只显示前5个
            text = elem.get_text()
            if '-->' in text:
                print(f"\n✅ 元素 {i} 包含SRT内容:")
                print(f"  标签: {elem.name}")
                print(f"  class: {elem.get('class')}")
                print(f"  长度: {len(text)} 字符")
        
        # 5. 提取完整的SRT内容
        print("\n🔍 尝试提取完整的SRT内容...")
        
        # 方法1：从第一个时间戳开始提取
        match = re.search(r'(\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->.*)', all_text, re.DOTALL)
        if match:
            srt_content = match.group(1)
            print(f"✅ 提取到SRT内容:")
            print(f"  长度: {len(srt_content)} 字符")
            print(f"  前200字符: {srt_content[:200]}...")
            
            # 保存提取的内容
            output_file = html_file.parent / f"{html_file.stem}_extracted.srt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(srt_content)
            print(f"  💾 已保存到: {output_file.name}")
        else:
            print("❌ 未找到SRT内容")
        
        # 6. 查找所有按钮
        print("\n🔍 查找所有按钮...")
        all_buttons = soup.find_all('button')
        print(f"找到 {len(all_buttons)} 个按钮")
        
        button_labels = {}
        for button in all_buttons:
            label = button.get('aria-label', 'no-label')
            button_labels[label] = button_labels.get(label, 0) + 1
        
        print("按钮标签统计:")
        for label, count in sorted(button_labels.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {label}: {count}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 步骤23 HTML分析工具")
    print("=" * 60)
    
    # 查找所有步骤23的HTML文件
    process_folder = Path("assets/Process_Folder")
    html_files = list(process_folder.glob("**/debug/step_23_response_*.html"))
    
    if not html_files:
        print("\n❌ 未找到步骤23的HTML文件")
        print("💡 请先运行 video_automation.py 并确保 SAVE_DEBUG_HTML = True")
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
    # 检查是否安装了 beautifulsoup4
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ 需要安装 beautifulsoup4")
        print("运行: pip install beautifulsoup4")
        sys.exit(1)
    
    main()
