## AI的二次开发

[TOC]

AI的二次开发中，有依赖AgentAPIMgr和ActionAPIMgr，AgentAPIMgr是Agent和GameReg进行交互的接口模块。ActionAPIMgr是和手机交互的动作接口模块。在本章我们先对这两部分进行介绍，再介绍AI插件。

## 1 AgentAPIMgr 介绍

### 1.1 整体流程

```
if __name__ == '__main__':
	# step1: AgentAPIMgr为对外接口类，用于和识别模块交互。
	agentAPI = AgentAPIMgr.AgentAPIMgr()

	#step2:初始化：初始化tbus,加载识别任务配置文件如task.json，配置文件的介绍详见三章节
    ret = agentAPI.Initialize("../cfg/task.json")
    if not ret:
        print('Agent API Init Failed')
        return

	#step3:发送识别命令到识别模块，参数介绍请详见二章节
    ret = agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, 1)
    if not ret:
        print('send message failed')
        
    while True:
		#step4:获取识别结果，参数介绍请详见第二章节
        msgDict = agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)

	#step5:资源释放，tbus资源释放
	agentAPI.Release()
```

### 1.2 agentAPI的介绍

* **AgentAPI.Initialize(confFile，referFile)**

初始化操作，输入参数confFile为 json格式的任务配置文件。referFile为json格式的参考任务配置文件。此配置文件的详细说明请见第3章的场景识别配置中的[任务配置文件说明](../SDKTool/TaskConf.md)。初始化的返回结果为True,表明初始化成功;False初始化失败，可根据屏幕打印的错误信息，定位原因。

- **AgentAPI.SendCmd(cmdID, cmdValue)**

发送命令给识别模块，返回值为True,表示发送成功，False表示发送失败。识别模块会根据发送的命令，改变识别器。输入参数详情见下表：

| **cmdID**          | **cmdValue**                   | **描述**                                                     |
| ------------------ | ------------------------------ | ------------------------------------------------------------ |
| MSG_SEND_GROUP_ID  | groupID（python数字类型）      | 发送任务groupID，识别模块接受此group下的任务列表信息，创建识别器（groupID的具体数值请参考对应json配置文件中的groupID字段），如发送groupID=1的任务：ret = agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, 1) |
| MSG_SEND_TASK_FLAG | 由taskid和对应操作组成的字典。 | key值为taskID，为配置文件中对应group下的”taskID”项， value为True/False表示打开/关闭taskID对应的识别器。在后续的识别结果中，会增加或是减少此task的识别结果。如,打开taskID为1的任务，关闭taskID为2的任务。taskDict ={}taskDict[1] = TruetaskDict[2] = Falseret = agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_TASK_FLAG, taskDict ) |
| MSG_SEND_ADD_TASK  | task参数列表                   | 增加一系列识别任务，识别模块接收到此消息后，根据参数列表创建一系列识别器。在后续的识别结果中，会增加此任务的识别结果。如增加taskID为10的任务：taskList =[]taskDict = dict()taskDict["taskID"] = 10taskDict["type"] = "fixed_obj"taskDict["elements"] = []elementDict = dict()elementDict["x"] = 946elementDict["y"] = 15elementDict["w"] = 220elementDict["h"] = 60elementDict["path"] = "../data/DNF/dnf_over.bmp"taskDict["elements"].append(elementDict)taskList.append(taskDict) agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_ADD_TASK, taskList) |
| MSG_SEND_DEL_TASK  | taskID 的 列表                 | 删除一系列识别任务，识别模块接收到此消息后，根据task的设置，删除相应的识别器。在后续的识别结果中，不会存在此task识别结果。如：删除taskID为10的任务：taskList =[]taskList.append(10)ret = agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_DEL_TASK, taskList) |
| MSG_SEND_CHG_TASK  | task参数列表                   | 改变一系列识别任务，识别模块接收到此消息后，根据新的任务参数，修改识别器。在后续的识别中，根据新识别器对图像做识别。如改变taskID为10的任务：taskList = []taskDict = dict()taskDict["taskID"] = 10taskDict["type"] = "fixed_obj"taskDict["elements"] = []elementDict = dict()elementDict["x"] = 1000elementDict["y"] = 0elementDict["w"] = 200elementDict["h"] = 200elementDict["path"] = "../data/DNF/dnf_playing.bmp"taskDict["elements"].append(elementDict)taskList.append(taskDict)ret = agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_CHG_TASK, taskList) |

 

- **AgentAPI.GetInfo(type)**

获取结果，结果的类型type有以下几种。

| **type**            | **Return**         | **描述**                                                     |
| ------------------- | ------------------ | ------------------------------------------------------------ |
| CUR_GROUP_TASK_INFO | 当前组任务参数列表 | 返回值为 python中的列表类型(list)如：groupTaskInfo = agentAPI.GetInfo(AgentAPIMgr.CUR_GROUP_TASK_INFO)for task in groupTaskInfo:taskID = task.get('taskID')type = task.get('type')elements = task.get('elements')      …… |
| CUR_GROUP_INFO      | 当前组的参数       | 返回值为python中的字典类型(dict)如:curGroupInfo = agentAPI.GetInfo(AgentAPIMgr.CUR_GROUP_INFO)groupID = curGroupInfo.get('groupID')groupName = curGroupInfo.get('name')groupTask = curGroupInfo.get('task')…… |
| GAME_RESULT_INFO    | 识别结果           | 返回值为python中的字典类型(dict)如:msgDict = agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)resultDic = msgDict['result']           groupID = msgDict['groupID']frameSeq = msgDict['frameSeq']deviceIndex = msgDict['deviceIndex']img = msgDict['image']..... |
| ALL_GROUP_INFO      | 所有组的参数       | 返回值为python中列表(list)类型。如：allGroupInfo = agentAPI.GetInfo(AgentAPIMgr.ALL_GROUP_INFO)for groupInfo in allGroupInfo:groupID = groupInfo.get('groupID')groupName = groupInfo.get('name')groupTask = groupInfo.get('task')    …… |

当调用AgentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)接口去获取当前帧游戏图像的处理结果时，会返回每个任务(task)的结果项。不同task类型的结果说明，请见文档 [Task识别结果说明](TaskRecognitionResults.md) 。

- **AgentAPI.Release()**

在程序的最后，调用此函数，释放tbus资源。

## 2 ActionAPIMgr介绍

### 2.1 整体流程

```
if __name__ == '__main__':
	#step1: ActionAPIMgr为对外接口类。
	actionAPI = ActionAPIMgr.ActionAPIMgr()

	#step2:初始化：初始化tbus 
    ret = actionAPI.Initialize()
    if not ret:
        print('Action API Init Failed')
        return

    #step3:发送动作
    actionAPI.SendAction(actionID=12, actionData={})  # 发送自定义12号动作
    actionAPI.Click(px=300, py=400, contact=0)  # 发送点击动作，点击（300, 400）位置

    #step4:资源释放，tbus资源释放
    actionAPI.Finish()
```

### 2.2  ActionAPI的介绍

- ActionAPI.Initialize()
  初始化操作，在其他方法之前调用。
- ActionAPI.Finish()
  结束操作，在进程退出时调用释放资源
- ActionAPI.Reset(frameSeq=-1)
  释放所有contact，frameSeq为帧序号
- ActionAPI.SendAction(actionID, actionData , frameSeq=-1)
  发送自定义动作，actionID为动作ID，actionData为对应的动作参数（字典）
- ActionAPI.MovingInit(centerX, centerY, radius, contact=0, frameSeq=-1, waitTime=1000)
  初始化移动摇杆中心点（centerX, centerY）和半径radius，触点ID为contact，之后等待时间waitTime毫秒
- ActionAPI.MovingFinish()
  释放移动摇杆初始化时的触点
- ActionAPI.Moving(dirAngle，frameSeq=-1，durationMS=50)
  控制移动摇杆向dirAngle方向滑动，滑动过程耗时durationMS毫秒
- ActionAPI.Move(px, py, contact=0, frameSeq=-1, waitTime=0)
  移动触点contact到（px, py）位置，瞬间移动不补充过渡点，之后等待时间waitTime毫秒
- ActionAPI.Click(px, py, contact=0, frameSeq=-1, durationMS=-1)
  点击触点contact在（px, py）位置，过程耗时durationMS毫秒
- ActionAPI.Down(px, py, contact=0, frameSeq=-1, waitTime=0)
  按压触点contact在（px, py）位置，之后等待时间waitTime毫秒
- ActionAPI.Up(contact, frameSeq=-1, waitTime=0)
  释放触点contact，之后等待时间waitTime毫秒
- ActionAPI.Swipe(sx, sy, ex, ey, contact=0, frameSeq=-1, durationMS=50, needUp=True)
  滑动触点contact从（sx, sy）到（ex, ey），中间会补充过渡点，过程耗时durationMS毫秒，根据needUp决定最后是否释放触点
- ActionAPI.SwipeMove(px, py, contact=0, frameSeq=-1, durationMS=50)
  移动触点contact到（px, py）位置，中间会补充过渡点，过程耗时durationMS毫秒

## 3. AI插件说明

### 3.1 AI插件介绍

- 平台中特定游戏的AI逻辑以AI插件的形式存在，AI插件主要包含两部分：Env插件和AI模型插件。
  Env插件
  Env插件通常实现与游戏业务相关的一些逻辑，如执行各种游戏动作输出、通过API设置图像识别任务并获取识别结果。

- AI模型插件
  AI模型插件通常用来实现特定的游戏AI算法，如强化学习算法、模仿学习算法、行为树等算法等。根据Env插件得到的游戏状态信息（游戏图像、游戏中技能状态、血条、敌人位置等）决策游戏动作，并执行对应的游戏动作。

平台定义了Env插件和AI模型插件的接口，继承并实现对应的插件接口，即可实现自己的AI插件，并由平台AI框架加载运行AI插件。Env插件和AI模型插件不是一一对应的关系，一个AI模型插件可以对应不同的Env插件。如果不同游戏使用了同样的AI算法，但游戏的一些业务逻辑存在差异，这种情况下每个游戏可以实现不同的Env插件，但可以使用同一个AI模型插件。

平台内置了DQN强化学习和模仿学习插件，可以通过配置cfg/task/agent/AgentAI.ini文件来直接使用内置AI插件，也可以通过配置cfg/task/agent/AgentAI.ini文件来使用用户开发的AI插件。

### 3.2 用户AI插件开发

下面以一个Speed游戏为例，说明用户该如何开发AI插件。开发后的Speed AI插件存放在src/PlugIn/ai/目录下，目录如下：

```
game_ai_sdk
└─src
    └─PlugIn
        └─ai
            └─speed
                   └─ SpeedAI.py
                   └─ SpeedEnv.py
```

其中SpeedEnv.py文件实现了Env插件，SpeedAI.py文件实现了AI模型插件。

其中SpeedEnv.py文件实现了Env插件，SpeedAI.py文件实现了AI模型插件。

修改cfg/task/agent/AgentAI.ini文件，让平台加载运行Speed AI插件，修改后的文件内容如下所示：

```
[AGENT_ENV]
UsePluginEnv = 1
EnvPackage = speed
EnvModule = SpeedEnv
EnvClass = SpeedEnv

[AI_MODEL]
UsePluginAIModel = 1
AIModelPackage = speed
AIModelModule = SpeedAI
AIModelClass = SpeedAI

[RUN_FUNCTION]
UseDefaultRunFunc = 1
;RunFuncPackage = MyPackage
;RunFuncModule = MyModule
;RunFuncName = MyRunFunc
```

- UsePluginEnv = 1  表示使用PlugIn目录下的Env插件，而非平台内置的Env插件。

- EnvPackage = speed  表示用户开发Env插件的Package名（Package名通常即为目录名）为speed

- EnvModule = SpeedEnv  表示用户开发Env插件的Module名（Module名通常即为文件名）为SpeedEnv

- EnvClass = SpeedEnv  表示用户开发的Env插件的Class名（Class名即为类名）为SpeedEnv

- UsePluginAIModel = 1 表示使用PlugIn目录下的AI模型插件

- AIModelPackage = speed  表示用户开发AI模型插件的Package名为speed

- AIModelModule = SpeedAI  表示用户开发AI模型插件的Module名为SpeedAI

- AIModelClass = SpeedAI  表示用户开发AI模型插件的Class名为SpeedAI

  ### 3.3 Env插件实现

  Env插件需要继承平台中的GameEnv类，并实现GameEnv的接口。
  SpeedEnv插件代码如下：

  ```
  import time
  import os
  import cv2
  
  from agentenv.GameEnv import GameEnv
  from AgentAPI import AgentAPIMgr
  from ActionAPI.ActionAPIMgr import ActionAPIMgr
  from util import util
  
  #游戏场景识别任务配置文件
  TASK_CFG_FILE = 'cfg/task/gameReg/Task.json'
  
  REG_GROUP_ID = 1
  
  BEGIN_TASK_ID = 1 #游戏开始识别任务ID
  WIN_TASK_ID = 2 #游戏结束识别任务ID
  LOSE_TASK_ID = 3  #游戏失败识别任务ID
  DATA_TASK_ID = 4  #游戏胜利识别任务ID
  
  GAME_STATE_INVALID = 0
  GAME_STATE_RUN = 1
  GAME_STATE_WIN = 2
  GAME_STATE_LOSE = 3
  
  class SpeedEnv(GameEnv):
      #构造函数
      def __init__(self):
          GameEnv.__init__(self)
          self.__frameIndex = -1
          self.__actionMgr = ActionAPIMgr()  #创建执行动作对象
          self.__agentAPI = AgentAPIMgr.AgentAPIMgr()  #创建场景识别对象
          self.Reset()
  
      #初始化函数，通常初始化动作模块和识别模块
      def Init(self):
          taskCfgFile = util.ConvertToSDKFilePath(TASK_CFG_FILE)
          self.__agentAPI.Initialize(taskCfgFile)
          self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, REG_GROUP_ID)
          self.__actionMgr.Initialize()
          return True
  
      #退出函数
      def Finish(self):
          self.__agentAPI.Release()
          self.__actionMgr.Finish()
  
      #游戏动作个数
      def GetActionSpace(self):
          return 3
  
      #输出游戏动作
      def DoAction(self, action):
          if action == 0:
              #执行点击动作1
              self.__actionMgr.Click(140, 570, contact=0, frameSeq=self.__frameIndex, durationMS=100)
          elif action == 1:
              #执行点击动作2
              self.__actionMgr.Click(300, 570, contact=0, frameSeq=self.__frameIndex, durationMS=100)
          elif action == 2:
              #不进行任何动作
              pass
  
      #根据识别模块API获取游戏状态信息，并返回状态信息
      def GetState(self):
          #get game data , image and state
          gameInfo = self._GetGameInfo()
          self.__frameIndex = gameInfo['frameSeq']
          image = gameInfo['image']
          state = self.__gameState
          img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  
          self.__isTerminal = True
          if state == GAME_STATE_RUN:
              self.__isTerminal = False
  
          return img
  
      #重置游戏状态，通常可以在每局游戏结束或开始时调用
      def Reset(self):
          self.__isTerminal = True
          self.__gameState = GAME_STATE_INVALID
  
      #根据识别模块获取的信息，判断游戏对局是否开始
      def IsEpisodeStart(self):
          gameInfo = self._GetGameInfo()
          if self.__gameState == GAME_STATE_RUN:
              self.__isTerminal = False
              return True
  
          return False
  
      #根据识别模块获取的信息，判断游戏对局是否结束
      def IsEpisodeOver(self):
          return self.__isTerminal
  
      #获取taskID对应的识别结果
      def _GetTemplateState(self, resultDict, taskID):
          state = False
          px = -1
          py = -1
          regResults = resultDict.get(taskID)
          if regResults is None:
              return (state, px, py)
  
          for item in regResults:
              flag = item['flag']
              if flag:
                  x = item['boxes'][0]['x']
                  y = item['boxes'][0]['y']
                  w = item['boxes'][0]['w']
                  h = item['boxes'][0]['h']
  
                  state = True
                  px = int(x + w/2)
                  py = int(y + h/2)
                  break
  
          return (state, px, py)
  
      #根据识别模块API获取识别的的游戏状态信息
      def _GetGameInfo(self):
          gameInfo = None
  
          while True:
              gameInfo = self.__agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)
              if gameInfo is None:
                  time.sleep(0.002)
                  continue
  
              result = gameInfo['result']
              if result is None:
                  time.sleep(0.002)
                  continue
  
              flag, _, _ = self._GetTemplateState(result, BEGIN_TASK_ID)
              if flag is True:
                  self.__gameState = GAME_STATE_RUN
  
              flag, _, _ = self._GetTemplateState(result, WIN_TASK_ID)
              if flag is True:
                  self.__gameState = GAME_STATE_WIN
  
              flag, _, _ = self._GetTemplateState(result, LOSE_TASK_ID)
              if flag is True:
                  self.__gameState = GAME_STATE_LOSE
  
              data = None
              if result.get(DATA_TASK_ID) is not None:
                  data = result.get(DATA_TASK_ID)[0]
  
              if data is None:
                  time.sleep(0.002)
                  continue
              else:
                  break
  
          return gameInfo
  ```
  
  

### 3.4 AI模型插件实现

AI模型插件需要继承平台中的AIModel类，并实现AIModel的接口。
实现QQSpeedAI AI模型插件举例：

```
import random

from aimodel.AIModel import AIModel
from agentenv.GameEnv import GameEnv

class SpeedAI(AIModel):
    #构造函数
    def __init__(self):
        AIModel.__init__(self)

    #初始化函数，参数agentEnv为 Env插件类实例对象
    def Init(self, agentEnv):
        self.__agentEnv = agentEnv
        return True

    #退出函数
    def Finish(self):
        pass

    #检测到每一局游戏开始后，AI算法进行的操作可以在此处实现，如一些变量的重置等
    def OnEpisodeStart(self):
        pass

    #检测到每一局游戏结束后，AI算法进行的操作可以在此处实现
    def OnEpisodeOver(self):
         self.__agentEnv.Reset()

    #当加载进入游戏场景时，需要进行的操作可以在此处实现
    def OnEnterEpisode(self):
        pass

    #当离开退出游戏场景时，需要进行的操作可以在此处实现
    def OnLeaveEpisode(self):
        pass

    #训练AI操作的每一个step实现,通常强化学习算法需要实现此接口,基于规则的AI无需训练,不需要实现此接口
    def TrainOneStep(self):
        image =  self.__agentEnv.GetState()

    #AI测试的每一个step实现，通常实现为agentEnv获取游戏状态数据，然后根据AI算法输出对应的游戏操作
    def TestOneStep(self):
        image =  self.__agentEnv.GetState()
        #本样例采用随机动作输出
        action = random.choice([0,1,2])
        self.__agentEnv.DoAction(action)
```



### 3.5 编译运行AI插件

编译运行AI插件时，请确保在game_ai_sdk虚拟环境下。
进入game_ai_sdk/build目录，执行如下命令即可编译Speed AI插件：

```
(game_ai_sdk)./build_plugin.sh
```

进入game_ai_sdk/bin目录，运行如下命令即可运行Speed AI插件：

```
(game_ai_sdk)python agentai.py
```

