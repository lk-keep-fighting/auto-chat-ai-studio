#!/bin/bash

# 步骤23和25测试快速启动脚本

echo "=================================="
echo "🧪 步骤23和步骤25数据保存测试工具"
echo "=================================="
echo ""
echo "测试内容："
echo "1. 初始化浏览器"
echo "2. 打开 AI Studio"
echo "3. 等待用户确认"
echo "4. 测试步骤23（SRT文件生成）"
echo "5. 测试步骤25（表格数据生成）"
echo "6. 验证保存结果"
echo ""
echo "=================================="
echo ""

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "🔧 激活虚拟环境..."
    source venv/bin/activate
fi

# 运行测试
echo "🚀 启动测试..."
echo ""
python test_step23_25.py

# 显示结果
echo ""
echo "=================================="
echo "📁 输出文件："
echo "  - 步骤23: assets/Process_Folder/test_步骤23_SRT文件/step_23_output.xlsx"
echo "  - 步骤25: assets/Process_Folder/test_步骤25_表格数据/step_25_output.xlsx"
echo "  - 日志: test_step23_25.log"
echo "=================================="
