@echo ------------------------------------- build api start -------------------
@rd /s /Q  ..\bin\API
@python CompilePy3Pyc.py ../src/API/  ../bin/API/
@echo ------------------------------------- build api end -------------------