import platform
__is_windows_system = platform.platform().lower().startswith('window')
__is_linux_system = platform.platform().lower().startswith('linux')
if __is_windows_system:
    from .demo_windows.PlatformWeTest import PlatformWeTest
elif __is_linux_system:
    from .demo_ubuntu16.PlatformWeTest import PlatformWeTest
else:
    raise Exception('system is not support!')

def GetInstance():
    return PlatformWeTest()