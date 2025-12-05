#!/bin/bash
# 快速启动脚本

echo "🚀 启动视频处理自动化..."

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "📦 激活虚拟环境..."
    source venv/bin/activate
fi

# 运行主脚本
python3 video_automation.py

echo ""
echo "✅ 脚本执行完成"
