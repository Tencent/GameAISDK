/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CEDGEMATCH_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CEDGEMATCH_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CObjDet.h"

// **************************************************************************************
//          CEdgeMatch Parameter Class Define
// **************************************************************************************

class CEdgeMatchParam : public CObjDetParam {
  public:
    CEdgeMatchParam() {
        m_nScaleLevel = 1;
        m_fMinScale = 1.0;
        m_fMaxScale = 1.0;
        m_oVecTmpls.clear();
    }
    virtual ~CEdgeMatchParam() {}

  public:
    int                  m_nScaleLevel;    // scale level for multi-scale matching
    float                m_fMinScale;     // min scale
    float                m_fMaxScale;     // max scale
    std::vector<tagTmpl> m_oVecTmpls;    // matching templates
};

// **************************************************************************************
//          CEdgeMatch Factory Class Define
// **************************************************************************************

class CEdgeMatchFactory : public IObjDetFactory {
  public:
    CEdgeMatchFactory();
    ~CEdgeMatchFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CEdgeMatch Class Define
// **************************************************************************************

class CEdgeMatch : public CObjDet {
  public:
    CEdgeMatch();
    ~CEdgeMatch();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

  private:
    int ParseParam(const CEdgeMatchParam *pParam);
    int ExtractEdge(const cv::Mat &oSrcImg, cv::Mat &oDstImg);
    int MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls,
        std::vector<tagBBox> &oVecBBoxes);

  private:
    std::vector<tagTmpl> m_oVecTmpls;  // matching templates
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CEDGEMATCH_H_
