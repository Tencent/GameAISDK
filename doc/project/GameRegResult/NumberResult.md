## number类型识别任务的结果解析

### 1  number类型识别任务结果说明

​	如果在识别任务配置文件中有类型为‘number的识别任务，如(taskid为5的识别任务类型为‘number’)，那么我们在Agent端会收到此任务的识别结果，number类型的结果示例如下面所示。其中‘‘groupID'’，”frameSeq“，”image“ ，”deviceIndex“。是Agent收到的GameReg进程发过来的图像帧结果的通用字段，”result“对应的是识别结果字段，存储识别结果的数据结构为字典，字典的key值为整型taskid，此值和识别任务的配置文件是一致的(如上文提到的任务的taskid为5)。字典的value值为对应的此任务的识别结果。一个识别任务(task)，可能会有多个元素(Element)组成，所以每个识别任务的结果是个列表，结果列表中的元素对应Element的识别结果。

```
{
	'groupID': int,
	'frameSeq': int,
	'image': mat,
	'deviceIndex': int,
	'result':
	{
		// taskID: result
		5: 
		[
			{
				# 如果当前Element没有识别数字，则flag为False。否则为True.
				'flag': bool,
				# 'num'为对应的数字值
				'num': float,
				# 检测数字的区域，为配置文件中的检测区域
				'x': int,
				'y': int,
				'w': int,
				'h': int
			}
		]
	}
}
```



### 2 number类型识别任务解析示例代码

GameReg进程把识别结果发送到共享内存中，Agent进程通过平台内置的AgentAPIMgr接收结果包，解析结果包中的类型为‘number'的任务的主要代码示例如下。

```
NUMBER_TASK_ID = 5

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

    # 获取类型为'number'的任务的结果
    def GetNumberState(self, taskResult):
        state = False
        number = -1
        if taskResult is None:
            return (state, number)

        for item in taskResult:
            # 如果当前Element没有识别数字，则flag为False。否则为True.
            flag = item['flag']
            if flag:
                number = int(item['num'])
                state = True
                break
        
        return (state, number)
            
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
                
			# 获取NUMBER_TASK_ID对应的任务的结果
            numberResult =  result.get(NUMBER_TASK_ID)
            # 解析NUMBER_TASK_ID对应的任务的结果
            state, number = self.GetNumberState(numberResult)
            # 根据需求做相应的处理
            break
            
    def IsEpisodeStart(self):
        return True

    def IsEpisodeOver(self):
        return False
                
```