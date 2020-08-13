# SDKTool部署说明

[TOC]

## 1 windows环境安装

### 1.1 安装python

​	如果本机已经安装 **python3.6.2**，则可以跳过此步骤

​      进入python官网https://www.python.org/downloads/

​      选择python3.6.2，如图所示：

![img](../img/ENV/python_install.png)

​      点击后拉到底部，选择安装包，如图所示：

![img](../img/ENV/python_windows.png)

​         之后打开安装文件，根据提示安装即可。

 

### 1.2 安装环境依赖

如果本机已经有python的环境，建议安装虚拟环境，进行环境隔离。通过以下命令安装虚拟环境。

```
pip install virtualenv //安装virtualenv
virtualenv env //创建虚拟环境，虚拟环境命名为"env"
env\Scripts\activate         // 进入虚拟环境
```

如果没有安装AI SDK的相关依赖，需要先安装相关依赖：

```
cd {path to AISDK} //进入到SDK目录
pip install -r requirements.txt // 安装依赖
```

如果没有安装SDKTool的相关依赖，需要安装SDKTool的相关依赖：

`cd {path to AISDK} //进入到SDK目录`

`pip install -r requirements_SDKTool.txt // 安装依赖`

