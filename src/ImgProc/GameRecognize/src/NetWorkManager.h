/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_NETWORKMANAGER_H_
#define GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_NETWORKMANAGER_H_

#include <time.h>
#include <queue>
#include <sstream>
#include <vector>


#include "Comm/Utils/TqcLog.h"
#include "Comm/Utils/TqcThreadPool.h"
#include "GameRecognize/src/IniConfClass.h"
#include "GameRecognize/src/SerializeProtobuf.h"
#include "GameRecognize/src/TaskMgr/TaskManager.h"

#ifdef LINUX
#include "Modules/tbus/libtbus/include/bus.h"
#else
#include "Modules/tbus/tbusdll/busdll/bus.h"
#endif  // WIN32

/*!
  * @class CSerialFrameResult
  * @brief 图像识别结果数据的序列化
*/
class CNetWorkManager {
  public:
    CNetWorkManager();
    ~CNetWorkManager();

  public:
    /*!
      * @brief 初始化
      * @return 0表示成功，-1表示失败
    */
    int Initialize(char* pszUserCfgPath);

    /*!
      * @brief 数据收发
      * @param[out] pVecTaskMsg
      * @param[out] pSrcImageInfo
      * @param[in] stFrameResult
      * @param[out] peSendTaskReportToMC
      * @return 0 or -1
    */
    int Update(std::vector<CTaskMessage> *pVecTaskMsg, tagSrcImgInfo *pSrcImageInfo,
        const tagFrameResult &stFrameResult, ESendTaskReportToMC *peSendTaskReportToMC);

    /*!
      * @brief 数据收发(SDKTool的数据收发)
      * @param[out] pVecTaskMsg
      * @param[out] pSrcImageInfo
      * @param[in] stFrameResult
      * @return 0 or -1
    */
    int UpdateForSDKTool(std::vector<CTaskMessage> *pVecTaskMsg,
        tagSrcImgInfo *pSrcImageInfo, const tagFrameResult &stFrameResult);

    /*!
      * @brief 发送结果数据给Agent或SDKTool
      * @param[in] stFrameResult
      * @return 0表示成功，-1表示失败
    */
    int SendFrameResult(const tagFrameResult &stFrameResult, int nAddr);

    /*!
      * @brief 从Agent接受任务数据
      * @param[out] pVecTaskMsg
      * @return 0表示成功，-1表示失败
      */
    //    int RecvFromAgent(std::vector<CTaskMessage> *pVecTaskMsg);

    /*!
      * @brief 从SDKTool接受任务数据
      * @param[out] pVecTaskMsg
      * @return 0表示成功，-1表示失败
    */
    int RecvTaskMsg(std::vector<CTaskMessage> *pVecTaskMsg, int nAddr);

    /*!
      * @brief 接收图像数据
      * @param[out] pSrcImageInfo
      * @return 0表示成功，-1表示失败
    */
    //    int RecvFromMC(tagSrcImgInfo *pSrcImageInfo);

    /*!
      * @brief 从SDKTool接收图像数据
      * @param[out] pSrcImageInfo
      * @return 0表示成功，-1表示失败
    */
    int RecvSrcImg(tagSrcImgInfo *pSrcImageInfo, int nAddr);

    /*!
      * @brief 从SDKTool接收数据
      * @param[out] pSrcImageInfo
      * @return 0表示成功，-1表示失败
    */
    int RecvFromSDKTool(tagSrcImgInfo *pSrcImageInfo, std::vector<CTaskMessage> *pVecTaskMsg,
        int nAddr);

    /*!
      * @brief 向图象帧队列中push帧数
      * @param[in] nFrameSeq
    */
    //    void PushToResQueue(int nFrameSeq);
    /*!
      * @brief 是否应该release
      * return true or false
    */
    bool GetSholdRelease() { return m_bShouldRelease; }

    /*!
      * @brief release
    */
    void Release();

  private:
    /*!
      * @brief 向MC发送reger初始化成功或失败
      * @return
    */
    int SendTaskReport(bool bState);

    /*!
      * @brief 向MC发一条注册信息
      * @return 0表示成功，-1表示失败
    */
    int RegisterToMC();

    /*!
      * @brief 向MC发一条反注册信息
      * @return 0表示成功，-1表示失败
    */
    int UnRegisterToMC();

    /*!
      * @brief 根据名字获取地址
      * @param[in] pAddrName
      * @param[out] nAddr
      * @return 0表示成功，-1表示失败
    */
    int GetTbusAddr(char *pAddrName, int *nAddr);

  private:
    int m_nSelfAddr;                       // 自己地址
    int m_nAgentAddr;                      // Agent地址
    int m_nMCAddr;                         // MC地址
    int m_nSDKToolAddr;                    // SDKTool地址

    bool m_bShouldRelease;                  // 是否应该release
    CSerialFrameResult oSerialFrameResult;  // 序列化帧处理结果的对象
    CUnSerialTaskMsg oUnSerialTaskMsg;      // 反序列化任务相关数据的对象
    CUnSerialSrcImg oUnSerialSrcImg;        // 反序列化图像数据的对象
};

#endif  // GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_NETWORKMANAGER_H_
/*!@}*/
