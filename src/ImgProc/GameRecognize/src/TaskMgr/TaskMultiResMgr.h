/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_MULTI_RES_MGR_H_
#define TASK_MULTI_RES_MGR_H_

#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/GameTime.h"
#include "Comm/Utils/TqcThreadPool.h"
#include "GameRecognize/src/FrameWorkDefine.h"
#include "GameRecognize/src/TaskMgr/TaskContext.h"
#include "GameRecognize/src/TaskMgr/TaskDataDeal.h"
#include "Modules/Json/include/json/json.h"
#include "Protobuf/common.pb.h"

/*!
@class : CMutiResMgr
@brief : 多分辨率处理的相关接口
*/
class CMutiResMgr
{
public:
    CMutiResMgr();
    ~CMutiResMgr();

    /*!
     * @brief 根据识别结果更新任务状态
     * @param[out] pmpTaskCtx 更新状态和参数后的任务列表
     * @param[in] stFrameResult 输入的任务结果
     * @return true or false
     */
    bool UpdateGameTask(std::map<int, TaskContext> *pmpTaskCtx, const tagFrameResult &stFrameResult);

    /*!
     * @brief 释放资源
     */
    void Release();

    /*!
     * @brief 读取refer配置文件
     * @param[out] pmpTaskParam 读取的refer任务参数
     * @param[in] strReferConfName 输入的refer配置文件名
     * @return true or false
     */
    bool LoadReferConfFile(std::map<int, CTaskParam> *pmpTaskParam, const std::string &strReferConfName);

    /*!
     * @brief 获取ObjTask任务ID
     * @param[in] nReferTaskID refer任务ID
     * @return obj任务ID
     */
    int GetObjTaskID(int nReferTaskID);

    /*!
     * @brief 根据目标任务ID获取参考任务ID
     * @param[in] nObjTaskID 目标任务ID
     * @param[out] pVecResTaskID 参考任务ID
     * @return true or false
     */
    bool GetReferTaskID(int nObjTaskID, std::vector<int> *pVecResTaskID);

private:
    /*!
     * @brief 多模板匹配算法的参数填充
     * @param[in] oElements json文件中读取的数据
     * @return true or false
     */
    // bool TemplateReferTask(int nTaskID, Json::Value &oElements);

    /*!
     * @brief 位置匹配算法参数填充
     * @param[out] pLocationParam location参数的指针
     * @param[in] nTaskID 任务ID
     * @param[in] oTask json文件中读取的数据
     * @return true or false
     */
    bool LocationReferTask(CLocationRegParam *pLocationParam, int nTaskID, const Json::Value &oTask);

    /*!
     * @brief 血条检测算法的参数填充
     * @param[out] pBloodLenParam 血条长度检测参数的指针
     * @param[in] nTaskID 任务ID
     * @param[in] oTask json文件中读取的数据
     * @return true or false
     */
    bool BloodReferTask(CBloodLengthRegParam *pBloodLenParam, int nTaskID, const Json::Value &oTask);

    /*!
     * @brief Rect类型参数填充
     * @param[in] oRectValue json文件中读取的数据
     * @param[out] pRect 输出的Rect数据
     * @return true or false
     */
    bool RectParam(cv::Rect *pRect, const Json::Value &oRectValue);

    /*!
     * @brief Rect数组类型参数填充
     * @param[in] oVecRectValue json文件中读取的数据
     * @param[out] pVecRect 输出的Rect数组数据
     * @return true or false
     */
    bool VecRectParam(std::vector<cv::Rect> *pVecRect, const Json::Value &oVecRectValue);

    /*!
     * @brief template模板类型参数填充
     * @param[in] oTmplValue json文件中读取的数据
     * @param[out] oTmpl 输出的tamplate数据
     * @return true or false
     */
//    bool TmplParam(tagTmpl &oTmpl, Json::Value &oTmplValue);

    /*!
     * @brief tamplate模板数组类型参数填充
     * @param[in] oVecTmplValue json文件中读取的数据
     * @param[out] pVecTmpl 输出的template数组数据
     * @return true or false
     */
    bool VecTmplParam(std::vector<tagTmpl> *pVecTmpl, const Json::Value &oVecTmplValue);

    /*!
     * @brief ObjElement数据填充
     * @param[in] oElements json文件中读取的数据
     * @param[out] pnVecTaskID 输出的int数组数据
     * @return true or false
     */
    bool ObjElements(tagTaskElementArray *pnVecTaskID, const Json::Value &oElements);

    /*!
     * @brief 更新location任务对应的objelement参数
     * @param[in] nTaskID refer任务ID
     * @param[out] pmpTaskCtx 任务上下文指针
     * @param[in] pRegResult 检测结果指针
     * @return true or false
     */
    bool UpdateLocationParam(int nTaskID, std::map<int, TaskContext> *pmpTaskCtx, IRegResult *pRegResult);

    /*!
     * @brief 更新template任务对应的objelement参数
     * @param[out] mpTaskCtx 任务队列
     * @param[in] pRegResult 检测结果指针
     * @param pThreadPoolMgr 线程池
     * @return true or false
     */
    // bool UpdateTemplateParam(IRegParam *pRegParam, IRegResult *pRegResult, CThreadPoolMgr *pThreadPoolMgr);

    /*!
     * @brief 更新blood检测任务对应的objelement参数
     * @param[in] nTaskID refer任务ID
     * @param[out] pmpTaskCtx 任务上下文指针
     * @param[in] pRegResult 检测结果指针
     * @return true or false
     */
    bool UpdateBloodRegParam(int nTaskID, std::map<int, TaskContext> *pmpTaskCtx, IRegResult *pRegResult);

    /*!
     * @brief 更新task任务参数
     * @param nTaskID refer任务ID
     * @param pTaskParam 任务参数指针
     * @param pRect 修改的区域
     * @param nRectSize Rect的个数
     * @param fScale 修改的scale
     * @return true or false
     */
    bool UpdateGameTaskParam(int nTaskID, CTaskParam *pTaskParam, cv::Rect *pRect, int nRectSize, float fScale);

    bool LoadReferElement(std::map<int, CTaskParam> *pmpTaskParam, const Json::Value &TaskList,
        const int nIdx, const int nTaskID);
private:
    tagReferObjTaskElements m_mpReferTaskID;    // 多分辨率任务ID对应的游戏任务ID以及element索引
    tagObjTaskReferID       m_mpObjTaskReferID; // 目标游戏任务对应的refer任务ID
};

#endif // TASK_MULTI_RES_MGR_H_
