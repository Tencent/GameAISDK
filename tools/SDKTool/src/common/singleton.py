# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import threading


class Singleton(type):
    # lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            # with Singleton.lock:
            if not hasattr(cls, "_instance"):
                cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance

# test case
if __name__ == "__main__":
    class ClassA(metaclass=Singleton):
        def __init__(self):
            super(ClassA, self).__init__()
            self.x = None
            self.y = dict()


    a1 = ClassA()
    a1.x = 10
    a2 = ClassA()
    a2.y = [1, 1, 2]
    print("addr a1 {}   a2 {}".format(a1, a2))
    print("x: a1 {}, a2 {}".format(a1.x, a2.x))
    print("y: a1 {}, a2 {}".format(a1.y, a2.y))

    class ClassB(metaclass=Singleton):
        def __init__(self):
            super(ClassB, self).__init__()

    b1 = ClassB()
    b2 = ClassB()

    print("b1 {} b2 {}".format(b1, b2))
