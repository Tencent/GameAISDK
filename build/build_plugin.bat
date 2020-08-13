@echo ------------------------------------- build plugin start -------------------

@rd /s /Q  ..\bin\PlugIn
@python CompilePy3Pyc.py ../src/PlugIn/  ../bin/PlugIn/

@echo ------------------------------------- build plugin end -------------------