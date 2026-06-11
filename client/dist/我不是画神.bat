::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAnk
::fBw5plQjdG8=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCuDJGmW+0g1Kw9HcCCuC1e5CrwZ5vzHaQJ2JpXw0hrw/3sAXXFwbuUL7yU=
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
:: 创建或清空log.txt文件
type nul > log.txt

:: 隐藏命令行窗口并将所有输出重定向到log.txt
start /min "" cmd /c "
    :: 设置代码页为UTF-8以支持中文输�?
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
        echo 游戏启动失败，错误代�?%errorlevel% >> log.txt 2>&1
    ) else (
        echo 游戏已成功运行并退�?> log.txt 2>&1
    )
    echo 游戏结束时间: %date% %time% >> log.txt 2>&1
")
