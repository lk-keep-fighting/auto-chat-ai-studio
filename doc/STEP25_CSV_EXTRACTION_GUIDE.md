# 步骤25 CSV格式提取指南

## 概述

v1.8.4 现在支持步骤25通过复制按钮提取CSV格式的数据，与步骤23的SRT提取方式类似。

## 修改内容

### 1. 新增通用剪贴板提取方法

添加了 `extract_content_by_clicking_copy_buttons()` 通用方法：

```python
def extract_content_by_clicking_copy_buttons(self, response_element, content_type="通用"):
    """通用方法：通过点击复制按钮获取剪贴板内容
    
    Args:
        response_element: 响应元素
        content_type: 内容类型（用于日志显示），如 "SRT"、"CSV"、"通用"
        
    Returns:
        内容列表（如果有多个复制按钮）或单个内容字符串（如果只有一个按钮）
    """
```

**特点：**
- ✅ 支持任意内容类型（SRT、CSV、JSON等）
- ✅ 自动检测复制按钮数量
- ✅ 单个按钮返回字符串，多个按钮返回列表
- ✅ 可自定义日志显示的内容类型

### 2. 改进步骤25的提取逻辑

步骤25现在支持两种提取方式：

**方法1：通过复制按钮获取CSV（推荐）**
```python
# 点击复制按钮获取CSV内容
csv_content = self.extract_content_by_clicking_copy_buttons(
    last_response_element, 
    content_type="CSV"
)

# 解析CSV为表格数据
df = pd.read_csv(io.StringIO(csv_content))
table_data = df.to_dict('records')
```

**方法2：从HTML DOM提取表格（备用）**
```python
# 原有的表格提取逻辑
table_data = self.extract_table_from_dom(last_response_element)
```

## 如何修改步骤25的提示词

### 原提示词（表格格式）

```
步骤25:【角色设定】
你是一名专业的数据整理专员，负责将之前生成的视频剪辑数据汇总为一张清洗干净的表格。

【输出格式】
请直接输出表格。表头如下：
| start | end | folder1 | folder2 | folder3 | music | cover_time | title |
```

**AI输出：** HTML表格
**提取方式：** 从DOM提取表格

### 新提示词（CSV格式）✅ 推荐

```
步骤25:【角色设定】
你是一名专业的数据整理专员，负责将之前生成的视频剪辑数据汇总为一张清洗干净的CSV表格。

【输出格式】
请直接输出CSV格式。表头如下：
start,end,folder1,folder2,folder3,music,cover_time,title

【输出要求】
1. 第一行必须是表头
2. 使用逗号分隔字段
3. 如果字段包含逗号，请用双引号包裹
4. 不要添加额外的格式或说明文字
```

**AI输出：** CSV文本（带复制按钮）
**提取方式：** 点击复制按钮获取剪贴板内容

## 工作流程

### CSV格式提取流程

```
Step 25 AI响应完成
    ↓
保存HTML调试文件
    ↓
方法1：查找复制按钮
    ├─ 找到复制按钮 → 点击
    ├─ 读取剪贴板内容（CSV）
    ├─ 解析CSV为DataFrame
    └─ 转换为字典列表
    ↓
成功 → 返回表格数据
    ↓
失败 → 方法2：从DOM提取表格
    ↓
保存为Excel文件
```

## 日志输出示例

### 成功通过复制按钮获取CSV

```
📊 步骤25：尝试提取CSV/表格数据...
💾 保存步骤25的HTML内容用于调试...
💾 已保存HTML调试文件: step_25_response_20241209_140000.html
🔍 方法1：尝试通过复制按钮获取CSV内容...
🔍 找到 1 个复制按钮
📋 点击复制按钮 1/1...
✅ 从复制按钮 1 获取到 2500 字符的CSV内容
✅ 总共获取了 1 个CSV内容
✅ 通过复制按钮获取到CSV内容
✅ 解析CSV得到 71 行数据
💾 保存输出数据到: assets/Process_Folder/Episode3
📊 步骤 25 数据: 71 行 x 8 列
✅ 保存步骤 25 数据: step_25_output.xlsx
```

### 回退到DOM提取

```
📊 步骤25：尝试提取CSV/表格数据...
🔍 方法1：尝试通过复制按钮获取CSV内容...
⚠️ 未找到复制按钮
🔍 方法2：尝试从HTML DOM提取表格数据...
⏳ 等待表格元素出现...
✅ 表格元素已出现
📋 找到 1 个表格，使用最后一个
✅ 从DOM提取到 71 行表格数据
```

## CSV格式示例

### AI输出的CSV格式

```csv
start,end,folder1,folder2,folder3,music,cover_time,title
00:01:42:00,00:01:47:00,,故事,1,,00:01:42:00,Brother Told Kidnappers: Kill Her!
00:01:47:00,00:01:52:00,,故事,2,,,,
00:01:52:00,00:01:57:00,,故事,3,,,,
00:01:57:00,00:02:02:00,,故事,4,,,,
```

### 解析后的数据结构

```python
[
    {
        'start': '00:01:42:00',
        'end': '00:01:47:00',
        'folder1': '',
        'folder2': '故事',
        'folder3': '1',
        'music': '',
        'cover_time': '00:01:42:00',
        'title': 'Brother Told Kidnappers: Kill Her!'
    },
    {
        'start': '00:01:47:00',
        'end': '00:01:52:00',
        'folder1': '',
        'folder2': '故事',
        'folder3': '2',
        'music': '',
        'cover_time': '',
        'title': ''
    },
    ...
]
```

## 优势对比

### CSV格式（通过复制按钮）✅ 推荐

**优点：**
- ✅ 获取的是AI实际生成的内容
- ✅ 避免HTML渲染问题
- ✅ 格式标准，易于解析
- ✅ 支持包含逗号的字段（用引号包裹）
- ✅ 与步骤23的提取方式一致

**缺点：**
- ⚠️ 需要修改提示词
- ⚠️ 依赖浏览器剪贴板权限

### 表格格式（从DOM提取）

**优点：**
- ✅ 不需要修改提示词
- ✅ 可视化效果好

**缺点：**
- ⚠️ 依赖HTML渲染
- ⚠️ 可能受页面样式影响
- ⚠️ 需要等待表格渲染完成

## 提示词模板

### 完整的步骤25提示词（CSV格式）

```
步骤25:【角色设定】
你是一名专业的数据整理专员，负责将之前生成的视频剪辑数据汇总为一张清洗干净的CSV表格。

【任务目标】
根据步骤24生成的剪辑数据，整理成标准的CSV格式表格。

【输出格式】
请直接输出CSV格式，不要添加任何说明文字。

表头（第一行）：
start,end,folder1,folder2,folder3,music,cover_time,title

【字段说明】
- start: 开始时间（格式：hh:mm:ss:ff）
- end: 结束时间（格式：hh:mm:ss:ff）
- folder1: 文件夹1路径
- folder2: 文件夹2路径
- folder3: 文件夹3路径
- music: 音乐文件名
- cover_time: 封面时间（格式：hh:mm:ss:ff）
- title: 标题文字

【输出要求】
1. 第一行必须是表头
2. 使用逗号分隔字段
3. 如果字段为空，保留逗号但不填内容
4. 如果字段包含逗号，请用双引号包裹
5. 不要添加额外的格式、说明文字或Markdown标记
6. 直接输出纯CSV文本

【示例】
start,end,folder1,folder2,folder3,music,cover_time,title
00:01:42:00,00:01:47:00,,故事,1,,00:01:42:00,Brother Told Kidnappers: Kill Her!
00:01:47:00,00:01:52:00,,故事,2,,,,
```

## 测试方法

### 1. 修改提示词文件

编辑你的提示词文件（例如 `prompts.txt`），将步骤25的提示词改为CSV格式。

### 2. 运行测试

```bash
# 运行完整测试
bash test/test_step23_25.sh

# 或只测试步骤25
python test/test_step25.py
```

### 3. 检查日志

```bash
# 查看步骤25的提取日志
grep "步骤25\|CSV\|复制按钮" automation.log | tail -30

# 查看保存的文件
ls -lh assets/Process_Folder/*/step_25_output.xlsx
```

### 4. 验证数据

```python
import pandas as pd

# 读取Excel文件
df = pd.read_excel('assets/Process_Folder/Episode3/step_25_output.xlsx')

# 查看数据
print(f"行数: {len(df)}")
print(f"列数: {len(df.columns)}")
print(f"列名: {df.columns.tolist()}")
print(df.head())
```

## 兼容性

### 向后兼容

如果不修改提示词，步骤25仍然会：
1. 尝试通过复制按钮获取CSV（如果有）
2. 回退到从DOM提取表格（原有逻辑）

**结论：** 修改是向后兼容的，不会破坏现有功能。

### 推荐做法

1. **新项目**：使用CSV格式提示词
2. **现有项目**：
   - 如果表格提取工作正常，可以继续使用
   - 如果遇到提取问题，改用CSV格式

## 常见问题

### Q: CSV格式和表格格式哪个更好？
A: CSV格式更可靠，因为：
- 直接从剪贴板获取，避免HTML解析问题
- 格式标准，pandas可以直接解析
- 与步骤23的提取方式一致

### Q: 如果AI输出的CSV格式不正确怎么办？
A: 会自动回退到DOM提取表格。同时可以：
- 检查提示词是否明确要求CSV格式
- 查看HTML调试文件分析AI的实际输出
- 调整提示词增加格式要求

### Q: 可以同时支持多个CSV文件吗？
A: 可以。如果有多个复制按钮，会获取第一个。如果需要支持多个CSV，可以参考步骤23的实现。

### Q: CSV中的字段包含逗号怎么办？
A: 在提示词中要求AI用双引号包裹包含逗号的字段，pandas会自动处理。

## 版本信息

- **版本**: v1.8.4
- **实现日期**: 2024-12-09
- **新增功能**: 步骤25支持CSV格式复制按钮提取
- **状态**: ✅ 已实现

## 相关文档

- [SRT_CLIPBOARD_EXTRACTION_GUIDE.md](SRT_CLIPBOARD_EXTRACTION_GUIDE.md) - 步骤23 SRT提取指南
- [V1.8.4_IMPLEMENTATION_COMPLETE.md](V1.8.4_IMPLEMENTATION_COMPLETE.md) - v1.8.4实现总结
- [doc/v1.8.4更新说明.md](doc/v1.8.4更新说明.md) - 详细更新说明
