#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发送提示词流程
验证按钮状态检测和发送功能
"""

from playwright.sync_api import sync_playwright
import time


def test_send_prompt():
    """测试发送提示词流程"""
    print("🧪 测试发送提示词流程")
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
        print("3. 确保已上传视频或准备好发送提示词")
        print("="*60)
        input("\n按 Enter 继续测试发送流程...")
        
        try:
            # 步骤1：查找输入框
            print("\n3️⃣ 查找输入框...")
            input_selectors = [
                'textarea[placeholder*="Enter"]',
                '[contenteditable="true"]',
                'div[role="textbox"]',
                'textarea',
            ]
            
            input_box = None
            for selector in input_selectors:
                try:
                    box = page.locator(selector).first
                    if box.count() > 0:
                        input_box = box
                        print(f"   ✅ 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_box:
                print("   ❌ 找不到输入框")
                return
            
            # 步骤2：填入测试提示词
            print("\n4️⃣ 填入测试提示词...")
            test_prompt = "请分析这个内容"
            
            input_box.click()
            time.sleep(0.3)
            input_box.fill(test_prompt)
            print(f"   ✅ 已填入: {test_prompt}")
            time.sleep(0.5)
            
            # 步骤3：查找 Run 按钮
            print("\n5️⃣ 查找 Run 按钮...")
            run_button_selectors = [
                'button[aria-label="Run"]',
                'button.run-button',
                'button[type="submit"][aria-label="Run"]',
            ]
            
            run_button = None
            for selector in run_button_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0:
                        run_button = btn
                        print(f"   ✅ 找到 Run 按钮: {selector}")
                        break
                except:
                    continue
            
            if not run_button:
                print("   ❌ 找不到 Run 按钮")
                print("   💡 尝试使用快捷键 Ctrl+Enter")
                page.keyboard.press("Control+Enter")
                print("   ✅ 已按快捷键")
                return
            
            # 步骤4：检查按钮初始状态
            print("\n6️⃣ 检查按钮初始状态...")
            try:
                is_disabled = run_button.get_attribute('aria-disabled')
                is_visible = run_button.is_visible()
                
                print(f"   📊 按钮可见: {is_visible}")
                print(f"   📊 aria-disabled: {is_disabled}")
                
                if is_disabled == 'true':
                    print("   ⚠️ 按钮当前不可用")
                else:
                    print("   ✅ 按钮当前可用")
            except Exception as e:
                print(f"   ⚠️ 检查状态失败: {e}")
            
            # 步骤5：等待按钮可用
            print("\n7️⃣ 等待按钮可用...")
            max_wait = 10
            waited = 0
            button_became_enabled = False
            
            while waited < max_wait:
                try:
                    is_disabled = run_button.get_attribute('aria-disabled')
                    
                    if is_disabled != 'true':
                        print(f"   ✅ 按钮已可用（等待了 {waited:.1f} 秒）")
                        button_became_enabled = True
                        break
                    else:
                        if waited % 2 == 0:  # 每 2 秒输出一次
                            print(f"   ⏳ 等待中... ({waited:.1f}/{max_wait} 秒)")
                except Exception as e:
                    print(f"   ⚠️ 检查失败: {e}")
                    break
                
                time.sleep(0.5)
                waited += 0.5
            
            if not button_became_enabled:
                print(f"   ⚠️ 等待超时（{max_wait} 秒），按钮仍不可用")
                print("   💡 尝试使用快捷键")
                page.keyboard.press("Control+Enter")
                print("   ✅ 已按快捷键")
                return
            
            # 步骤6：点击按钮
            print("\n8️⃣ 点击 Run 按钮...")
            try:
                run_button.click()
                print("   ✅ 已点击 Run 按钮")
            except Exception as e:
                print(f"   ❌ 点击失败: {e}")
                print("   💡 尝试使用快捷键")
                page.keyboard.press("Control+Enter")
                print("   ✅ 已按快捷键")
            
            # 步骤7：验证发送成功
            print("\n9️⃣ 验证发送成功...")
            time.sleep(2)
            
            # 检查按钮是否变为 Stop
            try:
                button_html = run_button.inner_html()
                button_class = run_button.get_attribute('class') or ''
                
                if 'Stop' in button_html or 'stoppable' in button_class:
                    print("   ✅ 发送成功！AI 正在处理")
                    print("   📊 按钮已变为 Stop 状态")
                else:
                    print("   ⚠️ 按钮状态未变化")
                    print("   💡 可能需要检查提示词是否有效")
            except Exception as e:
                print(f"   ⚠️ 验证失败: {e}")
            
            print("\n" + "="*60)
            print("✅ 测试完成！")
            print("="*60)
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
    test_send_prompt()
