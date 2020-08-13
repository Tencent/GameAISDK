@echo ------------------------------------- build cpp programe start -------------------

::devenv.com ..\src\ImgProc\Projects\Windows\UIRecognize\SDK.sln /Rebuild "Release"
::copy ..\src\ImgProc\Projects\Windows\sdk_installer\Release\sdk_installer.msi ..\bin\

if exist ..\bin\GameReg.exe (
    @del /f /s /q ..\bin\GameReg.exe
)
devenv.com ..\src\ImgProc\GameRecognize\Windows\GameReg.vcxproj /Rebuild "Release|x64"
@copy ..\src\ImgProc\GameRecognize\Windows\Release\GameReg.exe ..\bin\

if exist ..\bin\UIRecognize.exe (
    @del /f /s /q ..\bin\UIRecognize.exe
)
devenv.com ..\src\ImgProc\Projects\Windows\UIRecognize\UIRecognize.vcxproj /Rebuild "Release_cpu|x64"
@copy ..\src\ImgProc\Projects\Windows\UIRecognize\output\Release_cpu\UIRecognize.exe ..\bin\

@echo ------------------------------------- build cpp programe end -------------------