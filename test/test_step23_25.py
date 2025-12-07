#!/usr/bin/env python3
"""
步骤23和步骤25数据保存测试脚本

测试步骤23和步骤25的数据提取和保存功能
"""

import sys
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright
import pandas as pd

# 导入配置和主类
import config
from video_automation import VideoProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_step23_25.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Step23And25Tester(VideoProcessor):
    """步骤23和25测试类"""
    
    def test_steps(self):
        """测试步骤23和步骤25的数据提取和保存"""
        try:
            logger.info("=" * 60)
            logger.info("🧪 步骤23和步骤25数据保存测试")
            logger.info("=" * 60)
            
            # 1. 初始化浏览器
            logger.info("\n📱 步骤 1: 初始化浏览器")
            self.init_browser(headless=False, use_system_chrome=True)
            
            # 2. 打开AI Studio
            logger.info("\n🌐 步骤 2: 打开 AI Studio")
            self.open_ai_studio()
            
            # 3. 等待用户确认
            logger.info("\n⏸️  步骤 3: 等待用户确认")
            logger.info("=" * 60)
            logger.info("请确认以下事项：")
            logger.info("1. ✅ 已登录 Google 账号")
            logger.info("2. ✅ 已进入 AI Studio 对话界面")
            logger.info("3. ✅ 页面加载完成")
            logger.info("=" * 60)
            input("✅ 确认无误后，按 Enter 键继续测试...")
            
            # 测试步骤23
            logger.info("\n" + "=" * 60)
            logger.info("📝 测试步骤23：SRT文件生成")
            logger.info("=" * 60)
            
            step23_result = self.test_single_step(
                step_number=23,
                prompt="""步骤23：【角色设定】按内容要求生成2个srt文件的测试数据

【内容要求】
风格：电影解说旁白风格（第三人称，情绪饱满）。
覆盖：旁白内容必须填满计算出的时长，不要留白。

输出要求：
请输出修正后的纯旁白英文 SRT 文件。
格式：标准的 .srt 格式。
所有时间戳必须严格使用 hh:mm:ss,ms 格式（小时:分钟:秒,毫秒），并确保每一个时间戳都完全符合规范。""",
                step_name="步骤23_SRT文件"
            )
            
            # 测试步骤25
            logger.info("\n" + "=" * 60)
            logger.info("📝 测试步骤25：表格数据生成")
            logger.info("=" * 60)
            
            step25_result = self.test_single_step(
                step_number=25,
                prompt="""步骤25:按输出格式输出10行测试数据

【输出格式】
请直接输出表格。表头如下：
| start | end | folder1 | folder2 | folder3 | music | cover_time | title |""",
                step_name="步骤25_表格数据"
            )
            
            # 汇总结果
            logger.info("\n" + "=" * 60)
            logger.info("📊 测试结果汇总")
            logger.info("=" * 60)
            logger.info(f"步骤23: {'✅ 成功' if step23_result else '❌ 失败'}")
            logger.info(f"步骤25: {'✅ 成功' if step25_result else '❌ 失败'}")
            
            if step23_result and step25_result:
                logger.info("\n🎉 所有测试通过！")
                return True
            else:
                logger.error("\n❌ 部分测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # 不关闭浏览器，方便查看结果
            logger.info("\n💡 浏览器保持打开状态，方便查看结果")
            logger.info("💡 按 Ctrl+C 退出程序")
            try:
                input("\n按 Enter 键关闭浏览器并退出...")
            except KeyboardInterrupt:
                pass
            
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
    
    def test_single_step(self, step_number, prompt, step_name):
        """测试单个步骤"""
        try:
            logger.info(f"\n📝 步骤 {step_number}: 发送测试提示词")
            logger.info(f"提示词内容:\n{prompt}")
            logger.info("\n发送提示词...")
            
            success = self.send_prompt(prompt)
            if not success:
                logger.error(f"❌ 发送提示词失败")
                return False
            
            logger.info("✅ 提示词已发送")
            
            # 等待AI响应
            logger.info(f"\n⏳ 等待AI响应步骤 {step_number}...")
            response_result = self.wait_for_response(step_number=step_number)
            
            if response_result == "timeout_continue":
                logger.warning("⚠️ 响应超时，但继续提取数据")
            elif response_result in ["skip", "quit"]:
                logger.error(f"❌ 用户选择: {response_result}")
                return False
            
            logger.info("✅ AI响应完成")
            
            # 调试：截图并保存HTML
            logger.info("📸 截图当前页面...")
            self.take_screenshot(f"before_extract_step{step_number}")
            
            logger.info("💾 保存页面HTML...")
            try:
                html_content = self.page.content()
                html_file = Path("test_output") / f"step{step_number}_page.html"
                html_file.parent.mkdir(exist_ok=True)
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"✅ HTML已保存到: {html_file}")
            except Exception as e:
                logger.warning(f"⚠️ 保存HTML失败: {e}")
            
            # 提取数据
            logger.info(f"\n📊 提取步骤 {step_number} 数据")
            response = self.extract_response(step_number=step_number)
            
            logger.info(f"📊 数据类型: {type(response)}")
            logger.info(f"📊 数据量: {len(response) if response else 0}")
            
            if isinstance(response, list) and response:
                logger.info(f"📋 第一条数据: {response[0]}")
                logger.info(f"📋 数据列: {list(response[0].keys()) if isinstance(response[0], dict) else 'N/A'}")
            elif isinstance(response, str):
                logger.info(f"📝 文本数据预览: {response[:200]}...")
            
            if not response:
                logger.error("❌ 未提取到任何数据")
                return False
            
            # 保存数据
            logger.info(f"\n💾 保存步骤 {step_number} 数据")
            step_outputs = {step_number: response}
            
            # save_output_data 使用 self.process_folder (assets/Process_Folder/)
            output_folder = self.save_output_data(f"test_{step_name}", step_outputs)
            logger.info(f"数据已保存到: {output_folder}")
            
            # 验证保存结果
            logger.info(f"\n✅ 验证步骤 {step_number} 保存结果")
            output_file = output_folder / f"step_{step_number}_output.xlsx"
            
            if output_file.exists():
                file_size = output_file.stat().st_size
                logger.info(f"✅ 文件已创建: {output_file}")
                logger.info(f"📊 文件大小: {file_size} 字节")
                
                # 读取并显示数据
                try:
                    df = pd.read_excel(output_file)
                    logger.info(f"📊 数据行数: {len(df)}")
                    logger.info(f"📊 数据列数: {len(df.columns)}")
                    logger.info(f"📋 列名: {', '.join(df.columns.tolist())}")
                    logger.info("\n前3行数据:")
                    logger.info(df.head(3).to_string())
                    
                    logger.info(f"\n🎉 步骤 {step_number} 测试成功！")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ 读取Excel文件失败: {e}")
                    return False
            else:
                logger.error(f"❌ 文件未创建: {output_file}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 步骤 {step_number} 测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 步骤23和步骤25数据保存测试工具")
    logger.info("=" * 60)
    logger.info("\n测试内容：")
    logger.info("1. 初始化浏览器")
    logger.info("2. 打开 AI Studio")
    logger.info("3. 等待用户确认")
    logger.info("4. 测试步骤23（SRT文件生成）")
    logger.info("5. 测试步骤25（表格数据生成）")
    logger.info("6. 验证保存结果")
    logger.info("\n" + "=" * 60)
    
    try:
        tester = Step23And25Tester()
        success = tester.test_steps()
        
        if success:
            logger.info("\n✅ 所有测试通过")
            logger.info("📁 输出文件:")
            logger.info("  - 步骤23: assets/Process_Folder/test_步骤23_SRT文件/step_23_output.xlsx")
            logger.info("  - 步骤25: assets/Process_Folder/test_步骤25_表格数据/step_25_output.xlsx")
            return 0
        else:
            logger.error("\n❌ 测试失败")
            logger.error("📋 请查看日志: test_step23_25.log")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ 用户中断测试")
        return 1
    except Exception as e:
        logger.error(f"\n❌ 测试异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
