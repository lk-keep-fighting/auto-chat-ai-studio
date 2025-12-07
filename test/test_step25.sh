#!/bin/bash

# 步骤25测试快速启动脚本

echo "=================================="
echo "🧪 步骤25数据保存测试工具"
echo "=================================="
echo ""
echo "测试内容："
echo "1. 初始化浏览器"
echo "2. 打开 AI Studio"
echo "3. 等待用户确认"
echo "4. 发送步骤25测试提示词"
echo "5. 等待AI生成测试数据"
echo "6. 提取表格数据"
echo "7. 保存为Excel文件"
echo "8. 验证保存结果"
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
python test_step25.py

# 显示结果
echo ""
echo "=================================="
echo "📁 输出文件："
echo "  - Excel: test_output/test_step25/step_25_output.xlsx"
echo "  - 日志: test_step25.log"
echo "=================================="
