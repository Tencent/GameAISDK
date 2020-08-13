/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef GAMEREG_FRAMEWORK_H_
#define GAMEREG_FRAMEWORK_H_

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <vector>


#include "Comm/Utils/GameTime.h"
#include "Comm/Utils/IniConfig.h"
#include "Comm/Utils/JsonConfig.h"
#include "Comm/Utils/TqcLog.h"
#include "Comm/Utils/TqcThreadPool.h"
#include "GameRecognize/src/NetWorkManager.h"


/*!
@class CGameRegFrameWork
@brief GameReg进程框架实现类
*/
class CGameRegFrameWork
{
public:
    CGameRegFrameWork();
    ~CGameRegFrameWork();

    /*!
     * @brief 初始化
     * @return 0表示成功，-1表示失败
     */
    int Initialize();

    /*!
     * @brief run
     * return 0表示成功，-1表示失败
     */
    int Run();

    /*!
     * @brief 退出
     */
    void SetExited();

    /*!
     * @brief 释放资源
     */
    void Release();

    /*!
     * @brief 设置测试模式
     */
    void SetTestMode(bool bDebug, ETestMode eTestMode);

private:
    /*!
     * @brief run for SDK
     * return 0表示成功，-1表示失败
     */
    int RunForSDK();

    /*!
     * @brief run for SDKTool test
     * return 0表示成功，-1表示失败
     */
    int RunForSDKTool();

    /*!
     * @brief run for video test
     * return 0表示成功，-1表示失败
     */
    int RunForVideo();

    /*!
     * @brief 从视频获取图像帧
     * @param stSrcImgInfo[out] 图像帧信息
     * @return 0表示成功，-1表示失败
     */
//    int GetImgFromeVideo(tagSrcImgInfo &stSrcImgInfo);

    /*!
     * @brief 读取配置文件
     * @param[out] nThreadNum获取的线程数
     * @return 0表示成功，-1表示失败
     */
    int LoadConfg(int *nThreadNum);

     /*!
      * @brief 读取task.json配置文件，用于视频测试
      * @param oVecTaskMsg 消息数据，供TaskManager使用
      * @param strTaskCfg task.json路径
      * @return 0表示成功，-1表示失败
      */
    int LoadTaskCfg(std::vector<CTaskMessage> *oVecTaskMsg, std::string strTaskCfg);

    /*!
     * @brief 读取FixObj类型的任务参数
     * @param oTaskFixObjElements[in] Json变量
     * @param pFixObjRegParam[out] FixObj的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskFixObj(Json::Value oTaskFixObjElements, CFixObjRegParam *pFixObjRegParam);

    /*!
     * @brief 读取Pix类型的任务参数
     * @param oTaskPixElements[in] Json变量
     * @param pPixRegParam[out] pix的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskPix(Json::Value oTaskPixElements, CPixRegParam *pPixRegParam);

    /*!
     * @brief 读取Deform类型的任务参数
     * @param oTaskDeformElements[in] Json变量
     * @param pDeformRegParam[out] Deform的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskDeform(Json::Value oTaskDeformElements, CDeformObjRegParam *pDeformRegParam);

    /*!
     * @brief 读取Stuck类型的任务参数
     * @param oTaskStuckElements[in] Json变量
     * @param pStuckRegParam[out] Stuck的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskStuck(Json::Value oTaskStuckElements, CStuckRegParam *pStuckRegParam);

    /*!
     * @brief 读取number类型的任务参数
     * @param oTaskNumberElements[in] Json变量
     * @param pNumRegParam[out] Number的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskNumber(Json::Value oTaskNumberElements, CNumRegParam *pNumRegParam);

    /*!
     * @brief 读取FixBlood类型的任务参数
     * @param oTaskFixBloodElements[in] Json变量
     * @param pFixBloodRegParam[out] FixBlood的参数指针
     * @return 0表示成功，-1表示失败
     */
    int LoadTaskFixBlood(Json::Value oTaskFixBloodElements, CFixBloodRegParam *pFixBloodRegParam);

    /*!
     * @brief 读取Rect类型参数
     * @param oJsonRect[in] Json变量
     * @param oRect[out] 输出的Rect对象
     * @return 0表示成功，-1表示失败
     */
    int LoadRect(Json::Value oJsonRect, cv::Rect *oRect);

    /*!
     * @brief 读取模板参数
     * @param oJsonTemplates[in] Json变量
     * @param oVecTemplates[out] 输出的模板参数
     * @return 0表示成功，-1表示失败
     */
    int LoadTemplates(Json::Value oJsonTemplates, std::vector<tagTmpl> *oVecTemplates);

    /*!
     * @brief 初始化日志
     * @param strProgName 日志文件路径
     * @param strLevel 日志级别
     * @return true or false
     */
    bool CreateLog(const char *strProgName, const char *strLevel);

private:
    CGameTime m_oGameTime;               // 获取系统时间对象

    CNetWorkManager m_oNetWorkManager;   // 网络管理对象
    CThreadPoolMgr m_oThreadPoolMgr;     // 线程池对象
    CTaskManager m_oTaskManager;         // 任务管理对象
    bool m_bExited;
    bool m_bTestFlag;
    std::string m_strTestVideo;
    int m_nFrameRate;
    bool m_bMultiResolution;
    bool m_bConnectAgent;
    ETestMode m_eTestMode;               // GameReg以哪种模式运行，SDK，Video，SDKTool
};

#endif // GAMEREG_FRAMEWORK_H_
/*! @} */
