/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef SHOOT_GAME_BLOOD_REG_H_
#define SHOOT_GAME_BLOOD_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/ImgProcess/CGradMatch.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CShootGameBloodReg Structure Define
// **************************************************************************************

struct tagShootGameBloodRegParam
{
    int                  nBloodLength;
    int                  nMaxPointNum;
    int                  nFilterSize;
    int                  nScaleLevel;
    float                fMinScale;
    float                fMaxScale;
    cv::Rect             oROI;
    std::string          strCondition;
    std::vector<tagTmpl> oVecTmpls;

    tagShootGameBloodRegParam()
    {
        nBloodLength = 123;
        nMaxPointNum = 1024;
        nFilterSize  = 0;
        nScaleLevel  = 1;
        fMinScale    = 1.0;
        fMaxScale    = 1.0;
        oROI         = cv::Rect(-1, -1, -1, -1);
        strCondition = "";
        oVecTmpls.clear();
    }
};

struct tagShootGameBloodRegResult
{
    int      nState;
    tagBlood stBlood;
    cv::Rect oROI;

    tagShootGameBloodRegResult()
    {
        nState = 0;
        oROI   = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CShootGameBloodRegMethod Class Define
// **************************************************************************************

class CShootGameBloodRegMethod
{
public:
    CShootGameBloodRegMethod();
    ~CShootGameBloodRegMethod();

    int Initialize(const int nTaskID, const tagShootGameBloodRegParam *pParam);
    int Predict(const cv::Mat &oSrcImg, tagShootGameBloodRegResult &stResult);
    int Release();

private:
    int FillGradMatchParam(const tagShootGameBloodRegParam &stParam, CGradMatchParam &oParam);
    int FillColorDetParam(const tagShootGameBloodRegParam &stParam, CColorDetParam &oParam);

private:
    int      m_nTaskID;
    int      m_nBloodLength;
    cv::Rect m_oROI;

    CGradMatch m_oGradMatch;
    CColorDet  m_oColorDet;
};

// **************************************************************************************
//          CShootGameBloodRegParam Class Define
// **************************************************************************************

class CShootGameBloodRegParam : public IComnBaseRegParam
{
public:
    CShootGameBloodRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CShootGameBloodRegParam() {}

public:
    std::vector<tagShootGameBloodRegParam> m_oVecElements;
};

// **************************************************************************************
//          CShootGameBloodRegResult Class Define
// **************************************************************************************

class CShootGameBloodRegResult : public IComnBaseRegResult
{
public:
    CShootGameBloodRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CShootGameBloodRegResult() {}

    void SetResult(tagShootGameBloodRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagShootGameBloodRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int                        m_nResultNum;
    tagShootGameBloodRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CShootGameBloodReg Class Define
// **************************************************************************************

class CShootGameBloodReg : public IComnBaseReg
{
public:
    CShootGameBloodReg();
    ~CShootGameBloodReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagShootGameBloodRegParam> m_oVecParams; // vector of parameters
    std::vector<CShootGameBloodRegMethod>  m_oVecMethods; // vector of methods
};

#endif /* SHOOT_GAME_BLOOD_REG_H_ */
