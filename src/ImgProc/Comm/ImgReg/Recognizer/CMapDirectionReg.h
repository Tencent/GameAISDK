/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef MAP_DIRECTION_REG_H_
#define MAP_DIRECTION_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CMapDirectionReg Structure Define
// **************************************************************************************

struct tagMapDirectionRegParam
{
    int         nFilterSize;
    int         nMaxPointNum;
    int         nDilateSize;
    int         nErodeSize;
    int         nRegionSize;
    std::string strCondition;
    std::string strMyLocCondition;
    std::string strViewLocCondition;
    std::string strMapMaskPath;
    cv::Rect    oROI;

    tagMapDirectionRegParam()
    {
        nMaxPointNum        = 512;
        nFilterSize         = 1;
        nDilateSize         = 5;
        nErodeSize          = 2;
        nRegionSize         = 10;
        oROI                = cv::Rect(-1, -1, -1, -1);
        strCondition        = "";
        strMyLocCondition   = "";
        strViewLocCondition = "";
        strMapMaskPath      = "";
    }
};

struct tagMapDirectionRegResult
{
    int       nState;
    cv::Point oMyLocPoint;
    cv::Point oViewLocPoint;
    cv::Point oViewAnglePoint;
    cv::Rect  oROI;

    tagMapDirectionRegResult()
    {
        nState = 0;
        oROI   = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CMapDirectionRegColorDet Class Define
// **************************************************************************************

class CMapDirectionRegColorDet
{
public:
    CMapDirectionRegColorDet();
    ~CMapDirectionRegColorDet();

    int Initialize(const int nTaskID, tagMapDirectionRegParam *pParam);
    int Predict(const cv::Mat &oSrcImg, tagMapDirectionRegResult &stResult);
    int Release();

private:
    int FillColorDetParam(const tagMapDirectionRegParam &stParam, CColorDetParam &oParam);

private:
    int      m_nTaskID;
    int      m_nErodeSize;
    int      m_nDilateSize;
    int      m_nRegionSize;
    cv::Rect m_oROI;

    CColorDet m_oMyLocDet;
    CColorDet m_oViewLocDet;

    cv::Mat m_oMapMask;
};

// **************************************************************************************
//          CMapDirectionRegParam Class Define
// **************************************************************************************

class CMapDirectionRegParam : public IComnBaseRegParam
{
public:
    CMapDirectionRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CMapDirectionRegParam() {}

public:
    std::vector<tagMapDirectionRegParam> m_oVecElements;
};

// **************************************************************************************
//          CMapDirectionRegResult Class Define
// **************************************************************************************

class CMapDirectionRegResult : public IComnBaseRegResult
{
public:
    CMapDirectionRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CMapDirectionRegResult() {}

    void SetResult(tagMapDirectionRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagMapDirectionRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int                      m_nResultNum;
    tagMapDirectionRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CMapDirectionReg Class Define
// **************************************************************************************

class CMapDirectionReg : public IComnBaseReg
{
public:
    CMapDirectionReg();
    ~CMapDirectionReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagMapDirectionRegParam>  m_oVecParams;
    std::vector<CMapDirectionRegColorDet> m_oVecMethods;
};

#endif /* __MAP_DIRECTION_REG_H */
