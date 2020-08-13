/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef MAP_REG_H_
#define MAP_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CMapReg Structure Define
// **************************************************************************************

struct tagMapRegParam
{
    int         nFilterSize;
    int         nMaxPointNum;
    std::string strCondition;
    std::string strMyLocCondition;
    std::string strFriendsLocCondition;
    std::string strViewLocCondition;
    std::string strMapTempPath;
    std::string strMapMaskPath;
    cv::Rect    oROI;

    tagMapRegParam()
    {
        nMaxPointNum           = 512;
        nFilterSize            = 1;
        oROI                   = cv::Rect(-1, -1, -1, -1);
        strCondition           = "";
        strMyLocCondition      = "";
        strFriendsLocCondition = "";
        strViewLocCondition    = "";
        strMapTempPath         = "";
        strMapMaskPath         = "";
    }
};

struct tagMapRegResult
{
    int       nState;
    int       nFreindsPointNum;
    cv::Point oMyLocPoint;
    cv::Point szFriendsLocPoints[MAX_POINT_SIZE];
    cv::Point oViewLocPoint;
    cv::Point oViewAnglePoint;
    cv::Rect  oROI;

    tagMapRegResult()
    {
        nState           = 0;
        nFreindsPointNum = 0;
        oROI             = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CMapRegColorDet Class Define
// **************************************************************************************

class CMapRegColorDet
{
public:
    CMapRegColorDet();
    ~CMapRegColorDet();

    int Initialize(const int nTaskID, tagMapRegParam *pParam);
    int Predict(const cv::Mat &oSrcImg, tagMapRegResult &stResult);
    int Release();

private:
    int FillColorDetParam(const tagMapRegParam &stParam, CColorDetParam &oParam);

private:
    int      m_nTaskID;
    cv::Rect m_oROI;

    CColorDet m_oMyLocDet;
    CColorDet m_oFriendsLocDet;
    CColorDet m_oViewLocDet;

    cv::Mat m_oMapTemp;
    cv::Mat m_oMapMask;
};

// **************************************************************************************
//          CMapRegParam Class Define
// **************************************************************************************

class CMapRegParam : public IComnBaseRegParam
{
public:
    CMapRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CMapRegParam() {}

public:
    std::vector<tagMapRegParam> m_oVecElements;
};

// **************************************************************************************
//          CMapRegResult Class Define
// **************************************************************************************

class CMapRegResult : public IComnBaseRegResult
{
public:
    CMapRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CMapRegResult() {}

    void SetResult(tagMapRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagMapRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int             m_nResultNum;
    tagMapRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CMapReg Class Define
// **************************************************************************************

class CMapReg : public IComnBaseReg
{
public:
    CMapReg();
    ~CMapReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagMapRegParam>  m_oVecParams;
    std::vector<CMapRegColorDet> m_oVecMethods;
};

#endif /* __MAP_REG_H */

