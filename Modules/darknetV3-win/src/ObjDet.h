//
//  ObjDet.h
//  
//  Object Detection
//  Created by txjeremyli on 2018/02/01.
//  Copyright 2018 tencent. All rights reserved.
//

#ifndef __OBJ_DET_H
#define __OBJ_DET_H

#include "ImgComn.h"
#include "GradTmplMatch.h"

// **************************************************************************************
//          CObjectDetection Class
// **************************************************************************************

class CObjectDetection
{
public:
    CObjectDetection() {}
    virtual ~CObjectDetection() {}

    /*!
       @brief, initialize parameters
       @param[in] pvParam, parameter pointer
       @CTemplateDetection converts void* to tagTmplDetParam*
       @CCNNDetection converts void* to tagCNNDetParam*
       @return true or false
     */
    virtual bool Initialize(void *pvParam) = 0;

    /*!
       @brief, detect objects
       @param[in] oSrcImg, source image
       @param[out] oVecBBoxes, bounding boxes
       @return true or false
     */
    virtual bool Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes) = 0;

    /*!
       @brief, release parameters
       @return true or false
     */
    virtual bool Release() = 0;

protected:
    void                 *m_pvParam;   // parameter pointer
    char                 *m_pszPath;   // template path or CNN path
    cv::Mat              m_oSrcImg;    // source image
    std::vector<tagBBox> m_oVecBBoxes; // bounding boxes
};

// **************************************************************************************
//          CFeatureDetection Class
// **************************************************************************************

struct tagFeatDetParam
{
    char             *pszPath;
    enFeatureType    eFeature;
    enClassifierType eClassifier;

    cv::Size oImgStride;
    cv::Size oImgPadding;

    tagHOGParam stHOGParam;      // HOG parameters
    tagSVMParam stSVMparam;      // SVM parameters

    tagFeatDetParam()
    {
        eFeature    = FEATURE_TYPE_INVALID;
        eClassifier = CLASSIFIER_TYPE_INVALID;
        oImgStride  = cv::Size(8, 8);
        oImgPadding = cv::Size(32, 32);
    }
};

/*!
   @CFeatureDetection
   @brief, Feature-based detection method
 */
class CFeatureDetection : public CObjectDetection
{
public:
    CFeatureDetection();
    ~CFeatureDetection();

    // interface
    virtual bool Initialize(void *pvParam);
    virtual bool Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes);
    virtual bool Release();

private:
    /*!
       @brief, load classifier
       @param[in] pszPath, classifier path
       @param[out] stClassifier, Classifier
       @return true or false
     */
    bool LoadClassifier(const char *pszPath, tagClassifier &stClassifier);

    /*!
       @brief, classify image features
       @param[in] stFeature, features of source image
       @param[in] stClassifier, classifier
       @param[out] nClass, image class
       @param[out] fScore, confidence score
       @return true or false
     */
    bool Detect(const cv::Mat &oSrcImg, const tagClassifier &stClassifier, std::vector<tagBBox> &oVecBBoxes);

private:
    enFeatureType    m_eFeature;         // feature type
    enClassifierType m_eClassifier;      // classifier tpye
    cv::Size         m_oImgStride;       // image stride size
    cv::Size         m_oImgPadding;      // image padding size
    tagFeature       m_stFeature;        // image features
    tagClassifier    m_stClassifier;     // classifier
};

// **************************************************************************************
//          CTemplateDetection Class
// **************************************************************************************

struct tagTmplDetParam
{
    char                      *pszPath;
    enFeatureType             eFeature;
    enDistanceType            eDistance;
    std::vector<tagTmplParam> oVecTmplParams;
};

/*!
   @CTemplateDetection
   @brief, Template-based detection method
 */
class CTemplateDetection : public CObjectDetection
{
public:
    CTemplateDetection();
    ~CTemplateDetection();

    // interface
    virtual bool Initialize(void *pvParam);
    virtual bool Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes);
    virtual bool Release();

    /*!
       @brief, detect objects with class index
       @param[in] oSrcImg, source image
       @param[in] nIndex, class index
       @param[out] oVecBBoxes, bounding boxes
       @return true or false
     */
    bool PredictWithIndex(const cv::Mat &oSrcImg, int nIndex, std::vector<tagBBox> &oVecBBoxes);

    /*!
       @brief, detect objects with class range
       @param[in] oSrcImg, source image
       @param[in] nStart, start index
       @param[in] nEnd, end index
       @param[out] oVecBBoxes, bounding boxes
       @return true or false
     */
    bool PredictWithRange(const cv::Mat &oSrcImg, int nStart, int nEnd, std::vector<tagBBox> &oVecBBoxes);

private:
    /*!
       @brief, load classification templates
       @param[in] pszPath, template path
       @param[in] oVecTmplParams, template parameters
       @param[out] oVecTemplates, classification templates
       @return true or false
     */
    bool LoadTemplate(const char *pszPath, const std::vector<tagTmplParam> oVecTmplParams, std::vector<tagTemplate> &oVecTemplates);

    /*!
       @brief, match source image and detection templates
       @param[in] srcImg, source image
       @param[in] oVecTemplates, detection templates
       @param[out] oVecBBoxes, bounding boxes
       @return true or false
     */
    bool Match(const cv::Mat &oSrcImg, const std::vector<tagTemplate> &oVecTemplates, std::vector<tagBBox> &oVecBBoxes);

private:
    enFeatureType            m_eFeature;      // feature type
    enDistanceType           m_eDistance;     // distance type
    std::vector<tagTemplate> m_oVecTemplates; // detection templates
};

// **************************************************************************************
//          CCNNDetection Class
// **************************************************************************************

struct tagCNNDetParam
{
    char      *pszPath;
    enCNNType eCNN;
};

/*!
   @CCNNDetection
   @brief, CNN-based detection method
 */
class CCNNDetection : public CObjectDetection
{
public:
    CCNNDetection();
    ~CCNNDetection();

    // interface
    virtual bool Initialize(void *pvParam);
    virtual bool Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes);
    virtual bool Release();

private:
    /*!
       @brief, Load CNN
       @param[in] pszPath, CNN path
       @param[out] stCNN, CNN
       @return true or false
     */
    bool LoadCNN(const char *pszPath, tagCNN &stCNN);

    /*!
       @brief, ues CNN to detect objects in source image
       @param[in] oSrcImg, source image
       @param[in] stCNN, CNN
       @param[out] oVecBBoxes, bounding boxes
       @return true or false
     */
    bool Detect(const cv::Mat &oSrcImg, const tagCNN &stCNN, std::vector<tagBBox> &oVecBBoxes);

private:
    enCNNType m_eCNN;  // CNN type
    tagCNN    m_stCNN; // CNN
};

#endif /* __OBJ_DET_H */