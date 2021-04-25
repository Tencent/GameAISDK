# rainbow server部署

rainbow 部署方式有两种, 一种是本地部署(不支持在windows环境部署), 一种是镜像部署

## 1 本地部署

### 1.1 ubuntu 环境下部署

如果本机已经有python的环境，建议安装虚拟环境，进行环境隔离。

如果已经通过自动部署工具部署环境，则已经安装虚拟环境。通过以下命令，进行安装。

```
workon game_ai_sdk
```

如果不是通过自动部署工具部署环境，建议创建一个新的环境。

```
pip install virtualenv         // 如果权限不够，则加上sudo
virtualenv -p /usr/bin/python3 env // 创建虚拟环境，虚拟环境命名为"env"
source env/bin/activate         // 进入虚拟环境
```
如果Rainbow Server运行与sdktool是部署在相同的机器上,则不需要安装环境依赖.

如果Rainbow Server运行与sdktool是部署在不同的机器上, 需要安装Rainbow Server运行的依赖

安装依赖如下:

进入进入Rainbow Server目录, 执行命令:

```
cd Modules/rainbow/server
pip install -r requirements.txt

```

进入Rainbow Server目录，运行Rainbow Server。

```
cd Modules/rainbow/server  // 进入到Rainbow Server目录下
python main.py    // 启动Rainbow Server
```

## 2 镜像部署

### 2.1 获取镜像

1. 访问下载标题下的Rainbow模型server安装包, 点击安装包链接下载,下载地址:

https://aitest.qq.com./api/download/sdk/compile/?version=aisdk_v2.0.0&file=rainbow_server.tar

压缩包名称为: rainbow_server.tar

2. 如果目标机器上没有安装docker, 请安装docker

3. 执行命令 docker load < rainbow_server.tar 加载镜像, 加载完毕后, 会出现进行一条进行记录, 类似如下记录:

rainbow_server    latest    f326ebd1ea18        2 months ago        3.28GB

其中f326ebd1ea18是镜像ID

4. 执行命令 docker run -it -p nodePort:containerPort 镜像ID (如: 步骤6中的f326ebd1ea18) 启动镜像, 其中nodePort是母机的端口, containerPort容器端口, containerPort 默认是8888

## 3 端口修改

### 3.1 端口修改

如果端口被占用的情况:

1. 本地运行的情况直接修改cfg/server.ini文件中Port配置。

2. 如果是镜像方式的话,则先基于镜像运行起来, 修改cfg/server.ini文件中Port配置, 然后保存为新的镜像, 然后基于新的镜像运行