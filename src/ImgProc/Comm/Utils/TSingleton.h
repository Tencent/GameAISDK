/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_TSINGLETON_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_TSINGLETON_H_

#include <stdlib.h>
#include <memory>

/*!
  @class : TSingleton
  @brief : 实现对象实例全局唯一
*/
template<class T>
class TSingleton {
  public:
    static T* getInstance();

  protected:
    TSingleton(const TSingleton&) {}
    TSingleton&operator=(const TSingleton&) {}
    TSingleton() {}
    virtual ~TSingleton() {}

    static std::shared_ptr<T>&instance() {
        // 采用std标准库中的轻量级智能指针实现单件对象管理
        static std::shared_ptr<T> pInstance;

        return pInstance;
    }
};

template<class T>
T*TSingleton<T>::getInstance() {
    std::shared_ptr<T> &rInstance = instance();

    // Double-checked
    if (NULL == rInstance.get()) {
        if (NULL == rInstance.get()) {
            // 不使用instance().reset(new T),防止在编译器优化的情况下
            // 出现先将智能指针赋值，再进行构造
            std::shared_ptr<T> _au(new T);
            rInstance = _au;
        }
    }

    return rInstance.get();
}

#define DECLARE_SINGLETON_CLASS(type) \
    friend class std::shared_ptr<type>; \
    friend class TSingleton<type>;

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_TSINGLETON_H_
