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
        
        # 账号切换记录
        self.unavailable_accounts = set()  # 记录不可用的账号（遇到rate limit的）
        self.current_account = None  # 当前使用的账号
        
        # AI Studio 打开标记
        self.ai_studio_opened = False  # 标记是否已经打开过 AI Studio

        # 确保目录存在
        ensure_directories()

    def load_video_list(self):
        """加载视频列表"""
        if not self.video_list_file.exists():
            logger.error(f"❌ 找不到视频列表文件: {self.video_list_file}")
            return []

        try:
            df = pd.read_csv(self.video_list_file)
            
            # 清理列名（去除前后空格）
            df.columns = df.columns.str.strip()
            
            videos = []
            for _, row in df.iterrows():
                video_info = {
                    "filename": row["Filename"],
                    "duration": row["Duration"]
                }
                # 如果有line1和line2列，也加载进来
                if "line1" in row:
                    video_info["line1"] = row["line1"]
                if "line2" in row:
                    video_info["line2"] = row["line2"]
                videos.append(video_info)
            logger.info(f"✅ 加载了 {len(videos)} 个视频")
            return videos
        except Exception as e:
            logger.error(f"❌ 读取视频列表失败: {e}")
            logger.error(f"   可用的列名: {list(df.columns) if 'df' in locals() else '无法读取'}")
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

    def update_prompts_file(self, video_info):
        """更新提示词文件中的视频信息
        
        Args:
            video_info: 字典，包含 filename, duration, line1, line2 等字段
        """
        df = self.load_prompts()
        if df is None:
            return False

        # 更新视频名称
        if "视频名称" in df.columns:
            df.loc[0, "视频名称"] = video_info.get("filename", "")
        
        # 更新视频时长
        if "视频时长" in df.columns:
            df.loc[0, "视频时长"] = video_info.get("duration", "")
        
        # 更新line1
        if "line1" in df.columns and "line1" in video_info:
            df.loc[0, "line1"] = video_info.get("line1", "")
        
        # 更新line2（注意Excel中可能是lin2的拼写错误）
        if "line2" in df.columns and "line2" in video_info:
            df.loc[0, "line2"] = video_info.get("line2", "")
        elif "lin2" in df.columns and "line2" in video_info:
            df.loc[0, "lin2"] = video_info.get("line2", "")

        df.to_excel(self.prompts_file, index=False)
        logger.info(f"✅ 更新提示词文件: {video_info.get('filename')} - {video_info.get('duration')}")
        if "line1" in video_info:
            logger.info(f"   line1: {video_info.get('line1')}")
        if "line2" in video_info:
            logger.info(f"   line2: {video_info.get('line2')}")
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
        """打开 Google AI Studio 并等待用户确认（仅首次）"""
        logger.info(f"🌐 正在打开 {self.ai_studio_url}")
        try:
            # 使用更长的超时时间和更完整的等待策略
            self.page.goto(self.ai_studio_url, wait_until="networkidle", timeout=60000)
            logger.info("⏳ 等待页面完全加载...")
            
            # 等待页面稳定
            time.sleep(5)
            
            # 等待关键元素加载
            try:
                # 等待页面主要内容加载
                self.page.wait_for_selector('body', state="visible", timeout=10000)
                logger.info("✅ 页面主体已加载")
            except:
                logger.warning("⚠️ 等待页面主体超时，继续执行")
            
            self.take_screenshot("ai_studio_opened")
            logger.info("✅ AI Studio 已打开")
            
            # 只在首次打开时等待用户确认
            if config.WAIT_USER_CONFIRMATION and not self.ai_studio_opened:
                logger.info("📝 首次打开 AI Studio，需要用户确认")
                if not self.wait_for_user_confirmation():
                    logger.error("❌ 用户未确认，终止操作")
                    return False
                # 标记已经打开过
                self.ai_studio_opened = True
            elif self.ai_studio_opened:
                logger.info("✅ 非首次打开，跳过用户确认")
            else:
                # 不需要用户确认，自动检测登录状态
                if not self.check_login_status():
                    logger.info("🔐 需要登录")
                    if not self.wait_for_login():
                        return False
                    
                    # 登录后刷新页面
                    self.page.reload(wait_until="networkidle", timeout=60000)
                    time.sleep(3)
                
                # 标记已经打开过
                self.ai_studio_opened = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 打开 AI Studio 失败: {e}")
            self.take_screenshot("error_open_ai_studio")
            return False

    def check_and_close_upload_popup(self):
        """检查上传后是否有弹窗（如版权确认），如果有则关闭"""
        try:
            # 等待一下，让弹窗有时间出现
            time.sleep(2)
            
            # 检查是否有 Acknowledge 按钮（版权确认弹窗）
            acknowledge_selectors = [
                'button[aria-label*="Acknowledge"]',
                'button[aria-label*="acknowledgement"]',
                'button:has-text("Acknowledge")',
                'button.ms-button-primary:has-text("Acknowledge")',
            ]
            
            for selector in acknowledge_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.count() > 0 and button.is_visible(timeout=2000):
                        logger.warning("⚠️ 检测到上传后的弹窗（版权确认）")
                        self.take_screenshot("upload_popup_detected")
                        
                        # 点击 Acknowledge 按钮
                        button.click(timeout=5000)
                        logger.info("✅ 已点击 Acknowledge 按钮")
                        time.sleep(2)
                        self.take_screenshot("upload_popup_closed")
                        
                        return True  # 返回 True 表示有弹窗并已关闭
                except:
                    continue
            
            # 没有检测到弹窗
            logger.debug("✅ 未检测到上传后的弹窗")
            return False
            
        except Exception as e:
            logger.debug(f"检查上传弹窗时出错: {e}")
            return False
    
    def check_video_uploaded(self):
        """检查视频是否已成功上传到对话中"""
        try:
            # 查找视频缩略图或视频元素
            video_indicators = [
                'video',  # video 标签
                '[data-test-id*="video"]',
                'img[alt*="video"]',
                '.video-thumbnail',
                '[role="img"]',
            ]
            
            for selector in video_indicators:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0 and element.is_visible(timeout=2000):
                        logger.debug(f"✅ 检测到视频元素: {selector}")
                        return True
                except:
                    continue
            
            logger.warning("⚠️ 未检测到视频元素")
            return False
            
        except Exception as e:
            logger.debug(f"检查视频上传状态时出错: {e}")
            return False
    
    def upload_video(self, video_path):
        """上传视频文件 - 点击添加按钮，然后点击 Upload File"""
        logger.info(f"📤 正在上传视频: {video_path}")

        if not Path(video_path).exists():
            logger.error(f"❌ 视频文件不存在: {video_path}")
            return False

        try:
            # 等待页面完全加载
            logger.info("⏳ 等待页面加载完成...")
            time.sleep(3)
            
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
                    if add_button.count() > 0:
                        # 等待按钮可见
                        add_button.wait_for(state="visible", timeout=10000)
                        if add_button.is_visible():
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
            time.sleep(2)  # 增加等待时间，让菜单完全展开
            self.take_screenshot("add_button_clicked")

            # 步骤2：等待并点击 Upload File 按钮
            logger.info("2️⃣ 等待 Upload File 按钮...")
            upload_file_selectors = [
                'button[aria-label="Upload File"]',
                'button:has-text("Upload File")',
                'button[mat-menu-item]:has(span:has-text("Upload File"))',
            ]

            upload_file_button = None
            max_wait = 10  # 最多等待 10 秒
            waited = 0
            
            while waited < max_wait and not upload_file_button:
                for selector in upload_file_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.count() > 0 and btn.is_visible():
                            upload_file_button = btn
                            break
                    except:
                        continue
                
                if not upload_file_button:
                    time.sleep(0.5)
                    waited += 0.5

            if not upload_file_button:
                logger.error("❌ 找不到 Upload File 按钮")
                self.take_screenshot("error_no_upload_file_button")
                return False

            logger.info("✅ 找到 Upload File 按钮")

            # 步骤3：使用 file chooser 上传文件
            logger.info("3️⃣ 设置文件选择器并上传文件...")
            
            # 使用 file chooser 事件（必须在点击前设置）
            try:
                # 设置文件选择器监听，然后点击按钮
                with self.page.expect_file_chooser(timeout=30000) as fc_info:
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
            time.sleep(1)  # 增加等待时间
            try:
                # 方法1：按 Escape 键关闭菜单
                self.page.keyboard.press("Escape")
                logger.info("✅ 已按 Escape 键关闭菜单")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ 按 Escape 键失败: {e}")
                
                # 方法2：点击页面其他区域关闭菜单
                try:
                    # 点击页面中心区域
                    self.page.mouse.click(500, 300)
                    logger.info("✅ 已点击页面关闭菜单")
                    time.sleep(1)
                except Exception as e2:
                    logger.warning(f"⚠️ 点击关闭菜单失败: {e2}")
            
            # 步骤5：等待上传完成（检测上传进度）
            logger.info("⏳ 等待视频上传完成...")
            
            # 等待上传进度条消失或上传完成
            upload_wait_time = 0
            max_upload_wait = config.WAIT_AFTER_UPLOAD * 2  # 最多等待 2 倍时间
            
            while upload_wait_time < max_upload_wait:
                # 检查是否有上传进度指示器
                try:
                    # 常见的上传进度指示器
                    progress_selectors = [
                        '[role="progressbar"]',
                        '.upload-progress',
                        'text="Uploading"',
                        'text="上传中"',
                    ]
                    
                    uploading = False
                    for selector in progress_selectors:
                        try:
                            indicator = self.page.locator(selector).first
                            if indicator.count() > 0 and indicator.is_visible():
                                uploading = True
                                break
                        except:
                            continue
                    
                    if not uploading:
                        # 没有上传指示器，可能已完成
                        logger.info("✅ 未检测到上传进度指示器，可能已完成")
                        break
                    
                    # 每 5 秒输出一次进度
                    if upload_wait_time % 5 == 0:
                        logger.info(f"⏳ 上传中... ({upload_wait_time}/{max_upload_wait} 秒)")
                    
                    time.sleep(1)
                    upload_wait_time += 1
                    
                except Exception as e:
                    logger.debug(f"检查上传进度时出错: {e}")
                    break
            
            # 额外等待确保上传完成
            time.sleep(3)
            self.take_screenshot("video_uploaded")

            # 检查是否有弹窗（例如版权确认）
            logger.info("🔍 检查上传后是否有弹窗...")
            if self.check_and_close_upload_popup():
                logger.info("✅ 已处理上传后的弹窗")
                # 弹窗关闭后，返回特殊标记，让调用者刷新页面重新开始
                return "popup_closed_need_refresh"
            
            # 验证视频是否真正上传成功
            logger.info("🔍 验证视频上传状态...")
            if self.check_video_uploaded():
                logger.info("✅ 视频上传完成并已验证")
                return True
            else:
                logger.warning("⚠️ 视频可能未成功上传（未检测到视频元素）")
                logger.info("💡 建议：刷新页面重试")
                return True  # 仍然返回 True，让后续流程检测 Run 按钮状态

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
                    logger.error(f"❌ 等待按钮可用超时（{max_wait} 秒）")
                    self.take_screenshot("error_run_button_timeout")
                    
                    # 如果是步骤1，说明视频上传可能失败，返回特殊标记
                    if step_number == 1:
                        logger.error("❌ 步骤1的 Run 按钮超时不可用，可能视频上传失败")
                        return "upload_failed"
                    else:
                        # 其他步骤尝试使用快捷键
                        logger.warning("⚠️ 尝试使用快捷键")
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
    
    def check_rate_limit(self):
        """检查是否达到速率限制或配额超限"""
        try:
            # 检查 rate limit 和 quota exceeded 错误提示
            rate_limit_texts = [
                "You've reached your rate limit",
                "rate limit",
                "exceeded quota",  # 新增：配额超限
                "user has exceeded quota",  # 新增：用户配额超限
                "Please try again later",  # 新增：请稍后重试
                "请稍后再试",
                "达到速率限制",
                "配额已超限",  # 新增：中文配额超限
            ]
            
            for text in rate_limit_texts:
                try:
                    element = self.page.get_by_text(text, exact=False).first
                    if element.is_visible(timeout=1000):
                        logger.warning(f"⚠️ 检测到速率限制或配额超限: {text}")
                        self.take_screenshot("rate_limit_or_quota_exceeded")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"检查速率限制时出错: {e}")
            return False
    
    def get_current_account(self):
        """获取当前登录的账号（增强版，等待页面更新）"""
        try:
            # 等待页面稳定
            time.sleep(2)
            
            # 查找账号切换按钮，从中提取账号信息
            account_button_selectors = [
                'button.account-switcher-button',
                'button[class*="account-switcher"]',
            ]
            
            for selector in account_button_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.count() > 0:
                        # 等待按钮可见
                        button.wait_for(state="visible", timeout=5000)
                        
                        # 提取账号文本 - 尝试多种方法
                        account_text = None
                        
                        # 方法1: 从 inner_text 提取
                        try:
                            text = button.inner_text()
                            if '@' in text:
                                account_text = text.strip()
                        except:
                            pass
                        
                        # 方法2: 从子元素中查找邮箱
                        if not account_text:
                            try:
                                # 查找包含 @ 的 span 元素
                                email_span = button.locator('span:has-text("@")').first
                                if email_span.count() > 0:
                                    account_text = email_span.inner_text().strip()
                            except:
                                pass
                        
                        # 方法3: 从 aria-label 或 title 属性提取
                        if not account_text:
                            try:
                                aria_label = button.get_attribute('aria-label')
                                if aria_label and '@' in aria_label:
                                    account_text = aria_label.strip()
                            except:
                                pass
                        
                        if account_text and '@' in account_text:
                            logger.debug(f"检测到当前账号: {account_text}")
                            return account_text
                except Exception as e:
                    logger.debug(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            logger.warning("⚠️ 无法获取当前账号")
            return None
            
        except Exception as e:
            logger.debug(f"获取当前账号时出错: {e}")
            return None
    
    def close_popups(self):
        """关闭页面上的所有弹窗"""
        try:
            logger.info("🔍 检查并关闭弹窗...")
            
            # 常见的弹窗关闭按钮选择器
            close_button_selectors = [
                # 标准关闭按钮
                'button[aria-label="Close"]',
                'button[aria-label="关闭"]',
                'button[aria-label="Dismiss"]',
                'button[aria-label="Got it"]',
                'button[aria-label="OK"]',
                
                # 确认/同意按钮
                'button[aria-label*="Acknowledge"]',  # Acknowledge 按钮
                'button[aria-label*="acknowledgement"]',
                'button:has-text("Acknowledge")',
                'button:has-text("Accept")',
                'button:has-text("Agree")',
                'button:has-text("Continue")',
                'button:has-text("同意")',
                'button:has-text("接受")',
                'button:has-text("继续")',
                
                # 文本匹配
                'button:has-text("Close")',
                'button:has-text("关闭")',
                'button:has-text("Got it")',
                'button:has-text("OK")',
                'button:has-text("知道了")',
                
                # 属性匹配
                '[role="button"][aria-label*="close"]',
                '[role="button"][aria-label*="Close"]',
                '[role="button"][aria-label*="Acknowledge"]',
                
                # CSS 类匹配
                '.close-button',
                '.dismiss-button',
                'button.mdc-icon-button',  # Material Design 关闭按钮
                'button.ms-button-primary',  # MS Button Primary（可能是确认按钮）
                
                # 对话框内的主要按钮
                'mat-dialog-actions button',  # Material Dialog 操作按钮
                '.mat-mdc-dialog-actions button',  # Material Dialog 操作按钮
            ]
            
            closed_count = 0
            max_attempts = 5  # 最多尝试关闭5次（可能有多个弹窗）
            
            for attempt in range(max_attempts):
                found_popup = False
                
                for selector in close_button_selectors:
                    try:
                        # 查找所有匹配的关闭按钮
                        buttons = self.page.locator(selector).all()
                        
                        for button in buttons:
                            try:
                                # 检查按钮是否可见
                                if button.is_visible(timeout=1000):
                                    button.click(timeout=2000)
                                    closed_count += 1
                                    found_popup = True
                                    logger.info(f"✅ 已关闭弹窗 #{closed_count}")
                                    time.sleep(0.5)  # 等待弹窗关闭动画
                                    break
                            except:
                                continue
                        
                        if found_popup:
                            break
                            
                    except:
                        continue
                
                # 如果没有找到更多弹窗，退出循环
                if not found_popup:
                    break
                
                # 等待一下，看是否有新的弹窗出现
                time.sleep(1)
            
            if closed_count > 0:
                logger.info(f"✅ 共关闭了 {closed_count} 个弹窗")
                self.take_screenshot("popups_closed")
            else:
                logger.info("✅ 未检测到弹窗")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 关闭弹窗时出错: {e}")
            return False
    
    def switch_account(self):
        """切换 Google 账号"""
        logger.info("\n" + "="*60)
        logger.info("🔄 开始切换账号")
        logger.info("="*60)
        
        try:
            # 步骤1：获取当前账号并标记为不可用
            current_account = self.get_current_account()
            if current_account:
                logger.info(f"📧 当前账号: {current_account}")
                self.unavailable_accounts.add(current_account)
                logger.info(f"🚫 标记为不可用: {current_account}")
            else:
                logger.warning("⚠️ 无法获取当前账号")
            
            # 步骤2：点击账号切换按钮
            logger.info("1️⃣ 点击账号切换按钮...")
            account_button_selectors = [
                'button.account-switcher-button',
                'button[class*="account-switcher"]',
                'button[ms-button][variant="borderless"]',
            ]
            
            account_button = None
            for selector in account_button_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.count() > 0 and button.is_visible():
                        account_button = button
                        break
                except:
                    continue
            
            if not account_button:
                logger.error("❌ 找不到账号切换按钮")
                self.take_screenshot("error_no_account_button")
                return False
            
            account_button.click()
            logger.info("✅ 已点击账号切换按钮")
            time.sleep(2)
            self.take_screenshot("account_menu_opened")
            
            # 步骤3：点击"切换账号"按钮
            logger.info("2️⃣ 点击切换账号按钮...")
            switch_button_selectors = [
                'button.switch-account-button',
                'button:has-text("切换账号")',
                'button:has-text("Switch account")',
                'button[mat-stroked-button]:has-text("切换账号")',
            ]
            
            switch_button = None
            max_wait = 5
            waited = 0
            
            while waited < max_wait and not switch_button:
                for selector in switch_button_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.count() > 0 and btn.is_visible():
                            switch_button = btn
                            break
                    except:
                        continue
                
                if not switch_button:
                    time.sleep(0.5)
                    waited += 0.5
            
            if not switch_button:
                logger.error("❌ 找不到切换账号按钮")
                self.take_screenshot("error_no_switch_button")
                return False
            
            switch_button.click()
            logger.info("✅ 已点击切换账号按钮")
            time.sleep(3)
            self.take_screenshot("switch_account_clicked")
            
            # 步骤4：等待跳转到 Google 账号切换页面
            logger.info("3️⃣ 等待跳转到账号切换页面...")
            try:
                # 等待 URL 变化
                self.page.wait_for_url("**/accounts.google.com/**", timeout=10000)
                logger.info("✅ 已跳转到 Google 账号切换页面")
            except:
                logger.warning("⚠️ 未检测到 URL 跳转，可能已在账号选择页面")
            
            time.sleep(2)
            self.take_screenshot("google_account_page")
            
            # 步骤5：选择下一个可用账号
            logger.info("4️⃣ 选择下一个可用账号...")
            
            # 等待账号列表加载
            time.sleep(2)
            
            # 查找所有可用账号 - 使用更精确的选择器
            account_selectors = [
                'div[data-identifier]',  # Google 账号选择器（最常见）
                'div[role="link"]',
                'li[data-email]',
                'div[data-email]',
                'a[data-identifier]',
            ]
            
            available_accounts = []
            all_accounts_found = []  # 记录所有找到的账号（用于调试）
            
            for selector in account_selectors:
                try:
                    accounts = self.page.locator(selector).all()
                    logger.debug(f"选择器 {selector} 找到 {len(accounts)} 个元素")
                    
                    for account in accounts:
                        try:
                            # 尝试多种方法提取账号信息
                            account_text = None
                            
                            # 方法1: 从 data-identifier 属性提取
                            try:
                                identifier = account.get_attribute('data-identifier')
                                if identifier and '@' in identifier:
                                    account_text = identifier.strip()
                            except:
                                pass
                            
                            # 方法2: 从 data-email 属性提取
                            if not account_text:
                                try:
                                    email = account.get_attribute('data-email')
                                    if email and '@' in email:
                                        account_text = email.strip()
                                except:
                                    pass
                            
                            # 方法3: 从 inner_text 提取
                            if not account_text:
                                try:
                                    text = account.inner_text()
                                    if '@' in text:
                                        # 提取邮箱部分（可能包含名字）
                                        import re
                                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                                        if email_match:
                                            account_text = email_match.group()
                                except:
                                    pass
                            
                            if account_text and '@' in account_text:
                                all_accounts_found.append(account_text)
                                # 检查是否不可用
                                if account_text not in self.unavailable_accounts:
                                    available_accounts.append((account, account_text))
                                    logger.debug(f"  ✅ 可用账号: {account_text}")
                                else:
                                    logger.debug(f"  🚫 不可用: {account_text}")
                        except Exception as e:
                            logger.debug(f"  ⚠️ 提取账号信息失败: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"选择器 {selector} 查询失败: {e}")
                    continue
            
            # 去重账号列表
            unique_accounts = list(set(all_accounts_found))
            unique_available = []
            seen = set()
            for account, account_text in available_accounts:
                if account_text not in seen:
                    unique_available.append((account, account_text))
                    seen.add(account_text)
            available_accounts = unique_available
            
            # 输出统计信息
            logger.info(f"📊 找到 {len(unique_accounts)} 个不同账号，其中 {len(available_accounts)} 个可用")
            if unique_accounts:
                logger.info(f"📋 所有账号: {', '.join(unique_accounts)}")
            if self.unavailable_accounts:
                logger.info(f"🚫 不可用账号: {', '.join(self.unavailable_accounts)}")
            
            selected_account_text = None
            
            if not available_accounts:
                logger.warning("⚠️ 没有找到可用的账号")
                logger.info("💡 提示: 所有账号可能都已使用，或需要手动选择")
                
                # 等待用户手动选择
                logger.info("\n请手动选择一个账号，然后按 Enter 继续...")
                try:
                    input("👉 选择完成后按 Enter: ")
                    # 用户手动选择后，尝试获取当前账号
                    time.sleep(3)
                    selected_account_text = self.get_current_account()
                    if selected_account_text:
                        logger.info(f"📧 检测到选择的账号: {selected_account_text}")
                        self.switched_accounts.add(selected_account_text)
                        self.current_account = selected_account_text
                except KeyboardInterrupt:
                    return False
            else:
                # 自动选择第一个未使用的账号
                next_account, next_account_text = available_accounts[0]
                logger.info(f"📧 选择账号: {next_account_text}")
                
                try:
                    next_account.click()
                    logger.info("✅ 已点击账号")
                    
                    # 记录选择的账号
                    selected_account_text = next_account_text
                    self.switched_accounts.add(next_account_text)
                    self.current_account = next_account_text
                except Exception as e:
                    logger.error(f"❌ 点击账号失败: {e}")
                    return False
            
            # 步骤6：等待返回 AI Studio
            logger.info("5️⃣ 等待返回 AI Studio...")
            time.sleep(5)
            
            try:
                # 等待返回 AI Studio
                self.page.wait_for_url("**/aistudio.google.com/**", timeout=30000)
                logger.info("✅ 已返回 AI Studio")
            except:
                logger.warning("⚠️ 未检测到返回 AI Studio，可能需要手动操作")
            
            # 等待页面完全加载
            time.sleep(3)
            self.take_screenshot("account_switched")
            
            # 验证账号是否切换成功
            logger.info("6️⃣ 验证账号切换...")
            new_account = self.get_current_account()
            if new_account:
                logger.info(f"✅ 当前账号: {new_account}")
                # 更新记录
                if new_account != current_account:
                    logger.info(f"✅ 账号切换成功: {current_account} → {new_account}")
                    self.switched_accounts.add(new_account)
                    self.current_account = new_account
                else:
                    logger.warning(f"⚠️ 账号未改变，仍然是: {new_account}")
            else:
                logger.warning("⚠️ 无法验证新账号")
            
            # 步骤7：等待并关闭弹窗
            logger.info("7️⃣ 等待并关闭弹窗...")
            time.sleep(5)  # 等待5秒，让弹窗出现
            self.close_popups()
            
            logger.info("="*60)
            logger.info("✅ 账号切换完成")
            logger.info(f"📊 已切换账号数: {len(self.switched_accounts)}")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 切换账号失败: {e}")
            import traceback
            traceback.print_exc()
            self.take_screenshot("error_switch_account")
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
        """等待 AI 响应完成 - 通过检测按钮状态，并处理 rate limit
        
        每个步骤都不能跳过，会持续等待直到AI完成。
        如果超过3次超时，会询问用户是否继续等待。
        """
        if timeout is None:
            timeout = config.WAIT_FOR_RESPONSE * 6  # 默认 60 秒

        step_info = f"步骤 {step_number}" if step_number else ""
        logger.info(f"⏳ 等待 AI 响应{step_info}...")

        start_time = time.time()
        check_interval = 2
        last_status_log = 0
        timeout_count = 0  # 超时次数计数
        max_timeout_count = 3  # 最多3次超时后询问用户

        while True:  # 改为无限循环，直到AI完成
            elapsed = time.time() - start_time
            
            # 检查是否达到速率限制
            if self.check_rate_limit():
                logger.warning("⚠️ 检测到速率限制，尝试切换账号...")
                
                # 尝试切换账号
                if self.switch_account():
                    logger.info("✅ 账号切换成功，重新发送请求")
                    return "rate_limit_switched"
                else:
                    logger.error("❌ 账号切换失败")
                    logger.info("\n可选操作:")
                    logger.info("  1. 输入 'retry' - 重试切换账号")
                    logger.info("  2. 输入 'manual' - 手动切换后继续")
                    logger.info("  3. 输入 'skip' - 跳过当前视频")
                    logger.info("  4. 输入 'quit' - 退出程序")
                    
                    try:
                        user_input = input("\n👉 请输入操作: ").strip().lower()
                        
                        if user_input == 'retry':
                            if self.switch_account():
                                return "rate_limit_switched"
                        elif user_input == 'manual':
                            logger.info("请手动切换账号，完成后按 Enter 继续...")
                            input("👉 按 Enter 继续: ")
                            return "rate_limit_switched"
                        elif user_input == 'skip':
                            return "skip"
                        elif user_input == 'quit':
                            return "quit"
                    except KeyboardInterrupt:
                        return "quit"
                
                # 重置计时器
                start_time = time.time()
                timeout_count = 0
                continue
            
            # 检查是否被阻止
            if self.check_content_blocked():
                start_time = time.time()  # 重置计时器
                timeout_count = 0
                continue

            # 检查 AI 是否正在运行
            if self.is_ai_running():
                # AI 正在运行，继续等待
                current_time = time.time()
                if current_time - last_status_log > 10:  # 每 10 秒输出一次状态
                    elapsed_int = int(current_time - start_time)
                    logger.info(f"⏳ AI 正在处理... (已等待 {elapsed_int} 秒)")
                    last_status_log = current_time
                
                # 检查是否超时
                if elapsed > timeout:
                    timeout_count += 1
                    logger.warning(f"⚠️ 等待超时（第 {timeout_count} 次），但 AI 仍在运行")
                    
                    # 如果超过最大超时次数，询问用户
                    if timeout_count >= max_timeout_count:
                        logger.warning(f"⚠️ 已超时 {timeout_count} 次（{int(elapsed)} 秒）")
                        logger.info("\n" + "="*60)
                        logger.info(f"⚠️ AI 仍在处理{step_info}，已等待 {int(elapsed)} 秒")
                        logger.info("="*60)
                        logger.info("可选操作:")
                        logger.info("  1. 直接按 Enter - 继续等待")
                        logger.info("  2. 输入 'skip' - 跳过当前步骤（不推荐）")
                        logger.info("  3. 输入 'quit' - 退出程序")
                        
                        try:
                            user_input = input("\n👉 请输入操作（Enter继续等待）: ").strip().lower()
                            
                            if not user_input:
                                # 继续等待
                                logger.info("✅ 继续等待 AI 完成...")
                                start_time = time.time()  # 重置计时器
                                timeout_count = 0
                            elif user_input == 'skip':
                                logger.warning("⚠️ 用户选择跳过当前步骤")
                                return "skip"
                            elif user_input == 'quit':
                                logger.info("👋 用户选择退出")
                                return "quit"
                        except KeyboardInterrupt:
                            return "quit"
                    else:
                        # 还没到最大次数，自动继续等待
                        logger.info(f"💡 继续等待 AI 完成... (将在第 {max_timeout_count} 次超时后询问)")
                        start_time = time.time()  # 重置计时器
                
                time.sleep(check_interval)
                continue
            else:
                # AI 已完成，等待响应稳定
                logger.info("✅ AI 处理完成，等待响应稳定...")
                
                # 步骤25需要更长时间渲染表格
                if step_number == 25:
                    logger.info("📊 步骤25：等待表格渲染（5秒）...")
                    time.sleep(5)
                else:
                    time.sleep(3)
                break

            # 如果等待时间过长，截图记录
            if elapsed > timeout / 2 and elapsed % 30 < check_interval:
                self.take_screenshot(
                    f"waiting_response_step_{step_number}"
                    if step_number
                    else "waiting_response"
                )

        # AI 已完成
        logger.info(f"✅ AI 响应完成（总等待时间: {int(time.time() - start_time)} 秒）")
        self.take_screenshot(
            f"response_received_step_{step_number}"
            if step_number
            else "response_received"
        )

    def extract_response(self, step_number=None):
        """提取 AI 的响应内容"""
        try:
            # 获取最后的响应内容（使用正确的选择器）
            responses = self.page.locator('[data-turn-role="Model"]').all()
            logger.info(f"🔍 找到 {len(responses)} 个AI响应")
            
            if responses:
                # 选择最后一个非空的响应
                last_response_element = None
                for i in range(len(responses) - 1, -1, -1):
                    try:
                        text = responses[i].inner_text()
                        if text and len(text.strip()) > 0:
                            last_response_element = responses[i]
                            logger.info(f"📍 使用响应（索引 {i}），长度: {len(text)} 字符")
                            break
                    except:
                        continue
                
                if not last_response_element:
                    logger.warning("⚠️ 所有响应元素都为空")
                    last_response_element = responses[-1]
                    logger.info(f"📍 使用最后一个响应（索引 {len(responses)-1}）")
                
                # 检查响应是否为空，如果为空则等待一下
                try:
                    response_text = last_response_element.inner_text()
                    if not response_text or len(response_text.strip()) == 0:
                        logger.warning("⚠️ 响应元素为空，等待3秒后重试...")
                        time.sleep(3)
                        response_text = last_response_element.inner_text()
                        if not response_text or len(response_text.strip()) == 0:
                            logger.warning("⚠️ 响应仍然为空")
                            
                            # 调试：检查所有响应元素
                            logger.info("🔍 检查所有响应元素...")
                            for i, resp in enumerate(responses[-5:]):  # 检查最后5个
                                try:
                                    text = resp.inner_text()
                                    logger.info(f"  响应 {len(responses)-5+i}: {len(text)} 字符")
                                    if text:
                                        logger.info(f"    预览: {text[:100]}...")
                                except Exception as e:
                                    logger.warning(f"  响应 {len(responses)-5+i}: 无法读取 - {e}")
                            
                            # 尝试使用倒数第二个响应
                            if len(responses) >= 2:
                                logger.info("💡 尝试使用倒数第二个响应...")
                                last_response_element = responses[-2]
                                response_text = last_response_element.inner_text()
                                logger.info(f"📝 倒数第二个响应长度: {len(response_text)} 字符")
                except Exception as e:
                    logger.warning(f"⚠️ 检查响应文本失败: {e}")
                
                # 如果是步骤25，尝试直接从HTML DOM提取表格数据
                if step_number == 25:
                    logger.info("📊 步骤25：尝试从HTML DOM提取表格数据...")
                    
                    # 等待表格出现（最多等待10秒）
                    try:
                        logger.info("⏳ 等待表格元素出现...")
                        last_response_element.locator('table').first.wait_for(state='visible', timeout=10000)
                        logger.info("✅ 表格元素已出现")
                    except Exception as e:
                        logger.warning(f"⚠️ 等待表格超时: {e}")
                    
                    table_data = self.extract_table_from_dom(last_response_element)
                    if table_data:
                        logger.info(f"✅ 从DOM提取到 {len(table_data)} 行表格数据")
                        return table_data
                    else:
                        logger.warning("⚠️ 从DOM提取表格失败，回退到文本提取")
                
                # 默认：提取文本内容
                last_response = last_response_element.inner_text()
                logger.info(f"📝 提取响应文本，长度: {len(last_response)} 字符")
                if last_response:
                    logger.debug(f"响应内容预览: {last_response[:200]}...")
                else:
                    logger.warning("⚠️ 响应文本为空")
                return last_response
            else:
                logger.warning("⚠️ 未找到任何AI响应元素")
                return ""
        except Exception as e:
            logger.error(f"❌ 提取响应失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    def extract_table_from_dom(self, response_element):
        """从HTML DOM中直接提取表格数据"""
        try:
            # 查找表格元素
            tables = response_element.locator('table').all()
            if not tables:
                logger.warning("⚠️ 未找到表格元素")
                return None
            
            # 使用最后一个表格（通常是最新的）
            table = tables[-1]
            logger.info(f"📋 找到 {len(tables)} 个表格，使用最后一个")
            
            # 提取表头
            headers = []
            header_rows = table.locator('tr.table-header').all()
            if header_rows:
                header_row = header_rows[0]
                header_cells = header_row.locator('td').all()
                for cell in header_cells:
                    try:
                        text = cell.inner_text().strip()
                        headers.append(text)
                    except:
                        headers.append("")
                logger.info(f"📋 表头: {headers}")
            else:
                logger.warning("⚠️ 未找到表头")
                return None
            
            # 提取数据行
            table_data = []
            data_rows = table.locator('tr:not(.table-header)').all()
            logger.info(f"📊 找到 {len(data_rows)} 行数据")
            
            for row_index, row in enumerate(data_rows):
                try:
                    cells = row.locator('td').all()
                    row_dict = {}
                    
                    for col_index, cell in enumerate(cells):
                        try:
                            text = cell.inner_text().strip()
                            if col_index < len(headers):
                                header = headers[col_index]
                                row_dict[header] = text if text else ""
                            else:
                                row_dict[f"column_{col_index}"] = text if text else ""
                        except Exception as e:
                            logger.debug(f"提取单元格 [{row_index},{col_index}] 失败: {e}")
                            if col_index < len(headers):
                                row_dict[headers[col_index]] = ""
                    
                    if row_dict:
                        table_data.append(row_dict)
                        logger.debug(f"行 {row_index + 1}: {row_dict}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ 提取第 {row_index + 1} 行失败: {e}")
                    continue
            
            if table_data:
                logger.info(f"✅ 成功提取 {len(table_data)} 行数据")
                # 显示每列的统计
                for header in headers:
                    non_empty = sum(1 for row in table_data if row.get(header, ""))
                    logger.info(f"  - {header}: {non_empty}/{len(table_data)} 行有数据")
                return table_data
            else:
                logger.warning("⚠️ 未提取到任何数据")
                return None
            
        except Exception as e:
            logger.error(f"❌ 从DOM提取表格失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def parse_table_response(self, response_text):
        """解析 AI 响应中的表格数据
        
        尝试从响应文本中提取结构化的表格数据
        支持多种格式：Markdown表格、CSV格式、JSON格式等
        能够处理空单元格和不完整的行
        """
        import re
        import json
        
        if not response_text:
            return None
        
        try:
            # 方法1：尝试解析 Markdown 表格（改进版，支持空单元格）
            lines = response_text.strip().split('\n')
            table_data = []
            headers = []
            
            for i, line in enumerate(lines):
                # 跳过分隔线
                if re.match(r'^[\s\-\|]+$', line):
                    continue
                
                # 检查是否是表格行
                if '|' in line:
                    # 分割单元格，但保留空单元格
                    cells = line.split('|')
                    # 移除首尾的空单元格（Markdown 表格通常以 | 开头和结尾）
                    if cells and not cells[0].strip():
                        cells = cells[1:]
                    if cells and not cells[-1].strip():
                        cells = cells[:-1]
                    # 清理每个单元格的空白
                    cells = [cell.strip() for cell in cells]
                    
                    if cells:
                        if not headers:
                            # 第一行作为表头
                            headers = cells
                            logger.info(f"📋 检测到表头: {headers}")
                        else:
                            # 数据行：即使单元格数量不匹配也尝试解析
                            row_dict = {}
                            for j, header in enumerate(headers):
                                # 如果该列有数据，使用数据；否则使用空字符串
                                if j < len(cells):
                                    row_dict[header] = cells[j] if cells[j] else ""
                                else:
                                    row_dict[header] = ""
                            table_data.append(row_dict)
            
            if table_data:
                logger.info(f"✅ 解析到 {len(table_data)} 行表格数据")
                # 显示每列的非空数据统计
                if headers:
                    for header in headers:
                        non_empty = sum(1 for row in table_data if row.get(header, ""))
                        logger.info(f"  - {header}: {non_empty}/{len(table_data)} 行有数据")
                return table_data
            
            # 方法2：尝试解析 JSON 格式
            try:
                # 查找 JSON 数组
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    json_data = json.loads(json_match.group())
                    if isinstance(json_data, list) and json_data:
                        logger.info(f"✅ 解析到 {len(json_data)} 行 JSON 数据")
                        return json_data
            except:
                pass
            
            # 方法3：尝试解析 CSV 格式
            try:
                import io
                csv_data = pd.read_csv(io.StringIO(response_text))
                if not csv_data.empty:
                    logger.info(f"✅ 解析到 {len(csv_data)} 行 CSV 数据")
                    return csv_data.to_dict('records')
            except:
                pass
            
            logger.warning("⚠️ 无法解析为结构化数据，将保存原始文本")
            return None
            
        except Exception as e:
            logger.error(f"❌ 解析表格数据失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def extract_and_save_srt_files(self, text_content, output_folder):
        """从文本中提取并保存SRT文件
        
        Args:
            text_content: 包含SRT内容的文本
            output_folder: 输出文件夹
            
        Returns:
            保存的SRT文件列表
        """
        import re
        
        srt_files = []
        
        try:
            # 方法1：查找明确标记的SRT文件（如 "文件1:" 或 "File 1:"）
            # 分割文本，查找多个SRT块
            srt_pattern = r'(?:文件|File|SRT)\s*(\d+)[：:](.*?)(?=(?:文件|File|SRT)\s*\d+[：:]|$)'
            matches = re.findall(srt_pattern, text_content, re.DOTALL | re.IGNORECASE)
            
            if matches:
                logger.info(f"📋 找到 {len(matches)} 个标记的SRT文件")
                for i, (file_num, srt_content) in enumerate(matches, 1):
                    srt_file = output_folder / f"step_23_output_{file_num}.srt"
                    with open(srt_file, "w", encoding="utf-8") as f:
                        f.write(srt_content.strip())
                    srt_files.append(srt_file)
                    logger.info(f"✅ 保存SRT文件 {file_num}: {srt_file.name} ({len(srt_content)} 字符)")
            else:
                # 方法2：查找SRT格式的内容块（通过时间戳识别）
                # SRT格式：序号 + 时间戳 + 文本
                srt_block_pattern = r'(\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}.*?)(?=\n\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->|\Z)'
                
                # 尝试分割成多个SRT文件（通过连续的空行或特定标记）
                # 简单方法：如果文本很长，可能包含多个SRT文件，尝试按长度分割
                if '00:00:00,000' in text_content or '00:00:00,0' in text_content:
                    # 包含SRT时间戳，尝试保存
                    # 检查是否有多个SRT文件（通过查找多个起始时间戳）
                    start_timestamps = re.findall(r'^1\s+00:00:00', text_content, re.MULTILINE)
                    
                    if len(start_timestamps) > 1:
                        # 多个SRT文件，尝试分割
                        logger.info(f"📋 检测到 {len(start_timestamps)} 个SRT文件起始标记")
                        parts = re.split(r'(?=^1\s+00:00:00)', text_content, flags=re.MULTILINE)
                        parts = [p.strip() for p in parts if p.strip()]
                        
                        for i, part in enumerate(parts, 1):
                            if part:
                                srt_file = output_folder / f"step_23_output_{i}.srt"
                                with open(srt_file, "w", encoding="utf-8") as f:
                                    f.write(part)
                                srt_files.append(srt_file)
                                logger.info(f"✅ 保存SRT文件 {i}: {srt_file.name} ({len(part)} 字符)")
                    else:
                        # 单个SRT文件
                        srt_file = output_folder / "step_23_output_1.srt"
                        with open(srt_file, "w", encoding="utf-8") as f:
                            f.write(text_content.strip())
                        srt_files.append(srt_file)
                        logger.info(f"✅ 保存SRT文件: {srt_file.name} ({len(text_content)} 字符)")
            
            return srt_files
            
        except Exception as e:
            logger.error(f"❌ 提取SRT文件失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def save_output_data(self, video_name, step_outputs):
        """保存输出数据为 Excel"""
        output_folder = self.process_folder / video_name.replace(".mp4", "").replace(
            ".MP4", ""
        )
        output_folder.mkdir(exist_ok=True)

        logger.info(f"💾 保存输出数据到: {output_folder}")
        logger.info(f"📊 待保存的步骤: {list(step_outputs.keys())}")

        for step_num, data in step_outputs.items():
            logger.info(f"🔍 处理步骤 {step_num}, 数据类型: {type(data)}, 数据长度: {len(data) if data else 0}")
            
            if not data:
                logger.warning(f"⚠️ 步骤 {step_num} 数据为空，跳过")
                continue

            # 步骤23特殊处理：保存为SRT文件
            if step_num == 23 and isinstance(data, str):
                try:
                    srt_files = self.extract_and_save_srt_files(data, output_folder)
                    if srt_files:
                        logger.info(f"✅ 步骤 23 保存了 {len(srt_files)} 个SRT文件")
                        for srt_file in srt_files:
                            logger.info(f"  - {srt_file.name}")
                    else:
                        logger.warning("⚠️ 步骤 23 未找到SRT文件内容，保存为文本")
                        # 回退到保存为文本文件
                        text_file = output_folder / f"step_{step_num}_output.txt"
                        with open(text_file, "w", encoding="utf-8") as f:
                            f.write(data)
                        logger.info(f"✅ 已保存为文本文件: {text_file.name}")
                    continue
                except Exception as e:
                    logger.error(f"❌ 保存步骤 23 SRT文件失败: {e}")
                    # 继续使用默认的保存逻辑

            output_file = output_folder / f"step_{step_num}_output.xlsx"

            try:
                # 如果是列表（从DOM直接提取的表格数据）
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    logger.info(f"📊 步骤 {step_num} 数据: {len(df)} 行 x {len(df.columns)} 列")
                    logger.info(f"📋 列名: {', '.join(df.columns.tolist())}")
                    
                # 如果是字符串，尝试解析为表格数据
                elif isinstance(data, str):
                    # 尝试解析表格数据
                    parsed_data = self.parse_table_response(data)
                    
                    if parsed_data:
                        # 成功解析为结构化数据
                        df = pd.DataFrame(parsed_data)
                        logger.info(f"📊 步骤 {step_num} 解析到 {len(df)} 行 x {len(df.columns)} 列数据")
                        logger.info(f"📋 列名: {', '.join(df.columns.tolist())}")
                    else:
                        # 无法解析，保存为单列文本
                        df = pd.DataFrame({"输出内容": [data]})
                        logger.info(f"📝 步骤 {step_num} 保存为原始文本")
                        
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame([{"数据": str(data)}])

                # 写入Excel文件
                df.to_excel(output_file, index=False)
                
                # 验证文件是否真的被创建
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    logger.info(f"✅ 保存步骤 {step_num} 数据: {output_file.name} ({file_size} 字节)")
                else:
                    logger.error(f"❌ 文件未创建: {output_file.name}")

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

    def wait_for_user_action(self, error_msg, current_step=None):
        """等待用户处理错误后继续"""
        logger.error(f"\n{'='*60}")
        logger.error(f"❌ 错误: {error_msg}")
        logger.error(f"{'='*60}")
        
        if current_step:
            logger.info(f"📍 当前步骤: {current_step}")
        
        logger.info("\n可选操作:")
        logger.info("  1. 输入步骤号 (1-25) - 从指定步骤继续")
        logger.info("  2. 输入 'retry' - 重试当前步骤")
        logger.info("  3. 输入 'skip' - 跳过当前视频")
        logger.info("  4. 输入 'quit' - 退出程序")
        logger.info("  5. 直接按 Enter - 继续下一步")
        
        while True:
            try:
                user_input = input("\n👉 请输入操作: ").strip().lower()
                
                if not user_input:
                    # 直接按 Enter，继续
                    logger.info("✅ 继续执行...")
                    return "continue", None
                
                elif user_input == 'retry':
                    logger.info("🔄 重试当前步骤...")
                    return "retry", current_step
                
                elif user_input == 'skip':
                    logger.info("⏭️ 跳过当前视频...")
                    return "skip", None
                
                elif user_input == 'quit':
                    logger.info("👋 退出程序...")
                    return "quit", None
                
                elif user_input.isdigit():
                    step_num = int(user_input)
                    if 1 <= step_num <= 25:
                        logger.info(f"↪️ 从步骤 {step_num} 继续...")
                        return "goto", step_num
                    else:
                        logger.warning("⚠️ 步骤号必须在 1-25 之间")
                
                else:
                    logger.warning("⚠️ 无效的输入，请重新输入")
                    
            except KeyboardInterrupt:
                logger.warning("\n⚠️ 用户中断")
                return "quit", None
            except Exception as e:
                logger.error(f"❌ 输入错误: {e}")

    def process_single_video(self, video_info, start_step=1):
        """处理单个视频的完整流程（支持错误恢复）"""
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
            if start_step <= 1:
                try:
                    if not self.update_prompts_file(video_info):
                        action, step = self.wait_for_user_action("更新提示词文件失败", 1)
                        if action == "quit":
                            return False
                        elif action == "skip":
                            return False
                        elif action == "retry":
                            return self.process_single_video(video_info, start_step=1)
                        elif action == "goto":
                            return self.process_single_video(video_info, start_step=step)
                except Exception as e:
                    action, step = self.wait_for_user_action(f"更新提示词文件异常: {e}", 1)
                    if action == "quit":
                        return False
                    elif action == "skip":
                        return False
                    elif action == "retry":
                        return self.process_single_video(video_info, start_step=1)

            # 2. 获取提示词列表
            prompts = self.get_prompts_list()
            if not prompts:
                action, step = self.wait_for_user_action("没有找到提示词", 1)
                if action == "quit":
                    return False
                elif action == "skip":
                    return False
                return False

            logger.info(f"共有 {len(prompts)} 个提示词需要处理")

            # 3. 上传视频（如果需要）
            if start_step <= 1:
                try:
                    upload_result = self.upload_video(video_path)
                    
                    # 检查是否需要刷新页面（上传后出现弹窗）
                    if upload_result == "popup_closed_need_refresh":
                        logger.warning("⚠️ 上传后出现弹窗，已关闭")
                        logger.info("🔄 刷新页面并重新开始步骤1...")
                        
                        # 刷新页面
                        try:
                            self.page.reload(wait_until="networkidle", timeout=60000)
                            logger.info("✅ 页面已刷新")
                            time.sleep(3)
                        except Exception as e:
                            logger.error(f"❌ 刷新页面失败: {e}")
                        
                        # 重新开始步骤1
                        return self.process_single_video(video_info, start_step=1)
                    
                    elif not upload_result:
                        action, step = self.wait_for_user_action("上传视频失败", 1)
                        if action == "quit":
                            return False
                        elif action == "skip":
                            return False
                        elif action == "retry":
                            return self.process_single_video(video_info, start_step=1)
                        elif action == "goto":
                            return self.process_single_video(video_info, start_step=step)
                except Exception as e:
                    action, step = self.wait_for_user_action(f"上传视频异常: {e}", 1)
                    if action == "quit":
                        return False
                    elif action == "skip":
                        return False

            # 4. 发送第一个提示词并运行
            if start_step <= 1 and prompts:
                try:
                    send_result = self.send_prompt(prompts[0], step_number=1)
                    
                    # 检查是否是上传失败
                    if send_result == "upload_failed":
                        logger.error("❌ 检测到视频上传失败（Run按钮超时不可用）")
                        logger.info("🔄 尝试恢复：刷新页面并重新开始")
                        
                        # 刷新页面
                        try:
                            self.page.reload(wait_until="networkidle", timeout=60000)
                            logger.info("✅ 页面已刷新")
                            time.sleep(3)
                        except Exception as e:
                            logger.error(f"❌ 刷新页面失败: {e}")
                        
                        # 重新开始步骤1
                        logger.info("🔄 重新开始步骤1...")
                        return self.process_single_video(video_info, start_step=1)
                    
                    elif not send_result:
                        action, step = self.wait_for_user_action("发送步骤1失败", 1)
                        if action == "quit":
                            return False
                        elif action == "skip":
                            return False
                        elif action == "retry":
                            return self.process_single_video(video_info, start_step=1)
                        elif action == "goto":
                            return self.process_single_video(video_info, start_step=step)
                    
                    # 等待响应，处理 rate limit
                    response_result = self.wait_for_response(step_number=1)
                    
                    # 处理 rate limit 切换账号的情况
                    if response_result == "rate_limit_switched":
                        logger.info("🔄 账号已切换，会话已丢失")
                        logger.info("📤 需要重新上传视频并从步骤1开始")
                        # 从头开始（start_step=1 会重新上传视频）
                        return self.process_single_video(video_info, start_step=1)
                    elif response_result == "skip":
                        logger.info("⏭️ 跳过当前视频")
                        return False
                    elif response_result == "quit":
                        logger.info("👋 退出程序")
                        return False
                except Exception as e:
                    action, step = self.wait_for_user_action(f"步骤1异常: {e}", 1)
                    if action == "quit":
                        return False
                    elif action == "skip":
                        return False
                    elif action == "retry":
                        return self.process_single_video(video_info, start_step=1)

            # 5. 逐步发送剩余提示词（步骤2-25）
            step_outputs = {}

            for i, prompt in enumerate(prompts[1:], start=2):
                # 如果指定了起始步骤，跳过之前的步骤
                if i < start_step:
                    continue
                
                logger.info(f"\n{'─'*40}")
                logger.info(f"📝 步骤 {i}/{len(prompts)}")
                logger.info(f"{'─'*40}")

                try:
                    if not self.send_prompt(prompt, step_number=i):
                        action, step = self.wait_for_user_action(f"步骤 {i} 发送失败", i)
                        if action == "quit":
                            return False
                        elif action == "skip":
                            return False
                        elif action == "retry":
                            return self.process_single_video(video_info, start_step=i)
                        elif action == "goto":
                            return self.process_single_video(video_info, start_step=step)
                        elif action == "continue":
                            continue

                    # 等待响应，处理 rate limit
                    response_result = self.wait_for_response(step_number=i)
                    
                    # 处理 rate limit 切换账号的情况
                    if response_result == "rate_limit_switched":
                        logger.info("🔄 账号已切换，会话已丢失")
                        logger.info("📤 需要重新上传视频并从步骤1开始")
                        logger.info(f"💡 当前在步骤 {i}，切换后将从步骤1重新开始")
                        # 从头开始（start_step=1 会重新上传视频）
                        return self.process_single_video(video_info, start_step=1)
                    elif response_result == "skip":
                        logger.info("⏭️ 跳过当前视频")
                        return False
                    elif response_result == "quit":
                        logger.info("👋 退出程序")
                        return False

                    # 保存特定步骤的输出
                    if i in config.SAVE_STEPS:
                        response = self.extract_response(step_number=i)
                        step_outputs[i] = response
                        logger.info(f"💾 已捕获步骤 {i} 的输出")
                        logger.info(f"📊 步骤 {i} 数据类型: {type(response)}, 数据量: {len(response) if response else 0}")
                        if isinstance(response, list) and response:
                            logger.info(f"📋 步骤 {i} 第一条数据: {response[0]}")
                        self.take_screenshot(f"step_{i}_output")
                        
                except Exception as e:
                    action, step = self.wait_for_user_action(f"步骤 {i} 异常: {e}", i)
                    if action == "quit":
                        return False
                    elif action == "skip":
                        return False
                    elif action == "retry":
                        return self.process_single_video(video_info, start_step=i)
                    elif action == "goto":
                        return self.process_single_video(video_info, start_step=step)
                    elif action == "continue":
                        continue

            # 6. 保存输出数据
            try:
                self.save_output_data(video_name, step_outputs)
            except Exception as e:
                logger.error(f"❌ 保存输出数据失败: {e}")
                action, step = self.wait_for_user_action(f"保存数据异常: {e}", 25)
                if action == "quit":
                    return False

            logger.info(f"✅ 视频 {video_name} 处理完成")
            return True

        except Exception as e:
            logger.error(f"❌ 处理视频时出错: {e}")
            import traceback
            traceback.print_exc()
            self.take_screenshot("error_process_video")
            
            action, step = self.wait_for_user_action(f"处理视频异常: {e}", start_step)
            if action == "quit":
                return False
            elif action == "skip":
                return False
            elif action == "retry":
                return self.process_single_video(video_info, start_step=start_step)
            elif action == "goto":
                return self.process_single_video(video_info, start_step=step)
            
            return False

    def merge_all_excel_files(self):
        """合并所有输出的 Excel 文件"""
        logger.info("📊 开始合并所有 Excel 文件...")

        all_data = []
        for folder in self.process_folder.iterdir():
            if folder.is_dir() and folder.name != "videos":
                for excel_file in folder.glob("*.xlsx"):
                    # 跳过临时文件（以 .~ 或 ~$ 开头）
                    if excel_file.name.startswith('.~') or excel_file.name.startswith('~$'):
                        logger.debug(f"  ⏭️ 跳过临时文件: {excel_file.name}")
                        continue
                    
                    try:
                        df = pd.read_excel(excel_file)
                        all_data.append(df)
                        logger.info(f"  ✅ 读取: {excel_file.name}")
                    except Exception as e:
                        logger.warning(f"  ❌ 读取失败 {excel_file.name}: {e}")

        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)

            # 保存到 clips.xlsx
            self.clips_file.parent.mkdir(exist_ok=True)
            merged_df.to_excel(self.clips_file, index=False)
            logger.info(f"✅ 合并完成，保存到: {self.clips_file}")
            logger.info(f"📊 合并数据: {len(merged_df)} 行 x {len(merged_df.columns)} 列")
            return True
        else:
            logger.warning("❌ 没有找到可合并的文件")
            return False

    def run_final_processing(self):
        """运行最终的视频处理脚本"""
        process_script = self.output_folder / "process_video.py"
        
        if not process_script.exists():
            logger.warning(f"⚠️ 找不到处理脚本: {process_script}")
            return
        
        logger.info("\n" + "="*60)
        logger.info("🎬 准备运行最终处理脚本")
        logger.info("="*60)
        logger.info(f"📄 脚本路径: {process_script}")
        logger.info("")
        logger.warning("⚠️ 重要提示:")
        logger.warning("  1. process_video.py 需要正确配置资源文件夹才能运行")
        logger.warning("  2. 需要配置以下路径:")
        logger.warning("     - FONT_PATH: 字体文件路径")
        logger.warning("     - MUSIC_DIR: 音乐文件夹路径")
        logger.warning("     - FFMPEG_CMD: FFmpeg 命令路径")
        logger.warning("  3. 如果配置不正确，脚本会报错（这是正常的）")
        logger.warning("  4. 请根据实际情况修改 process_video.py 中的配置")
        logger.info("")
        logger.info("🚀 开始执行...")
        logger.info("="*60)
        
        try:
            # 执行脚本
            result = os.system(f"python3 {process_script}")
            
            if result == 0:
                logger.info("="*60)
                logger.info("✅ 最终处理脚本执行成功")
                logger.info("="*60)
            else:
                logger.warning("="*60)
                logger.warning("⚠️ 最终处理脚本执行失败")
                logger.warning("="*60)
                logger.warning("可能的原因:")
                logger.warning("  1. 资源文件夹配置不正确")
                logger.warning("  2. 缺少必需的文件（字体、音乐等）")
                logger.warning("  3. FFmpeg 未安装或路径不正确")
                logger.warning("")
                logger.warning("解决方案:")
                logger.warning("  1. 检查 process_video.py 中的配置")
                logger.warning("  2. 确保所有资源文件存在")
                logger.warning("  3. 安装并配置 FFmpeg")
                logger.warning("")
                logger.info("💡 提示: 如果只需要提取数据，可以忽略此错误")
                
        except Exception as e:
            logger.error(f"❌ 执行脚本时出错: {e}")
            logger.warning("💡 这是预期的错误，如果资源文件夹未配置")

    def run_batch(self):
        """运行一批视频的处理流程"""
        # 1. 加载视频列表
        videos = self.load_video_list()
        if not videos:
            logger.error("❌ 没有找到待处理的视频")
            return False

        # 2. 首次打开 AI Studio 并等待用户确认（仅首次）
        if not self.ai_studio_opened:
            logger.info("\n" + "="*60)
            logger.info("📋 步骤 1: 准备工作")
            logger.info("="*60)
            logger.info(f"✅ 已加载 {len(videos)} 个视频")
            logger.info("")
            
            if not self.open_ai_studio():
                logger.error("❌ 打开 AI Studio 失败")
                return False
        
        success_count = 0
        failed_videos = []

        # 3. 处理每个视频
        for i, video_info in enumerate(videos, start=1):
            logger.info(f"\n{'#'*60}")
            logger.info(f"# 进度: {i}/{len(videos)}")
            logger.info(f"# 视频: {video_info['filename']}")
            logger.info(f"{'#'*60}")

            result = self.process_single_video(video_info)
            
            # 检查是否用户要求退出
            if result == "quit":
                logger.info("👋 用户请求退出")
                return "quit"
            
            if result:
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
        try:
            self.merge_all_excel_files()
        except Exception as e:
            logger.error(f"❌ 合并数据失败: {e}")

        # 5. 运行最终处理
        logger.info("\n" + "=" * 60)
        logger.info("运行最终处理...")
        logger.info("=" * 60)
        try:
            self.run_final_processing()
        except Exception as e:
            logger.error(f"❌ 最终处理失败: {e}")

        # 6. 输出统计信息
        logger.info("\n" + "=" * 60)
        logger.info("🎉 本批次任务完成！")
        logger.info("=" * 60)
        logger.info(f"✅ 成功处理: {success_count}/{len(videos)} 个视频")

        if failed_videos:
            logger.warning(f"❌ 失败视频: {', '.join(failed_videos)}")
        
        return True

    def run(self, headless=None, use_system_chrome=None):
        """运行完整的自动化流程（支持循环执行）"""
        logger.info("🚀 视频处理自动化开始")
        logger.info(f"📁 工作目录: {self.base_dir}")
        logger.info(f"📝 日志文件: {config.LOG_FILE}")

        # 初始化浏览器
        if use_system_chrome is None:
            use_system_chrome = config.USE_SYSTEM_CHROME
        
        try:
            self.init_browser(headless=headless, use_system_chrome=use_system_chrome)
        except Exception as e:
            logger.error(f"❌ 初始化浏览器失败: {e}")
            return

        try:
            while True:
                # 运行一批视频
                result = self.run_batch()
                
                # 如果用户要求退出
                if result == "quit":
                    break
                
                # 批次完成后，询问用户下一步操作
                logger.info("\n" + "=" * 60)
                logger.info("📋 批次完成，请选择下一步操作")
                logger.info("=" * 60)
                logger.info("可选操作:")
                logger.info("  1. 输入 'continue' 或按 Enter - 重新加载 VideoList.csv 并继续")
                logger.info("  2. 输入 'quit' - 退出程序")
                
                while True:
                    try:
                        user_input = input("\n👉 请输入操作: ").strip().lower()
                        
                        if not user_input or user_input == 'continue':
                            logger.info("🔄 重新加载视频列表...")
                            break
                        elif user_input == 'quit':
                            logger.info("👋 退出程序...")
                            return
                        else:
                            logger.warning("⚠️ 无效的输入，请输入 'continue' 或 'quit'")
                    except KeyboardInterrupt:
                        logger.warning("\n⚠️ 用户中断")
                        return

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
