## pixel类型识别任务的结果解析

### 1  pixel类型识别任务结果说明

​	如果在识别任务配置文件中有类型为‘pixel’的识别任务，如(taskid为2的识别任务类型为‘fix object’)，那么我们在Agent端会收到此任务的识别结果，pixel类型的结果示例如下面所示。其中‘‘groupID'’，”frameSeq“，”image“ ，”deviceIndex“。是Agent收到的GameReg进程发过来的图像帧结果的通用字段，”result“对应的是识别结果字段，存储识别结果的数据结构为字典，字典的key值为整型taskid，此值和识别任务的配置文件是一致的(如上文提到的任务的taskid为2)。字典的value值为对应的此任务的识别结果。一个识别任务(task)，可能会有多个元素(Element)组成，所以每个识别任务的结果是个列表，结果列表中的元素对应Element的识别结果。

```
{
	'groupID': int,
	'frameSeq': int,
	'image': mat,
	'deviceIndex': int,
	'result':
	{
		// taskID: result
		2: 
		[
			{
				# 是否检测到满足条件的点
				'flag': bool,
				# 满足条件的点的位置（单位：像素）信息
				'points':
				[
					{
						'x': int,
						'y': int
					}
				]	
			}
	 	]
	}
}
```



### 2 pixel类型识别任务解析示例代码

GameReg进程把识别结果发送到共享内存中，Agent进程通过平台内置的AgentAPIMgr接收结果包，解析结果包中的类型为‘pixel’的任务的主要代码示例如下。

```
PIXEL_TASK_ID = 2

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
        
	# 获取类型为'pixel'的任务的结果
    def GetPixelTaskState(self, taskResult):
        state = False
        px = -1
        py = -1 
        if taskResult is None:
            return (state, px, py)

        totalX = 0
        totalY = 0
        totalNum = 0
        # 依次取每个Element的识别结果(result)
        for result in taskResult:
        # 如果当前Element没有找到符合R,G,B三通道筛选条件的点，则flag为False,'points'的值为空 
            if result['flag'] is False:
                continue
            state = result['flag']
            points = result['points']

            # 以第一个满足条件的Element为例，解析'points'的值，可根据需求更改
            for point in points:
                # 获取'x','y'的值
                x = point['x']
                y = point['y']
                totalX += x
                totalY += y
                totalNum += 1

            if totalNum > 0:
                px = totalX / totalNum
                py = totalY / totalNum
                break

        return (state, px, py)

                
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
                
			# 获取PIXEL_TASK_ID对应的任务的结果
            regResults = result.get(PIXEL_TASK_ID)
            # 解析PIXEL_TASK_ID对应的任务的结果
            state, x, y = self.GetPixelTaskState(regResults)
            # 根据需求做相应的处理
            break      
            
    def IsEpisodeStart(self):
        return True

    def IsEpisodeOver(self):
        return False
```