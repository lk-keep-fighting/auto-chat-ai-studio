# 步骤23和25测试与调试指南

## 快速开始

### 1. 运行测试
```bash
bash test/test_step23_25.sh
```

### 2. 分析结果
```bash
python analyze_test_results.py
```

### 3. 深入调试（如果需要）
```bash
# 分析步骤23的HTML
python analyze_step23_html.py

# 分析步骤25的HTML
python analyze_step25_html.py
```

## 完整工作流

### 阶段1：准备环境

```bash
# 1. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 2. 安装依赖（如果需要）
pip install beautifulsoup4 pandas openpyxl
```

### 阶段2：运行测试

```bash
# 运行步骤23和25的联合测试
bash test/test_step23_25.sh
```

测试会：
1. 初始化浏览器
2. 打开 AI Studio
3. 等待用户确认
4. 测试步骤23（SRT文件生成）
5. 测试步骤25（表格数据生成）
6. 自动保存HTML调试文件
7. 验证保存结果

### 阶段3：查看日志

```bash
# 查看测试日志
tail -100 test_step23_25.log

# 搜索关键信息
grep "步骤23" test_step23_25.log
grep "步骤25" test_step23_25.log
grep "保存HTML" test_step23_25.log
```

关键日志标记：
- ✅ 成功标记
- ⚠️ 警告标记
- ❌ 错误标记
- 💾 文件保存标记
- 🔍 查找/检测标记

### 阶段4：分析结果

```bash
# 运行综合分析工具
python analyze_test_results.py
```

分析工具会检查：
- SRT文件是否正确生成
- SRT内容是否干净（无UI元素）
- Excel文件是否正确生成
- 表格数据是否完整
- 调试文件是否已保存

### 阶段5：深入调试（如果有问题）

#### 步骤23问题调试

```bash
# 1. 分析HTML结构
python analyze_step23_html.py

# 2. 手动查看HTML
open assets/Process_Folder/test_步骤23_SRT文件/debug/step_23_response_*.html

# 3. 查看文本内容
cat assets/Process_Folder/test_步骤23_SRT文件/debug/step_23_text_*.txt

# 4. 搜索SRT时间戳
grep "00:00:00" assets/Process_Folder/test_步骤23_SRT文件/debug/step_23_text_*.txt
```

#### 步骤25问题调试

```bash
# 1. 分析HTML结构
python analyze_step25_html.py

# 2. 手动查看HTML
open assets/Process_Folder/test_步骤25_表格数据/debug/step_25_response_*.html

# 3. 查看文本内容
cat assets/Process_Folder/test_步骤25_表格数据/debug/step_25_text_*.txt

# 4. 搜索表格标记
grep "<table" assets/Process_Folder/test_步骤25_表格数据/debug/step_25_response_*.html
```

## 预期输出

### 步骤23成功输出

```
assets/Process_Folder/test_步骤23_SRT文件/
├── step_23_output_1.srt  ✅ SRT文件1
├── step_23_output_2.srt  ✅ SRT文件2
└── debug/
    ├── step_23_response_20241209_120000.html  💾 HTML调试文件
    └── step_23_text_20241209_120000.txt       💾 文本调试文件
```

SRT文件应该：
- ✅ 以序号1开始
- ✅ 包含正确的时间戳格式
- ✅ 无UI元素（code, Srt, download等）
- ✅ 无下一个文件的标题

### 步骤25成功输出

```
assets/Process_Folder/test_步骤25_表格数据/
├── step_25_output.xlsx  ✅ Excel文件
└── debug/
    ├── step_25_response_20241209_120100.html  💾 HTML调试文件
    └── step_25_text_20241209_120100.txt       💾 文本调试文件
```

Excel文件应该：
- ✅ 包含正确的列名（start, end, folder1, folder2等）
- ✅ 包含多行数据
- ✅ 数据格式正确

## 常见问题排查

### Q1: 步骤23生成了.txt文件而不是.srt文件

**原因**：未能识别SRT格式内容

**解决步骤**：
1. 查看日志：`grep "步骤23" test_step23_25.log`
2. 分析HTML：`python analyze_step23_html.py`
3. 查看HTML文件，找到SRT内容的位置
4. 根据HTML结构调整 `extract_srt_from_download_button()` 方法

### Q2: 步骤25的表格数据不完整

**原因**：表格提取逻辑有问题

**解决步骤**：
1. 查看日志：`grep "步骤25" test_step23_25.log`
2. 分析HTML：`python analyze_step25_html.py`
3. 查看HTML文件，检查表格结构
4. 根据HTML结构调整 `extract_table_from_dom()` 方法

### Q3: 没有生成调试HTML文件

**原因**：配置未启用

**解决步骤**：
1. 检查配置：`grep "SAVE_DEBUG_HTML" config.py`
2. 确保设置为：`SAVE_DEBUG_HTML = True`
3. 重新运行测试

### Q4: 分析工具报错

**原因**：缺少依赖

**解决步骤**：
```bash
pip install beautifulsoup4 pandas openpyxl
```

## 调试技巧

### 1. 使用浏览器开发者工具

在HTML文件中：
1. 打开开发者工具（F12）
2. 使用Elements面板查看DOM结构
3. 使用Console面板测试选择器
4. 使用Network面板查看请求

### 2. 使用正则表达式测试

```python
import re

# 测试SRT时间戳匹配
text = "00:00:00,000 --> 00:00:05,000"
if re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->', text):
    print("✅ 匹配成功")
```

### 3. 使用BeautifulSoup测试选择器

```python
from bs4 import BeautifulSoup

with open('step_23_response.html', 'r') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# 测试选择器
code_blocks = soup.find_all('pre')
print(f"找到 {len(code_blocks)} 个代码块")
```

## 工具清单

### 测试工具
- `test/test_step23_25.sh` - 联合测试脚本
- `test_step23_25.py` - Python测试脚本

### 分析工具
- `analyze_test_results.py` - 综合结果分析
- `analyze_step23_html.py` - 步骤23 HTML分析
- `analyze_step25_html.py` - 步骤25 HTML分析

### 清理工具
- `clean_existing_srt.py` - 批量清理SRT文件
- `force_clean_srt.py` - 强制清理SRT文件

## 配置选项

### config.py

```python
# 是否保存调试HTML
SAVE_DEBUG_HTML = True  # 推荐：True

# 是否保存截图
SAVE_SCREENSHOTS = True  # 推荐：True

# 是否等待用户确认
WAIT_USER_CONFIRMATION = True  # 测试时：True
```

## 相关文档

- [v1.8.3更新说明.md](doc/v1.8.3更新说明.md) - 最新更新说明
- [DEBUG_STEP23_README.md](DEBUG_STEP23_README.md) - 步骤23调试指南
- [测试用例使用指南.md](doc/测试用例使用指南.md) - 测试用例说明

## 技术支持

如果问题仍然存在：

1. 收集以下信息：
   - 测试日志（test_step23_25.log）
   - 调试HTML文件
   - 分析工具输出
   - 页面截图

2. 描述问题：
   - 预期行为
   - 实际行为
   - 错误信息

3. 提供环境信息：
   - 操作系统
   - Python版本
   - 浏览器版本
