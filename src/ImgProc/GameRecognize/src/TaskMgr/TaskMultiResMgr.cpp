/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "GameRecognize/src/TaskMgr/TaskMultiResMgr.h"

extern std::string g_strBaseDir;

CMutiResMgr::CMutiResMgr()
{}

CMutiResMgr::~CMutiResMgr()
{}

bool CMutiResMgr::LoadReferElement(std::map<int, CTaskParam> *pmpTaskParam, const Json::Value &TaskList,
                                   const int nIdx, const int nTaskID)
{
    std::string strRegType = TaskList[nIdx]["type"].asString();

    // todo 多分辨率的param类

    // refer task type  is "location" or "bloodlengthreg"
    if (strRegType == "location")
    {
        IRegParam         *pParam         = (*pmpTaskParam)[nTaskID].GetInstance(TYPE_REFER_LOCATION);
        CLocationRegParam *pLocationParam = dynamic_cast<CLocationRegParam*>(pParam);
        // read parameters from Json value to CLocationRegParam
        if (!LocationReferTask(pLocationParam, nTaskID, TaskList[nIdx]))
        {
            LOGE("LocationReferTask failed");
            return false;
        }
    }
    else if (strRegType == "bloodlengthreg")
    {
        IRegParam            *pParam         = (*pmpTaskParam)[nTaskID].GetInstance(TYPE_REFER_BLOODREG);
        CBloodLengthRegParam *pBloodLenParam = dynamic_cast<CBloodLengthRegParam*>(pParam);
        // read parameters from Json value to CBloodLengthRegParam
        if (!BloodReferTask(pBloodLenParam, nTaskID, TaskList[nIdx]))
        {
            LOGE("BloodReferTask failed");
            return false;
        }
    }
    else
    {
        LOGE("wrong type of refer task Type: %s in taskID: %d", strRegType.c_str(), nTaskID);
        return false;
    }

    return true;
}

// load and parser referfile
bool CMutiResMgr::LoadReferConfFile(std::map<int, CTaskParam> *pmpTaskParam, const std::string &strReferConfName)
{
    if (pmpTaskParam == NULL)
    {
        LOGE("pmpTaskParam is NULL");
        return false;
    }

    m_mpReferTaskID.clear();
    Json::Reader reader;
    Json::Value  root;

    // read and open file reference file
    std::ifstream iFile(strReferConfName);
    if (!iFile.is_open())
    {
        LOGE("can not open : %s", strReferConfName.c_str());
        return false;
    }

    // parser file with Json Format
    if (!reader.parse(iFile, root))
    {
        LOGE("can not read json content: %s", strReferConfName.c_str());
        return false;
    }

    // previous key name is "alltask" and new key name is "allTask"
    if (!root["alltask"].isArray() && !root["allTask"].isArray())
    {
        LOGE("key of 'alltask or allTask' is needed and should be array in %s", strReferConfName.c_str());
        return false;
    }

    // previous key name is "alltask" and new key name is "allTask"
    if (root["alltask"].size() < 1 && root["allTask"].size() < 1)
    {
        LOGE("alltask  or allTask array is empty in %s", strReferConfName.c_str());
        return false;
    }

    // previous key name is [alltask][groupID] and new key name is [allTask][groupID]
    if (!root["alltask"][0]["groupID"].isInt() && !root["allTask"][0]["groupID"].isInt())
    {
        LOGE("key of 'groupID' is needed in %s", strReferConfName.c_str());
        return false;
    }

    // previous key name is [alltask][groupID] and new key name is [allTask][groupID]
    int nGroupID = root["alltask"][0]["groupID"].asInt();
    if (0 == nGroupID)
    {
        nGroupID = root["allTask"][0]["groupID"].asInt();
    }

    // previous key name is [alltask][task] and new key name is [allTask][task]
    if (!root["alltask"][0]["task"].isArray() && !root["allTask"][0]["task"].isArray())
    {
        LOGE("key of 'task' is needed and should be array in %s", strReferConfName.c_str());
        return false;
    }

    // previous key name is [alltask][task] and new key name is [allTask][task]
    Json::Value TaskList = root["alltask"][0]["task"];
    int         nSize    = TaskList.size();
    if (0 == nSize)
    {
        TaskList = root["allTask"][0]["task"];
        nSize    = TaskList.size();
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        if (!TaskList[nIdx]["taskID"].isInt())
        {
            LOGE("key of 'taskID' is needed in %s, index is %d", strReferConfName.c_str(), nIdx);
            return false;
        }

        // 填充refer识别器的参数
        int nTaskID = TaskList[nIdx]["taskID"].asInt();
        (*pmpTaskParam)[nTaskID] = CTaskParam();
        (*pmpTaskParam)[nTaskID].SetTaskID(nTaskID);

        if (!TaskList[nIdx]["type"].isString())
        {
            LOGE("key of 'type' is needed in %s, taskID: %d", strReferConfName.c_str(), nTaskID);
            return false;
        }

        std::string strRegType = TaskList[nIdx]["type"].asString();

        // if (!TaskList[nIdx]["skipFrame"].isInt())
        // {
        //     LOGE("key of 'skipFrame' is needed in %s, taskID: %d", strReferConfName.c_str(), nTaskID);
        //     return false;
        // }

        // (*pmpTaskParam)[nTaskID].SetSkipFrame(TaskList[nIdx]["skipFrame"].asInt());

        // todo 多分辨率的param类

        // refer task type  is "location" or "bloodlengthreg"
        if (!LoadReferElement(pmpTaskParam, TaskList, nIdx, nTaskID))
        {
            return false;
        }
    }

    return true;
}

bool GetObjElements(const Json::Value &oTask, Json::Value &objElement)
{
    objElement = oTask["objElements"];

    if (objElement.isNull())
    {
        objElement = oTask["objElement"];
        if (objElement.isNull())
        {
            LOGE("get objElements or objElement failed");
            return false;
        }
    }

    return true;
}

// read parameters from Json value to CLocationRegParam
bool CMutiResMgr::LocationReferTask(CLocationRegParam *pLocationParam, int nTaskID, const Json::Value &oTask)
{
    if (pLocationParam == NULL)
    {
        LOGE("pLocationParam is NULL");
        return false;
    }

    if (!oTask["algorithm"].isString())
    {
        LOGE("key of 'algorithm' should be string, taskID: %d", nTaskID);
        return false;
    }

    // read oTask["algorithm"] and saved to pLocationParam->m_stParam.strAlgorithm
    pLocationParam->m_stParam.strAlgorithm = oTask["algorithm"].asString();

    // "Infer" Algorithm
    if (pLocationParam->m_stParam.strAlgorithm == "Infer")
    {
        // read oTask["inferROI"] and saved to pLocationParam->m_stParam.oInferROI
        if (!RectParam(&pLocationParam->m_stParam.oInferROI, oTask["inferROI"]))
        {
            LOGE("get inferROI failed");
            return false;
        }

        // read oTask["inferLocations"] and saved to pLocationParam->m_stParam.oVecInferLocations
        if (!VecRectParam(&pLocationParam->m_stParam.oVecInferLocations, oTask["inferLocations"]))
        {
            LOGE("get inferLocations failed");
            return false;
        }
    }
    // nothing to do with Algorithm "Detect"
    else if (pLocationParam->m_stParam.strAlgorithm == "Detect")
    {}
    else
    {
        LOGE("wrong type of algorithm, taskID: %d", nTaskID);
        return false;
    }

    if (oTask["location"].isNull())
    {
        LOGE("key of 'location' is needed, taskID is %d", nTaskID);
        return false;
    }

    // read oTask["location"] and saved to pLocationParam->m_stParam.oLocation
    if (!RectParam(&pLocationParam->m_stParam.oLocation, oTask["location"]))
    {
        LOGE("get location failed");
        return false;
    }

    // read oTask["minScale"], oTask["maxScale"], oTask["scaleLevel"], oTask["expandWidth"],
    // oTask["expandHeight"], oTask["matchCount"] to fMinScale, fMaxScale, nScaleLevel, fExpandWidth
    // fExpandHeight, nMatchCount of pLocationParam->m_stParam
    pLocationParam->m_stParam.fMinScale     = oTask["minScale"].asFloat();
    pLocationParam->m_stParam.fMaxScale     = oTask["maxScale"].asFloat();
    pLocationParam->m_stParam.nScaleLevel   = oTask["scaleLevel"].asInt();
    pLocationParam->m_stParam.fExpandWidth  = oTask["expandWidth"].asFloat();
    pLocationParam->m_stParam.fExpandHeight = oTask["expandHeight"].asFloat();
    pLocationParam->m_stParam.nMatchCount   = oTask["matchCount"].asInt();

    // read oTask["templates"] (Json value) and put value in pLocationParam->m_stParam.oVecTmpls
    if (!VecTmplParam(&pLocationParam->m_stParam.oVecTmpls, oTask["templates"]))
    {
        LOGE("get templates failed");
        return false;
    }

    int nObjTaskID = oTask["objTask"].asInt();

    // previous key name is "objElements" and new key name is "objElement"
    tagTaskElementArray nVecElements;
    Json::Value         objElement;
    if (!GetObjElements(oTask, objElement))
    {
        return false;
    }

    // read objElements List (Json value) and put value in nVecElements
    if (!ObjElements(&nVecElements, objElement))
    {
        LOGE("get objElement failed");
        return false;
    }

    m_mpReferTaskID[nTaskID].nObjTaskID   = nObjTaskID;
    m_mpReferTaskID[nTaskID].nVecElements = nVecElements;
    m_mpObjTaskReferID[nObjTaskID].push_back(nTaskID);

    return true;
}

// read parameters from Json value to CBloodLengthRegParam
bool CMutiResMgr::BloodReferTask(CBloodLengthRegParam *pBloodLenParam, int nTaskID, const Json::Value &oTask)
{
    if (pBloodLenParam == NULL)
    {
        LOGE("pBloodLenParam is NULL");
        return false;
    }

    pBloodLenParam->m_oElement.oAlgorithm = oTask["algorithm"].asString();

    // read oTask["location"] and saved to pBloodLenParam->m_oElement.oROI
    if (!RectParam(&pBloodLenParam->m_oElement.oROI, oTask["location"]))
    {
        LOGE("get location failed");
        return false;
    }

    // read oTask["minScale"], oTask["maxScale"], oTask["scaleLevel"], oTask["expandWidth"],
    // oTask["expandHeight"], oTask["matchCount"] to fMinScale, fMaxScale, nScaleLevel, fExpandWidth
    // fExpandHeight, nMatchCount of pBloodLenParam->m_oElement
    pBloodLenParam->m_oElement.fMinScale     = oTask["minScale"].asFloat();
    pBloodLenParam->m_oElement.fMaxScale     = oTask["maxScale"].asFloat();
    pBloodLenParam->m_oElement.nScaleLevel   = oTask["scaleLevel"].asInt();
    pBloodLenParam->m_oElement.fExpandWidth  = oTask["expandWidth"].asFloat();
    pBloodLenParam->m_oElement.fExpandHeight = oTask["expandHeight"].asFloat();
    pBloodLenParam->m_oElement.nMatchCount   = oTask["matchCount"].asInt();

    if (!oTask["Conditions"].isNull())
    {
        int nSize = oTask["Conditions"].size();

        for (int nIdx = 0; nIdx < nSize; ++nIdx)
        {
            pBloodLenParam->m_oElement.oVecConditions.push_back(oTask["Conditions"][nIdx].asString());
        }
    }

    // read oTask["templates"] (Json value) and put value in pBloodLenParam->m_oElement.oVecTmpls
    if (!VecTmplParam(&pBloodLenParam->m_oElement.oVecTmpls, oTask["templates"]))
    {
        LOGE("get templates failed");
        return false;
    }

    int nObjTaskID = oTask["objTask"].asInt();

    tagTaskElementArray nVecElements;
    // previous key name is "objElements" and new key name is "objElement"
    // read oTask["objElement"] List (Json value) and put value in nVecElements
    if (!ObjElements(&nVecElements, oTask["objElement"]) && !ObjElements(&nVecElements, oTask["objElements"]))
    {
        LOGE("get objElement failed");
        return false;
    }

    m_mpReferTaskID[nTaskID].nObjTaskID   = nObjTaskID;
    m_mpReferTaskID[nTaskID].nVecElements = nVecElements;

    return true;
}

// read objElements List (Json value) and put value in pnVecObjElements
bool CMutiResMgr::ObjElements(tagTaskElementArray *pnVecObjElements, const Json::Value &oElements)
{
    if (pnVecObjElements == NULL)
    {
        LOGE("pnVecObjElements is NULL");
        return false;
    }

    int nSize = oElements.size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        (*pnVecObjElements).push_back(oElements[nIdx].asInt());
    }

    return true;
}

// read oRectValue (Json value) and put value in poRect
bool CMutiResMgr::RectParam(cv::Rect *poRect, const Json::Value &oRectValue)
{
    if (poRect == NULL)
    {
        LOGE("poVecRect is null");
        return false;
    }

    poRect->x      = oRectValue["x"].asInt();
    poRect->y      = oRectValue["y"].asInt();
    poRect->width  = oRectValue["w"].asInt();
    poRect->height = oRectValue["h"].asInt();
    return true;
}

// read oVecRectValue (Json value) and put value in poVecRect
bool CMutiResMgr::VecRectParam(std::vector<cv::Rect> *poVecRect, const Json::Value &oVecRectValue)
{
    if (poVecRect == NULL)
    {
        LOGE("poVecRect is null");
        return false;
    }

    cv::Rect oRect;
    int      nSize = oVecRectValue.size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        // read oVecRectValue[nIdx] (Json value) and put value in oRect
        if (!RectParam(&oRect, oVecRectValue[nIdx]))
        {
            LOGE("get rect failed");
            return false;
        }

        (*poVecRect).push_back(oRect);
    }

    return true;
}

// read oVecTmplValue (Json value) and put value in poVecTmpl
bool CMutiResMgr::VecTmplParam(std::vector<tagTmpl> *poVecTmpl, const Json::Value &oVecTmplValue)
{
    if (poVecTmpl == NULL)
    {
        LOGE("poVecTmpl is null");
        return false;
    }

    tagTmpl oTmpl;
    int     nSize = oVecTmplValue.size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        oTmpl.fThreshold  = oVecTmplValue[nIdx]["threshold"].asFloat();
        oTmpl.strTmplPath = g_strBaseDir + oVecTmplValue[nIdx]["path"].asString();
        if (!oVecTmplValue[nIdx]["location"].isNull())
        {
            if (!RectParam(&oTmpl.oRect, oVecTmplValue[nIdx]["location"]))
            {
                LOGE("get location failed");
                return false;
            }
        }

        (*poVecTmpl).push_back(oTmpl);
    }

    return true;
}

// obtain object task ID with refer task ID
int CMutiResMgr::GetObjTaskID(int nReferTaskID)
{
    return m_mpReferTaskID[nReferTaskID].nObjTaskID;
}

// obtain refer taskList with object task ID
bool CMutiResMgr::GetReferTaskID(int nObjTaskID, std::vector<int> *pVecResTaskID)
{
    *pVecResTaskID = m_mpObjTaskReferID[nObjTaskID];
    return true;
}

// update task state(pmpTaskCtx) with recognizer results(stFrameResult)
bool CMutiResMgr::UpdateGameTask(std::map<int, TaskContext> *pmpTaskCtx, const tagFrameResult &stFrameResult)
{
    if (pmpTaskCtx == NULL)
    {
        LOGE("pmpTaskCtx is null");
        return false;
    }

    std::map<int, CTaskResult>           mpTaskResult = stFrameResult.mapTaskResult;
    std::map<int, CTaskResult>::iterator iter         = mpTaskResult.begin();

    for (; iter != mpTaskResult.end(); ++iter)
    {
        int nTaskID = iter->first;
        if ((*pmpTaskCtx)[nTaskID].GetTaskType() == TYPE_REFER)
        {
            tagTaskState stTaskState = (*pmpTaskCtx)[nTaskID].GetState();
            // if refer task state is TASK_STATE_OVER, ignore it
            if (stTaskState.eTaskExecState == TASK_STATE_OVER)
            {
                LOGW("refer task is over: %d", nTaskID);
                continue;
            }

            EREGTYPE   eRegType = iter->second.GetType();
            IRegResult *pResult = mpTaskResult[nTaskID].GetInstance(eRegType);

            switch (eRegType)
            {
            // get refer task result and update LocationParam
            case TYPE_REFER_LOCATION:
            {
                if (!UpdateLocationParam(nTaskID, pmpTaskCtx, pResult))
                {
                    LOGE("Update Location Param failed");
                    return false;
                }

                break;
            }

            // get refer task result and update TYPE_REFER_BLOODREG
            case TYPE_REFER_BLOODREG:
            {
                if (!UpdateBloodRegParam(nTaskID, pmpTaskCtx, pResult))
                {
                    LOGE("Update BloodReg Param failed");
                    return false;
                }

                break;
            }

            // input type is invalid, return false
            default:
            {
                LOGE("wrong refer reg type");
                return false;
            }
            }
        }
    }

    return true;
}

void UpdateFixObjRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                          tagTaskElementArray &oVecObjElements)
{
    CFixObjRegParam *pFixObjRegParam = dynamic_cast<CFixObjRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pFixObjRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pFixObjRegParam->m_oVecElements.size()));
            continue;
        }

        pFixObjRegParam->m_oVecElements[nObjElementIndex].nScaleLevel = 1;
        pFixObjRegParam->m_oVecElements[nObjElementIndex].fMinScale   = fScale;
        pFixObjRegParam->m_oVecElements[nObjElementIndex].fMaxScale   = fScale;
        pFixObjRegParam->m_oVecElements[nObjElementIndex].oROI        = pRect[nIdx];
    }
}

void UpdatePixRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                       tagTaskElementArray &oVecObjElements)
{
    CPixRegParam *pPixRegParam = dynamic_cast<CPixRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pPixRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pPixRegParam->m_oVecElements.size()));
            continue;
        }

        pPixRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateNumRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                       tagTaskElementArray &oVecObjElements)
{
    CNumRegParam *pNumRegParam = dynamic_cast<CNumRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pNumRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pNumRegParam->m_oVecElements.size()));
            continue;
        }

        pNumRegParam->m_oVecElements[nObjElementIndex].nScaleLevel = 1;
        pNumRegParam->m_oVecElements[nObjElementIndex].fMinScale   = fScale;
        pNumRegParam->m_oVecElements[nObjElementIndex].fMaxScale   = fScale;
        pNumRegParam->m_oVecElements[nObjElementIndex].oROI        = pRect[nIdx];
    }
}

void UpdateStuckRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                         tagTaskElementArray &oVecObjElements)
{
    CStuckRegParam *pStuckRegParam = dynamic_cast<CStuckRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pStuckRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pStuckRegParam->m_oVecElements.size()));
            continue;
        }

        pStuckRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateDeformObjRegParm(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                            tagTaskElementArray &oVecObjElements)
{
    CDeformObjRegParam *pDeformObjRegParam = dynamic_cast<CDeformObjRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pDeformObjRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pDeformObjRegParam->m_oVecElements.size()));
            continue;
        }

        pDeformObjRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateFixBloodRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                            tagTaskElementArray &oVecObjElements)
{
    CFixBloodRegParam *pFixBloodRegParam = dynamic_cast<CFixBloodRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pFixBloodRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pFixBloodRegParam->m_oVecElements.size()));
            continue;
        }

        pFixBloodRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateKingGloryBlood(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                          tagTaskElementArray &oVecObjElements)
{
    CKingGloryBloodRegParam *pKingGloryBloodRegParam = dynamic_cast<CKingGloryBloodRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pKingGloryBloodRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pKingGloryBloodRegParam->m_oVecElements.size()));
            continue;
        }

        pKingGloryBloodRegParam->m_oVecElements[nObjElementIndex].nScaleLevel  = 1;
        pKingGloryBloodRegParam->m_oVecElements[nObjElementIndex].fMinScale    = fScale;
        pKingGloryBloodRegParam->m_oVecElements[nObjElementIndex].fMaxScale    = fScale;
        pKingGloryBloodRegParam->m_oVecElements[nObjElementIndex].nBloodLength = pRect[nIdx].width;
    }
}

void UpdateMapReg(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                  tagTaskElementArray &oVecObjElements)
{
    CMapRegParam *pMapRegParam = dynamic_cast<CMapRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pMapRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pMapRegParam->m_oVecElements.size()));
            continue;
        }

        pMapRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateMapDirRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                          tagTaskElementArray &oVecObjElements)
{
    CMapDirectionRegParam *pMapRegParam = dynamic_cast<CMapDirectionRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pMapRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pMapRegParam->m_oVecElements.size()));
            continue;
        }

        pMapRegParam->m_oVecElements[nObjElementIndex].oROI = pRect[nIdx];
    }
}

void UpdateSGBloodRegParam(IRegParam *pParam, cv::Rect *pRect, const int nRectSize, const float fScale,
                           tagTaskElementArray &oVecObjElements)
{
    CShootGameBloodRegParam *pShootGameBloodRegParam = dynamic_cast<CShootGameBloodRegParam*>(pParam);

    for (int nIdx = 0; nIdx < nRectSize; ++nIdx)
    {
        int nObjElementIndex = oVecObjElements[nIdx];
        if (nObjElementIndex >= pShootGameBloodRegParam->m_oVecElements.size())
        {
            LOGE("out of range, idx: %d, size:%d", nObjElementIndex, \
                 static_cast<int>(pShootGameBloodRegParam->m_oVecElements.size()));
            continue;
        }

        pShootGameBloodRegParam->m_oVecElements[nObjElementIndex].nScaleLevel  = 1;
        pShootGameBloodRegParam->m_oVecElements[nObjElementIndex].fMinScale    = fScale;
        pShootGameBloodRegParam->m_oVecElements[nObjElementIndex].fMaxScale    = fScale;
        pShootGameBloodRegParam->m_oVecElements[nObjElementIndex].nBloodLength = pRect[nIdx].width;
    }
}
// update object task parameters with refer task results(pRect, nRectSize, fScale)
bool CMutiResMgr::UpdateGameTaskParam(int nTaskID, CTaskParam *pTaskParam, cv::Rect *pRect, int nRectSize, float fScale)
{
    if (pTaskParam == NULL)
    {
        LOGE("pRegResult is null");
        return false;
    }

    if (pRect == NULL)
    {
        LOGE("pRect is null");
        return false;
    }

    tagTaskElementArray oVecObjElements = m_mpReferTaskID[nTaskID].nVecElements;

    EREGTYPE  eRegType = pTaskParam->GetType();
    IRegParam *pParam  = pTaskParam->GetInstance(eRegType);

    switch (eRegType)
    {
    // update task parameters of type TYPE_FIXOBJREG with pRect, fScale
    case TYPE_FIXOBJREG:
    {
        UpdateFixObjRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_PIXREG with pRect, fScale
    case TYPE_PIXREG:
    {
        UpdatePixRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_NUMBER with pRect, fScale
    case TYPE_NUMBER:
    {
        UpdateNumRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_STUCKREG with pRect, fScale
    case TYPE_STUCKREG:
    {
        UpdateStuckRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_DEFORMOBJ with pRect
    case TYPE_DEFORMOBJ:
    {
        UpdateDeformObjRegParm(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_FIXBLOOD with pRect
    case TYPE_FIXBLOOD:
    {
        UpdateFixBloodRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_KINGGLORYBLOOD with pRect, fScale
    case TYPE_KINGGLORYBLOOD:
    {
        UpdateKingGloryBlood(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_MAPREG with pRect
    case TYPE_MAPREG:
    {
        UpdateMapReg(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_MAPDIRECTIONREG with pRect
    case TYPE_MAPDIRECTIONREG:
    {
        UpdateMapDirRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_MULTCOLORVAR:do nothing
    case TYPE_MULTCOLORVAR:
    {
        break;
    }

    // update task parameters of type TYPE_SHOOTBLOOD with fScale, pRect
    case TYPE_SHOOTBLOOD:
    {
        UpdateSGBloodRegParam(pParam, pRect, nRectSize, fScale, oVecObjElements);
        break;
    }

    // update task parameters of type TYPE_SHOOTHURT:do nothing
    case TYPE_SHOOTHURT:
    {
        break;
    }

    // input type is invalid, return false
    default:
    {
        LOGE("wrong type: %d", eRegType);
        return false;
    }
    }

    return true;
}

// update task parameters(pmpTaskCtx) with  Location results(pRegResult)
bool CMutiResMgr::UpdateLocationParam(int nTaskID, std::map<int, TaskContext> *pmpTaskCtx, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pRegResult is null");
        return false;
    }

    int         nObjTaskID    = m_mpReferTaskID[nTaskID].nObjTaskID;
    TaskContext *pTaskContext = &(*pmpTaskCtx)[nObjTaskID];

    CLocationRegResult *pLocationRst = dynamic_cast<CLocationRegResult*>(pRegResult);
    if (NULL == pLocationRst)
    {
        LOGE("pLocationRst is NULL");
        return false;
    }

    tagLocationRegResult stLocationRegResult;
    pLocationRst->GetResult(&stLocationRegResult);

    int nState = stLocationRegResult.nState;
    if (nState != 1)
    {
        LOGE("location predict failed");
        return false;
    }

    if (stLocationRegResult.nRectNum > 0)
    {
        // release previous recognizer
        // update game task parameters
        // create recognizer with new parameters
        pTaskContext->ReleaseRecognizer();
        CTaskParam *pTaskParam = pTaskContext->GetParams();
        // update object task parameters with refer task results
        // (pRect, stLocationRegResult.szRects, stLocationRegResult.nRectNum, stLocationRegResult.fScale)
        if (!UpdateGameTaskParam(nTaskID, pTaskParam, stLocationRegResult.szRects, \
                                 stLocationRegResult.nRectNum, stLocationRegResult.fScale))
        {
            LOGE("Update game task param failed");
            return false;
        }

        pTaskContext->CreateRecognizer(nObjTaskID);
        (*pmpTaskCtx)[nTaskID].SetStateFirst(TASK_STATE_OVER);

        std::vector<int> nVecReferTaskID = m_mpObjTaskReferID[nObjTaskID];
        bool             bShouldStart    = true;

        for (size_t nIdx = 0; nIdx < nVecReferTaskID.size(); ++nIdx)
        {
            int            nReferTaskID       = nVecReferTaskID[nIdx];
            TaskContext    *pReferTaskContext = &(*pmpTaskCtx)[nReferTaskID];
            ETaskExecState eTaskExecState     = pReferTaskContext->GetState().eTaskExecState;
            // if one of refer task state is not TASK_STATE_OVER, then object task should not start
            if (eTaskExecState != TASK_STATE_OVER)
            {
                bShouldStart = false;
            }
        }

        if (bShouldStart)
        {
            // set obj task state as TASK_STATE_RUNNING
            (*pmpTaskCtx)[nObjTaskID].SetStateFirst(TASK_STATE_RUNNING);
        }

        LOGI("refer task %d finish", nTaskID);
    }

    return true;
}

// update task parameters(pmpTaskCtx) with  Blood results(pRegResult)
bool CMutiResMgr::UpdateBloodRegParam(int nTaskID, std::map<int, TaskContext> *pmpTaskCtx, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pRegResult is null");
        return false;
    }

    if (pmpTaskCtx == NULL)
    {
        LOGE("pmpTaskCtx is null");
        return false;
    }

    int         nObjTaskID    = m_mpReferTaskID[nTaskID].nObjTaskID;
    TaskContext *pTaskContext = &(*pmpTaskCtx)[nObjTaskID];

    CBloodLengthRegResult *pBloodLenRst = dynamic_cast<CBloodLengthRegResult*>(pRegResult);
    if (NULL == pBloodLenRst)
    {
        LOGE("pBloodLenRst is NULL");
        return false;
    }

    tagBloodLengthRegResult stBloodLengthRegResult = pBloodLenRst->GetResult();

    int nState = stBloodLengthRegResult.nState;
    if (nState == 1)
    {
        // release previous recognizer
        // update game task parameters
        // create recognizer with new parameters
        pTaskContext->ReleaseRecognizer();
        CTaskParam *pTaskParam = pTaskContext->GetParams();

        // update object task parameters(pTaskParam) with refer task results
        // (stBloodLengthRegResult.oROI, 1, stBloodLengthRegResult.fScale)
        if (!UpdateGameTaskParam(nTaskID, pTaskParam, &stBloodLengthRegResult.oROI, 1, stBloodLengthRegResult.fScale))
        {
            LOGE("Update game task param failed");
            return false;
        }

        pTaskContext->CreateRecognizer(nObjTaskID);
        (*pmpTaskCtx)[nTaskID].SetStateFirst(TASK_STATE_OVER);

        std::vector<int> nVecReferTaskID = m_mpObjTaskReferID[nObjTaskID];
        bool             bShouldStart    = true;

        for (size_t nIdx = 0; nIdx < nVecReferTaskID.size(); ++nIdx)
        {
            int            nReferTaskID       = nVecReferTaskID[nIdx];
            TaskContext    *pReferTaskContext = &(*pmpTaskCtx)[nReferTaskID];
            ETaskExecState eTaskExecState     = pReferTaskContext->GetState().eTaskExecState;
            // if one of refer task state is not TASK_STATE_OVER, then object task should not start
            if (eTaskExecState != TASK_STATE_OVER)
            {
                bShouldStart = false;
            }
        }

        if (bShouldStart)
        {
            // set obj task state as TASK_STATE_RUNNING
            (*pmpTaskCtx)[nObjTaskID].SetStateFirst(TASK_STATE_RUNNING);
        }

        LOGI("refer task %d finish", nTaskID);
    }

    return true;
}

// release resource: do nothing now
void CMutiResMgr::Release()
{}

