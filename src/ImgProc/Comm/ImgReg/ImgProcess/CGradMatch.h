/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CGRADMATCH_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CGRADMATCH_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CObjDet.h"

#define MY_SQR(a) ((a) * (a))

#define EXPAND_SIZE        4
#define NEIGHBOR_THRESHOLD 4
#define WEAK_THRESHOLD     110
#define STRONG_THRESHOLD   105

// **************************************************************************************
//          CGradMatch Parameter Class Define
// **************************************************************************************

class CGradMatchParam : public CObjDetParam {
  public:
    CGradMatchParam() {
        m_nScaleLevel = 1;
        m_fMinScale = 1.0;
        m_fMaxScale = 1.0;
        m_strOpt = "-featureNum 16";
        m_oVecTmpls.clear();
    }
    virtual ~CGradMatchParam() {}

  public:
    int                  m_nScaleLevel;  // scale level for multi-scale matching
    float                m_fMinScale;  // min scale
    float                m_fMaxScale;  // max scale
    std::string          m_strOpt;  // method optional
    std::vector<tagTmpl> m_oVecTmpls;  // matching templates
};

// **************************************************************************************
//          CGradMatch Factory Class Define
// **************************************************************************************

class CGradMatchFactory : public IObjDetFactory {
  public:
    CGradMatchFactory();
    ~CGradMatchFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CGradMatch Class Define
// **************************************************************************************

// Gradient feature
struct tagGradFeature {
    int nX;     // column location
    int nY;     // row location
    int nLabel;     // quantization direction

    tagGradFeature() {
        nX = 0;
        nY = 0;
        nLabel = 0;
    }

    tagGradFeature(const int x, const int y, const int l) {
        nX = x;
        nY = y;
        nLabel = l;
    }
};

// Gradient template
struct tagGradTemplate {
    int         nClassID;  // class ID
    int         nWidth;  // template width
    int         nHeight;  // template height
    float       fThreshold;  // match threshold
    float       fScale;  // match score
    std::string strTmplName;  // template name
    std::string strTmplPath;  // template path

    std::vector<tagGradFeature> oVecGradFeature;

    tagGradTemplate() {
        nClassID = 0;
        nWidth = 0;
        nHeight = 0;
        fThreshold = 0.80f;
        fScale = 0.0f;
    }
};

// Gradient candidate point
struct tagGradCandidate {
    tagGradFeature stGradFeature;
    float          fScore;  // candidate score

    tagGradCandidate() {
        stGradFeature = tagGradFeature(0, 0, 0);
        fScore = 0;
    }

    tagGradCandidate(const int x, const int y, const int label, const float score) {
        stGradFeature = tagGradFeature(x, y, label);
        fScore = score;
    }
};

class CGradMatch : public CObjDet {
  public:
    CGradMatch();
    ~CGradMatch();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

  private:
    void ColorGradient(const cv::Mat &oImg, cv::Mat &oMagnitude, cv::Mat &oAngle);
    void GrayGradient(const cv::Mat &oImg, cv::Mat &oMagnitude, cv::Mat &oAngle);
    void ComputeMagnitude(const cv::Mat &oDx, const cv::Mat &oDy, cv::Mat &oMagnitude);
    void ComputeAngle(const cv::Mat &oDx, const cv::Mat &oDy, cv::Mat &oAngle);
    void QuantAngle(const cv::Mat &oMagnitude, cv::Mat &oAngle, cv::Mat &oOrientation,
        int nWeakThreshold = WEAK_THRESHOLD);
    void SpreadOrientation(const cv::Mat &oOrientation, cv::Mat &oBinaryMat, int nT = EXPAND_SIZE);
    void ComputeResponseMap(const cv::Mat &oBinaryMat, std::vector<cv::Mat> &oVecResponseMap);
    void Linearize(const cv::Mat &oResponseMap, cv::Mat &oLinearizedMap, int nT = EXPAND_SIZE);
    void SelectScatteredFeature(const std::vector<tagGradCandidate> &oVecCandidate,
        std::vector<tagGradFeature> &oVecGradFeature, int nFeatureNum, float fDist);
    void ComputeSimilarity(const std::vector<cv::Mat> &oVecLinearizedMap,
        const tagGradTemplate &stGradTemplate,
        cv::Mat &oSimilarity, int nRows, int nCols, int nT);
    // void ShowTemplate(const tagGradTemplate &stGradTemplate);

    int GetResponseMap(const cv::Mat &oImg, std::vector<cv::Mat> &oVecResponseMap,
        int nT = EXPAND_SIZE);
    int ParseParam(const CGradMatchParam *pParam);
    int MakeTemplate(const std::vector<tagTmpl> &oVecTmpls,
        std::vector<tagGradTemplate> &oVecGradTmpls, int nFeatureNum);
    int ExtractFeature(const cv::Mat &oMagnitude, const cv::Mat &oOrientation,
        tagGradTemplate &stGradTemplate, int nFeatureNum, int nStrongThreshold = STRONG_THRESHOLD);
    int Detect(const cv::Mat &oSrcImg, const std::vector<tagGradTemplate> &oVecGradTmpls,
        std::vector<tagBBox> &oVecBBoxes);
    int MatchTemplate(const std::vector<cv::Mat> &oVecLinearizedMap,
        const std::vector<tagGradTemplate> &oVecGradTempalte, std::vector<tagBBox> &oVecDetectBBox,
        int nRows, int nCols, int nT = EXPAND_SIZE);

  private:
    int                          m_nFeatureNum;
    std::vector<tagTmpl>         m_oVecTmpls;
    std::vector<tagGradTemplate> m_oVecGradTmpls;
};

void _OrUnaligned8u(const uchar *src, int src_stride, uchar *dst, int dst_stride,
    int nCol, int nRow);
bool _LessConfidence(const tagBBox &stBox1, const tagBBox &stBox2);
bool _LessScore(const tagGradCandidate &stCandidate1, const tagGradCandidate &stCandidate2);
static inline int _GetLabel(int nQuant);
const unsigned char* _AccessLinearMemory(const std::vector<cv::Mat> &oVecLinearizedMap,
    const tagGradFeature &stGradFeature, int nT, int nW);

#endif   // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CGRADMATCH_H_
