#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除浏览器会话脚本
用于清除保存的登录会话，下次运行时需要重新登录
"""

import shutil
from pathlib import Path


def clear_session():
    """清除保存的浏览器会话"""
    session_dir = Path(__file__).parent / ".browser_session"
    
    if session_dir.exists():
        try:
            shutil.rmtree(session_dir)
            print("✅ 会话已清除")
            print("💡 下次运行时需要重新登录")
            return True
        except Exception as e:
            print(f"❌ 清除会话失败: {e}")
            return False
    else:
        print("ℹ️ 没有找到保存的会话")
        return True


if __name__ == "__main__":
    print("🔐 清除浏览器会话")
    print("="*50)
    
    response = input("确定要清除保存的会话吗？(y/n): ")
    
    if response.lower() == 'y':
        clear_session()
    else:
        print("❌ 已取消")
