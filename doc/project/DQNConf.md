# DQN强化学习配置说明

强化学习也称试错学习，从随机的AI模型开始训练，训练过程中不断与实际游戏环境进行交互，通过大量的尝试各种动作，逐渐学习到最优的AI模型。

通过修改cfg/task/agent/AgentAI.ini文件内容如下，可以加载AI SDK内置的DQN强化学习算法：

```
[AGENT_ENV]
UsePluginEnv = 0
EnvPackage = agentenv
EnvModule = DQNEnv
EnvClass = DQNEnv

[AI_MODEL]
UsePluginAIModel = 0
AIModelPackage = dqn
AIModelModule = DQNAIModel
AIModelClass = DQNAIModel

[RUN_FUNCTION]
UseDefaultRunFunc = 1
;RunFuncPackage = MyPackage
;RunFuncModule = MyModule
;RunFuncName = MyRunFunc
```

- UsePluginEnv = 0 表示使用AI SDK内置的Env插件
- EnvPackage = agentenv 表示使用的Env插件的Package名（Python中Package名通常即为目录名）为agentenv 
- EnvModule = DQNEnv 表示使用的Env插件的Module名（Python中Module名通常即为文件名）为DQNEnv
- EnvClass = DQNEnv 表示使用的Env插件的Class名为DQNEnv
- UsePluginAIModel = 0 表示使用AI SDK内置的AI算法插件
- AIModelPackage = dqn 表示使用的AI算法插件的Package名为dqn
- AIModelModule = DQNAIModel 表示使用的AI算法插件的Module名为ImitationAI
- AIModelClass = DQNAIModel 表示使用的AI算法插件的Class名为ImitationAI

 