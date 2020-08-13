/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef STUCK_REG_H_
#define STUCK_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

#define MATCH_SIZE 64

// **************************************************************************************
//          CStuckReg Structure Define
// **************************************************************************************

struct tagStuckRegElement
{
    int         nMatchHeight;
    int         nMatchWidth;
    float       fIntervalTime;
    float       fThreshold;
    std::string strMaskPath;
    cv::Rect    oROI;

    tagStuckRegElement()
    {
        nMatchHeight  = 64;
        nMatchWidth   = 64;
        fIntervalTime = 5.0f;
        fThreshold    = 0.95f;
        strMaskPath   = "";
        oROI          = cv::Rect(-1, -1, -1, -1);
    }
};

struct tagStuckRegResult
{
    int      nState;
    cv::Rect oROI;

    tagStuckRegResult()
    {
        nState = 0;
        oROI   = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CStuckRegTmplMatch Class Define
// **************************************************************************************

class CStuckRegTmplMatch
{
public:
    CStuckRegTmplMatch();
    ~CStuckRegTmplMatch();

    int Initialize(const int nTaskID, const tagStuckRegElement &stParam);
    int Predict(const cv::Mat &oSrcImg, const int nFrameIdx, tagStuckRegResult &stResult);
    int Release();

private:
    int      m_nTaskID;
    int      m_nPrevState;
    int      m_nMatchHeight;
    int      m_nMatchWidth;
    float    m_fIntervalTime;
    float    m_fThreshold;
    clock_t  m_cTime;
    cv::Rect m_oROI;
    cv::Mat  m_oTmplImg;
    cv::Mat  m_oMaskImg;

    LockerHandle m_hStateLock;
    LockerHandle m_hTimeLock;
};

// **************************************************************************************
//          CStuckRegParam Class Define
// **************************************************************************************

class CStuckRegParam : public IComnBaseRegParam
{
public:
    CStuckRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CStuckRegParam() {}

public:
    std::vector<tagStuckRegElement> m_oVecElements;
};

// **************************************************************************************
//          CStuckRegResult Class Define
// **************************************************************************************

class CStuckRegResult : public IComnBaseRegResult
{
public:
    CStuckRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CStuckRegResult() {}

    void SetResult(tagStuckRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagStuckRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int               m_nResultNum;
    tagStuckRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CStuckReg Class Define
// **************************************************************************************

class CStuckReg : public IComnBaseReg
{
public:
    CStuckReg();
    ~CStuckReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagStuckRegElement> m_oVecParams; // vector of parameters
    std::vector<CStuckRegTmplMatch> m_oVecMethods; // vector of methods
};

#endif /* STUCK_REG_H_ */
