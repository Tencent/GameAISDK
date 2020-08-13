# AIClient工具包下载

- 获取AIClient 工具包代码：

```
cd phone_aiclientapi
git submodule update --init --recursive --remote
cd WrappedDeviceAPI/plugin/Platform_plugin/PlatformWeTest
git checkout ai-dev
git pull
cd -
pip install -r requirements.txt
```

- AIClient 主要目录结构介绍：

```
|-----phone_aiclientapi
|-----|-----aiclient-------------------------------------------负责与AISDK和手机设备通信
|-----|-----tools----------------------------------------------负责预申请资源
|-----|-----WrappedDeviceAPI-----------------------------------连接手机使用的组件
|-----|-----demo.py--------------------------------------------拉起AIClient的脚本
|-----|-----README.md------------------------------------------关于AIClient的使用及环境说明
|-----|-----requirements.txt-----------------------------------记录AIClient运行所需要的依赖包
```
