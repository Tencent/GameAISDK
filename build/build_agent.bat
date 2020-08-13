@echo ------------------------------------- build agent start -------------------

@rd /s /Q  ..\bin\AgentAI
@python CompilePy3Pyc.py ../src/AgentAI/  ../bin/AgentAI/
@copy ..\src\AgentAI\*.py  ..\bin\

@echo ------------------------------------- build agent end -------------------
