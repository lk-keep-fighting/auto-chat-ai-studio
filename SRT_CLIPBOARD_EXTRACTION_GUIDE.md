# SRT文件剪贴板提取功能说明

## 功能概述

v1.8.4 实现了通过点击复制按钮从剪贴板获取SRT文件的功能，**支持不确定个数的SRT文档**。

## 工作原理

### 1. 自动检测复制按钮数量
```python
# 查找所有复制按钮（iconname="content_copy"）
copy_buttons = response_element.locator('button[iconname="content_copy"]').all()
logger.info(f"🔍 找到 {len(copy_buttons)} 个复制按钮")
```

**支持场景：**
- ✅ 1个SRT文件 → 1个复制按钮
- ✅ 2个SRT文件 → 2个复制按钮
- ✅ 3个SRT文件 → 3个复制按钮
- ✅ N个SRT文件 → N个复制按钮

### 2. 按顺序点击并获取剪贴板内容
```python
for i, button in enumerate(copy_buttons):
    logger.info(f"📋 点击复制按钮 {i+1}/{len(copy_buttons)}...")
    button.click()
    time.sleep(0.5)  # 等待剪贴板更新
    
    # 读取剪贴板
    clipboard_content = self.page.evaluate('''
        async () => {
            return await navigator.clipboard.readText();
        }
    ''')
    
    # 验证SRT格式
    if '-->' in clipboard_content and re.search(r'\d{2}:\d{2}:\d{2},\d{3}', clipboard_content):
        srt_contents.append(clipboard_content)
```

### 3. 按顺序保存为文件
```python
for i, srt_content in enumerate(text_content, 1):
    srt_file = output_folder / f"step_23_output_{i}.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content.strip())
    logger.info(f"✅ 保存SRT文件 {i}: {srt_file.name}")
```

**输出文件命名：**
- 第1个复制按钮 → `step_23_output_1.srt`
- 第2个复制按钮 → `step_23_output_2.srt`
- 第3个复制按钮 → `step_23_output_3.srt`
- ...
- 第N个复制按钮 → `step_23_output_N.srt`

## 使用示例

### 场景1：2个SRT文件
**AI响应：**
```
SRT 文件 1：旁白测试数据（总时长：30.000 秒）
[复制按钮]
...

SRT 文件 2：旁白测试数据（总时长：30.000 秒）
[复制按钮]
...
```

**日志输出：**
```
🔍 找到 2 个复制按钮
📋 点击复制按钮 1/2...
✅ 从复制按钮 1 获取到 1620 字符的SRT内容
📋 点击复制按钮 2/2...
✅ 从复制按钮 2 获取到 1703 字符的SRT内容
✅ 总共获取了 2 个SRT文件的内容
📋 处理 2 个SRT文件（来自复制按钮）
✅ 保存SRT文件 1: step_23_output_1.srt (1620 字符)
✅ 保存SRT文件 2: step_23_output_2.srt (1703 字符)
```

**输出文件：**
```
assets/Process_Folder/Episode3/
├── step_23_output_1.srt
└── step_23_output_2.srt
```

### 场景2：4个SRT文件
**AI响应：**
```
SRT 文件 A：旁白 A
[复制按钮]

SRT 文件 B：旁白 B
[复制按钮]

SRT 文件 C：旁白 C
[复制按钮]

SRT 文件 D：旁白 D
[复制按钮]
```

**日志输出：**
```
🔍 找到 4 个复制按钮
📋 点击复制按钮 1/4...
✅ 从复制按钮 1 获取到 1200 字符的SRT内容
📋 点击复制按钮 2/4...
✅ 从复制按钮 2 获取到 1350 字符的SRT内容
📋 点击复制按钮 3/4...
✅ 从复制按钮 3 获取到 1450 字符的SRT内容
📋 点击复制按钮 4/4...
✅ 从复制按钮 4 获取到 1500 字符的SRT内容
✅ 总共获取了 4 个SRT文件的内容
📋 处理 4 个SRT文件（来自复制按钮）
✅ 保存SRT文件 1: step_23_output_1.srt (1200 字符)
✅ 保存SRT文件 2: step_23_output_2.srt (1350 字符)
✅ 保存SRT文件 3: step_23_output_3.srt (1450 字符)
✅ 保存SRT文件 4: step_23_output_4.srt (1500 字符)
```

**输出文件：**
```
assets/Process_Folder/Episode3/
├── step_23_output_1.srt
├── step_23_output_2.srt
├── step_23_output_3.srt
└── step_23_output_4.srt
```

### 场景3：1个SRT文件
**AI响应：**
```
SRT 文件：旁白数据
[复制按钮]
...
```

**日志输出：**
```
🔍 找到 1 个复制按钮
📋 点击复制按钮 1/1...
✅ 从复制按钮 1 获取到 2000 字符的SRT内容
✅ 总共获取了 1 个SRT文件的内容
📋 处理 1 个SRT文件（来自复制按钮）
✅ 保存SRT文件 1: step_23_output_1.srt (2000 字符)
```

**输出文件：**
```
assets/Process_Folder/Episode3/
└── step_23_output_1.srt
```

## 错误处理

### 单个按钮失败
如果某个复制按钮点击失败，会跳过该按钮继续处理其他按钮：

```
🔍 找到 3 个复制按钮
📋 点击复制按钮 1/3...
✅ 从复制按钮 1 获取到 1200 字符的SRT内容
📋 点击复制按钮 2/3...
⚠️ 点击复制按钮 2 失败: Timeout
📋 点击复制按钮 3/3...
✅ 从复制按钮 3 获取到 1500 字符的SRT内容
✅ 总共获取了 2 个SRT文件的内容
```

### 剪贴板内容不是SRT格式
如果剪贴板内容不包含SRT时间戳，会跳过：

```
📋 点击复制按钮 1/2...
⚠️ 复制按钮 1 的内容不是SRT格式
📋 点击复制按钮 2/2...
✅ 从复制按钮 2 获取到 1500 字符的SRT内容
```

### 所有按钮都失败
如果所有复制按钮都失败，会回退到其他提取方法：

```
🔍 找到 2 个复制按钮
📋 点击复制按钮 1/2...
⚠️ 点击复制按钮 1 失败: ...
📋 点击复制按钮 2/2...
⚠️ 点击复制按钮 2 失败: ...
🔍 方法2：尝试从表格中提取SRT内容...
```

## 技术细节

### 剪贴板API
使用Playwright的 `page.evaluate()` 执行JavaScript代码：
```javascript
async () => {
    try {
        return await navigator.clipboard.readText();
    } catch (e) {
        return null;
    }
}
```

### SRT格式验证
检查剪贴板内容是否包含：
1. 时间戳箭头：`-->`
2. 时间戳格式：`\d{2}:\d{2}:\d{2},\d{3}` (例如：`00:00:04,500`)

### 等待时间
每次点击按钮后等待0.5秒，确保剪贴板内容更新完成。

## 优势

### 1. 灵活性
- ✅ 自动适应任意数量的SRT文件
- ✅ 不需要预先知道文件数量
- ✅ 动态检测复制按钮

### 2. 可靠性
- ✅ 直接从剪贴板获取，避免HTML解析问题
- ✅ 获取完整的SRT内容，包括格式和换行
- ✅ 单个按钮失败不影响其他按钮

### 3. 准确性
- ✅ 获取的是AI实际复制的内容
- ✅ 避免HTML渲染问题
- ✅ 保留原始格式

## 回退机制

如果剪贴板方法失败，会自动尝试其他方法：

1. **方法1：剪贴板提取** ⭐ 优先
   - 点击复制按钮
   - 读取剪贴板内容

2. **方法2：表格提取** （备用）
   - 从HTML表格中提取
   - 构建SRT格式

3. **方法3：代码块提取** （备用）
   - 从 `<pre>`, `<code>` 元素提取

4. **方法4：文本搜索** （备用）
   - 在响应文本中搜索SRT格式

## 测试方法

### 运行测试
```bash
bash test/test_step23_25.sh
```

### 检查日志
```bash
# 查看复制按钮相关日志
grep "复制按钮\|clipboard" automation.log | tail -30

# 查看保存的文件
grep "step_23_output" automation.log | tail -20
```

### 验证文件
```bash
# 列出所有SRT文件
ls -lh assets/Process_Folder/*/step_23_output_*.srt

# 查看文件内容
head -20 assets/Process_Folder/*/step_23_output_1.srt
head -20 assets/Process_Folder/*/step_23_output_2.srt
```

## 常见问题

### Q: 如果AI返回10个SRT文件会怎样？
A: 代码会自动检测10个复制按钮，按顺序点击并保存为 `step_23_output_1.srt` 到 `step_23_output_10.srt`。

### Q: 如果某个复制按钮失败了怎么办？
A: 会跳过该按钮继续处理其他按钮，最后保存成功获取的SRT文件。

### Q: 文件编号会跳过失败的按钮吗？
A: 不会。文件编号是按成功获取的顺序排列的，例如如果第2个按钮失败，会保存为：
- 第1个按钮 → `step_23_output_1.srt`
- 第3个按钮 → `step_23_output_2.srt`

### Q: 如何知道获取了多少个SRT文件？
A: 查看日志中的 "✅ 总共获取了 X 个SRT文件的内容" 和 "✅ 步骤 23 保存了 X 个SRT文件"。

## 版本信息

- **版本**: v1.8.4
- **实现日期**: 2024-12-09
- **支持**: 不确定个数的SRT文档
- **状态**: ✅ 已实现并修复

## 相关文档

- [V1.8.4_IMPLEMENTATION_COMPLETE.md](V1.8.4_IMPLEMENTATION_COMPLETE.md) - 实现总结
- [BUGFIX_RE_IMPORT.md](BUGFIX_RE_IMPORT.md) - Bug修复说明
- [doc/v1.8.4更新说明.md](doc/v1.8.4更新说明.md) - 详细更新说明
- [doc/v1.8.4快速参考.md](doc/v1.8.4快速参考.md) - 快速参考
