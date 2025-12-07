# 步骤25数据保存测试工具

## 快速开始

### 方法1：使用启动脚本（推荐）

```bash
./test_step25.sh
```

### 方法2：直接运行Python脚本

```bash
python test_step25.py
```

## 测试流程

1. **初始化浏览器** - 启动系统Chrome浏览器
2. **打开AI Studio** - 自动访问 Google AI Studio
3. **等待用户确认** - 确认已登录并进入对话界面后按 Enter
4. **自动发送测试提示词** - 发送步骤25测试提示词
5. **等待AI响应** - 等待AI生成10行测试数据
6. **自动提取数据** - 从HTML DOM提取表格数据
7. **自动保存文件** - 保存为Excel文件
8. **验证结果** - 显示数据统计和前3行数据

## 测试提示词

```
步骤25:按输出格式输出10行测试数据

【输出格式】
请直接输出表格。表头如下：
| start | end | folder1 | folder2 | folder3 | music | cover_time | title |
```

## 输出文件

- **Excel文件**: `test_output/test_step25/step_25_output.xlsx`
- **日志文件**: `test_step25.log`

## 查看结果

### 查看Excel文件

```bash
open test_output/test_step25/step_25_output.xlsx
```

### 查看日志

```bash
# 查看完整日志
cat test_step25.log

# 实时查看日志
tail -f test_step25.log
```

## 成功标准

测试成功会显示：

```
✅ 文件已创建: test_output/test_step25/step_25_output.xlsx
📊 文件大小: 12345 字节
📊 数据行数: 10
📊 数据列数: 8
📋 列名: start, end, folder1, folder2, folder3, music, cover_time, title

前3行数据:
   start    end  folder1  folder2  folder3  music  cover_time  title
0  00:00  00:10  测试1    测试1    测试1    音乐1   00:05      标题1
1  00:10  00:20  测试2    测试2    测试2    音乐2   00:15      标题2
2  00:20  00:30  测试3    测试3    测试3    音乐3   00:25      标题3

🎉 测试成功！
```

## 故障排除

详细的故障排除指南请查看：**[步骤25测试指南.md](步骤25测试指南.md)**

### 常见问题

1. **数据量为0** - AI还没生成完就提取了，手动等待后再按Enter
2. **数据类型是字符串** - DOM提取失败，检查HTML结构
3. **文件未创建** - 保存过程异常，查看日志错误信息
4. **文件大小为0** - DataFrame为空，检查数据提取逻辑

## 清理测试文件

```bash
# 删除测试输出
rm -rf test_output

# 删除测试日志
rm test_step25.log
```

## 相关文档

- **[步骤25测试指南.md](步骤25测试指南.md)** - 详细的测试指南
- **[v1.7.2更新说明.md](v1.7.2更新说明.md)** - 数据保存日志增强说明
- **[使用指南.md](使用指南.md)** - 完整的使用教程

## 技术说明

### 测试脚本：`test_step25.py`

- 继承自 `VideoProcessor` 类
- 只测试步骤25的数据提取和保存
- 使用测试提示词生成10行测试数据
- 验证DOM提取和Excel保存功能

### 关键方法

1. `open_ai_studio()` - 打开AI Studio
2. `send_prompt()` - 发送测试提示词
3. `wait_for_response()` - 等待AI响应
4. `extract_response(step_number=25)` - 提取步骤25数据
5. `save_output_data()` - 保存为Excel文件

### 数据流程

```
测试提示词 → AI生成表格 → HTML DOM → extract_table_from_dom() 
→ List[Dict] → DataFrame → Excel文件
```

## 注意事项

- ⚠️ 测试会打开真实的浏览器
- ⚠️ 需要登录Google账号
- ⚠️ 需要网络连接
- ⚠️ AI生成数据需要时间，请耐心等待
- ⚠️ 测试完成后浏览器会保持打开，按Enter关闭

## 版本信息

- **版本**: v1.7.2
- **更新日期**: 2024-12-06
- **测试工具**: test_step25.py
- **启动脚本**: test_step25.sh
