/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskMessage.h"

using namespace std;

CTaskMessage::CTaskMessage() {
    m_pCmdMsg = NULL;
    m_EAgentMsgID = MSG_RECV_BEGIN;
}

CTaskMessage::~CTaskMessage() {
}

// 释放资源
void CTaskMessage::Release() {
    if (m_pCmdMsg != NULL) {
        m_pCmdMsg->Release();
        delete m_pCmdMsg;
        m_pCmdMsg = NULL;
    }
}

tagCmdMsg* CTaskMessage::GetInstance(const EAgentMsgID eMsgID) {
    m_EAgentMsgID = eMsgID;

    switch (eMsgID) {
    case  MSG_RECV_GROUP_ID:
    {
        // 创建任务消息
        CreateGroupMsg();
        break;
    }

    case MSG_RECV_TASK_FLAG:
    {
        // 创建flag消息
        CreateFlagMsg();
        break;
    }

    case MSG_RECV_ADD_TASK:
    {
        // 创建添加任务消息
        CreateAddTaskMsg();
        break;
    }

    case MSG_RECV_DEL_TASK:
    {
        // 创建删除任务消息
        CreateDelTaskMsg();
        break;
    }

    case MSG_RECV_CHG_TASK:
    {
        // 创建改变任务消息
        CreateChgTaskMsg();
        break;
    }

    case MSG_RECV_CONF_TASK:
    {
        // 创建conf任务
        CreateConfTaskMsg();
        break;
    }

    default:
    {
        LOGE("recv msg type %d is invalid", eMsgID);
        break;
    }
    }

    return m_pCmdMsg;
}

// 设置消息类型
void CTaskMessage::SetMsgType(const EAgentMsgID eMsgID) {
    m_EAgentMsgID = eMsgID;
}

// 获取消息类型
EAgentMsgID CTaskMessage::GetMsgType() {
    return m_EAgentMsgID;
}

// ===================================================================
// 实例化创建消息
// ===================================================================
void CTaskMessage::CreateGroupMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagAgentMsg();
    }
}

void CTaskMessage::CreateFlagMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagTaskFlagMsg();
    }
}

void CTaskMessage::CreateAddTaskMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagAgentMsg();
    }
}

void CTaskMessage::CreateDelTaskMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagDelTaskMsg();
    }
}

void CTaskMessage::CreateChgTaskMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagAgentMsg();
    }
}

void CTaskMessage::CreateConfTaskMsg() {
    if (!m_pCmdMsg) {
        m_pCmdMsg = new tagConfTaskMsg();
    }
}
