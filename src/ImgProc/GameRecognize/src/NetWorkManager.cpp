/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "GameRecognize/src/NetWorkManager.h"

extern std::string g_strBaseDir;

// ======================================================================
// 以下为NetWorkManager成员函数的实现
// ======================================================================

CNetWorkManager::CNetWorkManager() {
    m_nSelfAddr = -1;
    m_nAgentAddr = -1;
    m_nMCAddr = -1;
    m_nSDKToolAddr = -1;
    m_bShouldRelease = false;
}

CNetWorkManager::~CNetWorkManager() {
}

void CNetWorkManager::Release() {
    UnRegisterToMC();
    BusExit(m_nSelfAddr);
    CIniConf::getInstance()->closeFile();
}

int CNetWorkManager::Initialize(char* pszSysCfgPath) {
    // 获取tbus的地址，以及初始化通道
    char szPath[256] = { 0 };
    sprintf(szPath, "%s%s", pszSysCfgPath, TBUS_DIR);
    int nRet = CIniConf::getInstance()->loadFile(szPath);

    if (nRet != 0) {
        LOGE("load tbus cfg failed: %s", szPath);
        return -1;
    }

    // 获取GameReg地址
    nRet = GetTbusAddr("GameReg1Addr", &m_nSelfAddr);
    if (nRet != 0) {
        LOGE("get GameReg addr failed");
        return -1;
    }

    // 获取Agent地址
    nRet = GetTbusAddr("Agent1Addr", &m_nAgentAddr);
    if (nRet != 0) {
        LOGE("get Agent addr failed");
        return -1;
    }

    // 获取MC地址
    nRet = GetTbusAddr("MCAddr", &m_nMCAddr);
    if (nRet != 0) {
        LOGE("get MC addr failed");
        return -1;
    }

    // 获取SDKTool地址
    nRet = GetTbusAddr("SDKToolAddr", &m_nSDKToolAddr);
    if (nRet != 0) {
        LOGE("get SDKTool addr failed");
        return -1;
    }

    // 初始化自己的地址
    nRet = BusInit(m_nSelfAddr, szPath);
    if (nRet != 0) {
        LOGE("tbus init faild");
        return -1;
    }

    // 向MC发送注册消息
    nRet = RegisterToMC();
    if (nRet != 0) {
        LOGE("register to mc failed");
        return -1;
    }

    m_bShouldRelease = true;
    return 0;
}

int CNetWorkManager::RegisterToMC() {
    std::string      pstrDataBuf;
    CRegisterToMCMsg oRegisterToMCMsg;
    // 序列化注册的消息
    oRegisterToMCMsg.SerialRegisterMsg(&pstrDataBuf);

    // 发送给MC
    int nRet = BusSendTo(m_nMCAddr,
        reinterpret_cast<void*>(const_cast<char*>(pstrDataBuf.c_str())), pstrDataBuf.length());
    if (nRet < 0) {
        LOGW("send nRet:%d", nRet);
    }

    return 0;
}

int CNetWorkManager::UnRegisterToMC() {
    std::string pstrDataBuf;
    CRegisterToMCMsg oRegisterToMCMsg;
    // 序列化反注册的消息
    oRegisterToMCMsg.SerialUnRegisterMsg(&pstrDataBuf);

    // 发送给MC
    int nRet = BusSendTo(m_nMCAddr,
        reinterpret_cast<void *>(const_cast<char *>(pstrDataBuf.c_str())), pstrDataBuf.length());
    if (nRet < 0) {
        LOGW("send nRet:%d", nRet);
    }

    return 0;
}

int CNetWorkManager::SendTaskReport(bool bState) {
    std::string pstrDataBuf;
    CRegisterToMCMsg oRegisterToMCMsg;
    // 序列化任务初始化成功或者失败的消息，bState为true表示初始化成功，bState为false时表示初始化失败
    oRegisterToMCMsg.SerialTaskReportMsg(&pstrDataBuf, bState);

    // 发送给MC
    int nRet = BusSendTo(m_nMCAddr,
        reinterpret_cast<void *>(const_cast<char *>(pstrDataBuf.c_str())), pstrDataBuf.length());
    if (nRet < 0) {
        LOGW("send nRet:%d", nRet);
    }

    return 0;
}

int CNetWorkManager::RecvTaskMsg(std::vector<CTaskMessage> *pVecTaskMsg, int nAddr) {
    if (pVecTaskMsg == NULL) {
        LOGE("pVecTaskMsg is NULL");
        return -1;
    }

    // 从tbus接收task数据
    char *pDataBuf;
    int nLen = BusRecvFrom(nAddr, &pDataBuf);
    while (nLen > 0) {
        CTaskMessage oTaskMsg;
        // 反序列化task消息
        int nRet = oUnSerialTaskMsg.UnSerialize(&oTaskMsg, pDataBuf, nLen);
        if (nRet == -1) {
            LOGE("Unserialize TaskMessage failed");
            return -1;
        }

        if (nRet != 1) {
            pVecTaskMsg->push_back(oTaskMsg);
        }
        nLen = BusRecvFrom(m_nAgentAddr, &pDataBuf);
    }

    if (nLen < 0) {
        LOGE("recv from MC failed");
        return -1;
    }

    if (!pVecTaskMsg->empty()) {
        return 1;
    } else {
        return 0;
    }
}

int CNetWorkManager::RecvFromSDKTool(tagSrcImgInfo *pSrcImageInfo,
    std::vector<CTaskMessage> *pVecTaskMsg, int nAddr) {
    if (pSrcImageInfo == NULL) {
        LOGE("pSrcImageInfo is NULL");
        return -1;
    }

    // 从SDKTool接收task数据和图像数据
    char *pDataBuf, *pLastDataBuf;
    int nLen, nLastLen;
    nLen = BusRecvFrom(nAddr, &pDataBuf);

    while (nLen > 0) {
        tagMessage stMessage;
        stMessage.ParseFromArray(pDataBuf, nLen);
        EMSGIDENUM eMsgID = stMessage.emsgid();
        if (eMsgID == MSG_GAMEREG_INFO) {
            // 反序列化task消息
            CTaskMessage oTaskMsg;
            int nRet = oUnSerialTaskMsg.UnSerialize(&oTaskMsg, pDataBuf, nLen);
            if (nRet == -1) {
                LOGE("Unserialize TaskMessage failed");
                return -1;
            }

            if (nRet != 1) {
                pVecTaskMsg->push_back(oTaskMsg);
            }
            nLen = BusRecvFrom(nAddr, &pDataBuf);
        } else if (eMsgID == MSG_SRC_IMAGE_INFO) {
            pLastDataBuf = pDataBuf;
            nLastLen = nLen;
            nLen = BusRecvFrom(nAddr, &pDataBuf);
            if (nLen == 0) {
                // 反序列化图像消息
                int nRet = oUnSerialSrcImg.UnSerialize(pSrcImageInfo, pLastDataBuf, nLastLen);
                if (nRet == -1) {
                    LOGE("Unserialize SrcImg failed");
                    return -1;
                }

                return 1;
            }
        } else {
            LOGE("recv wrong msgID: %d", eMsgID);
            break;
        }
    }

    if (nLen < 0) {
        LOGE("recv from SDKTool failed");
        return -1;
    }

    return 0;
}

int CNetWorkManager::RecvSrcImg(tagSrcImgInfo *pSrcImageInfo, int nAddr) {
    if (pSrcImageInfo == NULL) {
        LOGE("pSrcImageInfo is NULL");
        return -1;
    }

    // 从tbus接收图像数据
    char *pDataBuf, *pLastDataBuf;
    int nLen, nLastLen;
    nLen = BusRecvFrom(nAddr, &pDataBuf);

    while (nLen > 0) {
        pLastDataBuf = pDataBuf;
        nLastLen = nLen;
        nLen = BusRecvFrom(nAddr, &pDataBuf);
        if (nLen == 0) {
            // 反序列化图像消息
            int nRet = oUnSerialSrcImg.UnSerialize(pSrcImageInfo, pLastDataBuf, nLastLen);
            if (nRet == -1) {
                LOGE("Unserialize SrcImg failed");
                return -1;
            }

            // LOGI("recv a frame sucess");
            return 1;
        }
    }

    if (nLen < 0) {
        LOGE("recv from SDKTool failed");
        return -1;
    }

    return 0;
}

int CNetWorkManager::SendFrameResult(const tagFrameResult &stFrameResult, int nAddr) {
    if (stFrameResult.oFrame.empty()) {
        return 0;
    }

    // 序列化图像消息
    std::string strFrameResult;
    int nRet = oSerialFrameResult.Serialize(&strFrameResult, stFrameResult);

    if (nRet != 0) {
        LOGE("serialize FrameResult failed");
        return -1;
    }

    // 将序列化后的图像消息发送出去
    nRet = BusSendTo(nAddr,
        reinterpret_cast<void *>(const_cast<char *>(strFrameResult.c_str())),
        strFrameResult.length());
    if (nRet < 0) {
        LOGW("send nRet:%d", nRet);
    }

    return 1;
}

int CNetWorkManager::GetTbusAddr(char *pAddrName, int *nAddr) {
    // 从配置文件中读取地址名字对应的地址
    char pzSelfBuf[16] = { 0 };
    int nRet = TSingleton<CIniConf>::getInstance()->getPrivateStr("BusConf", pAddrName,
        "1.1.1.1", pzSelfBuf, 16);
    if (nRet < 0) {
        LOGE("load GameRegAddr failed");
        return -1;
    }

    // 调用tbus的读取地址的接口
    if (0 != BusGetAddress(pzSelfBuf, nAddr)) {
        LOGE("GameReg get tbus addr failed");
        return -1;
    }

    return 0;
}

int CNetWorkManager::UpdateForSDKTool(std::vector<CTaskMessage> *pVecTaskMsg,
    tagSrcImgInfo *pSrcImageInfo, const tagFrameResult &stFrameResult) {
    if (pVecTaskMsg == NULL) {
        LOGE("pVecTaskMsg is NULL");
        return -1;
    }

    if (pSrcImageInfo == NULL) {
        LOGE("pSrcImageInfo is NULL");
        return -1;
    }

    pVecTaskMsg->clear();

    int nResUpdate = 0;

    // 从SDKTool接收任务消息，或者图像
    int nRet;
    nRet = RecvFromSDKTool(pSrcImageInfo, pVecTaskMsg, m_nSDKToolAddr);
    if (nRet < 0) {
        LOGE("recv from SDKTool failed");
    } else if (nRet == 1) {
        nResUpdate = 1;
    }

    // 发送给Agent识别结果
    nRet = SendFrameResult(stFrameResult, m_nSDKToolAddr);
    if (nRet < 0) {
        LOGE("send FrameResult failed");
    } else if (nRet == 1) {
        nResUpdate = 1;
    }

    return nResUpdate;
}

int CNetWorkManager::Update(std::vector <CTaskMessage> *pVecTaskMsg, tagSrcImgInfo *pSrcImageInfo,
    const tagFrameResult &stFrameResult, ESendTaskReportToMC *pSendTaskReportToMC) {
    if (pVecTaskMsg == NULL) {
        LOGE("pVecTaskMsg is NULL");
        return -1;
    }

    if (pSrcImageInfo == NULL) {
        LOGE("pSrcImageInfo is NULL");
        return -1;
    }

    if (pSendTaskReportToMC == NULL) {
        LOGE("pSendTaskReportToMC is NULL");
        return -1;
    }

    pVecTaskMsg->clear();

    int nResUpdate = 0;

    // 从Agent接收任务初始化或者设置任务状态的消息
    int nRet;
    nRet = RecvTaskMsg(pVecTaskMsg, m_nAgentAddr);
    if (nRet < 0) {
        LOGW("recv from Agent failed");
    } else if (nRet == 1) {
        nResUpdate = 1;
    }

    // 从MC接收图像
    nRet = RecvSrcImg(pSrcImageInfo, m_nMCAddr);
    if (nRet < 0) {
        LOGE("recv from MC failed");
    } else if (nRet == 1) {
        nResUpdate = 1;
    }

    // 发送给Agent识别结果
    nRet = SendFrameResult(stFrameResult, m_nAgentAddr);
    if (nRet < 0) {
        LOGE("send FrameResult failed");
    } else if (nRet == 1) {
        nResUpdate = 1;
    }

    if (*pSendTaskReportToMC == SEND_TRUE) {
        nRet = SendTaskReport(true);
    } else if (*pSendTaskReportToMC == SEND_FALSE) {
        nRet = SendTaskReport(false);
    }

    return nResUpdate;
}
