# 模仿学习配置说明

模仿学习是一种监督学习，根据采集到的玩家的游戏动作样本来训练AI。采用此算法需要首先采集玩家的动作样本，然后进行AI模型训练，最后加载AI模型来运行AI。

通过修改cfg/task/agent/AgentAI.ini文件内容如下，可以加载AI SDK内置的模仿学习算法：

```
[AGENT_ENV]
UsePluginEnv = 0
EnvPackage = agentenv
EnvModule = ImitationEnv
EnvClass = ImitationEnv
 
[AI_MODEL]
UsePluginAIModel = 0
AIModelPackage = ImitationLearning
AIModelModule = ImitationAI
AIModelClass = ImitationAI
 
[RUN_FUNCTION]
UseDefaultRunFunc = 1
;RunFuncPackage = MyPackage
;RunFuncModule = MyModule
;RunFuncName = MyRunFunc
```

 

- UsePluginEnv = 0  表示使用AI SDK内置的Env插件
- EnvPackage = agentenv  表示使用的Env插件的Package名为agentenv （Python中Package名通常即为目录名） EnvModule = ImitationEnv  表示使用的Env插件的Module名为ImitationEnv（Python中Module名通常即为文件名）
- EnvClass = ImitationEnv  表示使用的Env插件的Class名为ImitationEnv
- UsePluginAIModel = 0 表示使用AI SDK内置的AI算法插件
- AIModelPackage = ImitationLearning  表示使用的AI算法插件的Package名为ImitationLearning
- AIModelModule = ImitationAI  表示使用的AI算法插件的Module名为ImitationAI
- AIModelClass = ImitationAI  表示使用的AI算法插件的Class名为ImitationAI