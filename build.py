#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本
使用 PyInstaller 将程序打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
        return True
    except ImportError:
        print("❌ PyInstaller 未安装")
        return False


def install_pyinstaller():
    """安装 PyInstaller"""
    print("\n📦 正在安装 PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller 安装失败: {e}")
        return False


def clean_build():
    """清理之前的构建文件"""
    print("\n🧹 清理旧的构建文件...")
    dirs_to_clean = ["build", "dist"]
    files_to_clean = ["*.spec~"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  ✅ 已删除: {dir_name}/")
    
    print("✅ 清理完成")


def build_exe():
    """构建可执行文件"""
    print("\n🔨 开始构建可执行文件...")
    print("="*60)
    
    try:
        # 使用 spec 文件构建
        if os.path.exists("build.spec"):
            print("📝 使用 build.spec 配置文件")
            cmd = ["pyinstaller", "build.spec", "--clean"]
        else:
            print("📝 使用默认配置")
            cmd = [
                "pyinstaller",
                "--name=VideoAutomation",
                "--onedir",  # 打包为文件夹
                "--console",  # 显示控制台
                "--clean",
                "video_automation.py"
            ]
        
        subprocess.check_call(cmd)
        print("\n✅ 构建成功！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        return False


def show_result():
    """显示构建结果"""
    print("\n" + "="*60)
    print("🎉 打包完成！")
    print("="*60)
    
    dist_dir = Path("dist/VideoAutomation")
    if dist_dir.exists():
        print(f"\n📁 输出目录: {dist_dir.absolute()}")
        print("\n📦 包含文件:")
        
        # 列出主要文件
        exe_file = dist_dir / "VideoAutomation.exe" if sys.platform == "win32" else dist_dir / "VideoAutomation"
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"  ✅ {exe_file.name} ({size_mb:.1f} MB)")
        
        # 统计文件数量
        all_files = list(dist_dir.rglob("*"))
        file_count = len([f for f in all_files if f.is_file()])
        print(f"\n  总共 {file_count} 个文件")
        
        print("\n🚀 运行方式:")
        if sys.platform == "win32":
            print(f"  双击运行: {exe_file}")
            print(f"  或命令行: cd dist/VideoAutomation && VideoAutomation.exe")
        else:
            print(f"  命令行: cd dist/VideoAutomation && ./VideoAutomation")
    else:
        print("\n⚠️ 未找到输出目录")


def create_readme():
    """创建打包版本的 README"""
    readme_content = """# 视频处理自动化工具 - 打包版本

## 使用说明

### 首次运行

1. 解压到任意目录
2. 双击运行 `VideoAutomation.exe` (Windows) 或 `./VideoAutomation` (Mac/Linux)
3. 按照提示操作

### 准备工作

1. 准备视频文件，放在 `assets/Process_Folder/videos/` 目录
2. 准备提示词文件 `assets/Process_Folder/prompts.xlsx`
3. 准备视频列表 `assets/Process_Folder/videos/VideoList.csv`

### 配置

编辑 `config.py` 调整配置：
- `HEADLESS = False` - 显示浏览器窗口
- `USE_SYSTEM_CHROME = True` - 使用系统 Chrome
- `WAIT_BUTTON_ENABLED = 300` - 等待按钮超时时间

### 日志

- 运行日志：`automation.log`
- 截图：`screenshots/` 目录

### 问题排查

1. 查看 `automation.log` 日志文件
2. 查看 `screenshots/` 截图
3. 参考完整文档

### 注意事项

- 首次运行需要安装 Playwright 浏览器
- 需要登录 Google 账号（仅首次）
- 确保网络连接稳定

---

**版本**: v1.3.7
**更新**: 2024-12-05
"""
    
    dist_readme = Path("dist/VideoAutomation/README_打包版.txt")
    if dist_readme.parent.exists():
        with open(dist_readme, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"\n✅ 已创建: {dist_readme.name}")


def main():
    """主函数"""
    print("="*60)
    print("🚀 视频处理自动化工具 - 打包脚本")
    print("="*60)
    
    # 1. 检查 PyInstaller
    if not check_pyinstaller():
        print("\n是否安装 PyInstaller? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            if not install_pyinstaller():
                print("\n❌ 无法继续，请手动安装: pip install pyinstaller")
                return
        else:
            print("\n❌ 需要 PyInstaller 才能打包")
            print("安装命令: pip install pyinstaller")
            return
    
    # 2. 清理旧文件
    clean_build()
    
    # 3. 构建
    if not build_exe():
        print("\n❌ 构建失败，请检查错误信息")
        return
    
    # 4. 创建说明文件
    create_readme()
    
    # 5. 显示结果
    show_result()
    
    print("\n" + "="*60)
    print("✅ 全部完成！")
    print("="*60)


if __name__ == "__main__":
    main()
