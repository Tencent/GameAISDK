/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/ImgProcess/ImgComn.h"

int ConvertColorToGray(const int nTaskID, const cv::Mat &oSrcImg, cv::Mat &oGrayImg) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", nTaskID);
        return -1;
    }

    // check image type
    if (CV_8UC1 == oSrcImg.type()) {
        // source image is gray image
        oGrayImg = oSrcImg;
    } else if (CV_8UC3 == oSrcImg.type()) {
        // source image is BGR image
        oGrayImg = cv::Mat(oSrcImg.rows, oSrcImg.cols, CV_8UC1);
        cv::cvtColor(oSrcImg, oGrayImg, CV_BGR2GRAY);
    } else if (CV_8UC4 == oSrcImg.type()) {
        // source image is BGRA image
        oGrayImg = cv::Mat(oSrcImg.rows, oSrcImg.cols, CV_8UC1);
        cv::cvtColor(oSrcImg, oGrayImg, CV_BGRA2GRAY);
    } else {
        LOGE("task ID %d: unknown image type, please check", nTaskID);
        return -1;
    }

    return 1;
}

int LoadTemplate(const int nTaskID, const std::vector<tagTmpl> &oVecSrcTmpls,
    const std::vector<float> &oVecScales, std::vector<tagTmpl> &oVecDstTmpls) {
    // check the number of source templates
    if (oVecSrcTmpls.empty()) {
        LOGE("task ID %d: template vector is empty, please check", nTaskID);
        return -1;
    }

    // check the number of scales
    if (oVecScales.empty()) {
        LOGE("task ID %d: scale pyramid is invalid, please check", nTaskID);
        return -1;
    }

    oVecDstTmpls.clear();

    for (int i = 0; i < static_cast<int>(oVecSrcTmpls.size()); i++) {
        tagTmpl stSrcTmpl = oVecSrcTmpls[i];

        // check template threshold
        if (stSrcTmpl.fThreshold < 0 || stSrcTmpl.fThreshold > 1) {
            LOGE("task ID %d: template threshold is invalid, please check", nTaskID);
            return -1;
        }

        if (stSrcTmpl.oTmplImg.empty()) {
            // read and check template image
            cv::Mat oTmplImg = cv::imread(stSrcTmpl.strTmplPath);
            if (oTmplImg.empty()) {
                LOGE("task ID %d: cannot read template image %s, please check",
                    nTaskID, stSrcTmpl.strTmplPath.c_str());
                return -1;
            }

            // check ROI
            int nState = CheckROI(nTaskID, oTmplImg, stSrcTmpl.oRect);
            if (1 != nState) {
                LOGE("task ID %d: template rectangle is invalid, please check", nTaskID);
                return nState;
            }

            stSrcTmpl.oTmplImg = oTmplImg(stSrcTmpl.oRect);
        }

        // if exsit mask
        if (!stSrcTmpl.strMaskPath.empty()) {
            // read and check mask image
            cv::Mat oMaskImg = cv::imread(stSrcTmpl.strMaskPath);
            if (oMaskImg.empty()) {
                LOGE("task ID %d: cannot read mask image : %s, please check",
                    nTaskID, stSrcTmpl.strMaskPath.c_str());
                return -1;
            }

            cv::threshold(oMaskImg, oMaskImg, 127, 255, cv::THRESH_BINARY);

            // check ROI
            int nState = CheckROI(nTaskID, oMaskImg, stSrcTmpl.oRect);
            if (1 != nState) {
                LOGE("task ID %d: template rectangle is invalid, please check", nTaskID);
                return nState;
            }

            stSrcTmpl.oMaskImg = oMaskImg(stSrcTmpl.oRect);
        }

        // set output templates
        for (int j = 0; j < static_cast<int>(oVecScales.size()); j++) {
            // get scale
            float fScale = oVecScales[j];

            // set template
            tagTmpl stDstTmpl;
            stDstTmpl.nClassID = stSrcTmpl.nClassID;
            stDstTmpl.fThreshold = stSrcTmpl.fThreshold;
            stDstTmpl.strTmplName = stSrcTmpl.strTmplName;
            stDstTmpl.strTmplPath = stSrcTmpl.strTmplPath;
            stDstTmpl.strMaskPath = stSrcTmpl.strMaskPath;
            stDstTmpl.oRect = stSrcTmpl.oRect;

            int nRows = static_cast<int>(stSrcTmpl.oTmplImg.rows * fScale);
            int nCols = static_cast<int>(stSrcTmpl.oTmplImg.cols * fScale);

            // check template size
            if (nRows <= MIN_TEMPLATE_HEIGHT || nCols <= MIN_TEMPLATE_WIDTH) {
                LOGW("task ID %d: template size (cols: %d, rows: %d) is too small in scale %f",
                    nTaskID, nCols, nRows, fScale);
                continue;
            }

            cv::resize(stSrcTmpl.oTmplImg, stDstTmpl.oTmplImg, cv::Size(nCols, nRows));

            if (!stSrcTmpl.oMaskImg.empty()) {
                cv::resize(stSrcTmpl.oMaskImg, stDstTmpl.oMaskImg, cv::Size(nCols, nRows));
            }

            oVecDstTmpls.push_back(stDstTmpl);
        }
    }

    return 1;
}

bool LessScore(const tagBBox &stBBox1, const tagBBox &stBBox2) {
    // sort by score
    return stBBox1.fScore > stBBox2.fScore;
}

bool AscendBBoxX(const tagBBox &stBBox1, const tagBBox &stBBox2) {
    // sort by rect x
    return stBBox1.oRect.x < stBBox2.oRect.x;
}

int ComputeScale(const int nTaskID, const float fMinScale, const float fMaxScale,
    const int nScaleLevel, std::vector<float> *pVecScales) {
    // check min scale
    if (fMinScale <= 0) {
        LOGE("task ID %d: min scale %f is invalid, please check", nTaskID, fMinScale);
        return -1;
    }

    // check max scale
    if (fMaxScale <= 0) {
        LOGE("task ID %d: max scale %f is invalid, please check", nTaskID, fMaxScale);
        return -1;
    }

    // check scale level
    if (nScaleLevel < 1) {
        LOGE("task ID %d: scale level %d is invalid, please check", nTaskID, nScaleLevel);
        return -1;
    }

    pVecScales->clear();

    // compute scales
    if (1 == nScaleLevel) {
        pVecScales->push_back((fMinScale + fMaxScale) / 2.0f);
    } else {
        for (int i = 0; i < nScaleLevel; i++) {
            pVecScales->push_back(fMinScale + i * (fMaxScale - fMinScale) / (nScaleLevel - 1));
        }
    }

    return 1;
}

double IOU(const cv::Rect &oRect1, const cv::Rect &oRect2) {
    // compute min coordinate
    int nMinX = MAX(oRect1.x, oRect2.x);
    int nMinY = MAX(oRect1.y, oRect2.y);

    // compute max coordinate
    int nMaxX = MIN(oRect1.x + oRect1.width, oRect2.x + oRect2.width);
    int nMaxY = MIN(oRect1.y + oRect1.height, oRect2.y + oRect2.height);

    // compute area
    int nW = MAX(0, (nMaxX - nMinX + 1));
    int nH = MAX(0, (nMaxY - nMinY + 1));
    double dArea = nW * nH;

    // compute IOU
    double dIOU = dArea / (oRect1.area() + oRect2.area() - dArea);

    return (dIOU >= 0) ? dIOU : 0;
}

int MergeBBox(const std::vector<tagBBox> &oVecSrcBBoxes, std::vector<tagBBox> &oVecDstBBoxes,
    const double dOverlapThreshold, const int nCountThreshold) {
    // check the number of source bboxes
    int nBBoxNum = static_cast<int>(oVecSrcBBoxes.size());
    if (0 == nBBoxNum) {
        return 1;
    }

    oVecDstBBoxes.clear();

    // sort bboxes by score
    std::vector<tagBBox> oVecBBoxes = oVecSrcBBoxes;
    std::sort(oVecBBoxes.begin(), oVecBBoxes.end(), LessScore);

    std::vector<bool> oVecOverlap(nBBoxNum, false);
    // modify by berryjwang 0--->1
    std::vector<int> oVecCount(nBBoxNum, 1);

    // merge bboxes accoding to IOU
    for (int i = 0; i < nBBoxNum; i++) {
        if (!oVecOverlap[i]) {
            for (int j = i + 1; j < nBBoxNum; j++) {
                if (IOU(oVecBBoxes[i].oRect, oVecBBoxes[j].oRect) >= dOverlapThreshold) {
                    oVecOverlap[j] = true;
                    oVecCount[i]++;
                }
            }
        }
    }

    // filter bboxes accoding to overlap count
    for (int i = 0; i < nBBoxNum; i++) {
        if (!oVecOverlap[i] && oVecCount[i] >= nCountThreshold) {
            oVecDstBBoxes.push_back(oVecBBoxes[i]);
        }
    }

    return 1;
}

int CheckROI(const int nTaskID, const cv::Mat &oSrcImg, cv::Rect &oROI) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", nTaskID);
        return -1;
    }

    // check ROI x
    if (oROI.x >= oSrcImg.cols) {
        LOGE("task ID %d: ROI x %d is larger than image cols %d, please check",
            nTaskID, oROI.x, oSrcImg.cols);
        return -1;
    }

    // check ROI y
    if (oROI.y >= oSrcImg.rows) {
        LOGE("task ID %d: ROI y %d is larger than image rows %d, please check",
            nTaskID, oROI.y, oSrcImg.rows);
        return -1;
    }

    // check ROI width
    if (oROI.width < 0) {
        LOGE("task ID %d: ROI width %d is less than 0, please check", nTaskID, oROI.width);
        return -1;
    }

    // check ROI height
    if (oROI.height < 0) {
        LOGE("task ID %d: ROI height %d is less than 0, please check", nTaskID, oROI.height);
        return -1;
    }

    if (oROI.x < 0) {
        // LOGD("task ID %d: ROI x %d is less than 0", nTaskID, oROI.x);
        oROI.x = 0;
        // LOGD("task ID %d: new ROI x is %d", nTaskID, oROI.x);
    }

    if (oROI.y < 0) {
        // LOGD("task ID %d: ROI y %d is less than 0", nTaskID, oROI.y);
        oROI.y = 0;
        // LOGD("task ID %d: new ROI y is %d", nTaskID, oROI.y);
    }

    if (oROI.x + oROI.width > oSrcImg.cols) {
        // LOGD("task ID %d: ROI x %d + width %d is larger than image cols %d", nTaskID,
        // oROI.x, oROI.width, oSrcImg.cols);
        oROI.width = oSrcImg.cols - oROI.x;
        // LOGD("task ID %d: new ROI width is %d", nTaskID, oROI.width);
    }

    if (oROI.y + oROI.height > oSrcImg.rows) {
        // LOGD("task ID %d: ROI y %d + height %d is larger than image rows %d", nTaskID,
        // oROI.y, oROI.height, oSrcImg.rows);
        oROI.height = oSrcImg.rows - oROI.y;
        // LOGD("task ID %d: new ROI height is %d", nTaskID, oROI.height);
    }

    return 1;
}

int CombineROI(const int nTaskID, const std::vector<cv::Rect> &oVecROIs, cv::Rect &oROI) {
    // check the number of ROIs
    if (oVecROIs.empty()) {
        LOGE("task ID %d: ROI is empty, please check", nTaskID);
        return -1;
    }

    // only one ROI
    if (1 == static_cast<int>(oVecROIs.size())) {
        oROI = oVecROIs[0];
        return 1;
    }

    // initialize left-top and right-down coordinates
    int nMinX = static_cast<int>(1e+5);
    int nMinY = static_cast<int>(1e+5);
    int nMaxX = 0;
    int nMaxY = 0;

    // compute left-top and right-down coordinates
    for (int i = 0; i < static_cast<int>(oVecROIs.size()); i++) {
        if (oVecROIs[i].x < nMinX) {
            nMinX = oVecROIs[i].x;
        }

        if (oVecROIs[i].y < nMinY) {
            nMinY = oVecROIs[i].y;
        }

        if (oVecROIs[i].x + oVecROIs[i].width > nMaxX) {
            nMaxX = oVecROIs[i].x + oVecROIs[i].width;
        }

        if (oVecROIs[i].y + oVecROIs[i].height > nMaxY) {
            nMaxY = oVecROIs[i].y + oVecROIs[i].height;
        }
    }

    oROI = cv::Rect(nMinX, nMinY, nMaxX - nMinX, nMaxY - nMinY);

    return 1;
}

int DrawBBox(const cv::Mat &oSrcImg, const std::vector<tagBBox> &oVecBBoxes,
    const int nWaiteTime, const int nClassID) {
    cv::Mat oDisplayImg = oSrcImg.clone();

    // draw each bbox
    int nBBoxNum = static_cast<int>(oVecBBoxes.size());
    for (int nIdx = 0; nIdx < nBBoxNum; nIdx++) {
        if (-1 == nClassID) {
            // draw all bboxes
            cv::rectangle(oDisplayImg, oVecBBoxes[nIdx].oRect, cv::Scalar(0, 0, 255), 2);

            // draw template name
            cv::Point oPt;
            oPt.x = static_cast<int>(oVecBBoxes[nIdx].oRect.x + 0.5 * oVecBBoxes[nIdx].oRect.width);
            oPt.y = oVecBBoxes[nIdx].oRect.y;
            cv::putText(oDisplayImg, oVecBBoxes[nIdx].szTmplName, oPt,
                cv::FONT_HERSHEY_COMPLEX, 1, cv::Scalar(0, 0, 255), 2, 8, 0);
        } else {
            // draw bboxes with the class ID
            if (oVecBBoxes[nIdx].nClassID == nClassID) {
                cv::rectangle(oDisplayImg, oVecBBoxes[nIdx].oRect, cv::Scalar(0, 0, 255), 2);
            }
        }
    }

    cv::imshow("Result", oDisplayImg);
    cvWaitKey(nWaiteTime);

    return 1;
}

#ifdef WINDOWS
int GetPath(const int nTaskID, const std::string strPath,
    std::vector<std::string> *pVecPaths, std::vector<std::string> *pVecNames) {
    pVecPaths->clear();
    pVecNames->clear();

    intptr_t           hFile = 0;
    struct _finddata_t stFileInfo;

    hFile = _findfirst(strPath.c_str(), &stFileInfo);
    if (hFile == -1) {
        LOGE("task ID %d: template directory %s is invalid, please check",
            nTaskID, strPath.c_str());
        _findclose(hFile);
        return -1;
    }

    do {
        std::string strDirectory = strPath.substr(0, strPath.length() - 5);
        std::string strFilePath = strDirectory.append(stFileInfo.name);
        pVecPaths->push_back(strFilePath);

        std::string strName = stFileInfo.name;
        strName = strName.substr(0, strName.length() - 4);
        pVecNames->push_back(strName);
    } while (_findnext(hFile, &stFileInfo) == 0);

    _findclose(hFile);

    return 1;
}
#endif

#ifdef LINUX
int GetPath(const int nTaskID, const std::string strPath,
    std::vector<std::string> *pVecPaths, std::vector<std::string> *pVecNames) {
    pVecPaths->clear();
    pVecNames->clear();

    std::string strDirectory = strPath.substr(0, strPath.length() - 5);
    std::string strSuffix = strPath.substr(strPath.length() - 3, 3);

    DIR *pDir = NULL;
    if (!(pDir = opendir(strDirectory.c_str()))) {
        LOGE("task ID %d: template directory %s is invalid, please check",
            nTaskID, strDirectory.c_str());
        return -1;
    }

    struct dirent stEntry;
    struct dirent *pResult = NULL;

    while (!readdir_r(pDir, &stEntry, &pResult) && pResult != NULL) {
        if (0 == strcmp(stEntry.d_name, ".") || 0 == strcmp(stEntry.d_name, "..")) {
            continue;
        }

        std::string strFilePath = strDirectory + stEntry.d_name;

        if (strSuffix == strFilePath.substr(strFilePath.size() - strSuffix.size())) {
            pVecPaths->push_back(strFilePath);

            std::string strName = stEntry.d_name;
            strName = strName.substr(0, strName.length() - 4);
            pVecNames->push_back(strName);
        }
    }

    closedir(pDir);

    return 1;
}
#endif

int AnalyzeTmplPath(const int nTaskID, const std::vector<tagTmpl> &oVecSrcTmpls,
    std::vector<tagTmpl> &oVecDstTmpls) {
    // check the number of source templates
    if (oVecSrcTmpls.empty()) {
        LOGE("task ID %d: template vector is empty, please check", nTaskID);
        return -1;
    }

    oVecDstTmpls.clear();

    for (int i = 0; i < static_cast<int>(oVecSrcTmpls.size()); i++) {
        tagTmpl stTmpl = oVecSrcTmpls[i];

        // if find *. in template path, read all template paths and template names
        std::string sTmplPath = stTmpl.strTmplPath;
        if (-1 != sTmplPath.find("*.")) {
            std::vector<std::string> oVecPaths;
            std::vector<std::string> oVecNames;
            GetPath(nTaskID, sTmplPath, &oVecPaths, &oVecNames);

            for (int j = 0; j < static_cast<int>(oVecPaths.size()); j++) {
                tagTmpl stNewTmpl;
                stNewTmpl = stTmpl;
                stNewTmpl.strTmplPath = oVecPaths[j];
                stNewTmpl.strTmplName = oVecNames[j];
                AnalyzeFileName(nTaskID, oVecNames[j], stNewTmpl.strTmplName, stNewTmpl.nClassID);
                oVecDstTmpls.push_back(stNewTmpl);
            }
        } else {
            oVecDstTmpls.push_back(stTmpl);
        }
    }

    return 1;
}

int AnalyzeFileName(const int nTaskID, const std::string &strFileName,
    std::string &strTmplName, int &nClassID) {
    // find _ in file name
    size_t nLoc = strFileName.find("_");

    if (-1 == nLoc) {
        strTmplName = strFileName;
        nClassID = -1;

        return 1;
    }

    // get class ID
    std::string strNum = strFileName.substr(0, nLoc);
    nClassID = std::stoi(strNum);

    // get template name
    strTmplName = strFileName.substr(nLoc + 1, strFileName.length());

    return 1;
}

int ResizeRect(const cv::Rect &oSrcRect, float fXScale, float fYScale, cv::Rect &oDstRect) {
    oDstRect.x = static_cast<int>(oSrcRect.x * fXScale);
    oDstRect.y = static_cast<int>(oSrcRect.y * fYScale);
    oDstRect.width = static_cast<int>(oSrcRect.width * fXScale);
    oDstRect.height = static_cast<int>(oSrcRect.height * fYScale);

    return 1;
}

int ExpandRect(const cv::Rect &oSrcRect, int nExpandWidth, int nExpandHeight, cv::Rect &oDstRect) {
    // compute x and y
    oDstRect.x = static_cast<int>(oSrcRect.x - 0.5 * nExpandWidth);
    oDstRect.y = static_cast<int>(oSrcRect.y - 0.5 * nExpandHeight);

    // check x
    if (oDstRect.x < 0) {
        oDstRect.width = oSrcRect.width + nExpandWidth + oDstRect.x;
        oDstRect.x = 0;
    } else {
        oDstRect.width = oSrcRect.width + nExpandWidth;
    }

    // check y
    if (oDstRect.y < 0) {
        oDstRect.height = oSrcRect.height + nExpandHeight + oDstRect.y;
        oDstRect.y = 0;
    } else {
        oDstRect.height = oSrcRect.height + nExpandHeight;
    }

    return 1;
}

int AverageRect(const int nTaskID, const std::vector<cv::Rect> &oVecRects, cv::Rect &oAvgRect) {
    // check the number of rectangles
    if (oVecRects.empty()) {
        LOGE("task ID %d: there is no rectangle, please check", nTaskID);
        return -1;
    }

    // initialize coordinates
    oAvgRect = cv::Rect(0, 0, 0, 0);

    // compute total coordinates
    for (int i = 0; i < oVecRects.size(); i++) {
        oAvgRect.x += oVecRects[i].x;
        oAvgRect.y += oVecRects[i].y;
        oAvgRect.width += oVecRects[i].width;
        oAvgRect.height += oVecRects[i].height;
    }

    // average coordinates
    oAvgRect.x = static_cast<int>(oAvgRect.x / oVecRects.size());
    oAvgRect.y = static_cast<int>(oAvgRect.y / oVecRects.size());
    oAvgRect.width = static_cast<int>(oAvgRect.width / oVecRects.size());
    oAvgRect.height = static_cast<int>(oAvgRect.height / oVecRects.size());

    return 1;
}

int GetRGB(const int nTaskID, const std::string &strCondition, int &nRedLower, int &nRedUpper,
    int &nGreenLower, int &nGreenUpper, int &nBlueLower, int &nBlueUpper) {
    // check condition
    if (strCondition.empty()) {
        LOGE("task ID %d: RGB condition is empty, please check", nTaskID);
        return -1;
    }

    size_t nLocPrev;
    size_t nLocNext;

    // split condition
    nLocPrev = 0;
    nLocNext = 0;

    nLocNext = strCondition.find(",", nLocPrev + 1);
    std::string strRed = strCondition.substr(nLocPrev, nLocNext - nLocPrev);
    nLocPrev = nLocNext + 1;

    nLocNext = strCondition.find(",", nLocPrev + 1);
    std::string strGreen = strCondition.substr(nLocPrev, nLocNext - nLocPrev);
    nLocPrev = nLocNext + 1;

    nLocNext = strCondition.find(",", nLocPrev + 1);
    std::string strBlue = strCondition.substr(nLocPrev, nLocNext - nLocPrev);
    // nLocPrev = nLocNext + 1;

    // read red value
    nLocPrev = 0;
    nLocNext = 0;

    nLocNext = strRed.find("<", nLocPrev + 1);
    std::string strRedLower = strRed.substr(nLocPrev, nLocNext - nLocPrev);
    nLocPrev = nLocNext + 1;
    nRedLower = std::stoi(strRedLower);

    nLocNext = strRed.find("<", nLocPrev + 1);
    std::string strRedUpperr = strRed.substr(nLocNext + 1, strRed.length() - nLocNext);
    // nLocPrev  = nLocNext + 1;
    nRedUpper = std::stoi(strRedUpperr);

    // read green value
    nLocPrev = 0;
    nLocNext = 0;

    nLocNext = strGreen.find("<", nLocPrev + 1);
    std::string strGreenLower = strGreen.substr(nLocPrev, nLocNext - nLocPrev);
    nLocPrev = nLocNext + 1;
    nGreenLower = std::stoi(strGreenLower);

    nLocNext = strGreen.find("<", nLocPrev + 1);
    std::string strGreenUpperr = strGreen.substr(nLocNext + 1, strGreen.length() - nLocNext);
    // nLocPrev    = nLocNext + 1;
    nGreenUpper = std::stoi(strGreenUpperr);

    // red blue value
    nLocPrev = 0;
    nLocNext = 0;

    nLocNext = strBlue.find("<", nLocPrev + 1);
    std::string strBlueLower = strBlue.substr(nLocPrev, nLocNext - nLocPrev);
    nLocPrev = nLocNext + 1;
    nBlueLower = std::stoi(strBlueLower);

    nLocNext = strBlue.find("<", nLocPrev + 1);
    std::string strBlueUpperr = strBlue.substr(nLocNext + 1, strBlue.length() - nLocNext);
    // nLocPrev   = nLocNext + 1;
    nBlueUpper = std::stoi(strBlueUpperr);

    return 1;
}

int AddMask(const int nTaskID, const cv::Mat &oSrcImg, const cv::Mat &oMaskImg,
    const int &nMaskValue, cv::Mat &oDstImg) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", nTaskID);
        return -1;
    }

    // check mask image
    if (oMaskImg.empty()) {
        oSrcImg.copyTo(oDstImg);
        return 1;
    }

    // resize mask image according to source image
    cv::Mat oResizeMaskImg;
    cv::resize(oMaskImg, oResizeMaskImg, cv::Size(oSrcImg.cols, oSrcImg.rows));

    // get unmasked region from source image
    cv::Mat oBinImg;
    cv::threshold(oResizeMaskImg, oBinImg, 127, 255, cv::THRESH_BINARY);
    cv::Mat oUnmaskRegion;
    oSrcImg.copyTo(oUnmaskRegion, oBinImg);

    // get masked region from value image
    cv::Mat oBinImgInv;
    cv::threshold(oResizeMaskImg, oBinImgInv, 127, 255, cv::THRESH_BINARY_INV);
    cv::Mat oValueImg(oSrcImg.rows, oSrcImg.cols, CV_8UC3,
        cv::Scalar(nMaskValue, nMaskValue, nMaskValue));
    cv::Mat oMaskRegion;
    oValueImg.copyTo(oMaskRegion, oBinImgInv);

    cv::add(oUnmaskRegion, oMaskRegion, oDstImg);

    return 1;
}

int ConvertImgTo720P(const int nTaskID, const cv::Mat &oSrcImg, cv::Mat &oDstImg, float &fRatio) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", nTaskID);
        return -1;
    }

    int nLongSide = MAX(oSrcImg.cols, oSrcImg.rows);

    if (nLongSide == IMAGE_LONG_SIDE) {
        fRatio = 1.0f;
        oDstImg = oSrcImg.clone();
    } else {
        fRatio = static_cast<float>(nLongSide) / static_cast<float>(IMAGE_LONG_SIDE);
        int nRows = static_cast<int>(oSrcImg.rows / fRatio);
        int nCols = static_cast<int>(oSrcImg.cols / fRatio);

        cv::resize(oSrcImg, oDstImg, cv::Size(nCols, nRows));
    }

    return 1;
}
