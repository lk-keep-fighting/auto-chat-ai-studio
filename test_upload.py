#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频上传流程
"""

from playwright.sync_api import sync_playwright
import time
from pathlib import Path


def test_upload_flow():
    """测试上传流程"""
    print("🧪 测试视频上传流程")
    print("="*60)
    
    with sync_playwright() as p:
        # 启动浏览器
        print("1️⃣ 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 访问 AI Studio
        print("2️⃣ 访问 AI Studio...")
        page.goto("https://aistudio.google.com/")
        time.sleep(3)
        
        print("\n" + "="*60)
        print("请在浏览器中完成以下操作：")
        print("1. 登录 Google 账号（如需要）")
        print("2. 进入对话界面")
        print("="*60)
        input("\n按 Enter 继续测试上传流程...")
        
        # 测试上传流程
        print("\n3️⃣ 开始测试上传流程...")
        
        try:
            # 步骤1：点击添加按钮
            print("   a) 查找添加按钮...")
            add_button = page.locator('button[iconname="add_circle"]').first
            if add_button.count() > 0:
                print("   ✅ 找到添加按钮")
                add_button.click()
                print("   ✅ 已点击添加按钮")
                time.sleep(1)
            else:
                print("   ❌ 找不到添加按钮")
                return
            
            # 步骤2：查找 Upload File 按钮
            print("   b) 查找 Upload File 按钮...")
            upload_file_button = page.locator('button[aria-label="Upload File"]').first
            if upload_file_button.count() > 0 and upload_file_button.is_visible():
                print("   ✅ 找到 Upload File 按钮")
            else:
                print("   ❌ 找不到 Upload File 按钮")
                return
            
            # 步骤3：测试 file chooser
            print("   c) 测试 file chooser...")
            print("   ⚠️ 注意：点击后会弹出文件选择对话框")
            
            # 创建一个测试文件路径
            test_file = Path.home() / "Desktop" / "test.mp4"
            if not test_file.exists():
                test_file = Path.home() / "Downloads" / "test.mp4"
            
            print(f"   📁 测试文件: {test_file}")
            
            if test_file.exists():
                print("   🔄 使用 file chooser 方法...")
                with page.expect_file_chooser() as fc_info:
                    upload_file_button.click()
                    print("   ✅ 已点击 Upload File 按钮")
                
                file_chooser = fc_info.value
                file_chooser.set_files(str(test_file))
                print(f"   ✅ 已选择文件: {test_file.name}")
                
                # 步骤4：关闭浮窗菜单
                print("   d) 关闭浮窗菜单...")
                time.sleep(0.3)  # 等待文件选择完成
                try:
                    page.keyboard.press("Escape")
                    print("   ✅ 已按 Escape 键关闭菜单")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"   ⚠️ 关闭菜单失败: {e}")
                
                print("\n   ⏳ 等待上传...")
                time.sleep(5)
                print("   ✅ 上传流程完成")
            else:
                print(f"   ⚠️ 测试文件不存在: {test_file}")
                print("   💡 请手动测试：点击按钮后选择文件")
                input("   按 Enter 继续...")
            
            print("\n✅ 测试完成！")
            print("\n保持浏览器打开 10 秒以便查看结果...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            input("\n按 Enter 关闭...")
        
        finally:
            browser.close()


if __name__ == "__main__":
    test_upload_flow()
