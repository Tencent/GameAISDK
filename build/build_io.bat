@echo ------------------------------------- build io start -------------------

@rd /s /Q  ..\bin\pyIOService
@python CompilePy3Pyc.py ../src/IOService/pyIOService/  ../bin/pyIOService/
@copy ..\src\IOService\*.py  ..\bin\

@echo ------------------------------------- build io end -------------------