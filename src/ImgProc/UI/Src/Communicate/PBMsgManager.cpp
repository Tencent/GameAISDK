/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <bus.h>
#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcLog.h"
#include "Protobuf/common.pb.h"
#include "UI/Src/Communicate/DataComm.h"
#include "UI/Src/Communicate/PBMsgManager.h"

CPBMsgManager g_pbMsgMgr;

CPBMsgManager::CPBMsgManager()
{
    m_bExit       = false;
    m_bTbusEnable = false;
}

CPBMsgManager::~CPBMsgManager()
{
    m_bTbusEnable = false;
}

bool CPBMsgManager::Initialize(void *pTbusData)
{
    // 检查输入参数的合法性
    if (NULL == pTbusData)
    {
        LOGE("Tbus data is NULL");
        return false;
    }

    // 初始化tbus通道
    m_bTbusEnable = InitTBus(pTbusData);
    return m_bTbusEnable;
}

bool CPBMsgManager::InitTBus(void *pInitData)
{
    // 检查输入参数的合法性
    if (NULL == pInitData)
    {
        LOGE("input data is invalid, please check");
        return false;
    }

    stTBUSInitParams                             *pParam = reinterpret_cast<stTBUSInitParams*>(pInitData);
    int                                          nResult = -1;
    std::map<std::string, std::string>::iterator iter;

    // 依次获取通道名和通道地址
    for (iter = pParam->mapStrAddr.begin(); iter != pParam->mapStrAddr.end(); iter++)
    {
        // first:通道名的字符串，second:通道地址的字符串
        std::string strName = iter->first;
        std::string strAddr = iter->second;

        // 通道地址的字符串类型转为数字类型
        int         nAddr;
        // nResult = BusGetAddress(strAddr.c_str(), &nAddr);
        BusGetAddress(strAddr.c_str(), &nAddr);
        m_stTbusParas.mapAddr.insert(std::pair<std::string, int>(strName, nAddr));
    }
    // 依次初始化每个tbus通道
    std::map<std::string, int>::iterator itertmp;
    itertmp = m_stTbusParas.mapAddr.find(pParam->strSelfAddr);
    int nselfAddr = 0;
    if (itertmp != m_stTbusParas.mapAddr.end())
    {
        nselfAddr               = itertmp->second;
        m_stTbusParas.nSelfAddr = nselfAddr;
        // 调用tbus接口初始化
        nResult                 = BusInit(nselfAddr, pParam->szConfigFile);

        if (0 != nResult)
        {
            LOGE("BusInit Failed");
            return false;
        }
        else
        {
            return true;
        }
    }
    else
    {
        LOGE("get self addr failed, self addr name is %s", pParam->strSelfAddr.c_str());
        return false;
    }

    return true;
}

void CPBMsgManager::Release()
{
    // 释放通道资源
    ReleaseTBus();
}

void CPBMsgManager::ReleaseTBus()
{
    // 释放tbus通道资源
    BusExit(m_stTbusParas.nSelfAddr);
}

void CPBMsgManager::LockTbus()
{
    m_tbusAccess.Lock();
}

void CPBMsgManager::UnlockTbus()
{
    m_tbusAccess.UnLock();
}

bool CPBMsgManager::ReceiveMsg(MSG_HANDLER_ROUTINE pHandler, const char *strAddr)
{
    int  nPeerAddr    = -1;
    int  nRet         = 0;
    char *pszRecvBuff = NULL;
    char *pBuf        = NULL;

#ifdef UI_PROCESS
    tagMessage msg;
#else
    tagKingMessage msg;
#endif

    // 检查输入参数的合法性
    if (strAddr == NULL)
    {
        LOGE("There is no address.");
        return false;
    }

    // 获取通道名对应的整型地址
    nPeerAddr = m_stTbusParas.mapAddr[strAddr];

    // 循环收取数据，直至收到一个正常数据包
    do
    {
        LockTbus();
        // 从tbus通道中收帧，并存储在pszRecvBuff中
        nRet = BusRecvFrom(nPeerAddr, &pszRecvBuff);
        if (nRet > 0)
        {
            pBuf = static_cast<char*>(malloc(nRet));
            memcpy(pBuf, pszRecvBuff, nRet);
        }

        UnlockTbus();
        TqcOsSleep(10);
        // 如果收到exit相关的信号，此时退出
        if (IsExit())
        {
            if (pBuf)
            {
                free(pBuf);
                pBuf = NULL;
            }

            LOGI("Msg manager exited.");
            return true;
        }
    }
    while (nRet <= 0);

    // 从tbus通道中，循环收取并解析处理所有的消息
    // if (nRet > 0)
    // {
    do
    {
        // 通过protobuf解析包
        msg.ParseFromArray(pBuf, nRet);
        // 处理消息
        pHandler(reinterpret_cast<void*>(&msg));

        // 收取下一条消息
        LockTbus();
#if !defined(__APPLE__)
        nRet = BusRecvFrom(nPeerAddr, &pszRecvBuff);
#endif
        if (pBuf)
        {
            free(pBuf);
            pBuf = NULL;
        }

        if (nRet > 0)
        {
            pBuf = static_cast<char*>(malloc(nRet));
            memcpy(pBuf, pszRecvBuff, nRet);
        }

        UnlockTbus();
    }
    while (nRet > 0);

    // if (pBuf)
    // {
    //     free(pBuf);
    //     pBuf = NULL;
    // }

    return true;
    // }
    // else
    // {
    //     if (pBuf)
    //     {
    //         free(pBuf);
    //         pBuf = NULL;
    //     }

    //     return false;
    // }

    // if (pBuf)
    // {
    //     free(pBuf);
    //     pBuf = NULL;
    // }

    // return true;
}

void CPBMsgManager::SetExit(bool bExit)
{
    // 设置退出，一般由外部调用
    m_bExitLock.Lock();
    LOGI("set pb msg manager exit");
    m_bExit = bExit;
    m_bExitLock.UnLock();
}

bool CPBMsgManager::IsExit()
{
    // 检查是否需要退出
    m_bExitLock.Lock();
    bool bExit = m_bExit;
    m_bExitLock.UnLock();

    return bExit;
}

int CPBMsgManager::GetPeerAddr(const char *name)
{
    // 检查输入的合法性
    if (name == NULL)
    {
        LOGE("The Peer name is NULL.");
        return -1;
    }
    // 获取通道对应的整型地址，key为通道名，值为整数地址
    return m_stTbusParas.mapAddr[name];
}

bool CPBMsgManager::SendData(void *pData, int nLen, enPeerName eName)
{
    // 通过tbus发送数据包
    return SendDataByTbus(pData, nLen, eName);
}

bool CPBMsgManager::SendDataByTbus(void *pData, int nLen, enPeerName eName)
{
    // 检查是否需要通过tbus发送数据
    if (m_bTbusEnable == false)
    {
        return true;
    }
    // 检查输入的合法性
    if (NULL == pData || 0 == nLen || PEER_NONE == eName)
    {
        LOGE("InputParas is invalid, please check");
        return false;
    }

    int nPeerAddr = -1;

    // 通过通道名获取整数地址
    switch (eName)
    {
    case PEER_UIAUTO:
        // 获取"GameUIAutoAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameUIAutoAddr"];
        break;

    case PEER_AGENT:
        // 获取"GameAgentAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameAgentAddr"];
        break;

    case PEER_STRATEGY:
        // 获取"GameBTreeAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameBTreeAddr"];
        break;

    case PEER_UIRECOGNIZE:
        // 获取"GameUIRecognizeAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameUIRecognizeAddr"];
        break;

    case PEER_UIREGMGR:
        // 获取"GameUIRegMgrAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameUIRegMgrAddr"];
        break;

    case PEER_UIMATCH:
        // 获取"GameUIMatchAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["GameUIMatchAddr"];
        break;

    case PEER_MC:
        // 获取"MCAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["MCAddr"];
        break;

    case PEER_SDK_TOOLS:
        // 获取"SDKToolAddr"对应的整数地址
        nPeerAddr = m_stTbusParas.mapAddr["SDKToolAddr"];
        break;

    default:
        break;
    }

    // 通过tbus通道发送数据
    if (-1 != nPeerAddr)
    {
        LockTbus();
#if !defined(__APPLE__)
        // 调用tbus接口发送数据
        int nRes = BusSendTo(nPeerAddr, reinterpret_cast<char*>(pData), nLen);
#else
        int nRes = 0;
#endif
        UnlockTbus();

        if (0 == nRes)
        {
            return true;
        }
        else
        {
            LOGW("bus send data failed, ret %d, Peer Addr  %d", nRes, nPeerAddr);
            return false;
        }
    }
    else
    {
        LOGE("get peer address failed, please check");
        return false;
    }

    return true;
}
