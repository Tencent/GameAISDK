@echo ------------------------------------- build mc start -------------------

@rd /s /Q  ..\bin\pyManageCenter
@python CompilePy3Pyc.py ../src/ManageCenter/pyManageCenter/  ../bin/pyManageCenter/
@copy ..\src\ManageCenter\*.py  ..\bin\

@echo ------------------------------------- build mc end -------------------