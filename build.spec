# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将视频处理自动化工具打包为独立的可执行文件
"""

block_cipher = None

a = Analysis(
    ['video_automation.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('VERSION', '.'),
        ('requirements.txt', '.'),
        # 包含文档
        ('*.md', '.'),
        # 包含测试脚本
        ('test_*.py', '.'),
        ('demo.py', '.'),
        ('clear_session.py', '.'),
        ('verify_menu_close.py', '.'),
    ],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'pandas',
        'openpyxl',
        'logging',
        'pathlib',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoAutomation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoAutomation',
)
