#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 集中管理所有配置项
"""

from pathlib import Path


class Config:
    """配置类"""
    
    # ==================== 路径配置 ====================
    BASE_DIR = Path(__file__).parent
    PROCESS_FOLDER = BASE_DIR / "assets" / "Process_Folder"
    VIDEOS_FOLDER = PROCESS_FOLDER / "videos"
    PROMPTS_FILE = PROCESS_FOLDER / "prompts.xlsx"
    VIDEO_LIST_FILE = VIDEOS_FOLDER / "VideoList.csv"
    OUTPUT_FOLDER = BASE_DIR / "assets" / "vidoes"
    CLIPS_FILE = OUTPUT_FOLDER / "clips.xlsx"
    PROCESS_SCRIPT = OUTPUT_FOLDER / "process_video.py"
    
    # ==================== URL 配置 ====================
    AI_STUDIO_URL = "https://aistudio.google.com/"
    
    # ==================== 浏览器配置 ====================
    HEADLESS = False  # 是否无头模式
    BROWSER_TIMEOUT = 60000  # 浏览器超时时间（毫秒）
    USE_SYSTEM_CHROME = True  # 是否使用系统安装的 Chrome（推荐）
    WAIT_USER_CONFIRMATION = True  # 是否等待用户确认（推荐）
    
    # ==================== 等待时间配置 ====================
    WAIT_AFTER_UPLOAD = 15  # 上传视频后等待时间（秒）
    WAIT_AFTER_SEND = 3     # 发送提示词后等待时间（秒）
    WAIT_FOR_RESPONSE = 10  # 等待 AI 响应时间（秒）
    WAIT_BETWEEN_VIDEOS = 5 # 视频之间的休息时间（秒）
    WAIT_BUTTON_ENABLED = 300  # 等待按钮可用的最大时间（秒）- 5分钟，适应慢速网络
    CONTENT_BLOCKED_COOLDOWN = 60  # Content blocked 处理冷却时间（秒）
    
    # ==================== 页面选择器配置 ====================
    # 这些选择器可能需要根据实际页面调整
    SELECTORS = {
        # 文件上传 - 新的两步上传流程
        'add_button': 'button[iconname="add_circle"]',  # 添加按钮
        'upload_file_button': 'button[aria-label="Upload File"]',  # Upload File 按钮
        'file_input': 'input[data-test-upload-file-input]',  # 文件输入框
        
        # 输入框
        'input_box': 'textarea[placeholder*="Enter"], [contenteditable="true"]',
        'chat_input': 'div[role="textbox"]',
        
        # 发送/运行按钮
        'send_button': 'button[aria-label*="Send"], button:has-text("Send")',
        'run_button': 'button[aria-label="Run"]',  # Run/Stop 按钮
        
        # 响应内容
        'ai_response': '[data-message-author-role="model"]',
        'response_container': '.response-content',
        
        # 错误提示
        'content_blocked': 'text="Content blocked"',
        'error_message': '.error-message',
        
        # 加载状态
        'loading_indicator': '.loading, [aria-busy="true"]',
        'processing': 'text="Processing"',
    }
    
    # ==================== Excel 配置 ====================
    # prompts.xlsx 中的列名
    EXCEL_COLUMNS = {
        'video_name': '文件名称',
        'video_duration': '视频时长',
        'prompt_column': '提示词',  # 提示词所在的列
    }
    
    # ==================== 步骤配置 ====================
    TOTAL_STEPS = 25  # 总步骤数
    SAVE_STEPS = [23, 25]  # 需要保存输出的步骤
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = BASE_DIR / "automation.log"
    
    # ==================== 重试配置 ====================
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 5  # 重试延迟（秒）
    
    # ==================== 调试配置 ====================
    DEBUG_MODE = False  # 调试模式
    SAVE_SCREENSHOTS = True  # 是否保存截图
    SCREENSHOT_DIR = BASE_DIR / "screenshots"


# 创建全局配置实例
config = Config()


# 确保必要的目录存在
def ensure_directories():
    """确保所有必要的目录存在"""
    dirs = [
        config.PROCESS_FOLDER,
        config.VIDEOS_FOLDER,
        config.OUTPUT_FOLDER,
    ]
    
    if config.SAVE_SCREENSHOTS:
        dirs.append(config.SCREENSHOT_DIR)
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # 测试配置
    print("配置信息：")
    print(f"  基础目录: {config.BASE_DIR}")
    print(f"  视频目录: {config.VIDEOS_FOLDER}")
    print(f"  提示词文件: {config.PROMPTS_FILE}")
    print(f"  AI Studio URL: {config.AI_STUDIO_URL}")
    print(f"  总步骤数: {config.TOTAL_STEPS}")
    
    ensure_directories()
    print("\n✅ 目录检查完成")
