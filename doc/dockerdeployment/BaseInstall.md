# 使用docker部署AISDK&SDKTool说明

本方案是以windows和mac环境下的docker部署说明，linux下的可以直接使用原生环境部署。如要使用docker部署AISDK&SDKTool，可以参考mac环境下的部署流程。
基础环境安装指运行AISDK需要的依赖的安装，包括运行AIClient需要的运行环境依赖及采用docker运行AISDK需要安装的额外依赖。
运行AIclient的依赖可以参考AICient运行的环境依赖安装说明【doc/environment/AIClientEnv.md】，本文主要说明采用docker运行AISDK需要依赖的安装。

## 1 部署AISDK依赖安装

### 1.1 安装docker

1. 在docker官网(https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe)下载docker安装包
2. 双击下载的exe文件进行安装
3. 安装成功后，打开docker
4. 在终端输入“docker version”， 显示docker版本，则说明安装成功

## 2 部署SDKTool依赖安装

### 2.1 安装docker

	参见1.1节【安装docker】

### 2.2 安装VcXsrv(windows版本)

VcXsrv是将容器中显示的内容映射到母机上的工具（容器中无法显示，会报错）。
1. 从官网(https://sourceforge.net/projects/vcxsrv/)下载VcXsrv
2. 双击安装即可

### 2.3 安装socat(mac版本)

socat是用于和mac主机之间的通讯，安装如下：
	
	brew install socat     # 可能需要cask命令安装： brew cask install socat

### 2.4 安装xquartz(mac版本)

xquartz是将容器中显示的内容映射到母机上的工具。安装命令：

	brew install xquartz

