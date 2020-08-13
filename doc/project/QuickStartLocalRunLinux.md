## 本地启动

[TOC]

### 1  拉起AI SDK

1)  在终端中进入AI SDK的bin目录下，进入虚拟环境下（虚拟环境是自己创建的，具体方法可以自行查找资料，其中需要安装的依赖包就是AI SDK根目录下requirements.txt的依赖包，如果自己本地的环境没有互相干扰问题，也可以不进入虚拟环境），命令如下：

```
cd AI SDK/bin
workon game_ai_sdk（linux下需要先安装virtualenvwrapper依赖包，然后创建虚拟环境game_ai_sdk，才能使用该命令进入虚拟环境）
```

2) 拉起AI SDK的第一种，使用start脚本拉起（bin目录下），命令如下：

```
./start_ui_ai.sh
```

或只 拉起AISDK的AI服务

`./start_ai.sh`  

3)  拉起AI SDK的第二种，逐个进程拉起(bin目录下)，命令如下：

拉起AI SDK的UI+AI服务

```
python3 io_service.py
python3 agentai.py
python3 manage_center.py --runType=UI+AI   #如果只运行ai，不需要加--runType=UI+AI
./GameReg
./UIRecognize   #如果只运行ai，不需要执行该命令
```

注意：如果运行程序出现“error while loading shared libraries: libdarknetV3_CPU.so: cannot open shared object file: No such file or directory”类似的错误，可以运行一下命令解决：

`vim ~/.bashrc  #打开文件bashrc`

`export LD_LIBRARY_PATH=:/usr/local/lib   #在bashrc文件末尾添加命令`

`source ~/.bashrc  #更新文件bashrc`

### 2  配置phone_aiclient并拉起

- AI SDK/tools/AIClient/aiclient/cfg/network_comm_cfg/communication_cfg.ini

  service设置为2（表示运行UI+AI）

  services设置为1（表示只运行AI）

- AI SDK/tools/AIClient/aiclient/cfg/device_cfg/device.ini

  1） Long_edge修改该参数为640。

  2） is_portrait修改该参数为0

  3） show_raw_screen表示是否在pc中显示手机画面，0不显示，1显示。

- 拉起phone_aiclient

  在终端进入phone_aiclient目录下，在终端中进入虚拟环境下，执行如下命令：

  ```
  workon game_ai_sdk   #（linux下需要先安装virtualenvwrapper依赖包，然后创建虚拟环境game_ai_sdk，才能使用该命令进入虚拟环境）
  python3 demo.py    #拉起phone_aiclient
  ```

