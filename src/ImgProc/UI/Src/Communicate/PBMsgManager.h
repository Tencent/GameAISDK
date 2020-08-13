/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef PB_MSG_MANAGER_H_
#define PB_MSG_MANAGER_H_

#include "UI/Src/Communicate/DataComm.h"
class CPBMsgManager
{
public:
    CPBMsgManager();
    ~CPBMsgManager();

    bool Initialize(void *pTbusData);
    void Release();
    bool ReceiveMsg(MSG_HANDLER_ROUTINE pHandler, const char *strAddr);         // block if there is no msg.
    void SetExit(bool bExit);
    bool IsExit();
    bool InitTBus(void *pInitData);
    void ReleaseTBus();
    bool SendData(void *pData, int nLen, enPeerName eName);
    int  GetPeerAddr(const char *name);
    void LockTbus();
    void UnlockTbus();

private:
    bool SendDataByTbus(void *pData, int nLen, enPeerName eName);

private:
    bool        m_bExit;
    bool        m_bTbusEnable;
    CLock       m_bExitLock;
    stTBUSParas m_stTbusParas;

    CLock m_tbusAccess;
};

#endif // PB_MSG_MANAGER_H_
