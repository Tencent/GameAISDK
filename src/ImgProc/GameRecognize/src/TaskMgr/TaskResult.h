/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKRESULT_H_
#define GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKRESULT_H_

#include <map>
#include <string>

#include "GameRecognize/src/TaskMgr/TaskDefine.h"

/*!
  @class : CTaskResult
  @brief : 任务结果模块
*/

class CTaskResult {
  public:
    CTaskResult();
    ~CTaskResult();
    /*!
      * @brief 获取结果句柄
      * @param[in] eType 结果类型
      * @return 任务结果句柄
    */
    IRegResult *GetInstance(EREGTYPE eType);

    /*!
      * @brief 设置任务结果对应的识别类型
      * @param[in] eType 识别类型
    */
    void SetType(EREGTYPE eType);

    /*!
      * @brief 获取结果对应的识别类型
    */
    EREGTYPE GetType();

    /*!
      * @brief 设置TaskID
      * @param nTaskID
    */
    void SetTaskID(int nTaskID);

    /*!
      * @brief 获取TaskID
      * @return
    */
    int GetTaskID();

    /*!
      * @brief 释放m_pRegRst内存
    */
    void Release();

  private:
    /*!
      * @brief 创建ShootGameBlood算法的结果
    */
    void CreateShootBloodRegRst();

    /*!
      * @brief 创建ShootGameHurt算法的结果
    */
    void CreateShootHurtRegRst();

    /*!
      * @brief 创建MultColorVar算法的结果
    */
    void CreateMultColorVarRegRst();

    /*!
      * @brief 创建MapReg算法的结果
    */
    void CreateMapRegRst();

    /*!
      * @brief 创建MapDirectionReg算法的结果
    */
    void CreateMapDirectionRegRst();

    /*!
      * @brief 创建KingGloryBlood算法的结果
    */
    void CreateKingGloryBloodRst();

    /*!
      * @brief 创建固定位置血条检测类型任务结果
    */
    void CreateFixBloodRst();

    /*!
      * @brief 创建位置检测类型任务结果
    */
    void CreateLocationRst();

    /*!
      * @brief 创建血条检测类型任务结果
    */
    void CreateBloodRegRst();

    /*!
      * @brief 创建Stuck类型任务结果
    */
    void CreateStuckRst();

    /*!
      * @brief 创建FixObj类型任务结果
    */
    void CreateFixObjRst();

    /*!
      * @brief 创建PixReg类型任务结果
    */
    void CreatePixRst();

    /*!
      * @brief 创建DeformReg类型任务结果
    */
    void CreateDeformRst();

    /*!
      * @brief 创建NumberReg类型任务结果
    */
    void CreateNumberRst();

  private:
    IRegResult *m_pRegRst;             // 任务结果指针
    EREGTYPE m_eType;                  // 识别类型
    int m_nTaskID;                     // 任务ID
};

// 每一帧对应的所有结果
struct tagFrameResult {
    void Release() {
        for (std::map<int, CTaskResult>::iterator pIter = mapTaskResult.begin();
            pIter != mapTaskResult.end(); ++pIter) {
            pIter->second.Release();
        }
    }

    int     nframeSeq;
    int     ndeviceIndex;
    int     nResNum;            // 任务结果数
    std::string strJsonData;    // 转发给agent
    cv::Mat oFrame;
    // taskID , taskResult
    std::map<int, CTaskResult> mapTaskResult;
};

#endif   // GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKRESULT_H_
