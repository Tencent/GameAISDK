/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <memory.h>

#include "Comm/Utils/TqcMemoryPool.h"

/************************************************************************/
/* 内存映射表中的索引转化为内存起始地址 */
/************************************************************************/
void* index2addr(PMEMORYPOOL mem_pool, size_t index)
{
    char* p = reinterpret_cast<char*>(mem_pool->memory);
    void* ret = reinterpret_cast<void*>(p + index * MINUNITSIZE);

    return ret;
}

/************************************************************************/
/* 内存起始地址转化为内存映射表中的索引 */
/************************************************************************/
size_t addr2index(PMEMORYPOOL mem_pool, void* addr)
{
    char* start = reinterpret_cast<char*>(mem_pool->memory);
    char* p = reinterpret_cast<char*>(addr);
    size_t index = (p - start) / MINUNITSIZE;
    return index;
}

#if USE_DOUBLE_LINK
/************************************************************************/
/* 内存池起始地址对齐到ADDR_ALIGN字节 */
/************************************************************************/
size_t CheckAlignAddr(void*& pBuf)
{
    size_t align    = 0;
    size_t addr     = *(reinterpret_cast<int*>(pBuf));

    align   = (ADDR_ALIGN - addr % ADDR_ALIGN) % ADDR_ALIGN;
    pBuf    = reinterpret_cast<char*>(pBuf) + align;
    // pBuf = (char*)(((int)pBuf + (ADDR_ALIGN - 1)) & (~(ADDR_ALIGN - 1)));

    return align;
}

/************************************************************************/
/* 内存block大小对齐到MINUNITSIZE字节 */
/************************************************************************/
size_t CheckAlignBlock(size_t size)
{
    size_t align = size % MINUNITSIZE;
    return size - align;
}

/************************************************************************/
/* 分配内存大小对齐到SIZE_ALIGN字节 */
/************************************************************************/
size_t CheckAlignSize(size_t size)
{
    // orig: size = (size + SIZE_ALIGN - 1) / SIZE_ALIGN * SIZE_ALIGN;
    size = (size + SIZE_ALIGN - 1) & (~(SIZE_ALIGN-1));
    return size;
}

/************************************************************************/
/* 以下是链表相关操作 */
/************************************************************************/
memory_chunk* CreateList(memory_chunk* pool, size_t count)
{
    memory_chunk* head = NULL;

    if (!pool)
    {
        return NULL;
    }

    for (size_t i = 0; i < count; i++)
    {
        pool->pre = NULL;
        pool->next = head;
        if (head != NULL)
        {
            head->pre = pool;
        }
        head = pool;
        pool++;
    }

    return head;
}

memory_chunk* front_pop(memory_chunk*& pool)
{
    if (!pool)
    {
        return NULL;
    }
    memory_chunk* tmp = pool;
    pool = tmp->next;
    pool->pre = NULL;
    return  tmp;
}

void push_back(memory_chunk*& head, memory_chunk* element)
{
    if (head == NULL)
    {
        head = element;
        head->pre = element;
        head->next = element;
        return;
    }

    head->pre->next = element;
    element->pre = head->pre;
    head->pre = element;
    element->next = head;
}

void push_front(memory_chunk*& head, memory_chunk* element)
{
    element->pre = NULL;
    element->next = head;

    if (head != NULL)
    {
        head->pre = element;
    }

    head = element;
}

void delete_chunk(memory_chunk*& head, memory_chunk* element)
{
    // 在双循环链表中删除元素
    if (element == NULL)
    {
        return;
    }
    // element为链表头
    else if (element == head)
    {
        // 链表只有一个元素
        if (head->pre == head)
        {
            head = NULL;
        }
        else
        {
            head = element->next;
            head->pre = element->pre;
            head->pre->next = head;
        }
    }
    // element为链表尾
    else if (element->next == head)
    {
        head->pre = element->pre;
        element->pre->next = head;
    }
    else
    {
        element->pre->next = element->next;
        element->next->pre = element->pre;
    }

    element->pre = NULL;
    element->next = NULL;
}

/************************************************************************/
/* 生成内存池
* pBuf: 给定的内存buffer起始地址
* sBufSize: 给定的内存buffer大小
* 返回生成的内存池指针
 */
/************************************************************************/
PMEMORYPOOL CreateMemoryPool(void* pBuf, size_t sBufSize)
{
    PMEMORYPOOL mem_pool = (PMEMORYPOOL)pBuf;
    size_t      mem_pool_struct_size = sizeof(MEMORYPOOL);

    memset(pBuf, 0, sBufSize);

    // 计算需要多少memory map单元格
    mem_pool->mem_map_pool_count    = (sBufSize - mem_pool_struct_size + MINUNITSIZE - 1) / MINUNITSIZE;
    mem_pool->mem_map_unit_count    = (sBufSize - mem_pool_struct_size + MINUNITSIZE - 1) / MINUNITSIZE;
    mem_pool->pmem_map              = reinterpret_cast<memory_block*>(reinterpret_cast<char*>(pBuf) + mem_pool_struct_size);
    mem_pool->pfree_mem_chunk_pool  = reinterpret_cast<memory_chunk*>(reinterpret_cast<char*>(pBuf) +\
                                      mem_pool_struct_size + sizeof(memory_block) * mem_pool->mem_map_unit_count);

    mem_pool->memory = reinterpret_cast<char*>(pBuf) + mem_pool_struct_size+ sizeof(memory_block) *\
                                    mem_pool->mem_map_unit_count + sizeof(memory_chunk) * mem_pool->mem_map_pool_count;
    mem_pool->size = sBufSize - mem_pool_struct_size - sizeof(memory_block) * mem_pool->mem_map_unit_count\
                     - sizeof(memory_chunk) * mem_pool->mem_map_pool_count;
    size_t align = CheckAlignAddr(mem_pool->memory);
    mem_pool->size -= align;
    mem_pool->size = CheckAlignBlock(mem_pool->size);
    mem_pool->mem_block_count = mem_pool->size / MINUNITSIZE;
    // 链表化
    mem_pool->pfree_mem_chunk_pool = CreateList(mem_pool->pfree_mem_chunk_pool, mem_pool->mem_map_pool_count);
    // 初始化 pfree_mem_chunk，双向循环链表
    memory_chunk* tmp = front_pop(mem_pool->pfree_mem_chunk_pool);
    tmp->pre = tmp;
    tmp->next = tmp;
    tmp->pfree_mem_addr = NULL;
    mem_pool->mem_map_pool_count--;

    // 初始化 pmem_map
    mem_pool->pmem_map[0].count = mem_pool->mem_block_count;
    mem_pool->pmem_map[0].pmem_chunk = tmp;
    mem_pool->pmem_map[mem_pool->mem_block_count-1].start = 0;

    tmp->pfree_mem_addr = mem_pool->pmem_map;
    push_back(mem_pool->pfree_mem_chunk, tmp);
    mem_pool->free_mem_chunk_count = 1;
    mem_pool->mem_used_size = 0;
    return mem_pool;
}

/************************************************************************/
/* 暂时没用 */
/************************************************************************/
void ReleaseMemoryPool(PMEMORYPOOL* ppMem)
{
}

/************************************************************************/
/* 从内存池中分配指定大小的内存 
* pMem: 内存池 指针
* sMemorySize: 要分配的内存大小
* 成功时返回分配的内存起始地址，失败返回NULL
 */
/************************************************************************/
void* GetMemory(size_t sMemorySize, PMEMORYPOOL pMem)
{
    sMemorySize = CheckAlignSize(sMemorySize);
    size_t index = 0;
    memory_chunk* tmp = pMem->pfree_mem_chunk;

    for (index = 0; index < pMem->free_mem_chunk_count; index++)
    {
        if (tmp == NULL)
        {
            return NULL;
        }

        if (tmp->pfree_mem_addr->count * MINUNITSIZE >= sMemorySize)
        {
            break;
        }

        tmp = tmp->next;
    }

    if (index == pMem->free_mem_chunk_count)
    {
        return NULL;
    }

    pMem->mem_used_size += sMemorySize;
    if (tmp == NULL)
    {
        return NULL;
    }

    if (tmp->pfree_mem_addr->count * MINUNITSIZE == sMemorySize)
    {
        // 当要分配的内存大小与当前chunk中的内存大小相同时，从pfree_mem_chunk链表中删除此chunk
        size_t current_index = (tmp->pfree_mem_addr - pMem->pmem_map);
        delete_chunk(pMem->pfree_mem_chunk, tmp);
        tmp->pfree_mem_addr->pmem_chunk = NULL;

        push_front(pMem->pfree_mem_chunk_pool, tmp);
        pMem->free_mem_chunk_count--;
        pMem->mem_map_pool_count++;

        return index2addr(pMem, current_index);
    }
    else
    {
        // 当要分配的内存小于当前chunk中的内存时，更改pfree_mem_chunk中相应chunk的pfree_mem_addr

        // 复制当前mem_map_unit
        memory_block copy;
        copy.count = tmp->pfree_mem_addr->count;
        copy.pmem_chunk = tmp;
        // 记录该block的起始和结束索引
        memory_block* current_block = tmp->pfree_mem_addr;
        current_block->count = sMemorySize / MINUNITSIZE;
        size_t current_index = (current_block - pMem->pmem_map);
        pMem->pmem_map[current_index+current_block->count-1].start = current_index;
        current_block->pmem_chunk = NULL; // NULL表示当前内存块已被分配
        // 当前block被一分为二，更新第二个block中的内容
        pMem->pmem_map[current_index+current_block->count].count = copy.count - current_block->count;
        pMem->pmem_map[current_index+current_block->count].pmem_chunk = copy.pmem_chunk;
        // 更新原来的pfree_mem_addr
        tmp->pfree_mem_addr = &(pMem->pmem_map[current_index+current_block->count]);

        size_t end_index = current_index + copy.count - 1;
        pMem->pmem_map[end_index].start = current_index + current_block->count;
        return index2addr(pMem, current_index);
    }
}

/************************************************************************
 * 从内存池中释放申请到的内存
 * pMem：内存池指针
 * ptrMemoryBlock：申请到的内存起始地址
************************************************************************/
void FreeMemory(void *ptrMemoryBlock, PMEMORYPOOL pMem)
{
    size_t current_index = addr2index(pMem, ptrMemoryBlock);
    size_t size = pMem->pmem_map[current_index].count * MINUNITSIZE;

    // 判断与当前释放的内存块相邻的内存块是否可以与当前释放的内存块合并
    memory_block* pre_block = NULL;
    memory_block* next_block = NULL;
    memory_block* current_block = &(pMem->pmem_map[current_index]);

    // 第一个
    if (current_index == 0)
    {
        if (current_block->count < pMem->mem_block_count)
        {
            next_block = &(pMem->pmem_map[current_index+current_block->count]);
            // 如果后一个内存块是空闲的，合并
            if (next_block->pmem_chunk != NULL)
            {
                next_block->pmem_chunk->pfree_mem_addr = current_block;
                pMem->pmem_map[current_index+current_block->count+next_block->count-1].start = current_index;
                current_block->count += next_block->count;
                current_block->pmem_chunk = next_block->pmem_chunk;
                next_block->pmem_chunk = NULL;
            }
            // 如果后一块内存不是空闲的，在pfree_mem_chunk中增加一个chunk
            else
            {
                memory_chunk* new_chunk = front_pop(pMem->pfree_mem_chunk_pool);
                new_chunk->pfree_mem_addr = current_block;
                current_block->pmem_chunk = new_chunk;
                push_back(pMem->pfree_mem_chunk, new_chunk);
                pMem->mem_map_pool_count--;
                pMem->free_mem_chunk_count++;
            }
        }
        else
        {
            memory_chunk* new_chunk = front_pop(pMem->pfree_mem_chunk_pool);
            new_chunk->pfree_mem_addr = current_block;
            current_block->pmem_chunk = new_chunk;
            push_back(pMem->pfree_mem_chunk, new_chunk);
            pMem->mem_map_pool_count--;
            pMem->free_mem_chunk_count++;
        }
    }

    // 最后一个
    else if (current_index == pMem->mem_block_count-1)
    {
        if (current_block->count < pMem->mem_block_count)
        {
            pre_block = &(pMem->pmem_map[current_index-1]);
            size_t index = pre_block->count;
            pre_block = &(pMem->pmem_map[index]);

            // 如果前一个内存块是空闲的，合并
            if (pre_block->pmem_chunk != NULL)
            {
                pMem->pmem_map[current_index+current_block->count-1].start = current_index - pre_block->count;
                pre_block->count += current_block->count;
                current_block->pmem_chunk = NULL;
            }
            // 如果前一块内存不是空闲的，在pfree_mem_chunk中增加一个chunk
            else
            {
                memory_chunk* new_chunk = front_pop(pMem->pfree_mem_chunk_pool);
                new_chunk->pfree_mem_addr = current_block;
                current_block->pmem_chunk = new_chunk;
                push_back(pMem->pfree_mem_chunk, new_chunk);
                pMem->mem_map_pool_count--;
                pMem->free_mem_chunk_count++;
            }
        }
        else
        {
            memory_chunk* new_chunk = front_pop(pMem->pfree_mem_chunk_pool);
            new_chunk->pfree_mem_addr = current_block;
            current_block->pmem_chunk = new_chunk;
            push_back(pMem->pfree_mem_chunk, new_chunk);
            pMem->mem_map_pool_count--;
            pMem->free_mem_chunk_count++;
        }
    }
    else
    {
        next_block          = &(pMem->pmem_map[current_index+current_block->count]);
        pre_block           = &(pMem->pmem_map[current_index-1]);
        size_t index        = pre_block->start;
        pre_block           = &(pMem->pmem_map[index]);
        bool is_back_merge  = false;

        if (next_block->pmem_chunk == NULL && pre_block->pmem_chunk == NULL)
        {
            memory_chunk* new_chunk = front_pop(pMem->pfree_mem_chunk_pool);
            new_chunk->pfree_mem_addr = current_block;
            current_block->pmem_chunk = new_chunk;
            push_back(pMem->pfree_mem_chunk, new_chunk);
            pMem->mem_map_pool_count--;
            pMem->free_mem_chunk_count++;
        }

        // 后一个内存块
        if (next_block->pmem_chunk != NULL)
        {
            next_block->pmem_chunk->pfree_mem_addr = current_block;
            pMem->pmem_map[current_index+current_block->count+next_block->count-1].start = current_index;
            current_block->count += next_block->count;
            current_block->pmem_chunk = next_block->pmem_chunk;
            next_block->pmem_chunk = NULL;
            is_back_merge = true;
        }

        // 前一个内存块
        if (pre_block->pmem_chunk != NULL)
        {
            pMem->pmem_map[current_index+current_block->count-1].start = current_index - pre_block->count;
            pre_block->count += current_block->count;
            if (is_back_merge)
            {
                delete_chunk(pMem->pfree_mem_chunk, current_block->pmem_chunk);
                push_front(pMem->pfree_mem_chunk_pool, current_block->pmem_chunk);
                pMem->free_mem_chunk_count--;
                pMem->mem_map_pool_count++;
            }
            current_block->pmem_chunk = NULL;
        }
    }
    pMem->mem_used_size -= size;
}

#else

/************************************************************************/
/* 以下为大顶堆操作*/
void init_max_heap(size_t max_heap_size, memory_chunk* heap_arr, max_heap* heap)
{
    heap->maxSize = max_heap_size;
    heap->currentSize = 0;
    heap->heap = heap_arr;
}

bool is_heap_empty(max_heap* heap)
{
    return heap->currentSize == 0;
}

bool is_heap_full(max_heap* heap)
{
    return heap->currentSize == heap->maxSize;
}

memory_chunk* filter_up(max_heap* heap, size_t start)
{
    size_t i = start;
    size_t j = (i - 1) / 2;
    memory_chunk temp = heap->heap[i];
    while (i > 0)
    {
        if (temp.chunk_size <= heap->heap[j].chunk_size)
            break;
        else
        {
            heap->heap[i] = heap->heap[j];
            heap->heap[j].pfree_mem_addr->pmem_chunk = &(heap->heap[i]);
            i = j;
            j = (i - 1) / 2;
        }
    }
    heap->heap[i] = temp;
    return &(heap->heap[i]);
}

memory_chunk* filter_down(max_heap* heap, size_t start, size_t endOfHeap)
{
    size_t i = start;
    size_t j = i * 2 + 1;
    memory_chunk temp = heap->heap[i];
    while (j <= endOfHeap)
    {
        if (j < endOfHeap && heap->heap[j].chunk_size < heap->heap[j+1].chunk_size)
            j++;
        if (temp.chunk_size > heap->heap[j].chunk_size)
            break;
        else
        {
            heap->heap[i] = heap->heap[j];
            heap->heap[j].pfree_mem_addr->pmem_chunk = &(heap->heap[i]);
            i = j;
            j = 2 * i + 1;
        }
    }
    heap->heap[i] = temp;
    return &(heap->heap[i]);
}

memory_chunk* insert_heap(const memory_chunk& chunk, max_heap* heap)
{
    if (is_heap_full(heap))
    {
        return NULL;
    }
    heap->heap[heap->currentSize] = chunk;
    memory_chunk* ret = filter_up(heap, heap->currentSize);
    heap->currentSize++;
    return ret;
}

bool get_max(memory_chunk*& chunk, max_heap* heap)
{
    if (is_heap_empty(heap))
    {
        return false;
    }
    chunk = heap->heap;
    return true;
}

bool remove_max(max_heap* heap)
{
    if (is_heap_empty(heap))
    {
        return false;
    }
    heap->heap[0] = heap->heap[heap->currentSize - 1];
    heap->currentSize--;
    if (heap->currentSize > 0)
    {
        filter_down(heap, 0, heap->currentSize-1);
    }
    return true;
}

void remove_element(memory_chunk* chunk, max_heap* heap)
{
    // 删除某个非max元素有两步组成：
    // 1. 将该元素size增至最大（大于max element），然后将其上移至堆顶；
    // 2. 删除堆顶元素
    size_t index = chunk - heap->heap;
    chunk->chunk_size = MAXCHUNKSIZE;
    filter_up(heap, index);
    remove_max(heap);
}

memory_chunk* increase_element_value(memory_chunk* chunk, max_heap* heap, size_t increase_value)
{
    size_t index = chunk - heap->heap;
    chunk->chunk_size += increase_value;
    return filter_up(heap, index);
}

memory_chunk* decrease_element_value(memory_chunk* chunk, max_heap* heap, size_t decrease_value)
{
    size_t index = chunk - heap->heap;
    chunk->chunk_size -= decrease_value;
    return filter_down(heap, index, heap->currentSize-1);
}

/************************************************************************/
/* 内存池起始地址对齐到ADDR_ALIGN字节
/************************************************************************/
size_t check_align_addr(void*& pBuf)
{
    size_t align = 0;
    size_t addr = static_cast<int>(pBuf);
    align = (ADDR_ALIGN - addr % ADDR_ALIGN) % ADDR_ALIGN;
    pBuf = reinterpret_cast<char*>(pBuf) + align;
    return align;
}

/************************************************************************/
/* 内存block大小对齐到MINUNITSIZE字节
/************************************************************************/
size_t check_align_block(size_t size)
{
    size_t align = size % MINUNITSIZE;

    return size - align;
}

/************************************************************************/
/* 分配内存大小对齐到SIZE_ALIGN字节
/************************************************************************/
size_t check_align_size(size_t size)
{
    size = (size + SIZE_ALIGN - 1) / SIZE_ALIGN * SIZE_ALIGN;
    return size;
}

/************************************************************************/
/* 生成内存池
* pBuf: 给定的内存buffer起始地址
* sBufSize: 给定的内存buffer大小
* 返回生成的内存池指针
/************************************************************************/
PMEMORYPOOL CreateMemoryPool(void* pBuf, size_t sBufSize)
{
    memset(pBuf, 0, sBufSize);
    PMEMORYPOOL mem_pool = (PMEMORYPOOL)pBuf;
    // 计算需要多少memory map单元格
    size_t mem_pool_struct_size = sizeof(MEMORYPOOL);
    mem_pool->mem_map_unit_count = (sBufSize - mem_pool_struct_size + MINUNITSIZE - 1) / MINUNITSIZE;
    mem_pool->pmem_map = reinterpret_cast<memory_block*>(reinterpret_cast<char*>(pBuf) + mem_pool_struct_size);
    size_t max_heap_size = (sBufSize - mem_pool_struct_size + MINUNITSIZE - 1) / MINUNITSIZE;
    memory_chunk* heap_arr = reinterpret_cast<memory_chunk*>(reinterpret_cast<char*>(pBuf) +\
                             mem_pool_struct_size + sizeof(memory_block) * mem_pool->mem_map_unit_count);

    mem_pool->memory = reinterpret_cast<char*>(pBuf) + mem_pool_struct_size+ sizeof(memory_block) * \
                       mem_pool->mem_map_unit_count + sizeof(memory_chunk) * max_heap_size;
    mem_pool->size = sBufSize - mem_pool_struct_size - sizeof(memory_block) * mem_pool->mem_map_unit_count\
                     - sizeof(memory_chunk) * max_heap_size;
    size_t align = check_align_addr(mem_pool->memory);
    mem_pool->size -= align;
    mem_pool->size = check_align_block(mem_pool->size);
    mem_pool->mem_block_count = mem_pool->size / MINUNITSIZE;
    init_max_heap(mem_pool->mem_block_count, heap_arr, &(mem_pool->heap));
    memory_chunk chunk;
    chunk.chunk_size = mem_pool->mem_block_count;
    memory_chunk* pos = insert_heap(chunk, &(mem_pool->heap));

    // 初始化 pmem_map
    mem_pool->pmem_map[0].count = mem_pool->mem_block_count;
    mem_pool->pmem_map[0].pmem_chunk = pos;
    mem_pool->pmem_map[mem_pool->mem_block_count-1].start = 0;

    pos->pfree_mem_addr = mem_pool->pmem_map;
    mem_pool->mem_used_size = 0;
    return mem_pool;
}

/************************************************************************/
/* 暂时没用
/************************************************************************/
void ReleaseMemoryPool(PMEMORYPOOL* ppMem)
{
}

/************************************************************************/
/* 从内存池中分配指定大小的内存 
* pMem: 内存池 指针
* sMemorySize: 要分配的内存大小
* 成功时返回分配的内存起始地址，失败返回NULL
/************************************************************************/
void* GetMemory(size_t sMemorySize, PMEMORYPOOL pMem)
{
    sMemorySize = check_align_size(sMemorySize);
    size_t index = 0;
    memory_chunk* max_chunk;
    bool ret = get_max(max_chunk, &(pMem->heap));
    if (ret == false || max_chunk->chunk_size * MINUNITSIZE < sMemorySize)
    {
        printf("%d\n", ret);
        printf("%d\n", max_chunk->chunk_size);
        return NULL;
    }
    pMem->mem_used_size += sMemorySize;
    if (max_chunk->chunk_size * MINUNITSIZE == sMemorySize)
    {
        // 当要分配的内存大小与当前chunk中的内存大小相同时，从pfree_mem_chunk链表中删除此chunk
        size_t current_index = (max_chunk->pfree_mem_addr - pMem->pmem_map);
        remove_max(&(pMem->heap));

        return index2addr(pMem, current_index);
    }
    else
    {
        // 当要分配的内存小于当前chunk中的内存时，更改pfree_mem_chunk中相应chunk的pfree_mem_addr

        // 复制当前mem_map_unit
        memory_block copy;
        copy.count = max_chunk->pfree_mem_addr->count;
        copy.pmem_chunk = max_chunk;
        // 记录该block的起始和结束索引
        memory_block* current_block = max_chunk->pfree_mem_addr;
        current_block->count = sMemorySize / MINUNITSIZE;
        size_t current_index = (current_block - pMem->pmem_map);
        pMem->pmem_map[current_index+current_block->count-1].start = current_index;
        current_block->pmem_chunk = NULL; // NULL表示当前内存块已被分配
        // 当前block被一分为二，更新第二个block中的内容
        memory_chunk* pos = decrease_element_value(max_chunk, &(pMem->heap), current_block->count);
        pMem->pmem_map[current_index+current_block->count].count = copy.count - current_block->count;
        pMem->pmem_map[current_index+current_block->count].pmem_chunk = pos;
        // 更新原来的pfree_mem_addr
        pos->pfree_mem_addr = &(pMem->pmem_map[current_index+current_block->count]);

        size_t end_index = current_index + copy.count - 1;
        pMem->pmem_map[end_index].start = current_index + current_block->count;
        return index2addr(pMem, current_index);
    }
}
/************************************************************************/
/* 从内存池中释放申请到的内存
* pMem：内存池指针
* ptrMemoryBlock：申请到的内存起始地址
/************************************************************************/
void FreeMemory(void *ptrMemoryBlock, PMEMORYPOOL pMem)
{
    size_t current_index = addr2index(pMem, ptrMemoryBlock);
    size_t size = pMem->pmem_map[current_index].count * MINUNITSIZE;
    // 判断与当前释放的内存块相邻的内存块是否可以与当前释放的内存块合并
    memory_block* pre_block = NULL;
    memory_block* next_block = NULL;
    memory_block* current_block = &(pMem->pmem_map[current_index]);
    // 第一个
    if (current_index == 0)
    {
        if (current_block->count < pMem->mem_block_count)
        {
            next_block = &(pMem->pmem_map[current_index+current_block->count]);
            // 如果后一个内存块是空闲的，合并
            if (next_block->pmem_chunk != NULL)
            {
                memory_chunk* pos = increase_element_value(next_block->pmem_chunk, &(pMem->heap), current_block->count);
                pos->pfree_mem_addr = current_block;
                pMem->pmem_map[current_index+current_block->count+next_block->count-1].start = current_index;
                current_block->count += next_block->count;
                current_block->pmem_chunk = pos;
                next_block->pmem_chunk = NULL;
            }
            // 如果后一块内存不是空闲的，在pfree_mem_chunk中增加一个chunk
            else
            {
                memory_chunk new_chunk;
                new_chunk.chunk_size = current_block->count;
                new_chunk.pfree_mem_addr = current_block;
                memory_chunk* pos = insert_heap(new_chunk, &(pMem->heap));
                current_block->pmem_chunk = pos;
            }
        }
        else
        {
            memory_chunk new_chunk;
            new_chunk.chunk_size = current_block->count;
            new_chunk.pfree_mem_addr = current_block;
            memory_chunk* pos = insert_heap(new_chunk, &(pMem->heap));
            current_block->pmem_chunk = pos;
        }
    }

    // 最后一个
    else if (current_index == pMem->mem_block_count-1)
    {
        if (current_block->count < pMem->mem_block_count)
        {
            pre_block = &(pMem->pmem_map[current_index-1]);
            size_t index = pre_block->count;
            pre_block = &(pMem->pmem_map[index]);

            // 如果前一个内存块是空闲的，合并
            if (pre_block->pmem_chunk != NULL)
            {
                memory_chunk* pos = increase_element_value(pre_block->pmem_chunk, &(pMem->heap), current_block->count);
                pre_block->pmem_chunk = pos;
                pMem->pmem_map[current_index+current_block->count-1].start = current_index - pre_block->count;
                pre_block->count += current_block->count;
                current_block->pmem_chunk = NULL;
            }
            // 如果前一块内存不是空闲的，在pfree_mem_chunk中增加一个chunk
            else
            {
                memory_chunk new_chunk;
                new_chunk.chunk_size = current_block->count;
                new_chunk.pfree_mem_addr = current_block;
                memory_chunk* pos = insert_heap(new_chunk, &(pMem->heap));
                current_block->pmem_chunk = pos;
            }
        }
        else
        {
            memory_chunk new_chunk;
            new_chunk.chunk_size = current_block->count;
            new_chunk.pfree_mem_addr = current_block;
            memory_chunk* pos = insert_heap(new_chunk, &(pMem->heap));
            current_block->pmem_chunk = pos;
        }
    }
    else
    {
        next_block = &(pMem->pmem_map[current_index+current_block->count]);
        pre_block = &(pMem->pmem_map[current_index-1]);
        size_t index = pre_block->start;
        pre_block = &(pMem->pmem_map[index]);
        bool is_back_merge = false;
        if (next_block->pmem_chunk == NULL && pre_block->pmem_chunk == NULL)
        {
            memory_chunk new_chunk;
            new_chunk.chunk_size = current_block->count;
            new_chunk.pfree_mem_addr = current_block;
            memory_chunk* pos = insert_heap(new_chunk, &(pMem->heap));
            current_block->pmem_chunk = pos;
        }
        // 后一个内存块
        if (next_block->pmem_chunk != NULL)
        {
            memory_chunk* pos = increase_element_value(next_block->pmem_chunk, &(pMem->heap), current_block->count);
            pos->pfree_mem_addr = current_block;
            pMem->pmem_map[current_index+current_block->count+next_block->count-1].start = current_index;
            current_block->count += next_block->count;
            current_block->pmem_chunk = pos;
            next_block->pmem_chunk = NULL;
            is_back_merge = true;
        }
        // 前一个内存块
        if (pre_block->pmem_chunk != NULL)
        {
            pMem->pmem_map[current_index+current_block->count-1].start = current_index - pre_block->count;
            pre_block->count += current_block->count;
            memory_chunk* pos = increase_element_value(pre_block->pmem_chunk, &(pMem->heap), current_block->count);
            pre_block->pmem_chunk = pos;
            pos->pfree_mem_addr = pre_block;
            if (is_back_merge)
            {
                remove_element(current_block->pmem_chunk, &(pMem->heap));
            }
            current_block->pmem_chunk = NULL;
        }
    }
    pMem->mem_used_size -= size;
}

#endif

CGameRegMemPool::CGameRegMemPool()
{
    uCount = 0;
    m_pMemPool = NULL;
    m_MemPoolLock = TqcOsCreateMutex();
}

CGameRegMemPool::~CGameRegMemPool()
{
    TqcOsDeleteMutex(m_MemPoolLock);
}

int CGameRegMemPool::CreateMemPool(size_t sBufSize)
{
    void *pBuf = malloc(sBufSize);

    if (pBuf == NULL)
    {
        return -1;
    }
    else
    {
        m_pMemPool = CreateMemoryPool(pBuf, sBufSize);
        return 0;
    }
}

void CGameRegMemPool::DestroyMemPool()
{
    LOGI("ucount: %d", uCount);
    ReleaseMemoryPool(&m_pMemPool);
    TqcOsDeleteMutex(m_MemPoolLock);
}
