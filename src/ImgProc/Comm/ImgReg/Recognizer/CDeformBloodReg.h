/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef DEFORM_BLOOD_REG_H_
#define DEFORM_BLOOD_REG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/ImgProcess/CYOLOAPI.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CDeformBloodReg Structure Define
// **************************************************************************************

// parameter of each element
struct tagDeformBloodRegParam
{
    int         nBloodLength; // blood length
    int         nFilterSize; // filter size of erode and dilate operation
    int         nMaxPointNum; // the number of max points
    float       fThreshold; // threshold of blood detection
    cv::Rect    oROI; // detection ROI
    std::string strCondition; // blood color condition
    std::string strCfgPath; // config file path of yolo
    std::string strWeightPath; // weight file path of yolo
    std::string strNamePath; // name file path of yolo

    tagDeformBloodRegParam()
    {
        nBloodLength  = 100;
        nMaxPointNum  = 512;
        nFilterSize   = 1;
        fThreshold    = 0.50f;
        oROI          = cv::Rect(-1, -1, -1, -1);
        strCondition  = "";
        strCfgPath    = "";
        strWeightPath = "";
        strNamePath   = "";
    }
};

// result of each element
struct tagDeformBloodRegResult
{
    int      nState; // detection flag
    int      nBloodNum; // the number of bloods
    cv::Rect oROI; // detection ROI
    tagBlood szBloods[MAX_BLOOD_SIZE]; // bloods

    tagDeformBloodRegResult()
    {
        nState    = 0;
        nBloodNum = 0;
        oROI      = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CDeformBloodRegColorDet Class Define
// **************************************************************************************

class CDeformBloodRegColorDet
{
public:
    CDeformBloodRegColorDet();
    ~CDeformBloodRegColorDet();

    int Initialize(const int nTaskID, const tagDeformBloodRegParam &stParam);
    int Predict(const cv::Mat &oSrcImg, tagDeformBloodRegResult &stResult);
    int Release();

    int FillColorDetParam(const tagDeformBloodRegParam &stParam, CColorDetParam &oParam);
    int FillYOLOAPIParam(const tagDeformBloodRegParam &stElement, CYOLOAPIParam &oParam);

private:
    int      m_nTaskID; // task id
    int      m_nBloodLength; // blood length
    cv::Rect m_oROI; // detection ROI

    CYOLOAPI  m_oYOLOAPI; // yolo recognizer
    CColorDet m_oColorDet; // color detection recognizer
};

// **************************************************************************************
//          CDeformBloodRegParam Class Define
// **************************************************************************************

class CDeformBloodRegParam : public IComnBaseRegParam
{
public:
    CDeformBloodRegParam()
    {
        m_oVecElements.clear();
    }

    virtual ~CDeformBloodRegParam() {}

public:
    std::vector<tagDeformBloodRegParam> m_oVecElements; // parameters of deform blood recognizers
};

// **************************************************************************************
//          CDeformBloodRegResult Class Define
// **************************************************************************************

class CDeformBloodRegResult : public IComnBaseRegResult
{
public:
    CDeformBloodRegResult()
    {
        m_nResultNum = 0;
    }

    virtual ~CDeformBloodRegResult() {}

    void SetResult(tagDeformBloodRegResult szResults[], int *pResultNum)
    {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++)
        {
            m_szResults[i] = szResults[i];
        }
    }

    tagDeformBloodRegResult* GetResult(int *pResultNum)
    {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

private:
    int                     m_nResultNum; // the number of all elements
    tagDeformBloodRegResult m_szResults[MAX_ELEMENT_SIZE]; // results of all elements
};

// **************************************************************************************
//          CDeformBloodReg Class Define
// **************************************************************************************

class CDeformBloodReg : public IComnBaseReg
{
public:
    CDeformBloodReg();
    ~CDeformBloodReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

private:
    std::vector<tagDeformBloodRegParam>  m_oVecParams; // vector of parameters
    std::vector<CDeformBloodRegColorDet> m_oVecMethods; // vector of methods
};

#endif /* DEFORM_BLOOD_REG_H_ */
