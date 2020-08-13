/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef KING_GLORY_BLOOD_REG_H_
#define KING_GLORY_BLOOD_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/ImgReg/ImgProcess/CYOLOAPI.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CKingGloryBloodReg Structure Define
// **************************************************************************************

struct tagKingGloryBloodRegParam
{
    int                  nBloodLength;
    int                  nFilterSize;
    int                  nMaxPointNum;
    int                  nScaleLevel;
    float                fMinScale;
    float                fMaxScale;
    float                fThreshold;
    cv::Rect             oROI;
    std::string          strCondition;
    std::string          strCfgPath;
    std::string          strWeightPath;
    std::string          strNamePath;
    std::string          strMaskPath;
    std::vector<tagTmpl> oVecTmpls;

    tagKingGloryBloodRegParam()
    {
        nBloodLength  = 100;
        nMaxPointNum  = 512;
        nFilterSize   = 1;
        nScaleLevel   = 1;
        fMinScale     = 1.0;
        fMaxScale     = 1.0;
        fThreshold    = 0.50f;
        oROI          = cv::Rect(-1, -1, -1, -1);
        strCondition  = "";
        strCfgPath    = "";
        strWeightPath = "";
        strNamePath   = "";
        strMaskPath   = "";
        oVecTmpls.clear();
    }
};

struct tagKingGloryBloodRegResult
{
    int      nState;
    int      nBloodNum;
    cv::Rect oROI;
    tagBlood szBloods[MAX_BLOOD_SIZE];

    tagKingGloryBloodRegResult()
    {
        nState    = 0;
        nBloodNum = 0;
        oROI      = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CKingGloryBloodRegColorDet Class Define
// **************************************************************************************

class CKingGloryBloodRegColorDet
{
public:
    CKingGloryBloodRegColorDet();
    ~CKingGloryBloodRegColorDet();

    int Initialize(const int nTaskID, tagKingGloryBloodRegParam *pParam);
    int Predict(const cv::Mat &oSrcImg, tagKingGloryBloodRegResult &stResult);
    int Release();

private:
    int FillYOLOAPIParam(const tagKingGloryBloodRegParam &stParam, CYOLOAPIParam &oParam);
    int FillColorDetParam(const tagKingGloryBloodRegParam &stParam, CColorDetParam &oParam);
    int FillColorMatchParam(const tagKingGloryBloodRegParam &stParam, CColorMatchParam &oParam);

private:
    int      m_nTaskID;
    int      m_nBloodLength;
    cv::Rect m_oROI;

    CYOLOAPI    m_oYOLOAPI;
    CColorDet   m_oRedDet;
    CColorDet   m_oGreenDet;
    CColorDet   m_oBlueDet;
    CColorMatch m_oColorMatch;
};

// **************************************************************************************
//          CKingGloryBloodRegParam Class Define
// **************************************************************************************

class CKingGloryBloodRegParam : public IComnBaseRegParam
{
public:
    CKingGloryBloodRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CKingGloryBloodRegParam() {}

public:
    std::vector<tagKingGloryBloodRegParam> m_oVecElements;
};

// **************************************************************************************
//          CKingGloryBloodRegResult Class Define
// **************************************************************************************

class CKingGloryBloodRegResult : public IComnBaseRegResult
{
public:
    CKingGloryBloodRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CKingGloryBloodRegResult() {}

    void SetResult(tagKingGloryBloodRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagKingGloryBloodRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int                        m_nResultNum;
    tagKingGloryBloodRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CKingGloryBloodReg Class Define
// **************************************************************************************

class CKingGloryBloodReg : public IComnBaseReg
{
public:
    CKingGloryBloodReg();
    ~CKingGloryBloodReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagKingGloryBloodRegParam>  m_oVecParams; // vector of parameters
    std::vector<CKingGloryBloodRegColorDet> m_oVecMethods; // vector of methods
};

#endif /* KING_GLORY_BLOOD_REG_H_ */
