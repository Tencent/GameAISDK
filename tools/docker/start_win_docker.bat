if "%1" == "h" goto begin
mshta vbscript:createobject(“wscript.shell”).run(“%~nx0 h”,0)(window.close)&&exit
:begin

@echo off
@mode con lines=40 cols=100
color AF
title "sdktool navicate"

set pwd="%cd%"

:: kill exist process
taskkill /F /IM vcxsrv.exe

if %errorlevel% == 1 (
    echo "kill vcxsrv failed"
    pause
)

:: start VcXsrv
echo start VcXsrv......
start /wait "" "C:\Program Files\VcXsrv\xlaunch.exe"
if %errorlevel% == 1 (
    echo "start vcxsrv failed"
    pause
)
echo start VcXsrv successful

:: start adbkit, 7788 port
echo start adbkit, will use 7788 port
for /F %%i in ('adb devices') do ( set adb_device=%%i)
echo detect phone deviceid=%adb_device%
start /b adbkit usb-device-to-tcp -p 7788 %adb_device%
echo start adbkit successful
if %errorlevel% == 1 (
    echo "start adbkit failed"
    pause
)

cd %pwd%
docker run -v "%pwd%\..\..":/data1/game_ai_sdk -it base_aisdktoolclt_ubt16:debug-2.0.2 /bin/bash /data1/game_ai_sdk/bin/docker_start_service.sh

pause
