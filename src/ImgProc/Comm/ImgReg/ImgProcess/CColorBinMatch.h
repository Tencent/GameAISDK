/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORBINMATCH_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORBINMATCH_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/ImgProcess/CObjDet.h"

// **************************************************************************************
//          CColorBinMatchParam Class
// **************************************************************************************

class CColorBinMatchParam : public CObjDetParam {
  public:
    CColorBinMatchParam() {
        m_fMinScale = 1.0;
        m_fMaxScale = 1.0;
        m_nScaleLevel = 1;
        m_oROI = cv::Rect(-1, -1, -1, -1);
        m_oVecConditions.clear();
        m_strOpt = "-matchMethod SQDIFF_NORMED";
        m_oVecTmpls.clear();
    }
    virtual ~CColorBinMatchParam() {}

  public:
    float                    m_fMinScale;
    float                    m_fMaxScale;
    int                      m_nScaleLevel;
    cv::Rect                 m_oROI;
    std::string              m_strOpt;
    std::vector<std::string> m_oVecConditions;
    // CColorDetParam m_oParamColor;
    std::vector<tagTmpl> m_oVecTmpls;
};

// **************************************************************************************
//          CColorBinMatchFactory Class
// **************************************************************************************

class CColorBinMatchFactory : public IObjDetFactory {
  public:
    CColorBinMatchFactory();
    ~CColorBinMatchFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CColorBinMatch Class
// **************************************************************************************

class CColorBinMatch : public CObjDet {
  public:
    CColorBinMatch();
    ~CColorBinMatch();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

    int SetROI(cv::Rect const &oROI);

  private:
    int ParseParam(const CColorBinMatchParam *pParam);
    int MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls,
        std::vector<tagBBox> &oVecBBoxes);
    int FillColorDetParam(const std::string &strCondition, CColorDetParam &oParam);
    void ColorBinaryVector(std::vector<tagTmpl> *pVecTmpls);
    void ColorBinaryImage(const cv::Mat &oSrcImg, cv::Mat &oDstImg);
    // bool CompareValue(uchar uValue, float fThreshold, float fOffset);

  private:
    cv::Rect                    m_oROI;
    std::string                 m_strMatchMethod;
    std::vector<tagTmpl>        m_oVecTmpls;
    std::vector<CColorDetParam> m_oVecParams;
    std::vector<std::string>    m_oVecConditions;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORBINMATCH_H_

