# 使用docker运行AISDK&SDKTool的使用说明

使用docker运行AISDK的方式是：将AISDK运行在容器中，而消费AISDK服务的AiClient依旧运行在母机上。
使用docker运行SDKTool的方式是：将SDKTool和AISDK运行在容器中，SDKTool内容UI通过显示重定向的方式显示到母机上。

## 1 使用docker运行AISDK的使用说明

### 1.1 使用docker运行AISDK步骤

1. 下载AISDK镜像
	
		docker pull 836304831/aisdk:tagname   # tagname 换成实际的名称

2. 配置docker到母机的共享目录（windows下需要配置，mac和linux无需配置）
    docker->setting->Resources->FILE SHARING, 如设置路径为：E:\docker_share
    
3. 下载GAMEAISDK项目工程
    将GAMEAISDK项目下载到docker共享目录 E:\docker_share
    	git clone https://github.com/Tencent/GameAISDK.git
4. 运行docker容器
        docker run -v E:\\docker_share\\game_ai_sdk:/data1/game_ai_sdk -it -p 8898:8898 -p 8899:8899 836304831/aisdk:tagname /bin/bash
        
5. 编译GAMEAISDK
在容器中执行
    
        cd /data1/game_ai_sdk/build
        ./build_modules.sh {GPU|CPU}    #  参数CPU或GPU依赖自身环境决定
        ./build.sh {GPU|CPU}            #  参数CPU或GPU依赖自身环境决定
6. 启动AISDK服务
在容器中执行
        cd /data1/game_ai_sdk/bin
        ./start_ui_ai.sh                #  可选：./start_ai.sh ./start_ui.sh
7. 启动AiClient
在母机中启动AiClient消费AISDK服务，AiClient的操作参考【doc/environment/AIClientEnv.md】



## 2 使用docker运行SDKTool的使用说明

### 2.1 windows下使用docker运行SDKTool步骤

1. 下载SDKTool镜像
	
		docker pull 836304831/sdktool:tagname   # tagname 换成实际的名称

2. 配置docker到母机的共享目录
    docker->setting->Resources->FILE SHARING, 如设置路径为：E:\docker_share
    
3. 下载GAMEAISDK项目工程
    将GAMEAISDK项目下载到docker共享目录 E:\docker_share
    	git clone https://github.com/Tencent/GameAISDK.git

3. 打开VcXsrv
在母机上打开已经安装的VcXsrv

4. 运行docker容器
        docker run -v E:\\docker_share\\game_ai_sdk:/data1/game_ai_sdk -it -p 8898:8898 -p 8899:8899 836304831/aisdk:tagname /bin/bash
        
5. 编译GAMEAISDK(SDKTool中集成了AISDK的功能，编译好之后可以在SDKTool中使用)
在容器中执行
    
        cd /data1/game_ai_sdk/build
        ./build_modules.sh {GPU|CPU}    #  参数CPU或GPU依赖自身环境决定
        ./build.sh {GPU|CPU}            #  参数CPU或GPU依赖自身环境决定

6. 启动SDKTool服务
在容器中执行
        cd /data1/game_ai_sdk/tool/SDKTool
        python main.py
启动之后，母机上会显示SDKTool的ui，之后就可以进行游戏配置相关工作了

### 2.2 mac下使用docker运行SDKTool步骤

1. 下载SDKTool镜像
	
		docker pull 836304831/sdktool:tagname   # tagname 换成实际的名称
 
2. 下载GAMEAISDK项目工程
    将GAMEAISDK项目下载到制定目录,如：/Users/{username}/workspace_code
    	git clone https://github.com/Tencent/GameAISDK.git

3. 启动socat
在母机终端启动socat
        socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\"

4. 启动xquartz
在母机终端启动xquartz
        open -a xquartz

5. 运行docker容器
        docker run -v /Users/{username}/workspace_code/game_ai_sdk:/data1/game_ai_sdk -it -p 8898:8898 -p 8899:8899 836304831/aisdk:tagname /bin/bash
        
6. 编译GAMEAISDK(SDKTool中集成了AISDK的功能，编译好之后可以在SDKTool中使用)
在容器中执行
    
        cd /data1/game_ai_sdk/build
        ./build_modules.sh {GPU|CPU}    #  参数CPU或GPU依赖自身环境决定
        ./build.sh {GPU|CPU}            #  参数CPU或GPU依赖自身环境决定

7. 启动SDKTool服务
在容器中执行
        cd /data1/game_ai_sdk/tool/SDKTool
        python main.py
启动之后，母机上会显示SDKTool的ui，之后就可以进行游戏配置相关工作了
