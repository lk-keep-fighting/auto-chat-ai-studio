# 快速启动清单

## 测试前准备 ✓

- [ ] 虚拟环境已激活
  ```bash
  source venv/bin/activate  # macOS/Linux
  ```

- [ ] 依赖已安装
  ```bash
  pip install beautifulsoup4 pandas openpyxl
  ```

- [ ] 配置已检查
  ```bash
  grep "SAVE_DEBUG_HTML" config.py
  # 应该显示: SAVE_DEBUG_HTML = True
  ```

## 运行测试 ✓

- [ ] 启动测试脚本
  ```bash
  bash test/test_step23_25.sh
  ```

- [ ] 在浏览器中确认登录
  - 等待浏览器打开
  - 确认已登录 Google 账号
  - 按 Enter 继续

- [ ] 观察日志输出
  - 查找 ✅ 成功标记
  - 查找 ⚠️ 警告标记
  - 查找 💾 文件保存标记

## 检查输出 ✓

- [ ] 步骤23输出
  ```bash
  ls -la assets/Process_Folder/test_步骤23_SRT文件/
  # 应该看到: step_23_output_*.srt
  ```

- [ ] 步骤25输出
  ```bash
  ls -la assets/Process_Folder/test_步骤25_表格数据/
  # 应该看到: step_25_output.xlsx
  ```

- [ ] 调试文件
  ```bash
  ls -la assets/Process_Folder/*/debug/
  # 应该看到: step_23_response_*.html, step_25_response_*.html
  ```

## 分析结果 ✓

- [ ] 运行综合分析
  ```bash
  python analyze_test_results.py
  ```

- [ ] 检查SRT文件质量
  - [ ] 以序号1开始
  - [ ] 无UI元素
  - [ ] 时间戳格式正确

- [ ] 检查Excel文件质量
  - [ ] 列名正确
  - [ ] 数据完整
  - [ ] 格式正确

## 深入调试（如果需要）✓

- [ ] 分析步骤23 HTML
  ```bash
  python analyze_step23_html.py
  ```

- [ ] 分析步骤25 HTML
  ```bash
  python analyze_step25_html.py
  ```

- [ ] 手动查看HTML文件
  ```bash
  open assets/Process_Folder/*/debug/*.html
  ```

## 问题排查 ✓

### 如果步骤23失败

- [ ] 查看日志
  ```bash
  grep "步骤23" test_step23_25.log
  ```

- [ ] 检查是否生成.txt文件而不是.srt
  ```bash
  ls -la assets/Process_Folder/test_步骤23_SRT文件/*.txt
  ```

- [ ] 运行HTML分析
  ```bash
  python analyze_step23_html.py
  ```

- [ ] 查看HTML文件，找到SRT内容位置

### 如果步骤25失败

- [ ] 查看日志
  ```bash
  grep "步骤25" test_step23_25.log
  ```

- [ ] 检查Excel文件是否存在
  ```bash
  ls -la assets/Process_Folder/test_步骤25_表格数据/*.xlsx
  ```

- [ ] 运行HTML分析
  ```bash
  python analyze_step25_html.py
  ```

- [ ] 查看HTML文件，检查表格结构

## 清理（可选）✓

- [ ] 删除测试输出
  ```bash
  rm -rf assets/Process_Folder/test_步骤*
  ```

- [ ] 删除调试文件
  ```bash
  rm -rf assets/Process_Folder/*/debug
  ```

- [ ] 删除日志文件
  ```bash
  rm test_step23_25.log
  ```

## 文档参考 ✓

- [ ] [TEST_AND_DEBUG_GUIDE.md](TEST_AND_DEBUG_GUIDE.md) - 完整测试指南
- [ ] [DEBUG_STEP23_README.md](DEBUG_STEP23_README.md) - 步骤23调试
- [ ] [V1.8.3_COMPLETE_SUMMARY.md](V1.8.3_COMPLETE_SUMMARY.md) - 版本总结
- [ ] [doc/v1.8.3更新说明.md](doc/v1.8.3更新说明.md) - 详细说明

## 成功标准 ✓

### 步骤23
- [x] 生成.srt文件（不是.txt）
- [x] 文件以序号1开始
- [x] 无UI元素残留
- [x] 时间戳格式正确
- [x] 调试HTML已保存

### 步骤25
- [x] 生成.xlsx文件
- [x] 包含正确的列名
- [x] 包含多行数据
- [x] 数据格式正确
- [x] 调试HTML已保存

## 下一步 ✓

测试成功后：
- [ ] 运行完整的视频处理流程
- [ ] 监控生产环境日志
- [ ] 收集反馈和改进建议

测试失败后：
- [ ] 分析HTML结构
- [ ] 调整提取策略
- [ ] 重新测试
- [ ] 报告问题

---

**提示**: 使用 `grep "✓"` 可以快速查看已完成的项目
