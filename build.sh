#!/bin/bash
# 打包脚本 - Shell 版本

echo "=========================================="
echo "🚀 视频处理自动化工具 - 打包脚本"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查 PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "❌ PyInstaller 未安装"
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ PyInstaller 安装失败"
        exit 1
    fi
fi

echo "✅ PyInstaller 已安装"

# 清理旧文件
echo ""
echo "🧹 清理旧的构建文件..."
rm -rf build dist
echo "✅ 清理完成"

# 构建
echo ""
echo "🔨 开始构建..."
echo "=========================================="

if [ -f "build.spec" ]; then
    echo "📝 使用 build.spec 配置文件"
    pyinstaller build.spec --clean
else
    echo "📝 使用默认配置"
    pyinstaller \
        --name=VideoAutomation \
        --onedir \
        --console \
        --clean \
        video_automation.py
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 构建成功！"
    echo "=========================================="
    echo ""
    echo "📁 输出目录: dist/VideoAutomation/"
    echo ""
    echo "🚀 运行方式:"
    echo "  cd dist/VideoAutomation && ./VideoAutomation"
    echo ""
else
    echo ""
    echo "❌ 构建失败"
    exit 1
fi
