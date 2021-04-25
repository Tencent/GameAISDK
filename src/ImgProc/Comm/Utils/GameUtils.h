/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMEUTILS_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMEUTILS_H_

#include <stdio.h>

#include <queue>
#include <string>
#include <vector>

// for opencv
#include <opencv2/core/core.hpp>
#if CV_VERSION_EPOCH == 2
#define OPENCV2
#elif CV_VERSION_MAJOR == 3
#define  OPENCV3
#elif CV_VERSION_MAJOR == 4
#define OPENCV4
#else
#error Not support this OpenCV version
#endif
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/highgui/highgui.hpp>
#ifndef OPENCV2
#include <opencv2/imgcodecs/imgcodecs.hpp>
#endif
#include <opencv2/imgproc/imgproc.hpp>

#include "Comm/Utils/TqcCommon.h"

#define USE_MULTI_RESOLUTION_CODE 1

#ifndef GAME_TEMPLATE_THRESHOLD
#define GAME_TEMPLATE_THRESHOLD 0.7f
#endif  // GAME_TEMPLATE_THRESHOLD


struct tagActionState {
    int   nActionX;  // x coordinate of action point
    int   nActionY;  // y coordinate of action point
    float fActionThreshold;  // template match threshold
    int   nTmplExpdWPixel;  // expand width of action point as template width
    int   nTmplExpdHPixel;  // expand height of action point as template height
    float fROIExpdWRatio;
    float fROIExpdHRatio;
    tagActionState() {
        nActionX = -1;
        nActionY = -1;
        fActionThreshold = GAME_TEMPLATE_THRESHOLD;
        nTmplExpdWPixel = 25;
        nTmplExpdHPixel = 25;
        fROIExpdWRatio = 0.275f;
        fROIExpdHRatio = 0.275f;
    }

    tagActionState(int nInActionX, int nInActionY, float fInThreshold,
        int nInTmplExpdWPixel, int nInTmplExpdHPixel,
        float fInROIExpdWRatio, float fInROIExpdHRatio) {
        nActionX = nInActionX;
        nActionY = nInActionY;
        fActionThreshold = fInThreshold;
        nTmplExpdWPixel = nInTmplExpdWPixel;
        nTmplExpdHPixel = nInTmplExpdHPixel;
        fROIExpdWRatio = fInROIExpdWRatio;
        fROIExpdHRatio = fInROIExpdHRatio;
    }
};


struct tagUITemplateParam {
    int   nSampleX;         // x of sample in the image.
    int   nSampleY;         // y of sample in the image.
    int   nSampleW;         // width of sample in the image.
    int   nSampleH;         // height of sample in the image.
    float fThreshold;
    tagUITemplateParam() {
        nSampleX = 0;
        nSampleY = 0;
        nSampleW = 0;
        nSampleH = 0;
        fThreshold = static_cast<float>(GAME_TEMPLATE_THRESHOLD);
    }
};


struct stSampleImg {
    int        nLabel;
    const char *strFile;
};


struct stDetectResult {
    int m_nLable;
    int m_nLeftTopLocX;
    int m_nLeftTopLocY;
    int m_nWidth;
    int m_nHeight;
    stDetectResult() {
        m_nLable = -1;
        m_nLeftTopLocX = -1;
        m_nLeftTopLocY = -1;
        m_nWidth = 0;
        m_nHeight = 0;
    }
};


struct stFrame {
    int          nFrameSeq;
    unsigned int nTimestamp;
    cv::Mat      img;

    stFrame() {
        nFrameSeq = -1;
        nTimestamp = 0;
    }
};


struct tagPoint {
    int nPointX;
    int nPointY;
    tagPoint() {
        nPointX = 0;
        nPointY = 0;
    }
};


struct tagRectangle {
    int nPointX;  // x coordinate of top left Point
    int nPointY;  // y coordinate of top left Point
    int nWidth;   // width of rectangle
    int nHeight;  // height of rectangle
    tagRectangle() {
        nPointX = 0;
        nPointY = 0;
        nWidth = 0;
        nHeight = 0;
    }
};


// typedef std::vector<tagFrameDigitLabel>         FrameDigitArray;
typedef std::vector<cv::Rect>                   BoundingBoxArray;
typedef std::vector<std::vector<cv::Point> >    ContoursArray;
typedef std::vector<cv::KeyPoint>               KeyPoints;
typedef std::vector<KeyPoints>                  KeyPointsArray;
typedef std::vector<cv::Mat>                    MatArray;
typedef std::queue<stFrame>                     FrameQueue;
typedef std::queue<cv::Mat>                     MatQueue;


void GetPXSum(const cv::Mat &src, int &a, int nThreshold = 100);
bool GetBinaryDiff(const cv::Mat &src, cv::Mat &dst, cv::Mat &res, int nThresHold = 100);

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMEUTILS_H_



