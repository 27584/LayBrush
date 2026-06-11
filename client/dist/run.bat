@echo off
:: 创建或清空log.txt文件
type nul > log.txt

:: 隐藏命令行窗口并将所有输出重定向到log.txt
start /min "" cmd /c "
    :: 设置代码页为UTF-8以支持中文输出
    chcp 65001 >nul
    title client
    cd /d %~dp0
    echo 游戏启动时间: %date% %time% >> log.txt 2>&1
    
    :: 检查pythonw.exe是否存在
    if exist env\pythonw.exe (
        env\pythonw.exe main.py %* >> log.txt 2>&1
    ) else (
        :: 如果本地pythonw不存在，尝试使用系统安装的pythonw
        pythonw.exe main.py %* >> log.txt 2>&1
    )
    
    if errorlevel 1 (
        echo 游戏启动失败，错误代码 %errorlevel% >> log.txt 2>&1
    ) else (
        echo 游戏已成功运行并退出>> log.txt 2>&1
    )
    echo 游戏结束时间: %date% %time% >> log.txt 2>&1
")
