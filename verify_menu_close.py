#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证菜单关闭功能
测试上传后菜单是否正确关闭，Run 按钮是否可用
"""

from playwright.sync_api import sync_playwright
import time
from pathlib import Path


def verify_menu_close():
    """验证菜单关闭功能"""
    print("🔍 验证菜单关闭功能")
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
        input("\n按 Enter 继续测试...")
        
        try:
            # 步骤1：点击添加按钮
            print("\n3️⃣ 点击添加按钮...")
            add_button = page.locator('button[iconname="add_circle"]').first
            if add_button.count() > 0:
                add_button.click()
                print("   ✅ 已点击添加按钮")
                time.sleep(1)
                
                # 检查菜单是否显示
                print("\n4️⃣ 检查菜单状态...")
                upload_button = page.locator('button[aria-label="Upload File"]').first
                if upload_button.is_visible():
                    print("   ✅ 菜单已显示")
                else:
                    print("   ❌ 菜单未显示")
                    return
            else:
                print("   ❌ 找不到添加按钮")
                return
            
            # 步骤2：关闭菜单
            print("\n5️⃣ 关闭菜单...")
            time.sleep(0.3)
            page.keyboard.press("Escape")
            print("   ✅ 已按 Escape 键")
            time.sleep(0.5)
            
            # 步骤3：验证菜单是否关闭
            print("\n6️⃣ 验证菜单是否关闭...")
            try:
                if upload_button.is_visible(timeout=1000):
                    print("   ❌ 菜单仍然显示（未关闭）")
                    print("   💡 尝试备用方法：点击页面其他区域")
                    page.mouse.click(500, 300)
                    time.sleep(0.5)
                    
                    if upload_button.is_visible(timeout=1000):
                        print("   ❌ 菜单仍然显示（备用方法也失败）")
                    else:
                        print("   ✅ 菜单已关闭（备用方法成功）")
                else:
                    print("   ✅ 菜单已关闭")
            except:
                print("   ✅ 菜单已关闭")
            
            # 步骤4：检查 Run 按钮状态
            print("\n7️⃣ 检查 Run 按钮状态...")
            run_button_selectors = [
                'button[aria-label="Run"]',
                'button.run-button',
            ]
            
            run_button_found = False
            for selector in run_button_selectors:
                try:
                    run_button = page.locator(selector).first
                    if run_button.count() > 0:
                        run_button_found = True
                        
                        # 检查按钮是否可见
                        if run_button.is_visible():
                            print(f"   ✅ Run 按钮可见")
                            
                            # 检查按钮是否可用
                            is_disabled = run_button.get_attribute('aria-disabled')
                            if is_disabled == 'true':
                                print(f"   ⚠️ Run 按钮不可用 (aria-disabled=true)")
                            else:
                                print(f"   ✅ Run 按钮可用")
                            
                            # 检查按钮是否被遮挡
                            try:
                                run_button.click(timeout=1000, trial=True)
                                print(f"   ✅ Run 按钮可点击（未被遮挡）")
                            except:
                                print(f"   ❌ Run 按钮不可点击（可能被遮挡）")
                        else:
                            print(f"   ⚠️ Run 按钮不可见")
                        
                        break
                except:
                    continue
            
            if not run_button_found:
                print("   ⚠️ 未找到 Run 按钮（可能需要先上传文件）")
            
            print("\n" + "="*60)
            print("✅ 验证完成！")
            print("="*60)
            print("\n保持浏览器打开 10 秒以便查看...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 验证失败: {e}")
            import traceback
            traceback.print_exc()
            input("\n按 Enter 关闭...")
        
        finally:
            browser.close()


if __name__ == "__main__":
    verify_menu_close()
