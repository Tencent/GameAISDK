
/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef __YOLO2_DETECT_H
#define __YOLO2_DETECT_H

#include <string>
#include <math.h>
#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <opencv2/highgui/highgui.hpp>


#include "network.h"

extern "C" {
#include "detection_layer.h"
#include "region_layer.h"
#include "cost_layer.h"
#include "utils.h"
#include "parser.h"
#include "box.h"
#include "image.h"
#include "demo.h"
#include "option_list.h"
#include "stb_image.h"
}

//#include "darknet.h"
//#include "layer.h"
//#include "network.h"

#define MAX_OBJECT_SIZE 100

struct tagDetBBox
{
    int   m_nLeft;
    int   m_nTop;
    int   m_nWidth;
    int   m_nHeight;
    float m_fConfidence;
    int   m_nClass;

    tagDetBBox(const int nLeft, const int nTop, const int nWidth, const int nHeight, const float fConfidence, const int nClass)
    {
        m_nLeft       = nLeft;
        m_nTop        = nTop;
        m_nWidth      = nWidth;
        m_nHeight     = nHeight;
        m_fConfidence = fConfidence;
        m_nClass      = nClass;
    }

    tagDetBBox()
    {
        m_nLeft       = -1;
        m_nTop        = -1;
        m_nWidth      = 0;
        m_nHeight     = 0;
        m_fConfidence = 0;
        m_nClass      = -1;
    }
};


class CYOLOV2Det
{
public:
    CYOLOV2Det();
    ~CYOLOV2Det();

public:
    /*!
       @brief
       @param[in] pParam 初始化参数
       @return true,成功； false 失败
     */
    virtual bool Initialize(void *pParam);

    bool Initialize(char *szNetFile, char *szWeightFile);

    /*!
       @brief
     */
    virtual void Release();

    /*!
       @brief
       @param[in] oSrc 原图像
       @param[out] oVecResult 检测矩形框
       @return :
     */
    // virtual int  Detect(const cv::Mat &oSrc, std::vector<tagDetectBBox> &oVecResult);
    virtual int Detect(const cv::Mat &oSrc, tagDetBBox* &oVecResult, int &nNum);


    /*!
       @brief  (box1 and box2) / (box1 or box2)
       @param[in] box1 矩形框1
       @param[in] box2 矩形框2
       @return 两个矩形框的IOU值:
     */
    virtual float IOU(tagDetBBox &box1, tagDetBBox &box2);


private:
    /*!
       @brief
       @param[in]
       @param[in]
       @return :
     */
    void RestDetRet();

private:
    int   m_nClassNum;
    float m_fthresh;
    float m_fhier_thresh;
    float m_fnms;
    char  **m_pszNames;
// #ifdef LINUX
    void    *m_pstBoxes;
    float   **m_pfProbs;
    network m_pstNet;
// #endif
    tagDetBBox m_stDetectBBox[MAX_OBJECT_SIZE];
};

#endif
