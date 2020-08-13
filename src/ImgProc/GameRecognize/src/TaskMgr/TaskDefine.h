/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_DEFINE_H_
#define TASK_DEFINE_H_

#include <boost/thread.hpp>
#include <iostream>
#include <map>
#include <string>
#include <vector>

#include "Comm/ImgReg/Recognizer/CBloodLengthReg.h"
#include "Comm/ImgReg/Recognizer/CDeformObjReg.h"
#include "Comm/ImgReg/Recognizer/CFixBloodReg.h"
#include "Comm/ImgReg/Recognizer/CFixObjReg.h"
#include "Comm/ImgReg/Recognizer/CKingGloryBloodReg.h"
#include "Comm/ImgReg/Recognizer/CLocationReg.h"
#include "Comm/ImgReg/Recognizer/CMapDirectionReg.h"
#include "Comm/ImgReg/Recognizer/CMapReg.h"
#include "Comm/ImgReg/Recognizer/CMultColorVarReg.h"
#include "Comm/ImgReg/Recognizer/CNumReg.h"
#include "Comm/ImgReg/Recognizer/CPixReg.h"
#include "Comm/ImgReg/Recognizer/CShootGameBloodReg.h"
#include "Comm/ImgReg/Recognizer/CShootGameHurtReg.h"
#include "Comm/ImgReg/Recognizer/CStuckReg.h"
#include "Comm/Utils/TqcLog.h"
#include "Comm/Utils/TqcMemoryPool.h"
#include "Protobuf/common.pb.h"

// ==============================================================================
// 定义识别器需要的数据结构
// ==============================================================================
class CTaskParam
{
public:
    CTaskParam()
    {
        m_nTaskID    = 0;
        m_eType      = TYPE_BEGIN;
        m_pRegParam  = NULL;
        m_nSkipFrame = -1;
    }

    ~CTaskParam()
    {}

    void Release()
    {
        if (m_pRegParam != NULL)
        {
            delete m_pRegParam;
            m_pRegParam = NULL;
        }
    }

    /*!
     * @brief 设置任务结果对应的识别类型
     * @param[in] eType 识别类型
     */
    void SetType(EREGTYPE eType)
    {
        m_eType = eType;
    }

    /*!
     * @brief 获取结果对应的识别类型
     */
    EREGTYPE GetType()
    {
        return m_eType;
    }


    void SetTaskID(int nTaskID)
    {
        m_nTaskID = nTaskID;
    }


    int GetTaskID()
    {
        return m_nTaskID;
    }

    void SetSkipFrame(int nSkipFrame)
    {
        m_nSkipFrame = nSkipFrame;
    }


    int GetSkipFrame()
    {
        return m_nSkipFrame;
    }

    // 获取对象参数
    // 如果没有初始化，则new一个
    IRegParam* GetInstance(EREGTYPE eType)
    {
        if (NULL != m_pRegParam)
        {
            return m_pRegParam;
        }

        m_eType = eType;

        switch (eType)
        {
        case TYPE_FIXOBJREG:
        {
            m_pRegParam = new CFixObjRegParam();
            break;
        }

        case TYPE_PIXREG:
        {
            m_pRegParam = new CPixRegParam();
            break;
        }

        case TYPE_STUCKREG:
        {
            m_pRegParam = new CStuckRegParam();
            break;
        }

        case TYPE_NUMBER:
        {
            m_pRegParam = new CNumRegParam();
            break;
        }

        case TYPE_DEFORMOBJ:
        {
            m_pRegParam = new CDeformObjRegParam();
            break;
        }

        case TYPE_FIXBLOOD:
        {
            m_pRegParam = new CFixBloodRegParam();
            break;
        }

        case TYPE_KINGGLORYBLOOD:
        {
            m_pRegParam = new CKingGloryBloodRegParam();
            break;
        }

        case TYPE_MAPREG:
        {
            m_pRegParam = new CMapRegParam();
            break;
        }

        case TYPE_MAPDIRECTIONREG:
        {
            m_pRegParam = new CMapDirectionRegParam();
            break;
        }

        case TYPE_MULTCOLORVAR:
        {
            m_pRegParam = new CMultColorVarRegParam();
            break;
        }

        case TYPE_SHOOTBLOOD:
        {
            m_pRegParam = new CShootGameBloodRegParam();
            break;
        }

        case TYPE_SHOOTHURT:
        {
            m_pRegParam = new CShootGameHurtRegParam();
            break;
        }

        case TYPE_REFER_LOCATION:
        {
            m_pRegParam = new CLocationRegParam();
            break;
        }

        case TYPE_REFER_BLOODREG:
        {
            m_pRegParam = new CBloodLengthRegParam();
            break;
        }

        default:
        {
            LOGE("invalid type %d", eType);
            break;
        }
        }

        return m_pRegParam;
    }

private:
    int       m_nTaskID;
    EREGTYPE  m_eType;
    int       m_nSkipFrame;
    IRegParam *m_pRegParam;
};

// thread pool use
struct tagTask
{
    boost::function<void()> ofunc;
    int                     nLevel;
    int                     nOverload;
    tagTask()
    {
        nLevel    = -1;
        nOverload = -1;
    }
//    int                     nFrameSeq;
};

// runtime varient
struct tagRuntimeVar
{
    cv::Mat oSrcImage;
    int     nFrameSeq;
    int     nDeviceIndex;
    int     nTaskID;
};

// recv src image info from auto/MC
struct tagSrcImgInfo
{
    cv::Mat     oSrcImage;
    uint64_t    uFrameSeq;
    uint64_t    uDeviceIndex;
    std::string strJsonData;
};

// task type of receiving from Agent/MC


struct tagCmdMsg
{
    tagCmdMsg(){}
    virtual ~tagCmdMsg() {};
    virtual void Release() {};
};

// group message
struct tagAgentMsg : tagCmdMsg
{
    // taskID, taskParameters
    unsigned int              uGroupID;
    std::map<int, CTaskParam> mapTaskParams;

    tagAgentMsg()
    {
        uGroupID = 1;
    }

    virtual void Release()
    {}
};

// task flag message
struct tagTaskFlagMsg : tagCmdMsg
{
    // taskID, flag
    std::map<int, bool> mapTaskFlag;
};

//// delete task message
struct tagDelTaskMsg : tagCmdMsg
{
    // taskID
    std::vector<int> nVecTask;
};

struct tagConfTaskMsg : tagCmdMsg
{
    // conf file name
    std::vector<std::string> strVecConfName;
};

// ms
const int GM_WAITING_RESULT_TIME = 20;
#endif // TASK_DEFINE_H_
