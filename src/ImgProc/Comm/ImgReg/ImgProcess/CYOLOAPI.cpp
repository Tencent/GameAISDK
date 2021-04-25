/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/ImgProcess/CYOLOAPI.h"

extern int g_nMaxResultSize;

static void Mat2Image(const cv::Mat &oImg, image &stImg) {
    unsigned char *data = (unsigned char*)oImg.data;
    int           nHeight = oImg.rows;
    int           nWidth = oImg.cols;
    int           nChannel = oImg.channels();
    int           nStep = nWidth * nChannel;
    int           i, j, k;

#pragma omp parallel for

    for (i = 0; i < nHeight; ++i) {
        const unsigned char *p = oImg.ptr<unsigned char>(i);
        int                 nIndexBegin = i * nWidth;

        for (k = 0; k < nChannel; ++k) {
            int nChannelBegin = nIndexBegin + k * nWidth * nHeight;

            for (j = 0; j < nWidth; ++j) {
                stImg.data[nChannelBegin + j] = p[j * nChannel + k] / 255.;
            }
        }
    }
}

static int MaxIndex(float *pScores, int nCount) {
    if (nCount <= 0)
        return -1;

    int   i, nMaxIndex = 0;
    float fMax = pScores[0];

    for (i = 1; i < nCount; ++i) {
        if (pScores[i] > fMax) {
            fMax = pScores[i];
            nMaxIndex = i;
        }
    }

    return nMaxIndex;
}

// **************************************************************************************
//          CYOLO Class Functions
// **************************************************************************************

CYOLO::CYOLO() {
    m_pszNames = NULL;
    m_fThreshold = 0.5f;  // detection threshold
}

CYOLO::~CYOLO() {
}

int CYOLO::Initialize(char *pszCfgPath, char *pszWeightPath, char *pszNameFile, float fThreshold) {
    // check parameters
    if (NULL == pszCfgPath) {
        printf("cfg file is NULL, please check\n");
        return -1;
    }

    if (NULL == pszWeightPath) {
        printf("weight file is NULL, please check\n");
        return -1;
    }

    if (NULL == pszNameFile) {
        printf("name file is NULL, please check\n");
        return -1;
    }

    if (fThreshold < 0) {
        printf("threshold is invalid, please check\n");
        return -1;
    }

    // initialize networks
#ifdef WINDOWS
    for (int i = 0; i < g_nMaxResultSize; i++) {
        tagYoloNetWork stYoloNetWork;

        stYoloNetWork.Mutex = TqcOsCreateMutex();

        // load config
        stYoloNetWork.stNet = parse_network_cfg(pszCfgPath);
        if (NULL == stYoloNetWork.stNet.workspace) {
            LOGW("load cfg file %s failed", pszCfgPath);
            return -1;
        }

        // load weights
        load_weights(&stYoloNetWork.stNet, pszWeightPath);

        // set batch size to 1
        set_batch_network(&stYoloNetWork.stNet, 1);

        m_oVecNets.push_back(stYoloNetWork);
    }
#endif

#ifdef LINUX
    for (int nIdx = 0; nIdx < g_nMaxResultSize; ++nIdx) {
        tagYoloNetWork stYoloNetWork;

        stYoloNetWork.Mutex = TqcOsCreateMutex();

        // load config
        stYoloNetWork.pNet = parse_network_cfg(pszCfgPath);
        if (stYoloNetWork.pNet == NULL) {
            std::string strCfgPath = std::string(pszCfgPath);
            LOGE("load cfg of yolo failed: %s", strCfgPath.c_str());
            return -1;
        }

        // load weights
        if (-1 == load_weights(stYoloNetWork.pNet, pszWeightPath)) {
            free_network(stYoloNetWork.pNet);
            std::string strWeightPath = std::string(pszWeightPath);
            LOGE("load weight of yolo failed: %s", strWeightPath.c_str());
            return -1;
        }

        // set batch size to 1
        set_batch_network(stYoloNetWork.pNet, 1);

        m_oVecNets.push_back(stYoloNetWork);
    }

    // #ifdef NNPACK
    //      nnp_initialize();
    //      m_pNet->threadpool = pthreadpool_create(4);
    // #endif
#endif

    srand(time(0));

    // load class names
    m_pszNames = get_labels(pszNameFile);
    if (m_pszNames == NULL) {
        std::string strNameFile = std::string(pszNameFile);
        LOGE("load name of yolo failed: %s", strNameFile.c_str());
        return -1;
    }

    // copy parameters
    m_fThreshold = fThreshold;

    return 1;
}

int CYOLO::Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes) {
    // check parameters
    if (oSrcImg.empty()) {
        printf("source image is empty, please check\n");
        return -1;
    }

    oVecBBoxes.clear();

    int nBoxes = 0;
#ifdef WINDOWS
    network stNet;
    stNet.n = 0;

    // select free network
    int nIdx = 0;
    while (true) {
        for (; nIdx < g_nMaxResultSize; ++nIdx) {
            if (m_oVecNets[nIdx].IsFree()) {
                stNet = m_oVecNets[nIdx].stNet;
                break;
            }
        }

        if (stNet.n != 0) {
            break;
        }
    }

    // convert cv::Mat to Image
    cv::Mat oImg;
    cv::resize(oSrcImg, oImg, cv::Size(stNet.w, stNet.h));
    cv::cvtColor(oImg, oImg, CV_BGR2RGB);
    image stImg = make_image(oImg.cols, oImg.rows, oImg.channels());
    Mat2Image(oImg, stImg);

    // resize image
    image stImgResize = resize_image(stImg, stNet.w, stNet.h);

    // run inference in network
    network_predict(stNet, stImgResize.data);

    // get detection results
    detection *pDetResults = get_network_boxes(&stNet, oSrcImg.cols, oSrcImg.rows,
        m_fThreshold, .5, 0, 1, &nBoxes, 0);
    layer     stLayer = stNet.layers[stNet.n - 1];

    // set used network unwork
    m_oVecNets[nIdx].SetFree();
#endif

#ifdef LINUX
    network *pFreeNet = NULL;

    // select free network
    int nIdx = 0;
    while (true) {
        for (; nIdx < g_nMaxResultSize; ++nIdx) {
            if (m_oVecNets[nIdx].IsFree()) {
                pFreeNet = m_oVecNets[nIdx].pNet;
                break;
            }
        }

        if (pFreeNet != NULL) {
            break;
        }
    }

    // convert cv::Mat to Image
    cv::Mat oImg;
    cv::resize(oSrcImg, oImg, cv::Size(pFreeNet->w, pFreeNet->h));
    cv::cvtColor(oImg, oImg, CV_BGR2RGB);
    image stImg = make_image(oImg.cols, oImg.rows, oImg.channels());
    Mat2Image(oImg, stImg);

    // resize image
    image stImgResize = letterbox_image(stImg, pFreeNet->w, pFreeNet->h);

    // run inference in network
    float *pDatas = stImgResize.data;
    network_predict(pFreeNet, pDatas);

    // get detection results
    detection *pDetResults = get_network_boxes(pFreeNet, oSrcImg.cols, oSrcImg.rows,
        m_fThreshold, .5, 0, 1, &nBoxes);
    layer     stLayer = pFreeNet->layers[pFreeNet->n - 1];
    // printf("nBoxes %d\n", nBoxes);

    // set used network unwork
    m_oVecNets[nIdx].SetFree();
#endif

    // nms
    int nClasses = stLayer.classes;
    do_nms_sort(pDetResults, nBoxes, nClasses, .4);

    // char **names = get_labels("./Data/CJZC/yolov3.names");
    // draw_detections_v3(stImg, pDetResults, nBoxes, m_fThreshold, names, NULL, nClasses, 0);
    // show_image(stImg, "predictions");
    // cvWaitKey(0);

    // set results
    for (int i = 0; i < nBoxes; i++) {
        int   nClassIdx = MaxIndex(pDetResults[i].prob, nClasses);
        float fProb = pDetResults[i].prob[nClassIdx];

        if (fProb > m_fThreshold) {
            box stBox = pDetResults[i].bbox;

            int nLeft = (stBox.x - stBox.w / 2.) * oSrcImg.cols;
            int nRight = (stBox.x + stBox.w / 2.) * oSrcImg.cols;
            int nTop = (stBox.y - stBox.h / 2.) * oSrcImg.rows;
            int nDown = (stBox.y + stBox.h / 2.) * oSrcImg.rows;

            if (nLeft < 0)
                nLeft = 0;

            if (nRight > oSrcImg.cols - 1)
                nRight = oSrcImg.cols - 1;

            if (nTop < 0)
                nTop = 0;

            if (nDown > oSrcImg.rows - 1)
                nDown = oSrcImg.rows - 1;

            tagBBox stBBox;
            stBBox.nClassID = nClassIdx;
            snprintf(stBBox.szTmplName, sizeof(stBBox.szTmplName), "%s", m_pszNames[nClassIdx]);
            stBBox.fScore = fProb;
            stBBox.oRect = cv::Rect(nLeft, nTop, nRight - nLeft, nDown - nTop);
            oVecBBoxes.push_back(stBBox);
        }
    }

    // release pointers and structures
    free_detections(pDetResults, nBoxes);
    free_image(stImg);
    free_image(stImgResize);

    return 1;
}

int CYOLO::Release() {
    // release networks
#ifdef WINDOWS
    for (size_t nIdx = 0; nIdx < m_oVecNets.size(); ++nIdx) {
        free_network(m_oVecNets[nIdx].stNet);
        TqcOsDeleteMutex(m_oVecNets[nIdx].Mutex);
    }
#endif

#ifdef LINUX
    for (size_t nIdx = 0; nIdx < m_oVecNets.size(); ++nIdx) {
        if (m_oVecNets[nIdx].pNet != NULL) {
            free_network(m_oVecNets[nIdx].pNet);
            m_oVecNets[nIdx].pNet = NULL;
            TqcOsDeleteMutex(m_oVecNets[nIdx].Mutex);
        }
    }
#endif

    return 1;
}

// **************************************************************************************
//          CYOLOAPI Class Define
// **************************************************************************************

CYOLOAPI::CYOLOAPI() {
    m_nTaskID = -1;  // task id
    m_nMaskValue = 127;  // mask value
    m_oROI = cv::Rect(-1, -1, -1, -1);  // detection ROI
}

CYOLOAPI::~CYOLOAPI() {
}

int CYOLOAPI::Initialize(const CYOLOAPIParam &oParam) {
    // check parameters
    if (oParam.m_nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", oParam.m_nTaskID);
        return -1;
    }

    if (oParam.m_nMaskValue < 0 && oParam.m_nMaskValue > 255) {
        LOGE("task ID %d: mask value %d is invalid, please check",
            oParam.m_nTaskID, oParam.m_nMaskValue);
        return -1;
    }

    if (oParam.m_strCfgPath.empty()) {
        LOGE("task ID %d: cfg path is empty, please check", oParam.m_nTaskID);
        return -1;
    }

    if (oParam.m_strWeightPath.empty()) {
        LOGE("task ID %d: weight path is empty, please check", oParam.m_nTaskID);
        return -1;
    }

    if (oParam.m_strNamePath.empty()) {
        LOGE("task ID %d: name path is empty, please check", oParam.m_nTaskID);
        return -1;
    }

    if (oParam.m_fThreshold < 0) {
        LOGE("task ID %d: threshold %f is invalid, please check",
            oParam.m_nTaskID, oParam.m_fThreshold);
        return -1;
    }

    // copy parameters
    m_nTaskID = oParam.m_nTaskID;
    m_nMaskValue = oParam.m_nMaskValue;

    // set ROI
    if (-1 == oParam.m_oROI.width && -1 == oParam.m_oROI.height) {
        m_oROI = cv::Rect(0, 0, static_cast<int>(1e+4), static_cast<int>(1e+4));
    } else {
        m_oROI = oParam.m_oROI;
    }

    // set mask
    if (!oParam.m_strMaskPath.empty()) {
        // load mask
        m_oMask = cv::imread(oParam.m_strMaskPath);
        if (m_oMask.empty()) {
            LOGE("task ID %d: cannot read mask image : %s, please check",
                m_nTaskID, oParam.m_strMaskPath.c_str());
            return -1;
        }

        cv::threshold(m_oMask, m_oMask, 127, 255, cv::THRESH_BINARY);
    }

    // copy config file path
    char *pszCfgPath = const_cast<char*>(oParam.m_strCfgPath.c_str());

    // copy weight file path
    char *pszWeightPath = const_cast<char*>(oParam.m_strWeightPath.c_str());

    // copy name file path
    char *pszNamePath = const_cast<char*>(oParam.m_strNamePath.c_str());

    // initialize method
    int nState = m_oYOLO.Initialize(pszCfgPath, pszWeightPath, pszNamePath, oParam.m_fThreshold);
    if (1 != nState) {
        LOGE("task ID %d: CYOLO initialization failed", m_nTaskID);
        return nState;
    }

    return 1;
}

int CYOLOAPI::Predict(const CYOLOAPIData &oData, CYOLOAPIResult &oResult) {
    // check parameters
    if (oData.m_oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    // check ROI
    nState = CheckROI(m_nTaskID, oData.m_oSrcImg, m_oROI);
    if (1 != nState) {
        LOGE("task ID %d: ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    oResult.m_oVecBBoxes.clear();

    // use mask on source image
    cv::Mat oSrcImg;
    AddMask(m_nTaskID, oData.m_oSrcImg, m_oMask, m_nMaskValue, oSrcImg);

    // run method
    std::vector<tagBBox> oVecBBoxes;
    nState = m_oYOLO.Predict(oSrcImg(m_oROI), oVecBBoxes);
    if (1 != nState) {
        LOGE("task ID %d: CYOLO predict failed, please check", m_nTaskID);
        return nState;
    }

    if (oVecBBoxes.empty()) {
        return 1;
    }

    // set result
    MergeBBox(oVecBBoxes, oResult.m_oVecBBoxes, 0.50);

    for (int i = 0; i < static_cast<int>(oResult.m_oVecBBoxes.size()); i++) {
        oResult.m_oVecBBoxes[i].oRect.x += m_oROI.x;
        oResult.m_oVecBBoxes[i].oRect.y += m_oROI.y;
    }

    sort(oResult.m_oVecBBoxes.begin(), oResult.m_oVecBBoxes.end(), LessScore);

    return 1;
}

int CYOLOAPI::Release() {
    // release method
    m_oYOLO.Release();

    return 1;
}
