## fix object类型识别任务的结果解析

### 1  fix object类型识别任务结果说明

​	如果在识别任务配置文件中有类型为‘fix object’的识别任务，如(taskid为1的识别任务类型为‘fix object’)，那么我们在Agent端会收到此任务的识别结果，fix object类型的结果示例如下面所示。其中‘‘groupID'’，”frameSeq“，”image“ ，”deviceIndex“。是Agent收到的GameReg进程发过来的图像帧结果的通用字段，”result“对应的是识别结果字段，存储识别结果的数据结构为字典，字典的key值为整型taskid，此值和识别任务的配置文件是一致的(如上文提到的任务的taskid为1)。字典的value值为对应的此任务的识别结果。一个识别任务(task)，可能会有多个元素(Element)组成，所以每个识别任务的结果是个列表，结果列表中的元素对应Element的识别结果。

```
{
	'groupID': int,
	'frameSeq': int,
	'image': mat,
	'deviceIndex': int,
	'result':
	{
		// taskID: 1 对应的识别类型未"fix object"
		1: 
		[
			{
				// 是否检测到模板区域
				'flag': bool,
				// 模板的搜索区域
				'ROI':
				{
                    'x': int,
					'y': int,
					'w': int,
					'h': int
				},
				// 模板的最终匹配位置，又被称为识别到的位置，可有多个
				'boxes':
				[
					{
						'tmplName': str,
						'score': float,
						'scale': float,
						'classID': int,
						'x': int,
						'y': int,
						'w': int,
						'h': int
					}
				]			
			}
		]
	}
}
```



### 2 fix object类型识别任务解析示例代码

GameReg进程把识别结果发送到共享内存中，Agent进程通过平台内置的AgentAPIMgr接收结果包，解析结果包中的类型为‘fix object’的任务的主要代码示例如下。

```
FIX_OBJECT_TASK_ID = 1

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

    # 获取类型为'fix object'的任务的结果
    def GetFixObjTaskState(self, taskResult):
        state = False
        px = -1
        py = -1
        if taskResult is None:
            return (state, px, py)

        # 依次取每个Element的识别结果(result)
        for result in taskResult:
            flag = result.get('flag')
            state = flag
            # 如果当前Element匹配到模板，则flag为True
            if flag:
                # 'boxes'对应的值为列表，每一项表示一个匹配区域('x', 'y','w', 'h'，单位：像素)
                boxes = result.get('boxes')

                # 以第一个匹配位置('boxes'的第一元素)为例，可根据需求更改
                for box in boxes:
                    x = box.get('x')
                    y = box.get('y')
                    w = box.get('w')
                    h = box.get('h')
                    px = int(x + w / 2)
                    py = int(y + h / 2)
                    break
            else:
                # 如果当前Element没有匹配到模板，则flag为False。'roi'字段为配置的检测区域字段
                roi = result.get('ROI')
                x = roi.get('x')
                y = roi.get('y')
                w = roi.get('w')
                h = roi.get('h')
                px = int(x + w / 2)
                py = int(y + h / 2)
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
                
			# 获取FIXOBJECT_TASK_ID对应的任务的结果
            regResults = result.get(FIX_OBJECT_TASK_ID)
            # 解析FIXOBJECT_TASK_ID对应的任务的结果
            state, px, py = self.GetFixObjTaskState(regResults)
            # 根据需求做相应的处理
            break  
            
    def IsEpisodeStart(self):
        return True

    def IsEpisodeOver(self):
        return False
```