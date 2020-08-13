
/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef DATA_MANAGER_H_
#define DATA_MANAGER_H_

#include "UI/Src/Communicate/DataComm.h"

class CDataManager
{
public:
    CDataManager();
    ~CDataManager();

    bool            Initialize(enSourceType srcType, enSourceType dstType);
    bool            InitializeFromData(enSourceType srcType, enSourceType dstType,
                                       const void *pInitData);
    bool            GetNextFrame(cv::Mat *pFrame, int step = 1);
    cv::Mat*        GetNextFrame(int step);
    bool            PopOneFrame();
    // void            Release(enGameName game, enSourceType type);
    void           Release(enSourceType type);
    int             GetFrameSeq();
    void            SetExit(bool bExit);
    enSourceType    GetSrcType();
    enSourceType    GetDstType();
    bool            IsEndFrame();

    // Frame Queue
    void    PushFrameQueue(int nQueueIndex, const stFrame &frame);
    stFrame PopFrameQueue(int nQueueIndex);
    stFrame PopLastFrameQueue(int nQueueIndex);     // Pop all the frames in queue and return the latest frame.
    int     GetFrameQueueSize(int nQueueIndex);

    // Message Queue
    // void        PushMsgQueue(stGameMsg *pMsg);
    // stGameMsg*  PopMsgQueue();

    // Source Frame Queue from video, picture or tbus.
    void    PushSrcFrameQueue(const stFrame  &frame);
    stFrame PopSrcFrameQueue();
    stFrame PopSrcLastFrameQueue();     // Pop all the frames in queue and return the latest frame.
    int     GetSrcFrameQueueSize();

    // Game State
    void    SetGameState(int gameState);
    int     GetGameState();
    void    SetScreenOrient(int screen);
    int     GetScreenOrient();

private:
    bool GetNextFrameByVideo(cv::Mat *pFrame);
    bool GetNextFrameByPicture(cv::Mat *pFrame);
    bool GetNextFrameByTBus(cv::Mat *pFrame);

    bool InitSrcVideo(const void *pInitData);
    bool InitSrcPicture(const void *pInitData);

private:
    enSourceType m_srcType;
    enSourceType m_dstType;
    // enGameName m_gameName;
    cv::VideoCapture m_decoder;
    tagPicParams     m_picInfo;
    int              m_nFrame;
    int              m_nFrameSeq;
    bool             m_bExit;

    // Screen orientation
    int   m_screenOrient;
    CLock m_screenOrientLock;

    FrameQueue m_frameQueue[FRAME_QUEUE_NUM];
    CLock      m_frameQueueLock[FRAME_QUEUE_NUM];

    // Result message.
    // GameMsgQueue m_msgQueue;
    // CLock m_msgQueueLock;

    // Source Frame Queue from video, picture or tbus.
    FrameQueue m_srcFrameQueue;
    CLock      m_srcFrameQueueLock;

    // Game State.
    int   m_nGameState;
    CLock m_gameStateLock;

public:
    cv::Mat m_currentFrame;
    cv::Mat *m_pCurrentFrame;
};

void MsgHandler(void *pMsg);
#endif // DATA_MANAGER_H_
