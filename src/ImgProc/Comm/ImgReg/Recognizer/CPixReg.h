/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef PIX_REG_H_
#define PIX_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CPixReg Structure Define
// **************************************************************************************

struct tagPixRegElement
{
    int         nFilterSize;
    int         nMaxPointNum;
    std::string strCondition;
    cv::Rect    oROI;

    tagPixRegElement()
    {
        nFilterSize  = 1;
        nMaxPointNum = 512;
        strCondition = "";
        oROI         = cv::Rect(-1, -1, -1, -1);
    }
};

struct tagPixRegResult
{
    int       nState;
    int       nPointNum;
    cv::Point szPoints[MAX_POINT_SIZE];
    cv::Mat   oDstImg;

    tagPixRegResult()
    {
        nState    = 0;
        nPointNum = 0;
    }
};

// **************************************************************************************
//          CPixRegParam Class Define
// **************************************************************************************

class CPixRegParam : public IComnBaseRegParam
{
public:
    CPixRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CPixRegParam() {}

public:
    std::vector<tagPixRegElement> m_oVecElements;
};

// **************************************************************************************
//          CPixRegResult Class Define
// **************************************************************************************

class CPixRegResult : public IComnBaseRegResult
{
public:
    CPixRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CPixRegResult() {}

    void SetResult(tagPixRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagPixRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int             m_nResultNum;
    tagPixRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CPixReg Class Define
// **************************************************************************************

class CPixReg : public IComnBaseReg
{
public:
    CPixReg();
    ~CPixReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    int FillColorDetParam(const tagPixRegElement &stParam, CColorDetParam &oParam);

private:
    std::vector<tagPixRegElement> m_oVecParams; // vector of parameters
    std::vector<CColorDet>        m_oVecMethods; // vector of methods
};

#endif /* PIX_REG_H_ */
