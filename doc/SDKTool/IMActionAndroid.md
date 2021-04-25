# Android手机定义动作

这里以TTKP为例  
- TTKP需要配置三个动作，滑，跳和一个None。

1. None动作类型，即游戏中不做任何动作  

![img](../img/New_SDKTool/ProjectIMTrain/actionNone.png)  

2. click动作类型，即游戏中的滑行动作

![img](../img/New_SDKTool/ProjectIMTrain/actionSlip.png)  

3. click动作类型，即游戏中的跳跃动作

![img](../img/New_SDKTool/ProjectIMTrain/actionJump.jpg) 

· contact:指触点的标识,可以取-1到9的整数。0到9代表动作对应的触点，-1表示不点击

· name:定义动作的名字，可以自己定义

· id:定义动作的id，通常是从0开始的

· type：定义动作的类型，down、up、click、swipe、joystick、key 

path:定义动作范围的图像路径

region:定义动作的范围

sceneTask:关连task任务

配置“定义动作”时，若工具中没有手机画面，可点击工具栏上的连接手机按钮![img](../img/New_SDKTool/ProjectIMTrain/phoneIco.png)

稍等工具中就会出现手机画面，然后选择type类型，双击actionRegion，此时工具中的画面会静止，在静止的画面中框选动作范围，框选完后，双击画面，程序会自动填写path路径，同时也会将配置的图像存储下来