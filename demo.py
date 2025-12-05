#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本 - 展示如何使用 VideoProcessor 类
"""

from video_automation import VideoProcessor
from config import config


def demo_basic_usage():
    """基本使用演示"""
    print("="*60)
    print("演示：基本使用")
    print("="*60)
    
    # 创建处理器实例
    processor = VideoProcessor()
    
    # 显示配置信息
    print(f"\n📁 工作目录: {processor.base_dir}")
    print(f"📝 提示词文件: {processor.prompts_file}")
    print(f"🎬 视频目录: {processor.videos_folder}")
    print(f"📊 输出目录: {processor.output_folder}")
    
    # 加载视频列表
    print("\n" + "-"*60)
    print("加载视频列表...")
    print("-"*60)
    videos = processor.load_video_list()
    
    if videos:
        print(f"\n找到 {len(videos)} 个视频：")
        for i, video in enumerate(videos, 1):
            print(f"  {i}. {video['filename']} ({video['duration']})")
    else:
        print("\n⚠️ 没有找到视频")
    
    # 加载提示词
    print("\n" + "-"*60)
    print("加载提示词...")
    print("-"*60)
    prompts = processor.get_prompts_list()
    
    if prompts:
        print(f"\n找到 {len(prompts)} 个提示词")
        print("\n前 3 个提示词：")
        for i, prompt in enumerate(prompts[:3], 1):
            print(f"  {i}. {prompt[:60]}...")
    else:
        print("\n⚠️ 没有找到提示词")


def demo_config():
    """配置信息演示"""
    print("\n" + "="*60)
    print("演示：配置信息")
    print("="*60)
    
    print("\n浏览器配置：")
    print(f"  无头模式: {config.HEADLESS}")
    print(f"  超时时间: {config.BROWSER_TIMEOUT}ms")
    
    print("\n等待时间配置：")
    print(f"  上传后等待: {config.WAIT_AFTER_UPLOAD}秒")
    print(f"  发送后等待: {config.WAIT_AFTER_SEND}秒")
    print(f"  响应等待: {config.WAIT_FOR_RESPONSE}秒")
    print(f"  视频间隔: {config.WAIT_BETWEEN_VIDEOS}秒")
    
    print("\n步骤配置：")
    print(f"  总步骤数: {config.TOTAL_STEPS}")
    print(f"  保存步骤: {config.SAVE_STEPS}")
    
    print("\n重试配置：")
    print(f"  最大重试: {config.MAX_RETRIES}次")
    print(f"  重试延迟: {config.RETRY_DELAY}秒")


def demo_selectors():
    """选择器配置演示"""
    print("\n" + "="*60)
    print("演示：页面选择器")
    print("="*60)
    
    print("\n当前配置的选择器：")
    for key, value in config.SELECTORS.items():
        print(f"  {key:20s}: {value}")


def main():
    """主演示函数"""
    print("\n" + "🎬"*30)
    print("视频处理自动化 - 演示脚本")
    print("🎬"*30 + "\n")
    
    try:
        # 演示1：基本使用
        demo_basic_usage()
        
        # 演示2：配置信息
        demo_config()
        
        # 演示3：选择器配置
        demo_selectors()
        
        print("\n" + "="*60)
        print("✅ 演示完成！")
        print("="*60)
        
        print("\n💡 提示：")
        print("  - 运行 'python video_automation.py' 开始处理视频")
        print("  - 运行 'python test_connection.py' 测试浏览器连接")
        print("  - 查看 '使用指南.md' 了解详细用法")
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
