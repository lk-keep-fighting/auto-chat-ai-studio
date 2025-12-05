#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理自动化脚本
基于 Playwright 实现 Google AI Studio 的浏览器自动化
"""

import os
import sys
import time
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import config, ensure_directories


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class VideoProcessor:
    """视频处理自动化类"""

    def __init__(self):
        # 使用配置文件中的路径
        self.base_dir = config.BASE_DIR
        self.process_folder = config.PROCESS_FOLDER
        self.videos_folder = config.VIDEOS_FOLDER
        self.prompts_file = config.PROMPTS_FILE
        self.video_list_file = config.VIDEO_LIST_FILE
        self.output_folder = config.OUTPUT_FOLDER
        self.clips_file = config.CLIPS_FILE

        self.ai_studio_url = config.AI_STUDIO_URL
        self.page = None
        self.browser = None
        self.context = None
        self.playwright = None
        
        # Content blocked 处理标记
        self.content_blocked_handled = False
        self.last_blocked_time = 0

        # 确保目录存在
        ensure_directories()

    def load_video_list(self):
        """加载视频列表"""
        if not self.video_list_file.exists():
            logger.error(f"❌ 找不到视频列表文件: {self.video_list_file}")
            return []

        try:
            df = pd.read_csv(self.video_list_file)
            videos = []
            for _, row in df.iterrows():
                videos.append(
                    {"filename": row["Filename"], "duration": row["Duration"]}
                )
            logger.info(f"✅ 加载了 {len(videos)} 个视频")
            return videos
        except Exception as e:
            logger.error(f"❌ 读取视频列表失败: {e}")
            return []

    def load_prompts(self):
        """加载提示词文件"""
        if not self.prompts_file.exists():
            logger.error(f"❌ 找不到提示词文件: {self.prompts_file}")
            return None

        try:
            df = pd.read_excel(self.prompts_file)
            logger.info(f"✅ 加载提示词文件，共 {len(df)} 行")
            return df
        except Exception as e:
            logger.error(f"❌ 读取提示词文件失败: {e}")
            return None

    def update_prompts_file(self, video_name, duration):
        """更新提示词文件中的视频名称和时长"""
        df = self.load_prompts()
        if df is None:
            return False

        # 假设文件中有 '文件名称' 和 '视频时长' 列
        if "文件名称" in df.columns:
            df.loc[0, "文件名称"] = video_name
        if "视频时长" in df.columns:
            df.loc[0, "视频时长"] = duration

        df.to_excel(self.prompts_file, index=False)
        print(f"✅ 更新提示词文件: {video_name} - {duration}")
        return True

    def get_prompts_list(self):
        """获取所有提示词（步骤1-25）"""
        df = self.load_prompts()
        if df is None:
            return []

        prompts = []
        # 假设提示词在某一列中，按步骤排列
        for col in df.columns:
            if "步骤" in col or "step" in col.lower() or "提示" in col:
                for val in df[col].dropna():
                    if val and str(val).strip():
                        prompts.append(str(val).strip())

        # 如果没有找到，尝试读取所有非空值
        if not prompts:
            for _, row in df.iterrows():
                for val in row.dropna():
                    if (
                        val
                        and str(val).strip()
                        and str(val) not in ["文件名称", "视频时长"]
                    ):
                        prompts.append(str(val).strip())

        print(f"✅ 提取了 {len(prompts)} 个提示词")
        return prompts

    def get_chrome_user_data_dir(self):
        """获取 Chrome 用户数据目录"""
        import platform
        import os
        
        system = platform.system()
        home = Path.home()
        
        if system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "Google" / "Chrome"
        elif system == "Windows":
            return home / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
        elif system == "Linux":
            return home / ".config" / "google-chrome"
        else:
            return None
    
    def init_browser(self, headless=None, use_system_chrome=True):
        """初始化浏览器，支持使用系统 Chrome 和默认用户配置"""
        if headless is None:
            headless = config.HEADLESS

        logger.info("正在启动浏览器...")
        self.playwright = sync_playwright().start()
        
        if use_system_chrome and not headless:
            # 使用系统 Chrome 和默认用户配置
            chrome_user_data = self.get_chrome_user_data_dir()
            
            if chrome_user_data and chrome_user_data.exists():
                logger.info(f"🌐 使用系统 Chrome 浏览器")
                logger.info(f"📁 用户数据目录: {chrome_user_data}")
                
                try:
                    # 使用 channel="chrome" 启动系统 Chrome
                    self.browser = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(chrome_user_data / "Default"),
                        channel="chrome",  # 使用系统安装的 Chrome
                        headless=False,
                        args=[
                            "--start-maximized",
                            "--disable-blink-features=AutomationControlled",
                        ],
                        viewport=None,
                    )
                    self.context = self.browser
                    self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
                    self.page.set_default_timeout(config.BROWSER_TIMEOUT)
                    logger.info("✅ 系统 Chrome 已启动，使用默认用户配置")
                    return
                    
                except Exception as e:
                    logger.warning(f"⚠️ 启动系统 Chrome 失败: {e}")
                    logger.info("将使用 Chromium 浏览器")
        
        # 回退到使用 Chromium 和会话状态
        logger.info("📝 使用 Chromium 浏览器")
        session_dir = self.base_dir / ".browser_session"
        session_dir.mkdir(exist_ok=True)
        
        # 检查是否存在已保存的会话
        if (session_dir / "state.json").exists():
            logger.info("🔑 检测到已保存的会话，正在加载...")
            try:
                self.browser = self.playwright.chromium.launch(
                    headless=headless, args=["--start-maximized"]
                )
                self.context = self.browser.new_context(
                    viewport=None,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    storage_state=str(session_dir / "state.json")
                )
                logger.info("✅ 会话已加载")
            except Exception as e:
                logger.warning(f"⚠️ 加载会话失败: {e}，将创建新会话")
                self.browser = self.playwright.chromium.launch(
                    headless=headless, args=["--start-maximized"]
                )
                self.context = self.browser.new_context(
                    viewport=None,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                )
        else:
            logger.info("📝 首次运行，将创建新会话")
            self.browser = self.playwright.chromium.launch(
                headless=headless, args=["--start-maximized"]
            )
            self.context = self.browser.new_context(
                viewport=None,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
        
        self.page = self.context.new_page()
        self.page.set_default_timeout(config.BROWSER_TIMEOUT)
        logger.info("✅ 浏览器已启动")

    def close_browser(self):
        """关闭浏览器，保存会话状态"""
        try:
            # 如果使用的是 persistent context，不需要保存会话
            # 因为会话已经保存在系统 Chrome 的用户数据中
            if self.context and self.context != self.browser:
                # 只有在使用 Chromium 时才保存会话
                self.save_session()
            
            if self.page and self.page != self.context.pages[0] if hasattr(self.context, 'pages') else True:
                try:
                    self.page.close()
                except:
                    pass
            
            if self.browser:
                self.browser.close()
            
            if self.playwright:
                self.playwright.stop()
            
            logger.info("✅ 浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")

    def take_screenshot(self, name="screenshot"):
        """截图保存"""
        if config.SAVE_SCREENSHOTS and self.page:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}.png"
                filepath = config.SCREENSHOT_DIR / filename
                self.page.screenshot(path=str(filepath))
                logger.debug(f"截图已保存: {filepath}")
            except Exception as e:
                logger.warning(f"截图失败: {e}")

    def save_session(self):
        """保存浏览器会话状态"""
        try:
            session_dir = self.base_dir / ".browser_session"
            session_dir.mkdir(exist_ok=True)
            
            # 保存会话状态
            self.context.storage_state(path=str(session_dir / "state.json"))
            logger.info("💾 会话状态已保存")
            return True
        except Exception as e:
            logger.error(f"❌ 保存会话失败: {e}")
            return False
    
    def check_login_status(self):
        """检查是否已登录"""
        try:
            # 检查页面上是否有登录相关的元素
            # 这里需要根据实际页面调整
            time.sleep(2)
            
            # 如果页面包含登录按钮，说明未登录
            login_indicators = [
                'text="Sign in"',
                'text="登录"',
                'text="Login"',
                'button:has-text("Sign in")',
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.page.locator(indicator).first
                    if element.is_visible(timeout=2000):
                        logger.info("⚠️ 检测到未登录状态")
                        return False
                except:
                    continue
            
            logger.info("✅ 已登录状态")
            return True
            
        except Exception as e:
            logger.debug(f"检查登录状态时出错: {e}")
            return False
    
    def wait_for_login(self):
        """等待用户手动登录"""
        logger.info("\n" + "="*60)
        logger.info("🔐 请在浏览器中完成登录")
        logger.info("="*60)
        logger.info("1. 请登录你的 Google 账号")
        logger.info("2. 完成必要的授权")
        logger.info("3. 登录完成后，脚本会自动继续")
        logger.info("4. 会话将被保存，下次无需重复登录")
        logger.info("="*60)
        
        # 等待用户登录
        max_wait = 300  # 最多等待 5 分钟
        waited = 0
        check_interval = 5
        
        while waited < max_wait:
            if self.check_login_status():
                logger.info("✅ 登录成功！")
                # 保存会话状态
                self.save_session()
                return True
            
            time.sleep(check_interval)
            waited += check_interval
            
            if waited % 30 == 0:
                logger.info(f"⏳ 等待登录中... ({waited}/{max_wait} 秒)")
        
        logger.error("❌ 登录超时")
        return False
    
    def wait_for_user_confirmation(self):
        """等待用户确认已登录并进入对话界面"""
        logger.info("\n" + "="*60)
        logger.info("👤 请确认以下操作")
        logger.info("="*60)
        logger.info("1. 确保已登录 Google 账号")
        logger.info("2. 进入 AI Studio 对话界面")
        logger.info("3. 准备好开始处理视频")
        logger.info("="*60)
        logger.info("")
        
        # 等待用户在终端按 Enter
        try:
            input("✅ 完成上述操作后，按 Enter 键继续...")
            logger.info("✅ 用户已确认，继续执行")
            self.take_screenshot("user_confirmed")
            return True
        except KeyboardInterrupt:
            logger.warning("❌ 用户取消操作")
            return False
        except Exception as e:
            logger.error(f"❌ 等待用户确认时出错: {e}")
            return False
    
    def open_ai_studio(self):
        """打开 Google AI Studio 并等待用户确认"""
        logger.info(f"🌐 正在打开 {self.ai_studio_url}")
        try:
            self.page.goto(self.ai_studio_url, wait_until="domcontentloaded")
            time.sleep(3)
            self.take_screenshot("ai_studio_opened")
            
            logger.info("✅ AI Studio 已打开")
            
            # 根据配置决定是否等待用户确认
            if config.WAIT_USER_CONFIRMATION:
                if not self.wait_for_user_confirmation():
                    logger.error("❌ 用户未确认，终止操作")
                    return False
            else:
                # 不需要用户确认，自动检测登录状态
                if not self.check_login_status():
                    logger.info("🔐 需要登录")
                    if not self.wait_for_login():
                        return False
                    
                    # 登录后刷新页面
                    self.page.reload(wait_until="domcontentloaded")
                    time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 打开 AI Studio 失败: {e}")
            self.take_screenshot("error_open_ai_studio")
            return False

    def upload_video(self, video_path):
        """上传视频文件 - 点击添加按钮，然后点击 Upload File"""
        logger.info(f"📤 正在上传视频: {video_path}")

        if not Path(video_path).exists():
            logger.error(f"❌ 视频文件不存在: {video_path}")
            return False

        try:
            # 步骤1：点击添加按钮（add_circle 图标按钮）
            logger.info("1️⃣ 点击添加按钮...")
            add_button_selectors = [
                'button[iconname="add_circle"]',
                'button[data-test-add-chunk-menu-button]',
                'button[aria-label*="Insert assets"]',
                'button:has(span.material-symbols-outlined:has-text("add_circle"))',
            ]

            add_button = None
            for selector in add_button_selectors:
                try:
                    add_button = self.page.locator(selector).first
                    if add_button.count() > 0 and add_button.is_visible():
                        break
                except:
                    continue

            if not add_button:
                logger.error("❌ 找不到添加按钮")
                self.take_screenshot("error_no_add_button")
                return False

            # 点击添加按钮
            add_button.click()
            logger.info("✅ 已点击添加按钮")
            time.sleep(1)
            self.take_screenshot("add_button_clicked")

            # 步骤2：点击 Upload File 按钮
            logger.info("2️⃣ 点击 Upload File 按钮...")
            upload_file_selectors = [
                'button[aria-label="Upload File"]',
                'button:has-text("Upload File")',
                'button[mat-menu-item]:has(span:has-text("Upload File"))',
            ]

            upload_file_button = None
            for selector in upload_file_selectors:
                try:
                    upload_file_button = self.page.locator(selector).first
                    if upload_file_button.count() > 0 and upload_file_button.is_visible():
                        break
                except:
                    continue

            if not upload_file_button:
                logger.error("❌ 找不到 Upload File 按钮")
                self.take_screenshot("error_no_upload_file_button")
                return False

            # 步骤3：使用 file chooser 上传文件
            logger.info("3️⃣ 设置文件选择器并上传文件...")
            
            # 使用 file chooser 事件（必须在点击前设置）
            try:
                # 设置文件选择器监听，然后点击按钮
                with self.page.expect_file_chooser() as fc_info:
                    upload_file_button.click()
                    logger.info("✅ 已点击 Upload File 按钮")
                
                # 获取文件选择器并设置文件
                file_chooser = fc_info.value
                file_chooser.set_files(str(video_path))
                logger.info(f"✅ 已选择文件: {Path(video_path).name}")
                
            except Exception as e:
                logger.warning(f"⚠️ file chooser 方法失败: {e}")
                logger.info("尝试直接设置 input 元素...")
                
                # 备用方法：直接查找并设置 input[type="file"]
                file_input_selectors = [
                    'input[data-test-upload-file-input]',
                    'input[type="file"][multiple]',
                    'button[aria-label="Upload File"] input[type="file"]',
                ]
                
                file_input = None
                for selector in file_input_selectors:
                    try:
                        file_input = self.page.locator(selector).first
                        if file_input.count() > 0:
                            break
                    except:
                        continue
                
                if file_input:
                    file_input.set_input_files(str(video_path))
                    logger.info(f"✅ 已选择文件: {Path(video_path).name}")
                else:
                    raise Exception("无法找到文件输入元素")

            # 步骤4：关闭浮窗菜单
            logger.info("4️⃣ 关闭浮窗菜单...")
            time.sleep(0.3)  # 等待文件选择完成
            try:
                # 方法1：按 Escape 键关闭菜单
                self.page.keyboard.press("Escape")
                logger.info("✅ 已按 Escape 键关闭菜单")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"⚠️ 按 Escape 键失败: {e}")
                
                # 方法2：点击页面其他区域关闭菜单
                try:
                    # 点击页面中心区域
                    self.page.mouse.click(500, 300)
                    logger.info("✅ 已点击页面关闭菜单")
                    time.sleep(0.5)
                except Exception as e2:
                    logger.warning(f"⚠️ 点击关闭菜单失败: {e2}")
            
            # 等待上传完成
            logger.info("⏳ 等待视频上传完成...")
            time.sleep(config.WAIT_AFTER_UPLOAD)
            self.take_screenshot("video_uploaded")

            logger.info("✅ 视频上传完成")
            return True

        except Exception as e:
            logger.error(f"❌ 上传视频失败: {e}")
            import traceback
            traceback.print_exc()
            self.take_screenshot("error_upload_video")
            return False

    def send_prompt(self, prompt_text, step_number=None):
        """发送提示词到对话框"""
        step_info = f"步骤 {step_number}" if step_number else "提示词"
        logger.info(f"📝 发送{step_info}: {prompt_text[:50]}...")

        try:
            # 尝试多个可能的输入框选择器
            input_selectors = [
                config.SELECTORS["input_box"],
                config.SELECTORS["chat_input"],
                "textarea",
                '[contenteditable="true"]',
                'div[role="textbox"]',
            ]

            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.page.locator(selector).first
                    if input_box.count() > 0:
                        break
                except:
                    continue

            if not input_box:
                logger.error("❌ 找不到输入框")
                self.take_screenshot("error_no_input_box")
                return False

            # 清空并填入新内容
            input_box.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            time.sleep(0.3)

            # 填入提示词
            input_box.fill(prompt_text)
            logger.info(f"✅ 已填入提示词")
            time.sleep(0.5)

            # 等待 Run 按钮变为可用状态
            logger.info("⏳ 等待 Run 按钮可用...")
            run_button = None
            run_button_selectors = [
                'button[aria-label="Run"]',
                'button.run-button',
                'button[type="submit"][aria-label="Run"]',
            ]
            
            # 查找 Run 按钮
            for selector in run_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0:
                        run_button = btn
                        break
                except:
                    continue
            
            if not run_button:
                logger.warning("⚠️ 找不到 Run 按钮，尝试使用快捷键")
                self.page.keyboard.press("Control+Enter")
            else:
                # 等待按钮变为可用（aria-disabled != "true"）
                max_wait = config.WAIT_BUTTON_ENABLED
                waited = 0
                last_log_time = 0
                
                while waited < max_wait:
                    try:
                        is_disabled = run_button.get_attribute('aria-disabled')
                        if is_disabled != 'true':
                            logger.info(f"✅ Run 按钮已可用（等待了 {waited:.1f} 秒）")
                            break
                    except:
                        pass
                    
                    # 每 10 秒输出一次进度
                    if waited - last_log_time >= 10:
                        logger.info(f"⏳ 等待按钮可用中... ({waited:.0f}/{max_wait} 秒)")
                        last_log_time = waited
                    
                    time.sleep(0.5)
                    waited += 0.5
                
                # 检查是否超时
                if waited >= max_wait:
                    logger.warning(f"⚠️ 等待按钮可用超时（{max_wait} 秒），尝试使用快捷键")
                    self.page.keyboard.press("Control+Enter")
                else:
                    # 点击 Run 按钮（增加超时时间）
                    try:
                        run_button.click(timeout=10000)  # 10秒超时
                        logger.info("✅ 已点击 Run 按钮")
                    except Exception as e:
                        logger.warning(f"⚠️ 点击 Run 按钮失败: {e}，尝试使用快捷键")
                        self.page.keyboard.press("Control+Enter")

            time.sleep(config.WAIT_AFTER_SEND)
            self.take_screenshot(
                f"sent_prompt_step_{step_number}" if step_number else "sent_prompt"
            )

            logger.info(f"✅ 已发送{step_info}")
            return True

        except Exception as e:
            logger.error(f"❌ 发送提示词失败: {e}")
            self.take_screenshot("error_send_prompt")
            return False

    def check_content_blocked(self):
        """检查是否出现 Content blocked（带去重逻辑）"""
        try:
            # 检查多种可能的错误提示
            error_texts = ["Content blocked", "内容被阻止", "blocked", "error"]

            for text in error_texts:
                try:
                    blocked_element = self.page.get_by_text(text, exact=False).first
                    if blocked_element.is_visible(timeout=1000):
                        current_time = time.time()
                        
                        # 检查是否在短时间内已经处理过（冷却时间内不重复处理）
                        cooldown = config.CONTENT_BLOCKED_COOLDOWN
                        if current_time - self.last_blocked_time < cooldown:
                            logger.debug(f"⏭️ Content blocked 已在 {int(current_time - self.last_blocked_time)} 秒前处理过，跳过")
                            return False
                        
                        logger.warning(f"⚠️ 检测到错误提示: {text}")
                        self.take_screenshot("content_blocked")

                        # 自动输入"继续"
                        logger.info("正在输入'继续'...")
                        self.send_prompt("继续")
                        
                        # 更新处理时间
                        self.last_blocked_time = current_time
                        
                        time.sleep(3)
                        return True
                except:
                    continue
        except Exception as e:
            logger.debug(f"检查 Content blocked 时出错: {e}")

        return False

    def is_ai_running(self):
        """检查 AI 是否正在运行（通过按钮状态判断）"""
        try:
            # 查找 Run 按钮
            run_button_selectors = [
                'button[aria-label="Run"]',
                'button.run-button',
                'button[type="submit"][aria-label="Run"]',
            ]
            
            for selector in run_button_selectors:
                try:
                    run_button = self.page.locator(selector).first
                    if run_button.count() > 0:
                        # 检查按钮是否包含 "Stop" 文本或 stoppable 类
                        button_html = run_button.inner_html()
                        button_class = run_button.get_attribute('class') or ''
                        
                        # 如果按钮显示 "Stop" 或包含 stoppable 类，说明 AI 正在运行
                        if 'Stop' in button_html or 'stoppable' in button_class:
                            return True
                        
                        # 如果按钮显示 "Run"，说明 AI 已完成
                        if 'Run' in button_html and 'Stop' not in button_html:
                            return False
                except:
                    continue
            
            # 默认返回 False（假设已完成）
            return False
            
        except Exception as e:
            logger.debug(f"检查 AI 运行状态时出错: {e}")
            return False
    
    def wait_for_response(self, timeout=None, step_number=None):
        """等待 AI 响应完成 - 通过检测按钮状态"""
        if timeout is None:
            timeout = config.WAIT_FOR_RESPONSE * 6  # 默认 60 秒

        step_info = f"步骤 {step_number}" if step_number else ""
        logger.info(f"⏳ 等待 AI 响应{step_info}...")

        start_time = time.time()
        check_interval = 2
        last_status_log = 0

        while time.time() - start_time < timeout:
            # 检查是否被阻止
            if self.check_content_blocked():
                start_time = time.time()  # 重置计时器
                continue

            # 检查 AI 是否正在运行
            if self.is_ai_running():
                # AI 正在运行，继续等待
                current_time = time.time()
                if current_time - last_status_log > 10:  # 每 10 秒输出一次状态
                    elapsed = int(current_time - start_time)
                    logger.info(f"⏳ AI 正在处理... (已等待 {elapsed} 秒)")
                    last_status_log = current_time
                
                time.sleep(check_interval)
                continue
            else:
                # AI 已完成，等待响应稳定
                logger.info("✅ AI 处理完成，等待响应稳定...")
                time.sleep(3)
                break

            # 如果等待时间过长，截图记录
            if time.time() - start_time > timeout / 2:
                self.take_screenshot(
                    f"waiting_response_step_{step_number}"
                    if step_number
                    else "waiting_response"
                )

        # 最终检查
        if self.is_ai_running():
            logger.warning("⚠️ AI 仍在运行，但已达到超时时间")
        else:
            logger.info("✅ AI 响应完成")

        self.take_screenshot(
            f"response_received_step_{step_number}"
            if step_number
            else "response_received"
        )

    def extract_response(self):
        """提取 AI 的响应内容"""
        try:
            # 获取最后的响应内容（需要根据实际页面调整选择器）
            responses = self.page.locator('[data-message-author-role="model"]').all()
            if responses:
                last_response = responses[-1].inner_text()
                return last_response
            return ""
        except Exception as e:
            print(f"❌ 提取响应失败: {e}")
            return ""

    def save_output_data(self, video_name, step_outputs):
        """保存输出数据为 Excel"""
        output_folder = self.process_folder / video_name.replace(".mp4", "").replace(
            ".MP4", ""
        )
        output_folder.mkdir(exist_ok=True)

        logger.info(f"💾 保存输出数据到: {output_folder}")

        for step_num, data in step_outputs.items():
            if not data:
                continue

            output_file = output_folder / f"step_{step_num}_output.xlsx"

            try:
                # 尝试解析为表格数据
                # 这里需要根据实际数据格式调整
                if isinstance(data, str):
                    # 如果是文本，保存为单列
                    df = pd.DataFrame({"输出内容": [data]})
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([{"数据": str(data)}])

                df.to_excel(output_file, index=False)
                logger.info(f"✅ 保存步骤 {step_num} 数据: {output_file.name}")

            except Exception as e:
                logger.error(f"❌ 保存步骤 {step_num} 数据失败: {e}")

                # 尝试保存为文本文件
                try:
                    text_file = output_folder / f"step_{step_num}_output.txt"
                    with open(text_file, "w", encoding="utf-8") as f:
                        f.write(str(data))
                    logger.info(f"✅ 已保存为文本文件: {text_file.name}")
                except Exception as e2:
                    logger.error(f"❌ 保存文本文件也失败: {e2}")

        return output_folder

    def process_single_video(self, video_info, retry_count=0):
        """处理单个视频的完整流程"""
        video_name = video_info["filename"]
        duration = video_info["duration"]
        video_path = self.videos_folder / video_name

        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 开始处理视频: {video_name}")
        logger.info(f"{'='*60}")
        
        # 重置 Content blocked 处理标记（每个视频独立处理）
        self.last_blocked_time = 0

        try:
            # 1. 更新提示词文件
            if not self.update_prompts_file(video_name, duration):
                logger.error("更新提示词文件失败")
                return False

            # 2. 获取提示词列表
            prompts = self.get_prompts_list()
            if not prompts:
                logger.error("❌ 没有找到提示词")
                return False

            logger.info(f"共有 {len(prompts)} 个提示词需要处理")

            # 3. 打开 AI Studio
            if not self.open_ai_studio():
                return False

            # 4. 上传视频
            if not self.upload_video(video_path):
                return False

            # 5. 发送第一个提示词并运行
            if prompts:
                if not self.send_prompt(prompts[0], step_number=1):
                    return False
                self.wait_for_response(step_number=1)

            # 6. 逐步发送剩余提示词（步骤2-25）
            step_outputs = {}

            for i, prompt in enumerate(prompts[1:], start=2):
                logger.info(f"\n{'─'*40}")
                logger.info(f"📝 步骤 {i}/{len(prompts)}")
                logger.info(f"{'─'*40}")

                if not self.send_prompt(prompt, step_number=i):
                    logger.warning(f"步骤 {i} 发送失败，尝试继续...")
                    continue

                self.wait_for_response(step_number=i)

                # 保存特定步骤的输出
                if i in config.SAVE_STEPS:
                    response = self.extract_response()
                    step_outputs[i] = response
                    logger.info(f"💾 已捕获步骤 {i} 的输出")
                    self.take_screenshot(f"step_{i}_output")

            # 7. 保存输出数据
            self.save_output_data(video_name, step_outputs)

            logger.info(f"✅ 视频 {video_name} 处理完成")
            return True

        except Exception as e:
            logger.error(f"❌ 处理视频时出错: {e}")
            self.take_screenshot("error_process_video")

            # 重试逻辑
            if retry_count < config.MAX_RETRIES:
                logger.info(
                    f"⏳ {config.RETRY_DELAY} 秒后重试 ({retry_count + 1}/{config.MAX_RETRIES})..."
                )
                time.sleep(config.RETRY_DELAY)
                return self.process_single_video(video_info, retry_count + 1)
            else:
                logger.error(f"❌ 已达到最大重试次数，跳过视频: {video_name}")
                return False

    def merge_all_excel_files(self):
        """合并所有输出的 Excel 文件"""
        print("\n📊 开始合并所有 Excel 文件...")

        all_data = []
        for folder in self.process_folder.iterdir():
            if folder.is_dir() and folder.name != "videos":
                for excel_file in folder.glob("*.xlsx"):
                    try:
                        df = pd.read_excel(excel_file)
                        all_data.append(df)
                        print(f"  ✅ 读取: {excel_file.name}")
                    except Exception as e:
                        print(f"  ❌ 读取失败 {excel_file.name}: {e}")

        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)

            # 保存到 clips.xlsx
            self.clips_file.parent.mkdir(exist_ok=True)
            merged_df.to_excel(self.clips_file, index=False)
            print(f"✅ 合并完成，保存到: {self.clips_file}")
            return True
        else:
            print("❌ 没有找到可合并的文件")
            return False

    def run_final_processing(self):
        """运行最终的视频处理脚本"""
        process_script = self.output_folder / "process_video.py"
        if process_script.exists():
            print(f"\n🎬 运行最终处理脚本: {process_script}")
            os.system(f"python3 {process_script}")
        else:
            print(f"⚠️ 找不到处理脚本: {process_script}")

    def run(self, headless=None, use_system_chrome=None):
        """运行完整的自动化流程"""
        logger.info("🚀 视频处理自动化开始")
        logger.info(f"📁 工作目录: {self.base_dir}")
        logger.info(f"📝 日志文件: {config.LOG_FILE}")

        # 1. 加载视频列表
        videos = self.load_video_list()
        if not videos:
            logger.error("❌ 没有找到待处理的视频")
            return

        # 2. 初始化浏览器
        if use_system_chrome is None:
            use_system_chrome = config.USE_SYSTEM_CHROME
        self.init_browser(headless=headless, use_system_chrome=use_system_chrome)

        success_count = 0
        failed_videos = []

        try:
            # 3. 处理每个视频
            for i, video_info in enumerate(videos, start=1):
                logger.info(f"\n{'#'*60}")
                logger.info(f"# 进度: {i}/{len(videos)}")
                logger.info(f"# 视频: {video_info['filename']}")
                logger.info(f"{'#'*60}")

                if self.process_single_video(video_info):
                    success_count += 1
                else:
                    failed_videos.append(video_info["filename"])

                # 每个视频之间稍作休息
                if i < len(videos):
                    logger.info(f"\n⏸️ 休息 {config.WAIT_BETWEEN_VIDEOS} 秒...")
                    time.sleep(config.WAIT_BETWEEN_VIDEOS)

            # 4. 合并所有 Excel 文件
            logger.info("\n" + "=" * 60)
            logger.info("开始合并数据...")
            logger.info("=" * 60)
            self.merge_all_excel_files()

            # 5. 运行最终处理
            logger.info("\n" + "=" * 60)
            logger.info("运行最终处理...")
            logger.info("=" * 60)
            self.run_final_processing()

            # 6. 输出统计信息
            logger.info("\n" + "=" * 60)
            logger.info("🎉 所有任务完成！")
            logger.info("=" * 60)
            logger.info(f"✅ 成功处理: {success_count}/{len(videos)} 个视频")

            if failed_videos:
                logger.warning(f"❌ 失败视频: {', '.join(failed_videos)}")

        except KeyboardInterrupt:
            logger.warning("\n⚠️ 用户中断")
        except Exception as e:
            logger.error(f"\n❌ 发生错误: {e}")
            import traceback

            traceback.print_exc()
        finally:
            # 7. 关闭浏览器
            self.close_browser()
            logger.info(f"\n📝 完整日志已保存到: {config.LOG_FILE}")


def main():
    """主函数"""
    processor = VideoProcessor()

    # headless=False 表示显示浏览器窗口，方便调试
    # headless=True 表示无头模式，后台运行
    processor.run(headless=False)


if __name__ == "__main__":
    main()
