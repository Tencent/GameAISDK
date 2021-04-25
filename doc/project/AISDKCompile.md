## 编译AISDK

1.  编译依赖文件（初次使用该AISDK时需要编译）：

	进入AISDK/build目录，执行以下命令：

	```
	./build_modules.sh  {GPU|CPU}
	```

	将会在AISDK/bin目录下生成三个so文件，分别是libtbus.so、libjsoncpp.so、tbus.cpython-35m-x86_64-linux-gnu.so

2.  进入build目录：

	执行./build.sh {GPU|CPU} 编译SDK对应的GPU或CPU版本

	成功编译后，会在game_ai_sdk/bin目录生成下面这些文件  

	如果选择的是 SDKAutoInstall_Ubuntu16.04_cpu 自动安装包
	
	```
	./build.sh CPU
	```

	如果选择的是 SDKAutoInstall_Ubuntu16.04_gpu 自动安装包
	
	```
	./build.sh GPU
	```

3.  成功编译后，会在game_ai_sdk/bin目录生成下面这些文件  

	![img](../img/2019-06-261-23-56img.png)
	
	​图1 编译前的bin目录
	
	![img](../img/2019-06-211-31-04img.png)                                                        
	图2 编译后的bin目录