/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef ORB_MATCH_H_
#define ORB_MATCH_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CObjDet.h"

// **************************************************************************************
//          CORBMatch Parameter Class Define
// **************************************************************************************

class CORBMatchParam : public CObjDetParam
{
public:
    CORBMatchParam()
    {
        m_nFeatureNum = 500;
        m_nLevel = 8;
        m_nEdgeThreshold = 13;
        m_fScaleFactor = 1.2f;

        m_nScaleLevel = 1;
        m_fMinScale   = 1.0;
        m_fMaxScale   = 1.0;
        m_oVecTmpls.clear();
    }
    virtual ~CORBMatchParam() {}

public:
    int m_nFeatureNum; // ORB parameter
    int m_nLevel; // ORB parameter
    int m_nEdgeThreshold; // ORB parameter
    float m_fScaleFactor; // ORB parameter

    int                  m_nScaleLevel; // scale level for multi-scale matching
    float                m_fMinScale; // min scale
    float                m_fMaxScale; // max scale
    std::vector<tagTmpl> m_oVecTmpls; // matching templates
};

// **************************************************************************************
//          CORBMatch Factory Class Define
// **************************************************************************************

class CORBMatchFactory : public IObjDetFactory
{
public:
    CORBMatchFactory();
    ~CORBMatchFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CORBMatch Class Define
// **************************************************************************************

class CORBMatch : public CObjDet
{
public:
    CORBMatch();
    ~CORBMatch();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

private:
    int ParseParam(const CORBMatchParam *pParam);
    int MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls, std::vector<tagBBox> &oVecBBoxes);

private:
    cv::Ptr<cv::ORB>     m_oORB; // ORB
    std::vector<tagTmpl> m_oVecTmpls; // matching templates
};

#endif /* ORB_MATCH_H_ */
