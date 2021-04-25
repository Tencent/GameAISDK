/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <bus.h>
#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcLog.h"
#include "Protobuf/common.pb.h"
#include "UI/Src/Communicate/DataComm.h"
#include "UI/Src/Communicate/DataManager.h"

CDataManager g_dataMgr;

CDataManager::CDataManager() {
    m_srcType = DATA_SRC_INVALID;
    m_dstType = DATA_SRC_INVALID;
    // m_gameName     = GAME_NAME_INVALID;
    m_nFrame = 0;
    m_nFrameSeq = 0;
    m_bExit = false;
    m_nGameState = -1;
    m_screenOrient = PB_SCREEN_ORI_LANDSCAPE;
    m_pCurrentFrame = NULL;
}

CDataManager::~CDataManager() {
    // Release frame queue.
    for (int i = 0; i < FRAME_QUEUE_NUM; i++) {
        m_frameQueueLock[i].Lock();

        while (m_frameQueue[i].size() > 0) {
            m_frameQueue[i].pop();
        }

        m_frameQueueLock[i].UnLock();
    }

    // Release Source frame
    m_srcFrameQueueLock.Lock();

    while (m_srcFrameQueue.size() > 0) {
        m_srcFrameQueue.pop();
    }

    m_srcFrameQueueLock.UnLock();

    // m_msgQueueLock.Lock();

    // while (m_msgQueue.size() > 0)
    // {
    //     stGameMsg *pMsg = m_msgQueue.front();

    //     // delete pMsg;
    //     m_msgQueue.pop();
    // }

    // m_msgQueueLock.UnLock();
}

//
// Get current type of frame source.
//
enSourceType CDataManager::GetSrcType() {
    return m_srcType;
}

//
// Get current type of frame destination.
//
enSourceType CDataManager::GetDstType() {
    return m_dstType;
}

//
// Set the type of source and destination
//
bool CDataManager::InitializeFromData(enSourceType srcType, enSourceType dstType,
    const void *pInitData) {
    bool res = false;

    m_srcType = srcType;
    // m_gameName = game;
    m_nFrame = 0;

    switch (srcType) {
    case DATA_SRC_VIDEO:
        res = InitSrcVideo(pInitData);
        break;

    case DATA_SRC_PICTURE:
        res = InitSrcPicture(pInitData);
        break;

    case DATA_SRC_TBUS:
        return true;

    default:
        break;
    }

    return res;
}

//
// Init video decoder.
//
bool CDataManager::InitSrcVideo(const void *pInitData) {
    const char *pFileName = reinterpret_cast<const char*>(pInitData);

    if (!m_decoder.open(pFileName)) {
        LOGE("Cannot open file: %s", pFileName);
        return false;
    }

    return true;
}

//
// Initialize source picture folder.
//
bool CDataManager::InitSrcPicture(const void *pInitData) {
    const tagPicParams *pParam = reinterpret_cast<const tagPicParams*>(pInitData);

    memcpy(&m_picInfo, pParam, sizeof(tagPicParams));

    m_nFrame = m_picInfo.nStart;

    return true;
}

//
// Release video decoder.
//
void CDataManager::Release(enSourceType type) {
    switch (type) {
    case DATA_SRC_VIDEO:
        m_decoder.release();
        break;

    case DATA_SRC_PICTURE:
        break;

    case DATA_SRC_TBUS:
        break;

    default:
        break;
    }
}

//
// Get the next frame from frame source.
//
cv::Mat* CDataManager::GetNextFrame(int step) {
    cv::Mat *pFrame = NULL;
    cv::Mat frame;

    bool res = GetNextFrame(&frame, step);

    if (res) {
        pFrame = &m_currentFrame;
    } else {
        pFrame = NULL;
    }

    m_pCurrentFrame = pFrame;
    return pFrame;
}

//
// Check if there is no next frame.
//
bool CDataManager::IsEndFrame() {
    if (m_pCurrentFrame == NULL)
        return true;
    else
        return false;
}

//
// Get the next frame.
//
bool CDataManager::GetNextFrame(cv::Mat *pFrame, int step) {
    bool res = false;
    LOGD("begin get next frame");
    switch (m_srcType) {
    case DATA_SRC_VIDEO:
        res = GetNextFrameByVideo(pFrame);
        m_nFrame++;
        break;

    case DATA_SRC_PICTURE:
        res = GetNextFrameByPicture(pFrame);
        m_nFrame += step;
        break;

    case DATA_SRC_TBUS:
        res = GetNextFrameByTBus(pFrame);
        m_nFrame++;
        break;

    default:
        break;
    }

    if (res) {
        m_currentFrame = *pFrame;
    }
    LOGD("begin get next success");
    return res;
}

//
// Get the next frame from the video.
//
bool CDataManager::GetNextFrameByVideo(cv::Mat *pFrame) {
    if (pFrame == NULL) {
        return false;
    }

    m_decoder >> *pFrame;

    if (pFrame->empty()) {
        LOGE("%s(%d): at the end of frames.", __FUNCTION__, __LINE__);
        return false;
    }

    m_nFrameSeq++;
    return true;
}

//
// Get the next frame from the pictures.
//
bool CDataManager::GetNextFrameByPicture(cv::Mat *pFrame) {
    if (pFrame == NULL) {
        return false;
    }

    if (m_nFrame > m_picInfo.nEnd) {
        LOGE("%s(%d): at the end of frames.", __FUNCTION__, __LINE__);
        return false;
    }

    char buf[TQC_PATH_STR_LEN];
    memset(buf, 0, TQC_PATH_STR_LEN);
    SNPRINTF(buf, sizeof(buf), "%s/%s%d.%s", m_picInfo.filePath, m_picInfo.fileName, m_nFrame,
        m_picInfo.fileSuffix);

    *pFrame = cv::imread(buf);
    if (pFrame->empty()) {
        LOGE("%s(%d): cannot find file(%s).", __FUNCTION__, __LINE__, buf);
        return false;
    }

    m_nFrameSeq++;
    return true;
}

//
// Because data manager is single thread, we should synchronize with
// the main thread.
//
void CDataManager::SetExit(bool bExit) {
    LOGI("set data manager exit");
    m_bExit = bExit;
}

//
// Get the next frame from the tbus.
//
bool CDataManager::GetNextFrameByTBus(cv::Mat *pFrame) {
    stFrame frame1;

    if (pFrame == NULL) {
        return false;
    }

    do {
        frame1 = PopSrcLastFrameQueue();
        *pFrame = frame1.img;
        m_nFrameSeq = frame1.nFrameSeq;

        if (pFrame->cols > 0 && pFrame->rows > 0) {
            break;
        } else {
            TqcOsSleep(50);
        }

        if (m_bExit) {
            LOGI("Data mananger exited.");
            return false;
        }
    } while (1);

    return true;
}

//
// Get the frame sequence which receives from the tbus.
//
int CDataManager::GetFrameSeq() {
    return m_nFrameSeq;
}

//
// Put the received frame to the queue.
//
void CDataManager::PushFrameQueue(int nQueueIndex, const stFrame &frame) {
    if (nQueueIndex < 0 || nQueueIndex >= FRAME_QUEUE_NUM) {
        LOGE("Wrong queue index(%d).", nQueueIndex);
        return;
    }

    m_frameQueueLock[nQueueIndex].Lock();
    m_frameQueue[nQueueIndex].push(frame);
    m_frameQueueLock[nQueueIndex].UnLock();
}

//
// Get frame from the queue.
//
stFrame CDataManager::PopFrameQueue(int nQueueIndex) {
    stFrame frame;

    if (nQueueIndex < 0 || nQueueIndex >= FRAME_QUEUE_NUM) {
        LOGE("Wrong queue index(%d).", nQueueIndex);
        return frame;
    }

    m_frameQueueLock[nQueueIndex].Lock();
    if (m_frameQueue[nQueueIndex].size() > 0) {
        frame = m_frameQueue[nQueueIndex].front();
        m_frameQueue[nQueueIndex].pop();
    }

    m_frameQueueLock[nQueueIndex].UnLock();

    return frame;
}

//
// Get the latest frame.
//
stFrame CDataManager::PopLastFrameQueue(int nQueueIndex) {
    stFrame frame;

    if (nQueueIndex < 0 || nQueueIndex >= FRAME_QUEUE_NUM) {
        LOGE("Wrong queue index(%d).", nQueueIndex);
        return frame;
    }

    m_frameQueueLock[nQueueIndex].Lock();

    while (m_frameQueue[nQueueIndex].size() > 0) {
        frame = m_frameQueue[nQueueIndex].front();
        m_frameQueue[nQueueIndex].pop();
    }

    m_frameQueueLock[nQueueIndex].UnLock();

    return frame;
}

//
// Get current queue size.
//
int CDataManager::GetFrameQueueSize(int nQueueIndex) {
    int size = 0;

    m_frameQueueLock[nQueueIndex].Lock();
    size = m_frameQueue[nQueueIndex].size();
    m_frameQueueLock[nQueueIndex].UnLock();
    return size;
}

//
// Save frame.
//
void CDataManager::PushSrcFrameQueue(const stFrame &frame) {
    m_srcFrameQueueLock.Lock();
    m_srcFrameQueue.push(frame);
    m_srcFrameQueueLock.UnLock();
}

//
// Load frame.
//
stFrame CDataManager::PopSrcFrameQueue() {
    stFrame frame;

    m_srcFrameQueueLock.Lock();
    if (m_srcFrameQueue.size() > 0) {
        frame = m_srcFrameQueue.front();
        m_srcFrameQueue.pop();
    }

    m_srcFrameQueueLock.UnLock();

    return frame;
}

//
// Get the latest frame.
//
stFrame CDataManager::PopSrcLastFrameQueue() {
    stFrame frame;

    m_srcFrameQueueLock.Lock();

    while (m_srcFrameQueue.size() > 0) {
        frame = m_srcFrameQueue.front();
        m_srcFrameQueue.pop();
    }

    m_srcFrameQueueLock.UnLock();

    return frame;
}

//
// Get the queue size.
//
int CDataManager::GetSrcFrameQueueSize() {
    int size = 0;

    m_srcFrameQueueLock.Lock();
    size = m_srcFrameQueue.size();
    m_srcFrameQueueLock.UnLock();
    return size;
}

//
// Get one frame from the queue.
//
bool CDataManager::PopOneFrame() {
    PopSrcLastFrameQueue();
    return true;
}

//
// Set current game state, which is one of NONE/START/RUN/OVER/WIN.
//
void CDataManager::SetGameState(int gameState) {
    m_gameStateLock.Lock();
    if (m_nGameState != gameState)
        LOGI("Game state change to: %d", gameState);

    m_nGameState = gameState;
    m_gameStateLock.UnLock();
}

//
// Set orientation of screen.
//
void CDataManager::SetScreenOrient(int screen) {
    m_screenOrientLock.Lock();
    m_screenOrient = screen;
    m_screenOrientLock.UnLock();
}

int CDataManager::GetScreenOrient() {
    int nRes = -1;

    m_screenOrientLock.Lock();
    nRes = m_screenOrient;
    m_screenOrientLock.UnLock();

    return nRes;
}

int CDataManager::GetGameState() {
    m_gameStateLock.Lock();
    int gameState = m_nGameState;
    m_gameStateLock.UnLock();

    return gameState;
}

void MsgHandler(void *pMsg) {
#ifdef UI_PROCESS
    tagMessage msg = *(reinterpret_cast<tagMessage*>(pMsg));
#else
    tagKingMessage msg = *(reinterpret_cast<tagKingMessage*>(pMsg));
#endif

    int nMsgID = msg.emsgid();

    switch (nMsgID) {
    case MSG_SRC_IMAGE_INFO:
    {
        int     nWidth = msg.stsrcimageinfo().nwidth();
        int     nHeight = msg.stsrcimageinfo().nheight();
        cv::Mat img;
        stFrame frame;
        int     nFrameSeq = msg.stsrcimageinfo().uframeseq();
        if (nWidth > 0 && nHeight > 0) {
            std::string strData = msg.stsrcimageinfo().byimagedata();
            img.create(nHeight, nWidth, CV_8UC3);
            memcpy(img.data, strData.c_str(), strData.length());
            frame.nFrameSeq = nFrameSeq;
            frame.img = img;
            g_dataMgr.PushSrcFrameQueue(frame);
        } else {
            LOGE("Wrong Parameters, MsgID is %d, nWidth is %d, nHeight is %d",
                MSG_SRC_IMAGE_INFO, nWidth, nHeight);
        }

        break;
    }

    case MSG_UI_STATE_IMG:
    {
        // LOGE("MsgID is %d", MSG_SRC_IMAGE_INFO);

        int gameState = msg.stuiapistate().egamestate();
        g_dataMgr.SetGameState(gameState);

        int screenOrient = msg.stuiapistate().escreenori();
        g_dataMgr.SetScreenOrient(screenOrient);

        tagSrcImageInfo srcInfo = msg.stuiapistate().stuiimage();
        int             nWidth = srcInfo.nwidth();
        int             nHeight = srcInfo.nheight();
        cv::Mat         img;
        stFrame         frame;
        int             nFrameSeq = srcInfo.uframeseq();
        if (nWidth > 0 && nHeight > 0) {
            std::string strData = srcInfo.byimagedata();
            img.create(nHeight, nWidth, CV_8UC3);
            memcpy(img.data, strData.c_str(), strData.length());
            frame.nFrameSeq = nFrameSeq;
            frame.img = img;
            g_dataMgr.PushSrcFrameQueue(frame);
        } else {
            LOGE("Wrong Parameters, MsgID is %d, nWidth is %d, nHeight is %d",
                MSG_SRC_IMAGE_INFO, nWidth, nHeight);
        }

        break;
    }

    default:
        LOGE("Receive unknown message: %d", nMsgID);
        break;
    }
}
