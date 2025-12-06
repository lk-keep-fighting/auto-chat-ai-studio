# 视频处理自动化工具

> 基于 Python + Playwright 的浏览器自动化工具，用于批量处理视频并通过 Google AI Studio 提取数据。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40.0-green.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能特点

- 🎬 自动批量处理视频
- 🤖 自动执行 25 步 AI 对话流程
- 🔄 智能异常处理和自动重试
- 📊 自动保存和合并数据
- 📝 完整的日志和截图记录
- ⚙️ 灵活的配置系统

## 🚀 快速开始

### 安装

```bash
# 使用安装脚本（推荐）
chmod +x setup.sh
./setup.sh

# 或手动安装
pip install -r requirements.txt
playwright install chromium
```

### 运行

```bash
# 使用启动脚本
chmod +x run.sh
./run.sh

# 或直接运行
python video_automation.py
```

### 首次使用

1. 准备视频文件和提示词
2. 运行脚本
3. 手动登录 Google 账号（仅首次）
4. 等待自动处理完成

详细步骤请查看 **[开始使用.md](开始使用.md)** 📖

## 📚 文档

| 文档 | 说明 |
|------|------|
| **[开始使用.md](开始使用.md)** | 5 分钟快速上手指南 ⭐ |
| **[使用指南.md](使用指南.md)** | 详细使用教程和故障排除 |
| **[快速参考.md](快速参考.md)** | 常用命令和配置速查 |
| **[项目说明.md](项目说明.md)** | 项目架构和技术栈 |
| **[视频处理流程.md](视频处理流程.md)** | 业务流程说明 |

## 📁 项目结构

```
.
├── video_automation.py      # 主自动化脚本
├── config.py                # 配置文件
├── test_connection.py       # 测试脚本
├── demo.py                  # 演示脚本
├── requirements.txt         # Python 依赖
└── assets/
    ├── Process_Folder/
    │   ├── prompts.xlsx     # 提示词文件
    │   ├── videos/          # 视频目录
    │   └── [视频名]/        # 输出目录
    └── vidoes/
        └── clips.xlsx       # 合并数据
```

## 🎯 工作流程

```
读取视频列表 → 更新提示词 → 打开 AI Studio → 上传视频 → 
执行 25 步对话 → 保存输出 → 循环处理 → 合并数据 → 完成
```

## ⚙️ 配置

编辑 `config.py` 调整配置：

```python
# 浏览器模式
HEADLESS = False  # True=无头模式
USE_SYSTEM_CHROME = True  # True=使用系统 Chrome（推荐）
WAIT_USER_CONFIRMATION = True  # True=等待用户确认（推荐）

# 等待时间（秒）
WAIT_AFTER_UPLOAD = 15
WAIT_FOR_RESPONSE = 10

# 日志和截图
LOG_LEVEL = "INFO"
SAVE_SCREENSHOTS = True
```

### 工作流程

1. **打开浏览器** - 自动打开系统 Chrome
2. **访问 AI Studio** - 自动访问 Google AI Studio
3. **用户确认** - 等待你确认已登录并进入对话界面
4. **自动处理** - 按 Enter 后自动处理所有视频

### 浏览器选择

**推荐：使用系统 Chrome**（默认）
- ✅ 使用本机已安装的 Chrome 浏览器
- ✅ 使用默认用户配置，已登录的账号直接可用
- ✅ 打开页面后等待用户确认
- ✅ 更稳定可靠

**备选：使用 Chromium**
- 设置 `USE_SYSTEM_CHROME = False`
- 使用 Playwright 自带的 Chromium
- 需要手动登录（会保存会话）

## 🧪 测试

```bash
# 测试浏览器连接
python test_connection.py

# 测试视频上传流程
python test_upload.py

# 测试发送提示词流程
python test_send_prompt.py

# 验证菜单关闭功能
python verify_menu_close.py

# 查看功能演示
python demo.py
```

## 📦 打包

将程序打包为独立的可执行文件：

```bash
# Windows
build.bat

# macOS/Linux
./build.sh

# 或使用 Python 脚本（跨平台）
python build.py
```

详细说明请查看 **[打包说明.md](打包说明.md)** 📦

## 📊 输出

- **步骤输出**: `assets/Process_Folder/[视频名]/step_*.xlsx`
- **合并数据**: `assets/vidoes/clips.xlsx`
- **日志文件**: `automation.log`
- **截图文件**: `screenshots/`

## 🐛 故障排除

查看日志：
```bash
cat automation.log
```

实时监控：
```bash
tail -f automation.log
```

更多问题请查看 **[使用指南.md](使用指南.md)** 的故障排除章节。

## 🔧 技术栈

- **Python 3.8+** - 主要编程语言
- **Playwright** - 浏览器自动化
- **Pandas** - 数据处理
- **OpenPyXL** - Excel 操作

## 📝 注意事项

- ⚠️ 首次使用需要手动登录 Google 账号（会话会自动保存）
- ⚠️ 后续运行会自动加载会话，无需重复登录
- ⚠️ 确保网络连接稳定
- ⚠️ 大视频需要更长上传时间
- ⚠️ 页面结构变化时需要更新选择器

### 会话管理

```bash
# 清除会话（需要重新登录）
python clear_session.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🎉 开始使用

准备好了吗？查看 **[开始使用.md](开始使用.md)** 开始你的第一次自动化处理！

---

**版本**: v1.6.0 | **更新**: 2024-12-05
