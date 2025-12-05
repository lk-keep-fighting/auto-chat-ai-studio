@echo off
REM 打包脚本 - Windows 批处理版本

echo ==========================================
echo 🚀 视频处理自动化工具 - 打包脚本
echo ==========================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python
    pause
    exit /b 1
)

echo ✅ Python 已安装

REM 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ PyInstaller 未安装
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller 已安装

REM 清理旧文件
echo.
echo 🧹 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✅ 清理完成

REM 构建
echo.
echo 🔨 开始构建...
echo ==========================================

if exist build.spec (
    echo 📝 使用 build.spec 配置文件
    pyinstaller build.spec --clean
) else (
    echo 📝 使用默认配置
    pyinstaller ^
        --name=VideoAutomation ^
        --onedir ^
        --console ^
        --clean ^
        video_automation.py
)

if errorlevel 1 (
    echo.
    echo ❌ 构建失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 构建成功！
echo ==========================================
echo.
echo 📁 输出目录: dist\VideoAutomation\
echo.
echo 🚀 运行方式:
echo   双击运行: dist\VideoAutomation\VideoAutomation.exe
echo   或命令行: cd dist\VideoAutomation ^&^& VideoAutomation.exe
echo.

pause
