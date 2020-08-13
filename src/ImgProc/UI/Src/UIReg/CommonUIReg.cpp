/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "UI/Src/UIReg/CommonUIReg.h"
#include "Comm/ImgReg/Recognizer/CLocationReg.h"

CCommonUIReg::CCommonUIReg()
{
    m_stVecParam.clear();
    m_oVecCfg.clear();
    m_oVecOrbMatch.clear();
    m_nVecUseTemplMatch.clear();
    m_nTmplMatchIndex = -1;
    m_nPreUID         = -1;
    m_nSameFrameCnt   = 0;
}

CCommonUIReg::~CCommonUIReg()
{}

bool CCommonUIReg::Initialize(const UIStateArray &oVecCfg)
{
    return FillRegParam(oVecCfg);
}

int CCommonUIReg::Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst)
{
    // check parameters, if m_oVecCfg.size() is 0, no sample UIs¡£
    if (0 == m_oVecCfg.size())
    {
        LOGD("size is 0");
        return 0;
    }

    // Predict common UIs, return nIndex is matched UI index
    int      nIndex = -1;
    cv::Rect dstRect;
    nIndex = Predict(stFrameCtx.oFrame, m_stVecParam, dstRect);

    int nRstIndex     = nIndex;
    int nSameFrameCnt = -1;
    if (-1 != nIndex)
    {
        // get same frame count config
        nSameFrameCnt = m_oVecCfg[nIndex].nCheckSameFrameCnt;
    }

    // index is same as previous one:
    // 1) check sample file: if same, set flag as true
    // 2) check receieve frame: if same, set falg as true
    // 3) if  a) flag is true b) same frame count is less than threshold 3) type is not UI_ACTION_DRAG_AND_CHECK
    //    reset result index as -1

    if (nIndex != m_nPreUID)
    {
        LOGD("index is not equal to previous UID");
        bool bFlag = false;
        // method 1, compare UI sample, same UI sample image with different UI ID
        if (m_nPreUID != -1 && nIndex != -1
            && (0 == strcmp(m_oVecCfg[nIndex].strSampleFile, m_oVecCfg[m_nPreUID].strSampleFile)))
        {
            LOGD("set flag as true");
            bFlag = true;
        }

        // method 2, check current frame is same as previous frame
        if (!m_oPreFrame.empty() && nIndex != -1 && stFrameCtx.oFrame.cols == m_oPreFrame.cols
            && stFrameCtx.oFrame.rows == m_oPreFrame.rows)
        {
            cv::Mat oResult(1, 1, CV_32FC1);
            cv::matchTemplate(stFrameCtx.oFrame, m_oPreFrame, oResult, CV_TM_SQDIFF_NORMED);

            double    dMinVal;
            double    dMaxVal;
            cv::Point oMinLoc;
            cv::Point oMaxLoc;
            cv::minMaxLoc(oResult, &dMinVal, &dMaxVal, &oMinLoc, &oMaxLoc);

            float fScore = static_cast<float>(1 - dMinVal);
            if (fScore > 0.98)
            {
                LOGD("score > 0.98, set flag as true");
                bFlag = true;
            }
        }

        if (nIndex != -1
            && bFlag
            && m_nSameFrameCnt < nSameFrameCnt
            && m_oVecCfg[nIndex].actionType != UI_ACTION_DRAG_AND_CHECK)
        {
            m_nSameFrameCnt++;
            LOGI("same frame, diff stateID, discard curStateID, send none action");
            nRstIndex = -1;
        }
    }
    // index is same as previous one, check frame count
    else if (nIndex != -1)
    {
        m_nSameFrameCnt++;
        if (m_nSameFrameCnt < nSameFrameCnt)
        {
            nRstIndex = -1;
        }
    }

    if (nRstIndex == nIndex && nIndex != -1)
    {
        m_nSameFrameCnt = 0;
    }

    m_nPreUID = nIndex;
    stFrameCtx.oFrame.copyTo(m_oPreFrame);

    if (-1 != nRstIndex)
    {
        LOGD("result index is %d, package message", nRstIndex);
        tagUIState stUIState;
        stUIState      = m_oVecCfg[nRstIndex];
        stUIRegRst.nID = stUIState.nId;
        tagUnitAction stAction;
        stAction.eAction = stUIState.actionType;
        int nPtx    = dstRect.x;
        int nPtY    = dstRect.y;
        int nWidth  = dstRect.width;
        int nHeight = dstRect.height;
        stAction.stClickPt = stUIState.stAction1;

        stAction.stVecDragPt.push_back(stUIState.stAction1);
        stAction.stVecDragPt.push_back(stUIState.stAction2);

        stAction.nDuringTimeMs = stUIState.nActionDuringTime;
        stAction.nSleepTimeMs  = stUIState.nActionSleepTimeMs;
        stUIRegRst.oVecActions.push_back(stAction);
        stUIRegRst.oSampleImage = m_stVecParam[nIndex].oUIImg;
    }

    return nRstIndex;
}

bool CCommonUIReg::FillRegParam(const UIStateArray &oVecCfg)
{
    m_oVecCfg = oVecCfg;
    int nSize = m_oVecCfg.size();

    for (int i = 0; i < nSize; i++)
    {
        tagUIState        stUIState = m_oVecCfg[i];
        tagCommonRegParam stRegParam;

        // read UID
        stRegParam.nUID = stUIState.nId;
        // read key point threshold
        stRegParam.nKeyPtThr = stUIState.nMatched;

        // read UI image, if not exist, return false
        stRegParam.oUIImg = cv::imread(stUIState.strSampleFile);
        if (stRegParam.oUIImg.empty())
        {
            LOGE("read image %s failed", stUIState.strSampleFile);
            return false;
        }

        cv::Ptr<cv::ORB> pOrb = cv::ORB::create();
        if (pOrb == NULL)
        {
            LOGE("%s(%d): cannot allocate ORB detector.", __FUNCTION__, __LINE__);
            return false;
        }

        KeyPoints kp;
        cv::Mat   dp;
        pOrb->detectAndCompute(stRegParam.oUIImg, cv::Mat(), kp, dp);

        // get template params
        stRegParam.eTmplOp = stUIState.tempOp;

        if (stUIState.tempOp == UI_TEMPLATE_OR)
        {
            m_nVecUseTemplMatch.push_back(1);
        }
        else if (stUIState.tempOp == UI_TEMPLATE_AND)
        {
            m_nVecUseTemplMatch.push_back(stUIState.nTemplate);
        }
        else
        {
            m_nVecUseTemplMatch.push_back(0);
        }

        for (int i = 0; i < stUIState.nTemplate; i++)
        {
            tagTmplateParam oTmplParam;
            int             nX = stUIState.szTemplState[i].stTemplParam.nSampleX;
            int             nY = stUIState.szTemplState[i].stTemplParam.nSampleY;
            int             nW = stUIState.szTemplState[i].stTemplParam.nSampleW;
            int             nH = stUIState.szTemplState[i].stTemplParam.nSampleH;
            oTmplParam.oSrcRect   = cv::Rect(nX, nY, nW, nH);
            oTmplParam.fThreshold = stUIState.szTemplState[i].stTemplParam.fThreshold;
            stRegParam.stVecTmplParam.push_back(oTmplParam);
        }

        // build orb math param;
        CORBMatchParam param;
        param.m_nEdgeThreshold = 31;

        tagTmpl stTmpl;
        stTmpl.oTmplImg = stRegParam.oUIImg;
        if (kp.size() > 0)
        {
            stTmpl.fThreshold = stRegParam.nKeyPtThr * 1.0f / kp.size();
        }
        else
        {
            stTmpl.fThreshold = 0.0f;
        }

        stTmpl.oRect = cv::Rect(0, 0, stRegParam.oUIImg.cols, stRegParam.oUIImg.rows);
        param.m_oVecTmpls.push_back(stTmpl);
        param.m_oROI    = cv::Rect(0, 0, stRegParam.oUIImg.cols, stRegParam.oUIImg.rows);
        param.m_nTaskID = stUIState.nId;

        // add ORB Matcher
        CORBMatch oORBMatch;
        if (oORBMatch.Initialize(&param) > 0)
        {
            m_oVecOrbMatch.push_back(oORBMatch);
        }
        else
        {
            LOGE("orb match initialize failed");
            return false;
        }

        m_stVecParam.push_back(stRegParam);
    }

    LOGI("fill hall reg param over");
    return true;
}

int CCommonUIReg::Predict(const cv::Mat &frame, const std::vector<tagCommonRegParam> &stParam, cv::Rect &DstRect)
{
    m_nTmplMatchIndex = -1;
    CObjDetData oImgProData;

    oImgProData.m_oSrcImg = frame;
    oImgProData.m_oROI    = cv::Rect(0, 0, frame.cols, frame.rows);

    CObjDetResult      oResult;
    std::vector<float> fKPTVecMatch;
    std::vector<bool>  bTmplVecMatch;

    for (int i = 0; i < m_oVecOrbMatch.size(); i++)
    {
        // first:orb Match
        m_oVecOrbMatch[i].Predict(&oImgProData, &oResult);
        if (oResult.m_oVecBBoxes.size() <= 0)
        {
            // if orb match failed
            // push 0 to orb match result
            fKPTVecMatch.push_back(0);
            // if orb match failed, there is no need to process match template
            bTmplVecMatch.push_back(false);
            continue;
        }
        else
        {
            // orb match success: put the score of orb match result
            fKPTVecMatch.push_back(oResult.m_oVecBBoxes.at(0).fScore);
        }

        // second: template match
        bool bMatch = CheckMatch(frame, stParam[i]);
        // push match result to bTmplVecMatch
        bTmplVecMatch.push_back(bMatch);
        LOGD("index is %d, key point match result is %zd, template match result is %d",
             i, oResult.m_oVecBBoxes.size(), bMatch);
    }

    // if find template match result and return template match UI index
    return FindMatch(fKPTVecMatch, bTmplVecMatch);
}

bool CCommonUIReg::CheckMatch(const cv::Mat &frame, const tagCommonRegParam &stRegParam)
{
    if (stRegParam.stVecTmplParam.size() == 0)
    {
        return true;
    }

    // detect each template
    std::vector<bool> bVecFound;

    for (int j = 0; j < stRegParam.stVecTmplParam.size(); j++)
    {
        tagTmplateParam stTmplParam = stRegParam.stVecTmplParam[j];
        cv::Rect        dstRC;
        dstRC.width  = 0;
        dstRC.height = 0;
        float fMinVal = 0.0f;
        int   nRes    = DetectRect(stRegParam.nUID, frame, stRegParam.oUIImg, stTmplParam.oSrcRect,
                                   stTmplParam.fThreshold, &dstRC, &fMinVal);

        if (dstRC.width != 0 && dstRC.height != 0)
        {
            bVecFound.push_back(true);
        }
        else
        {
            bVecFound.push_back(false);
        }
    }

    bool bMatched = false;

    switch (stRegParam.eTmplOp)
    {
    case UI_TEMPLATE_AND:
        bMatched = true;

        for (int i = 0; i < bVecFound.size(); i++)
        {
            // If there is one unmatched template image,
            // we should return false.
            if (bVecFound[i] == false)
            {
                bMatched = false;
                break;
            }
        }

        break;

    case UI_TEMPLATE_OR:
        bMatched = false;

        for (int i = 0; i < bVecFound.size(); i++)
        {
            // If there is one unmatched template image,
            // we should return false.
            if (bVecFound[i] == true)
            {
                bMatched = true;
                break;
            }
        }

        break;

    default:
        break;
    }

    return bMatched;
}

int CCommonUIReg::FindMatch(const std::vector<float> &fKPTVecMatch, const std::vector<bool> &bTmplVecMatch)
{
    int   nIndex    = -1;
    int   nMatchNum = 0;
    float fMaxScroe = 0;

    for (int i = 0; i < m_nVecUseTemplMatch.size(); i++)
    {
        // with template but match failed
        if (!bTmplVecMatch[i])
        {
            continue;
        }

        // use template
        // update condition 1) or 2)
        // 1) more number of templates
        // 2) same number of tamplates, but more orb match points
        if (m_nVecUseTemplMatch[i] > 0)
        {
            if (m_nVecUseTemplMatch[i] > nMatchNum)
            {
                nMatchNum = m_nVecUseTemplMatch[i];
                nIndex    = i;
            }
            else if (m_nVecUseTemplMatch[i] == nMatchNum && nIndex >= 0)
            {
                if (fKPTVecMatch[i] > fKPTVecMatch[nIndex])
                {
                    nMatchNum = m_nVecUseTemplMatch[i];
                    nIndex    = i;
                }
            }
        }
        // without template
        // update condtion: with more orb match points(score is bigger)
        else
        {
            if (fKPTVecMatch[i] > fMaxScroe)
            {
                fMaxScroe = fKPTVecMatch[i];
                nMatchNum = 0;
                nIndex    = i;
            }
        }
    }

    return nIndex;
}
