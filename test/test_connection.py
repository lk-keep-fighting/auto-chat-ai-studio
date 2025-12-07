#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证浏览器自动化是否正常工作
"""

from playwright.sync_api import sync_playwright
import time


def test_browser():
    """测试浏览器启动和基本操作"""
    print("🧪 开始测试浏览器自动化...")
    
    with sync_playwright() as p:
        # 启动浏览器
        print("1️⃣ 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 访问 Google AI Studio
        print("2️⃣ 访问 Google AI Studio...")
        page.goto("https://aistudio.google.com/")
        time.sleep(3)
        
        # 截图
        print("3️⃣ 截图保存...")
        page.screenshot(path="test_screenshot.png")
        print("   ✅ 截图已保存: test_screenshot.png")
        
        # 等待用户查看
        print("\n✅ 测试成功！浏览器将在 10 秒后关闭...")
        print("   请检查浏览器窗口和截图文件")
        time.sleep(10)
        
        # 关闭浏览器
        browser.close()
        print("✅ 浏览器已关闭")


def test_file_structure():
    """测试文件结构是否正确"""
    print("\n🧪 检查文件结构...")
    
    from pathlib import Path
    
    base_dir = Path(__file__).parent
    required_paths = [
        base_dir / "assets" / "Process_Folder" / "videos",
        base_dir / "assets" / "Process_Folder" / "prompts.xlsx",
        base_dir / "assets" / "Process_Folder" / "videos" / "VideoList.csv",
        base_dir / "assets" / "vidoes",
    ]
    
    all_ok = True
    for path in required_paths:
        if path.exists():
            print(f"   ✅ {path.relative_to(base_dir)}")
        else:
            print(f"   ❌ {path.relative_to(base_dir)} (不存在)")
            all_ok = False
    
    if all_ok:
        print("\n✅ 文件结构检查通过")
    else:
        print("\n⚠️ 部分文件缺失，请检查")
    
    return all_ok


def main():
    """主测试函数"""
    print("="*60)
    print("视频处理自动化 - 测试工具")
    print("="*60)
    
    # 测试文件结构
    file_ok = test_file_structure()
    
    if not file_ok:
        print("\n⚠️ 文件结构不完整，建议先修复")
        response = input("是否继续测试浏览器？(y/n): ")
        if response.lower() != 'y':
            return
    
    # 测试浏览器
    try:
        test_browser()
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
