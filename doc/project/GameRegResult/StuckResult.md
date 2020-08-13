## stuck类型识别任务的结果解析

### 1  stuck类型识别任务结果说明

​	如果在识别任务配置文件中有类型为‘stuck’的识别任务，如(taskid为3的识别任务类型为‘stuck’)，那么我们在Agent端会收到此任务的识别结果，stuck类型的结果示例如下面所示。其中‘‘groupID'’，”frameSeq“，”image“ ，”deviceIndex“。是Agent收到的GameReg进程发过来的图像帧结果的通用字段，”result“对应的是识别结果字段，存储识别结果的数据结构为字典，字典的key值为整型taskid，此值和识别任务的配置文件是一致的(如上文提到的任务的taskid为3)。字典的value值为对应的此任务的识别结果。一个识别任务(task)，可能会有多个元素(Element)组成，所以每个识别任务的结果是个列表，结果列表中的元素对应Element的识别结果。

```
{
	'groupID': int,
	'frameSeq': int,
	'image': mat,
	'deviceIndex': int,
	'result':
	{
		// taskID: result
		3: 
		[
			{
				# 是否卡住, true表示卡住，否则表示未卡住
				'flag': bool,
				# 判断是否卡住的检测图像区域
				'x': int,
				'y': int,
				'w': int,
				'h': int
			}
		]
	}
}
```



### 2 stuck类型识别任务解析示例代码

GameReg进程把识别结果发送到共享内存中，Agent进程通过平台内置的AgentAPIMgr接收结果包，解析结果包中的类型为‘stuck’的任务的主要代码示例如下。

```
STUCK_TASK_ID = 3

class GameXXXEnv(GameEnv):
    def __init__(self):
        GameEnv.__init__(self)
        self.__agentAPI = None
    
    def Init(self):
        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()
        ret = self.__agentAPI.Initialize(taskCfgFile, referCfgFile)
        if not ret:
            self.logger.error('Agent API Init Failed')
            return False

        ret = self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, 1)
        if not ret:
            self.logger.error('send message failed')
            return False
        # 其他内容省略
        return True

   	# 获取类型为'stuck'的任务的结果
    def GetStuckState(self, taskResult):
        state = False
        if taskResult is None:
            return state
        
         for result in taskResult:
            # 以第一个元素为例，'flag' 字段为True,表示检测当前为卡住状态,否则表示未卡住。
            state = result.get('flag')
            return state
            
    def GetGameInfo(self):
        while True:
            # 通过api接口，获取当前帧的处理结果
            gameInfo = self.__agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)
            if gameInfo is None:
                continue
            
            # 获取所有识别任务的结果
            result = gameInfo['result']
            if result is None:
                continue
                
			# 获取STUCK_TASK_ID对应的任务的结果
            regResults = result.get(STUCK_TASK_ID)
            # 解析BEGIN_TASK_ID对应的任务的结果
            state = self.GetStuckState(regResults)
            # 根据需求做相应的处理
            break    
     
    def IsEpisodeStart(self):
        return True

    def IsEpisodeOver(self):
        return False
```