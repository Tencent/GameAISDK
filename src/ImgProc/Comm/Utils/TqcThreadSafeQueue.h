/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef GAMEREG_THREADSAFEQUEUE_H
#define GAMEREG_THREADSAFEQUEUE_H

#include <condition_variable>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <string>

template<class T, class Container = std::queue<T>>
class ThreadSafeQueue {
public:
    ThreadSafeQueue() = default;

    // push操作，加锁实现同步
    template <class Element>
    void Push(Element&& element) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push(std::forward<Element>(element));
        not_empty_cv_.notify_one();
    }

    // pop操作，加锁实现同步
    void WaitAndPop(T *t) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_cv_.wait(lock, [this] {
            return !queue_.empty();
        });

        *t = std::move(queue_.front());
        queue_.pop();
    }

    // WaitAndPop操作，加锁实现同步
    std::shared_ptr<T> WaitAndPop() {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_cv_.wait(lock, [this]() {
            return !queue_.empty();
        });

        std::shared_ptr<T> t_ptr = std::make_shared<T>(queue_.front());
        queue_.pop();

        return t_ptr;
    }

    // TryPop, 非阻塞
    bool TryPop(T *t) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return false;
        }

        *t = std::move(queue_.front());
        queue_.pop();

        return true;
    }

    // TryPop操作，非阻塞
    std::shared_ptr<T> TryPop() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return std::shared_ptr<T>();
        }

        std::shared_ptr<T> t_ptr = std::make_shared<T>(queue_.front());
        queue_.pop();

        return t_ptr;
    }

    // 判断是否为空
    bool IsEmpty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }

private:
    ThreadSafeQueue(const ThreadSafeQueue&) = delete;
    ThreadSafeQueue& operator=(const ThreadSafeQueue&) = delete;
    ThreadSafeQueue(ThreadSafeQueue&&) = delete;
    ThreadSafeQueue& operator=(ThreadSafeQueue&&) = delete;

private:
    Container queue_;

    std::condition_variable not_empty_cv_;
    mutable std::mutex mutex_;
};

#endif // GAMEREG_THREADSAFEQUEUE_H
