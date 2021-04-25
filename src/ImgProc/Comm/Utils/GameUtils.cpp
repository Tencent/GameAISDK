/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Utils/GameUtils.h"

#include <map>

#if OPENCV_2
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/opencv.hpp>
#else
#include <opencv2/calib3d/calib3d.hpp>
#include <opencv2/features2d.hpp>
#include <opencv2/imgproc.hpp>
#endif

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcLog.h"

void GetPXSum(const cv::Mat &src, int &a, int nThreshold) {
#if defined(OPENCV4)
    cv::threshold(src, src, nThreshold, 255, cv::THRESH_BINARY);
#else
    cv::threshold(src, src, nThreshold, 255, CV_THRESH_BINARY);
#endif

    a = 0;

    for (int i = 0; i < src.rows; i++) {
        for (int j = 0; j < src.cols; j++) {
            a += src.at<uchar>(i, j);
        }
    }
}

bool GetBinaryDiff(const cv::Mat &src, cv::Mat &dst, cv::Mat &res, int nThresHold) {
    cv::Mat imgResult;

    if (src.cols != dst.cols || src.rows != dst.rows)
        return false;

#if defined(OPENCV4)
    threshold(dst, dst, 100, 255, cv::THRESH_BINARY);
    threshold(src, src, 100, 255, cv::THRESH_BINARY);
#else
    threshold(dst, dst, 100, 255, CV_THRESH_BINARY);
    threshold(src, src, 100, 255, CV_THRESH_BINARY);
#endif

    absdiff(dst, src, imgResult);

    res = imgResult;

    return true;
}
