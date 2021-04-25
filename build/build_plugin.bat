@echo ------------------------------------- build plugin start -------------------

@rd /s /Q  ..\bin\PlugIn
xcopy ..\src\PlugIn\*  ..\bin\PlugIn\* /E

@echo ------------------------------------- build plugin end -------------------