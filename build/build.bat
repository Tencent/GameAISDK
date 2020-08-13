@call gen_pb.bat
@call build_agent.bat
@call build_api.bat
@call build_io.bat
@call build_mc.bat
@call build_plugin.bat
if exist ..\src\ImgProc (
    @call build_cpp.bat
)

@copy ..\Modules\tbus\tbusdll\x64\Release\busdll.dll ..\bin\
@copy ..\Modules\tbus\pytbus\windows\tbus.cp35-win_amd64.pyd ..\bin\
@copy ..\Modules\tbus\pytbus\windows\tbus.cp36-win_amd64.pyd ..\bin\
@copy ..\Modules\opencv-3.4.2\x64\vc15\bin\opencv_world342.dll ..\bin\
@copy ..\Modules\darknetV3-win\3rdparty\dll\x64\pthreadVC2.dll ..\bin\
if exist ..\src\ImgProc (
    @copy ..\src\ImgProc\Projects\Windows\Dep\api-ms-win-downlevel-shlwapi-l1-1-0.dll ..\bin\
    @copy ..\src\ImgProc\Projects\Windows\Dep\concrt140.dll ..\bin\
    @copy ..\src\ImgProc\Projects\Windows\Dep\msvcp140.dll ..\bin\
    @copy ..\src\ImgProc\Projects\Windows\Dep\msvcr100.dll ..\bin\
)