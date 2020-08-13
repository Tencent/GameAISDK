@echo off

if [%1] == [] (
echo "Please set release dir!"
exit /B
)

@md %1
@xcopy /e /i ..\bin %1\bin
@xcopy /e /i ..\cfg %1\cfg
@xcopy /e /i ..\data %1\data
@xcopy /e /i ..\log %1\log
@md %1\tools
@xcopy /e /i ..\tools\SDKTool %1\tools\SDKTool
@xcopy /i ..\*.txt %1\