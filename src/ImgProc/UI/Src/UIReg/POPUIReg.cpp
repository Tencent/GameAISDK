/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CLocationReg.h"
#include "Comm/Utils/GameUtils.h"
#include "Comm/Utils/TqcLog.h"
#include "UI/Src/UIReg/POPUIReg.h"

CPOPUIReg::CPOPUIReg()
{
    m_bGamePOPUI  = false;
    m_bDevPOPUI   = false;
    m_nFrameCount = 0;
    m_stGameParam.clear();
    m_stDevParam.clear();
    m_oVecGameCfg.clear();
    m_oVecDevCfg.clear();
}

CPOPUIReg::~CPOPUIReg()
{}

bool CPOPUIReg::Initialize(CUICfg *pUICfg)
{
    // check input parameters
    if (NULL == pUICfg)
    {
        LOGE("Input UICfg is NULL, POP UI Initialize failed");
        return false;
    }

    // fill game pop ui param
    bool bRst = FillGamePOPUIRegParam(pUICfg);
    if (!bRst)
    {
        LOGE("fill game pop ui param failed");
        return false;
    }

    // fill dev pop ui param
    bRst = FillDevPOPUIRegParam(pUICfg);
    if (!bRst)
    {
        LOGE("fill dev pop ui param failed");
        return false;
    }

    LOGI("fill pop ui success");
    return true;
}

int CPOPUIReg::Predict(const cv::Mat &frame, std::vector<tagPOPUIParam> &stParam, cv::Rect &dstRect)
{
    float  fVal   = 0.0;
    float  fTotal = 1.0f;
    int    nIndex = -1;
    double dVal   = 1.0f;

    for (size_t i = 0; i < stParam.size(); i++)
    {
        cv::Rect dstRC;
        float    fMinVal;
        // detect close icons with multi-Process
        int nRes = DetectCloseIcon(stParam[i].nID, frame, stParam[i].oTemplImg, stParam[i].oSrcRect,
                                   stParam[i].fThreshold, &dstRC, &fMinVal);

        // detect failed, continue detect next pop UI
        if (nRes != 1)
        {
            continue;
        }

        if (dstRC.width != 0 && dstRC.height != 0)
        {
            // We should use width x height x fMinVal, because the big matched area
            // is the better.
            float fTmp    = dstRC.width * dstRC.height * fMinVal;
            bool  bUpdate = false;

            // If the matched value is bigger than 0.93, we will use matched value only.
            // Otherwise, we will check width x height x fMinVal.
            if (fMinVal > 0.93 || fVal > 0.93)
            {
                if (fVal < fMinVal)
                    bUpdate = true;
            }
            else
            {
                if (fTotal < fTmp)
                    bUpdate = true;
            }
            if (bUpdate)
            {
                nIndex = i;
                dVal   = 0.1;
                // dstRegion = cv::Rect(dstRC.x, dstRC.y, dstRC.width, dstRC.height);
                fVal    = fMinVal;
                fTotal  = fTmp;
                dstRect = dstRC;
            }
        }
    }

    return nIndex;
}

int CPOPUIReg::Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst)
{
    // check input frame invalid
    if (stFrameCtx.oFrame.empty())
    {
        LOGE("input image is empty");
        return -1;
    }

    m_bGamePOPUI = false;
    m_bDevPOPUI  = false;

    // if number of DevPOPUI and GamePOPUI is 0, there is no need to process.
    m_nFrameCount = stFrameCtx.nFrameCount;
    cv::Mat frame = stFrameCtx.oFrame;
    if (0 == m_stDevParam.size() && 0 == m_stGameParam.size())
    {
        LOGI("count of close icon configure item is 0, please check");
        return -1;
    }

    // check current frame is same as previous one
    if (!IsFrameSame(frame))
    {
        LOGI("current frame is not same as previous");
        return -1;
    }

    // check GamePOPUI template
    tagPOPUIParam stPOPUIParam;
    tagUIState    stUIState;
    cv::Rect      dstRect;
    // first: check game POPUI template, return the index of UIs
    int           nIndex = Predict(frame, m_stGameParam, dstRect);
    cv::Mat       sampleImg;
    if (-1 == nIndex)
    {
        // second: if detect game popUI failed, check devPOPUI template, return the index of UIs
        nIndex = Predict(frame, m_stDevParam, dstRect);
        if (-1 != nIndex)
        {
            stPOPUIParam = m_stDevParam[nIndex];
            stUIState    = m_oVecDevCfg[nIndex];
            sampleImg    = m_oVecDevCfg[nIndex].sampleImg;
            m_bDevPOPUI  = true;
        }
    }
    else
    {
        stPOPUIParam = m_stGameParam[nIndex];
        stUIState    = m_oVecGameCfg[nIndex];
        sampleImg    = m_oVecGameCfg[nIndex].sampleImg;
        m_bGamePOPUI = true;
    }

    // if detect success, package it
    if (m_bDevPOPUI || m_bGamePOPUI)
    {
        stUIRegRst.nID = stPOPUIParam.nID;
        tagUnitAction stAction;
        stAction.eAction = stUIState.actionType;
        int nPtx    = dstRect.x;
        int nPtY    = dstRect.y;
        int nWidth  = dstRect.width;
        int nHeight = dstRect.height;
        stAction.stClickPt.nActionX = static_cast<int>(nPtx + nWidth / 2);
        stAction.stClickPt.nActionY = static_cast<int>(nPtY + nHeight / 2);
        stAction.nDuringTimeMs      = stUIState.nActionDuringTime;
        stAction.nSleepTimeMs       = stUIState.nActionSleepTimeMs;
        stUIRegRst.oVecActions.push_back(stAction);
        stUIRegRst.oSampleImage = sampleImg;
    }

    return nIndex;
}

bool CPOPUIReg::IsDevPOPUI()
{
    return m_bDevPOPUI;
}

bool CPOPUIReg::IsGamePOPUI()
{
    return m_bGamePOPUI;
}

// fill Game POPUI Param
bool CPOPUIReg::FillGamePOPUIRegParam(CUICfg *pUICfg)
{
    CPOPUICfg *pPOPUICfg = dynamic_cast<CPOPUICfg*>(pUICfg);

    m_oVecGameCfg = pPOPUICfg->GetGameCloseIcons();
    return FillPOPUIParam(m_oVecGameCfg, &m_stGameParam);
}

bool CPOPUIReg::FillPOPUIParam(const UIStateArray &oVecCfg, std::vector<tagPOPUIParam> *pstVecParam)
{
    int nSize = oVecCfg.size();

    for (int i = 0; i < nSize; i++)
    {
        tagUIState stUIState = oVecCfg[i];

        tagPOPUIParam stPOPUIParam;
        // POPUI params: UID
        stPOPUIParam.nID        = stUIState.nId;
        // POPUI params: match template thrshold
        stPOPUIParam.fThreshold = stUIState.szTemplState[0].stTemplParam.fThreshold;
        // POPUI params: sample ROI(x,y,w,h)
        int nSampleX = stUIState.szTemplState[0].stTemplParam.nSampleX;
        int nSampleY = stUIState.szTemplState[0].stTemplParam.nSampleY;
        int nSampleW = stUIState.szTemplState[0].stTemplParam.nSampleW;
        int nSampleH = stUIState.szTemplState[0].stTemplParam.nSampleH;
        stPOPUIParam.oSrcRect  = cv::Rect2i(nSampleX, nSampleY, nSampleW, nSampleH);
        stPOPUIParam.oTemplImg = cv::imread(stUIState.strSampleFile);
        if (stPOPUIParam.oTemplImg.empty())
        {
            LOGE("read image %s failed", stUIState.strSampleFile);
            return false;
        }

        pstVecParam->push_back(stPOPUIParam);
    }

    return true;
}

// fill dev POPUI Param
bool CPOPUIReg::FillDevPOPUIRegParam(CUICfg *pUICfg)
{
    CPOPUICfg *pPOPUICfg = dynamic_cast<CPOPUICfg*>(pUICfg);

    m_oVecDevCfg = pPOPUICfg->GetDeviceCloseIcons();
    return FillPOPUIParam(m_oVecDevCfg, &m_stDevParam);
}


bool CPOPUIReg::IsFrameSame(const cv::Mat &frame)
{
    // if last frame is empty, this is the first time to compare, set current frame to m_lastFrame
    if (m_lastFrame.empty())
    {
        frame.copyTo(m_lastFrame);
        return false;
    }

    // if size of last frame is not equal to current frame(windows), no need to compare
    if (m_lastFrame.cols != frame.cols || m_lastFrame.rows != frame.rows)
    {
        frame.copyTo(m_lastFrame);
        return false;
    }

    // 截取图像中间区域，比较是否相同。
    // 中间区域参数，width的GAME_UI_DIALOG_SIZE_RATIO(默认为0.8),height的GAME_UI_DIALOG_SIZE_RATIO(默认为0.8)
    bool bRes       = false;
    int  origWidth  = frame.cols;
    int  origHeight = frame.rows;
    int  width      = (static_cast<int>((origWidth * GAME_UI_DIALOG_SIZE_RATIO) + 16)) &
                      (~(GAME_UI_DIALOG_BLOCK_WIDTH - 1));
    int height = (static_cast<int>((origHeight * GAME_UI_DIALOG_SIZE_RATIO) + 16)) &
                 (~(GAME_UI_DIALOG_BLOCK_WIDTH - 1));
    int x          = (origWidth - width) / 2;
    int y          = (origHeight - height) / 2;
    int blockNumX  = width / GAME_UI_DIALOG_BLOCK_WIDTH;
    int blockNumY  = height / GAME_UI_DIALOG_BLOCK_HEIGHT;
    int totalBlock = blockNumX * blockNumY;
    int sameBlock  = 0;

    cv::Rect dstRC = cv::Rect(x, y, width, height);
    cv::Mat  src;
    cv::Mat  dst;

    frame(dstRC).copyTo(src);
    m_lastFrame(dstRC).copyTo(dst);

    // split image into GAME_UI_DIALOG_BLOCK_WIDTH * GAME_UI_DIALOG_BLOCK_HEIGHT blocks
    for (int i = 0; i < blockNumY; i++)
    {
        for (int j = 0; j < blockNumX; j++)
        {
            // 取第j, i块图像区域
            x = j * GAME_UI_DIALOG_BLOCK_WIDTH;
            y = i * GAME_UI_DIALOG_BLOCK_HEIGHT;
            cv::Rect dstBlkRC = cv::Rect(x, y, GAME_UI_DIALOG_BLOCK_WIDTH, GAME_UI_DIALOG_BLOCK_HEIGHT);
            cv::Mat  srcBlk   = src(dstBlkRC);
            cv::Mat  dstBlk   = dst(dstBlkRC);
            cv::Mat  resBlk;
            int      diff;

            // binary image and match it
            GetBinaryDiff(srcBlk, dstBlk, resBlk);
            // threshold result mat, and sum none-zero pixel number
            GetPXSum(resBlk, diff);
            // if sum less than 30, and the block is valid
            if (diff < 30)
                sameBlock++;
        }
    }

    // computer ratio of valid block number
    float fRatio = static_cast<float>(sameBlock) / static_cast<float>(totalBlock);
    if (fRatio > 0.8f)
    {
        bRes = true;
        LOGW("Screen is freezon. %d / %d, ratio: %0.3f", sameBlock, totalBlock, fRatio);
    }
    else
    {
        LOGD("Screen is not freezon. %d / %d, ratio: %0.3f", sameBlock, totalBlock, fRatio);
    }

    // copy current frame to m_lastFrame
    frame.copyTo(m_lastFrame);
    return bRes;
}
