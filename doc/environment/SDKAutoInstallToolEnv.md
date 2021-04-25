# SDK环境自动部署工具说明

SDK环境自动部署工具是一个shell脚本，让用户能够自动化得部署SDK的环境，减少人力以及错误率。



## 1 目录结构

以Ubuntu16.04的包为例：

```
|-----SDKAutoInstall_Ubuntu16.04_cpu
|-----|-----AutoDeploy_first.sh-------------------------------------------------用于安装cuda（暂时不用）
|-----|-----AutoDeploy_Ubuntu16.04.sh------------------------------------在线自动部署脚本
|-----|----- cuda-repo-ubuntu1604_9.0.176-1_amd64.deb--------------用于安装cuda
|-----|----- cudnn7.0.tar.gz---------------------------------cudnn库文件
|-----|----- opencv3.4.2.tar.gz-------------------------------------------opencv库文件
|-----|----- protobuf-3.2.0.so.tar.gz-------------------------------------------PB库文件
|-----|-----tensorflow_gpu-1.8.0-cp35-cp35m-linux_x86_64.whl-----tensorflow包
```

 

## 2  使用步骤

SDKAutoInstallTool地址如下：https://aitest.qq.com./api/download/autotool/?version=SDKAutoInstall_tool&file=SDKAutoInstall_tool.zip
根据操作系统版本下载对应工具包。在连接外网正常时使用工具，将工具包解压后进入工具目录，以SDKAutoInstall_Ubuntu16.04_cpu 包为例 执行自动部署脚本：

```
cd SDKAutoInstall_Ubuntu16.04_cpu
dos2unix AutoDeploy_Ubuntu16.04.sh
chmod +x AutoDeploy_Ubuntu16.04.sh
./AutoDeploy_Ubuntu16.04.sh
```

当提示Done时，说明环境搭建成功，重启电脑。

```
sudo reboot
```

若出现错误，会提示执行出错的命令，可以单独运行命令来排查错误，重新运行脚本后，会从出错的地方开始执行。

若出现如下错误：

```
W: GPG error: http://security.ubuntu.com trusty-security Release: The following signatures couldn’t be verified because the public key is not available: NO_PUBKEY 40976EAF437D05B5
```

则说明缺少公钥，执行如下命令，注意红色字体，要和报错的一致：

```
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 40976EAF437D05B5
```

若出现如下错误：

```
W: GPG 错误：http://extras.ubuntu.com trusty Release: 下列签名无效： BADSIG 16126D3A3E5C1192 Ubuntu Extras Archive Automatic Signing Key <ftpmaster@ubuntu.com
```

则执行如下命令：

```
sudo apt-get clean
cd /var/lib/apt
sudo mv lists lists.old
sudo mkdir -p lists/partial
sudo apt-get clean
sudo apt-get update
```

 

