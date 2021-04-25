/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IMGCOMN_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IMGCOMN_H_

#include <math.h>
#include <stdio.h>
#include <time.h>

#include <iostream>
#include <string>
#include <vector>

#include <opencv2/core/core.hpp>
#include <opencv2/core/version.hpp>
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/ml/ml.hpp>
#include <opencv2/objdetect/objdetect.hpp>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcLog.h"


#ifdef LINUX
#include <dirent.h>
#endif

#if CV_VERSION_MAJOR == 3
#define  OPENCV3
#else
#error Not support this OpenCV version
#endif

#define MAX_ELEMENT_SIZE 16
#define MAX_CHAR_SIZE    256
#define MAX_POINT_SIZE   1024
#define MAX_BBOX_SIZE    128
#define MAX_BLOOD_SIZE   32

#define MIN_TEMPLATE_WIDTH  1
#define MIN_TEMPLATE_HEIGHT 1

#define IMAGE_WIDTH      1280
#define IMAGE_HEIGHT     720
#define IMAGE_LONG_SIDE  1280
#define IMAGE_SHORT_SIDE 720

// **************************************************************************************
//          Structure Define
// **************************************************************************************

// template
struct tagTmpl {
    int         nClassID;  // class ID
    float       fThreshold;  // match threshold
    std::string strTmplName;  // template name
    std::string strTmplPath;  // template path
    std::string strMaskPath;  // mask path
    cv::Rect    oRect;  // template rectangle
    cv::Mat     oTmplImg;  // template image
    cv::Mat     oMaskImg;  // mask image

    tagTmpl() {
        nClassID = -1;
        fThreshold = 0.95f;
        oRect = cv::Rect(-1, -1, -1, -1);
    }
};

// bounding box
struct tagBBox {
    int      nClassID;
    float    fScore;
    float    fScale;
    char     szTmplName[MAX_CHAR_SIZE];
    cv::Rect oRect;

    tagBBox() {
        nClassID = -1;
        fScore = 0.0f;
        fScale = 0.0f;
        szTmplName[0] = '\0';
        oRect = cv::Rect(-1, -1, -1, -1);
    }

    tagBBox(int ID, float score, float scale, std::string name, cv::Rect rect) {
        nClassID = ID;
        fScore = score;
        fScale = scale;
        snprintf(szTmplName, sizeof(szTmplName), "%s", name.c_str());
        oRect = rect;
    }
};

// blood
struct tagBlood {
    int      nClassID;
    int      nLevel;
    float    fScore;
    float    fPercent;  // blood percent
    char     szName[MAX_CHAR_SIZE];
    cv::Rect oRect;

    tagBlood() {
        nClassID = 0;
        nLevel = 0;
        fScore = 0.0f;
        fPercent = 0.0f;
        szName[0] = '\0';
        oRect = cv::Rect(-1, -1, -1, -1);
    }
};

// recognize data
struct tagRegData {
    int     nFrameIdx;  // frame index
    cv::Mat oSrcImg;  // source image

    tagRegData() {
        nFrameIdx = -1;
    }
};

// **************************************************************************************
//          Function Define
// **************************************************************************************
int ConvertColorToGray(const int nTaskID, const cv::Mat &oSrcImg, cv::Mat &oGrayImg);
int LoadTemplate(const int nTaskID, const std::vector<tagTmpl> &oVecSrcTmpls,
    const std::vector<float> &oVecScales, std::vector<tagTmpl> &oVecDstTmpls);
bool LessScore(const tagBBox &stBBox1, const tagBBox &stBBox2);
bool AscendBBoxX(const tagBBox &stBBox1, const tagBBox &stBBox2);

int ComputeScale(const int nTaskID, const float fMinScale, const float fMaxScale,
    const int nScaleLevel, std::vector<float> *pVecScale);
double IOU(const cv::Rect &oRect1, const cv::Rect &oRect2);
int MergeBBox(const std::vector<tagBBox> &oVecSrcBBoxes, std::vector<tagBBox> &oVecDstBBoxes,
    const double dOverlapThreshold = 0.50, const int nCountThreshold = 1);
int CheckROI(const int nTaskID, const cv::Mat &oSrcImg, cv::Rect &oROI);
int CombineROI(const int nTaskID, const std::vector<cv::Rect> &oVecROIs, cv::Rect &oROI);
int DrawBBox(const cv::Mat &oSrcImg, const std::vector<tagBBox> &oVecBBoxes,
    const int nWaiteTime = 0, const int nClassID = -1);
int GetPath(const int nTaskID, const std::string strPath,
    std::vector<std::string> *pVecPaths, std::vector<std::string> *pVecNames);
int AnalyzeTmplPath(const int nTaskID, const std::vector<tagTmpl> &oVecSrcTmpls,
    std::vector<tagTmpl> &oVecDstTmpls);
int AnalyzeFileName(const int nTaskID, const std::string &strFileName,
    std::string &strTmplName, int &nClassID);

int ResizeRect(const cv::Rect &oSrcRect, float fXScale, float fYScale, cv::Rect &oDstRect);
int ExpandRect(const cv::Rect &oSrcRect, int nExpandWidth, int nExpandHeight, cv::Rect &oDstRect);
int AverageRect(const int nTaskID, const std::vector<cv::Rect> &oVecRects, cv::Rect &oAvgRect);

int GetRGB(const int nTaskID, const std::string &strCondition,
    int &nRedLower, int &nRedUpper, int &nGreenLower, int &nGreenUpper,
    int &nBlueLower, int &nBlueUpper);

int AddMask(const int nTaskID, const cv::Mat &oSrcImg, const cv::Mat &oMaskImg,
    const int &nMaskValue, cv::Mat &oDstImg);

int ConvertImgTo720P(const int nTaskID, const cv::Mat &oSrcImg, cv::Mat &oDstImg, float &fRatio);
#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IMGCOMN_H_
