@echo off
setlocal enabledelayedexpansion
:: 防止中文乱码
chcp 65001 >nul

:: ================= 配置 =================
set "TOOL=C:\FFmpeg\bin\ffprobe.exe"
set "RESULT=VideoList.csv"
:: =======================================

echo 正在处理，请稍候...

:: 写入表头
echo Filename,Duration > "%RESULT%"

:: 循环处理视频
for %%F in (*.mp4 *.avi *.mov *.mkv *.wmv *.ts) do (
    
    :: 1. 先清空变量
    set "DUR="
    
    :: 2. 运行命令并将结果保存到临时文件 temp.txt
    :: 注意：这种写法不怕文件名里的单引号
    "%TOOL%" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -sexagesimal "%%F" > temp.txt
    
    :: 3. 从临时文件读取内容到变量
    set /p DUR=<temp.txt
    
    :: 4. 如果读取到了时长，就写入 CSV
    if defined DUR (
        echo "%%~nxF",!DUR! >> "%RESULT%"
        echo [OK] %%~nxF
    ) else (
        echo [失败] 无法读取: %%~nxF
    )
)

:: 删除临时文件
del temp.txt >nul 2>&1

echo.
echo ==========================================
echo 处理完成！请查看: %RESULT%
echo ==========================================
pause