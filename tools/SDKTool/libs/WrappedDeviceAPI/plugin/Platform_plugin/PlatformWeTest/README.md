[TOC]

## get code

```
$ git clone --recursive http://git.code.oa.com/cloud-open-libs/wt-open-component.git
```

## run

### 1) run standalone demo

Please checkout demo branch at first.

```
$ git checkout demo
```

1. connect usb cable with your phone to PC
2. install apk/MultitouchTest_53.apk and run it in the phone
3. run PlatformWeTest.py

Th demo code will use protobuf to communicate with touchserver/cloudscreen.

### 2) run with AI SDK

Please checkout ai-dev branch

```
$ git checkout ai-dev
```

```
PlatformWeTest.init(self, serial=None, is_portrait=True, long_edge=None, **kwargs):
```

- `serial=xxx`
- `is_portrait=True/False`, default is `True`
- `long_edge=1080`, default is `None`
- `standalone=True/False`, default is `True`. if `True`, the SDK will install cloudscreen/touchserver
- `enable_notify=True/False`, default is `False`. if `True`, the SDK will notify WeTestGAssists to capture picture and mark touch point

The code in master is for AI sdk, which need IPlatformProxy.py

## Known issues

- cloudscreen cause high cpu usage

## requirments

1. python 3.X
2. protobuf