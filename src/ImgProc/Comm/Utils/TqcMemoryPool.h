/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TQC_MEMORY_POOL_H_
#define TQC_MEMORY_POOL_H_

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcLog.h"
#include "Comm/Utils/TSingleton.h"

#define USE_DOUBLE_LINK         1

#if USE_DOUBLE_LINK
#define MINUNITSIZE             64
#define ADDR_ALIGN              8
#define SIZE_ALIGN              MINUNITSIZE

struct memory_chunk;
typedef struct memory_block
{
    size_t          count;
    size_t          start;
    memory_chunk*   pmem_chunk;
} memory_block;

// 可用的内存块结构体
typedef struct memory_chunk
{
    memory_block*   pfree_mem_addr;
    memory_chunk*   pre;
    memory_chunk*   next;
} memory_chunk;

// 内存池结构体
typedef struct MEMORYPOOL
{
    void            *memory;
    size_t          size;
    memory_block*   pmem_map;
    memory_chunk*   pfree_mem_chunk;
    memory_chunk*   pfree_mem_chunk_pool;
    size_t          mem_used_size;              // 记录内存池中已经分配给用户的内存的大小
    size_t          mem_map_pool_count;         // 记录链表单元缓冲池中剩余的单元的个数，个数为0时不能分配单元给pfree_mem_chunk
    size_t          free_mem_chunk_count;       // 记录 pfree_mem_chunk链表中的单元个数
    size_t          mem_map_unit_count;         //
    size_t          mem_block_count;            // 一个 mem_unit 大小为 MINUNITSIZE
} MEMORYPOOL, *PMEMORYPOOL;

/************************************************************************/
/* 生成内存池
 * pBuf: 给定的内存buffer起始地址
 * sBufSize: 给定的内存buffer大小
 * 返回生成的内存池指针
 */
/************************************************************************/
PMEMORYPOOL CreateMemoryPool(void* pBuf, size_t sBufSize);

/************************************************************************/
/* 暂时没用 */
/***********************************************************************/
void ReleaseMemoryPool(PMEMORYPOOL* ppMem);

/************************************************************************/
/* 从内存池中分配指定大小的内存
 * pMem: 内存池 指针
 * sMemorySize: 要分配的内存大小
 * 成功时返回分配的内存起始地址，失败返回NULL
 */
/************************************************************************/
void* GetMemory(size_t sMemorySize, PMEMORYPOOL pMem);

/************************************************************************/
/* 从内存池中释放申请到的内存
 * pMem：内存池指针
 * ptrMemoryBlock：申请到的内存起始地址
 */
/************************************************************************/
void FreeMemory(void *ptrMemoryBlock, PMEMORYPOOL pMem);

#else

#define _MEMORYPOOL_H
#include <stdlib.h>
#define MINUNITSIZE 64
#define ADDR_ALIGN 8
#define SIZE_ALIGN MINUNITSIZE
#define MAXCHUNKSIZE 1024*1024*64
struct memory_chunk;
typedef struct memory_block
{
    size_t count;
    size_t start;
    memory_chunk* pmem_chunk;
}memory_block;
typedef struct memory_chunk
{
    size_t chunk_size;
    memory_block* pfree_mem_addr;
}memory_chunk;
typedef struct max_heap
{
    memory_chunk *heap;
    size_t maxSize;
    size_t currentSize;
}max_heap;
typedef struct MEMORYPOOL
{
    void *memory;
    size_t size;
    memory_block* pmem_map;
    max_heap heap;
    size_t mem_used_size; // 记录内存池中已经分配给用户的内存的大小
    size_t free_mem_chunk_count; // 记录 pfree_mem_chunk链表中的单元个数
    size_t mem_map_unit_count; //
    size_t mem_block_count; // 一个 mem_unit 大小为 MINUNITSIZE
}MEMORYPOOL, *PMEMORYPOOL;
/************************************************************************/
/* 生成内存池
* pBuf: 给定的内存buffer起始地址
* sBufSize: 给定的内存buffer大小
* 返回生成的内存池指针
/************************************************************************/
PMEMORYPOOL CreateMemoryPool(void* pBuf, size_t sBufSize);
/************************************************************************/
/* 暂时没用
/************************************************************************/
void ReleaseMemoryPool(PMEMORYPOOL* ppMem);
/************************************************************************/
/* 从内存池中分配指定大小的内存
* pMem: 内存池 指针
* sMemorySize: 要分配的内存大小
* 成功时返回分配的内存起始地址，失败返回NULL
/************************************************************************/
void* GetMemory(size_t sMemorySize, PMEMORYPOOL pMem);
/************************************************************************/
/* 从内存池中释放申请到的内存
* pMem：内存池指针
* ptrMemoryBlock：申请到的内存起始地址
/************************************************************************/
void FreeMemory(void *ptrMemoryBlock, PMEMORYPOOL pMem);

#endif

/*!
 * CGameRegMemPool，单例
 * 内存池的封装，支持对象内存分配
 */
class CGameRegMemPool : public TSingleton<CGameRegMemPool>
{
public:
    CGameRegMemPool();
    ~CGameRegMemPool();

    /*!
     * @brief 创建内存池
     * @param sBufSize
     * @return 0成功，-1失败
     */
    int CreateMemPool(size_t sBufSize);

    /*!
     * 回收内存池
     */
    void DestroyMemPool();

    /*!
     * @brief 分配内存
     * @tparam T 类型T
     * @param[in] sMemorySize
     * @return T类型指针
     */
    template <typename T>
    T *AllocPoolMemory()
    {
        void *pBuf = NULL;

        TqcOsAcquireMutex(m_MemPoolLock);
        pBuf = GetMemory(sizeof(T), m_pMemPool);
        T *pT = new(pBuf)T();
        uCount++;
        TqcOsReleaseMutex(m_MemPoolLock);

        return pT;
    }

    /*!
     * @brief 回收内存
     * @tparam T 类型T
     * @param[in] ptrMemoryBlock 对象地址
     */
    template <typename T>
    void FreePoolMemory(T *ptrMemoryBlock)
    {
        if (ptrMemoryBlock == NULL)
        {
            LOGE("memory block is NULL");
            return;
        }

        TqcOsAcquireMutex(m_MemPoolLock);
        ptrMemoryBlock->~T();
        FreeMemory(reinterpret_cast<void *>(ptrMemoryBlock), m_pMemPool);
        uCount--;
        TqcOsReleaseMutex(m_MemPoolLock);
    }

private:
    PMEMORYPOOL m_pMemPool;      // 内存池
    LockerHandle m_MemPoolLock;  // 锁
    unsigned int uCount;         // 用于调试
};


// void    CreateEventMemPool();
// void    DestroyEventMemPool();
// void*   AllocateEventMemory(TCGuint size, TCGbool *pbUsePool);
// void    ReleaseEventMemory(void *p, TCGbool bUsePool);
//
// #define TCG_TEX_MEM_CACHE_SIZE          (6*1024*1024)
// #define TCG_TEX_MEM_SINGLE_SIZE         (4*1024*1024)
// #define TCG_TEX_MEM_POOL_SIZE           (TCG_TEX_MEM_CACHE_SIZE+TCG_TEX_MEM_SINGLE_SIZE)
//
// void    CreateTexMemPool();
// void    DestroyTexMemPool();
// void  * AllocateTexMemory(TCGuint size, TCGbool *pbUsePool);
// void    ReleaseTexMemory(void *p, TCGbool bUsePool);

#endif // TQC_MEMORY_POOL_H_
