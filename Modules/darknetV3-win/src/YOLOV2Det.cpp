/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */


#include <time.h>
#include <stdlib.h>
#include <stdio.h>


#include "YOLOV2Det.h"


//#include <sys/time.h>
//
//
//unsigned int TqcOsGetMicroSeconds(void)
//{
//    unsigned int   time;
//    struct timeval tv;
//
//    /* Return the time of day in milliseconds. */
//    gettimeofday(&tv, 0);
//    time = (tv.tv_sec * 1000000) + tv.tv_usec;
//
//    return time;
//}


static int MaxIndex(float *pScores, int nCount)
{
    if (nCount <= 0)
        return -1;

    int   i, nMaxIndex = 0;
    float fMax = pScores[0];

    for (i = 1; i < nCount; ++i)
    {
        if (pScores[i] > fMax)
        {
            fMax      = pScores[i];
            nMaxIndex = i;
        }
    }

    return nMaxIndex;
}


static int  FilterDetectBBoxs(tagDetBBox *pstBBox, int nWidth, int nHeight, int nNum, float fThresh, detection *dets, int nClasses)
{
    int i;
    int nVaildCnt = 0;

    for (i = 0; i < nNum; ++i)
    {
        int   nCla  = MaxIndex(dets[i].prob, nClasses);
        float fProb = dets[i].prob[nCla];

        if (fProb > fThresh)
        {
            box stBox = dets[i].bbox;

            int nLeft  = (stBox.x - stBox.w / 2.) * nWidth;
            int nRight = (stBox.x + stBox.w / 2.) * nWidth;
            int nTop   = (stBox.y - stBox.h / 2.) * nHeight;
            int nBot   = (stBox.y + stBox.h / 2.) * nHeight;

            if (nLeft < 0)
                nLeft = 0;

            if (nRight > nWidth - 1)
                nRight = nWidth - 1;

            if (nTop < 0)
                nTop = 0;

            if (nBot > nHeight - 1)
                nBot = nHeight - 1;

            pstBBox[nVaildCnt++] = tagDetBBox(nLeft, nTop, nRight - nLeft, nBot - nTop, fProb, nCla);
            if (nVaildCnt > MAX_OBJECT_SIZE)
            {
                break;
            }

            // oVecBBox.push_back(tagDetectBBox(nLeft, nTop, nRight - nLeft, nBot - nTop, fProb, nCla));
        }
    }

    return nVaildCnt;
}



static void MatIntoImage(const cv::Mat &oSrc, image &stImage)
{
    unsigned char *data    = (unsigned char*)oSrc.data;
    int           nHeight  = oSrc.rows;
    int           nWidth   = oSrc.cols;
    int           nChannel = oSrc.channels();
    int           nStep    = nWidth * nChannel;
    int           i, j, k;

    #pragma omp parallel for

    for (i = 0; i < nHeight; ++i)
    {
        const unsigned char *p          = oSrc.ptr<unsigned char>(i);
        int                 nIndexBegin = i * nWidth;

        for (k = 0; k < nChannel; ++k)
        {
            int nChannelBegin = nIndexBegin + k * nWidth * nHeight;

            for (j = 0; j < nWidth; ++j)
            {
                stImage.data[nChannelBegin + j] = p[j * nChannel + k] / 255.;
            }
        }
    }
}

static float get_pixel(image stImage, int nPosX, int nPosY, int nChannels)
{
    assert(nPosX < stImage.w && nPosY < stImage.h && nChannels < stImage.c);
    return stImage.data[nChannels * stImage.h * stImage.w + nPosY * stImage.w + nPosX];
}

static void set_pixel(image stImage, int nPosX, int nPosY, int nChannels, float fVal)
{
    if (nPosX < 0 || nPosY < 0 || nChannels < 0 || nPosX >= stImage.w || nPosY >= stImage.h || nChannels >= stImage.c)
        return;

    assert(nPosX < stImage.w && nPosY < stImage.h && nChannels < stImage.c);
    stImage.data[nChannels * stImage.h * stImage.w + nPosY * stImage.w + nPosX] = fVal;
}

static void embed_image(image stSource, image stDest, int nDx, int nDy)
{
    int x, y, k;

    for (k = 0; k < stSource.c; ++k)
    {
        for (y = 0; y < stSource.h; ++y)
        {
            for (x = 0; x < stSource.w; ++x)
            {
                float fVal = get_pixel(stSource, x, y, k);
                set_pixel(stDest, nDx + x, nDy + y, k, fVal);
            }
        }
    }
}

image LetterboxImage(image stImage, int nWidth, int nHeight)
{
    int nNewW = stImage.w;
    int nNewH = stImage.h;

    if ((static_cast<float>(nWidth) / stImage.w) < (static_cast<float>(nWidth) / stImage.h))
    {
        nNewW = nWidth;
        nNewH = (stImage.h * nWidth) / stImage.w;
    }
    else
    {
        nNewW = nHeight;
        nNewH = (stImage.w * nHeight) / stImage.h;
    }

    image stResized = resize_image(stImage, nNewW, nNewH);
    image stBoxed   = make_image(nWidth, nHeight, stImage.c);
    fill_image(stBoxed, .5);
    embed_image(stResized, stBoxed, (nWidth - nNewW) / 2, (nHeight - nNewH) / 2);
    free_image(stResized);
    return stBoxed;
}

bool CYOLOV2Det::Initialize(void *pParam)
{
    if (NULL == pParam)
    {
        return false;
    }
}

bool CYOLOV2Det::Initialize(char *szNetFile, char *szWeightFile)
{
    if (NULL == szNetFile || NULL == szWeightFile)
    {
        printf("input file is NULL\n");
        return false;
    }

    m_pstNet = parse_network_cfg(szNetFile);
    load_weights(&m_pstNet, szWeightFile);
    srand(2222222);
    m_fthresh      = 0.10f;
    m_fhier_thresh = 0.5f;
    m_fnms = 0.1f;

    #ifdef NNPACK
    nnp_initialize();
    m_pstNet->threadpool = pthreadpool_create(4);
    #endif
    layer stlayer = m_pstNet.layers[m_pstNet.n - 1];

    // box *pstBox;
    box *pstBox = reinterpret_cast<box*>(calloc(stlayer.w * stlayer.h * stlayer.n, sizeof(box)));
    m_pstBoxes = reinterpret_cast<void*>(pstBox);
    m_pfProbs = reinterpret_cast<float**>(calloc(stlayer.w * stlayer.h * stlayer.n, sizeof(*m_pfProbs)));

    for (int j = 0; j < stlayer.w * stlayer.h * stlayer.n; ++j)
    {
        m_pfProbs[j] = reinterpret_cast<float*>(calloc(stlayer.classes + 1, sizeof(*m_pfProbs)));
    }

    return true;
}

int CYOLOV2Det::Detect(const cv::Mat &oSrcImage, tagDetBBox* &pstResult, int &nNum)
{
    if (oSrcImage.empty())
    {
        printf("input image is empty, please check \n");
        return -1;
    }

    RestDetRet();
    cv::Mat      oProImg     = oSrcImage.clone();
    //unsigned int nResizeCost = TqcOsGetMicroSeconds();
    float fscaleX = oProImg.cols * 1.0 / m_pstNet.w;
    float fscaleY = oProImg.rows * 1.0 / m_pstNet.h;
    cv::resize(oProImg, oProImg, cv::Size(m_pstNet.w, m_pstNet.h));
    image stImage = make_image(oProImg.cols, oProImg.rows, oProImg.channels());
    int   nSize   = oProImg.cols * oProImg.rows * oProImg.channels();
    cv::cvtColor(oProImg, oProImg, CV_BGR2RGB);

    MatIntoImage(oProImg, stImage);
    layer stlayer = m_pstNet.layers[m_pstNet.n - 1];
    float *pDatas   = stImage.data;
    float **pfProbs = reinterpret_cast<float**>(m_pfProbs);
    network_predict(m_pstNet, pDatas);
	int letter = 0;
    int nboxes = 0;
    //printf("%d\n", nboxes);
    detection *dets = get_network_boxes(&m_pstNet, oSrcImage.cols, oSrcImage.rows, m_fthresh, 0.5, 0, 1, &nboxes, letter);
    

    do_nms_sort(dets, nboxes, stlayer.classes, m_fnms);
    //printf("%d\n", nboxes);
    nNum = FilterDetectBBoxs(m_stDetectBBox, oSrcImage.cols, oSrcImage.rows, nboxes, m_fthresh, dets, stlayer.classes);
    //printf("%d\n", nNum);
    //box *pstBox = reinterpret_cast<box*>(m_pstBoxes);
    //get_region_boxes(stlayer, oSrcImage.cols, oSrcImage.rows, m_pstNet->w, m_pstNet->h, m_fthresh, pfProbs, pstBox, 0, 0, 0, m_fhier_thresh, 1);

    //do_nms_obj(pstBox, pfProbs, stlayer.w * stlayer.h * stlayer.n, stlayer.classes, m_fnms);

    //nNum = FilterDetectBBoxs(m_stDetectBBox, oSrcImage.cols, oSrcImage.rows, stlayer.w * stlayer.h * stlayer.n, m_fthresh, pstBox, pfProbs, stlayer.classes);
    free_image(stImage);
    pstResult = m_stDetectBBox;

    return 1;
}

void CYOLOV2Det::Release()
{
    free(m_pstBoxes);
    layer stlayer = m_pstNet.layers[m_pstNet.n - 1];
#ifdef NNPACK
    pthreadpool_destroy(m_pstNet->threadpool);
    nnp_deinitialize();
#endif

    free_ptrs(reinterpret_cast<void**>(m_pfProbs), stlayer.w * stlayer.h * stlayer.n);
}


CYOLOV2Det::CYOLOV2Det()
{}

CYOLOV2Det::~CYOLOV2Det()
{
    m_pszNames = NULL;
}

float CYOLOV2Det::IOU(tagDetBBox &box1, tagDetBBox &box2)
{
#if defined(LINUX) && !defined(UI_PROCESS)
    box stPredict;

    stPredict.x = static_cast<float>(box1.m_nLeft);
    stPredict.y = static_cast<float>(box1.m_nTop);
    stPredict.w = static_cast<float>(box1.m_nWidth);
    stPredict.h = static_cast<float>(box1.m_nHeight);

    box stTrue;
    stTrue.x = static_cast<float>(box2.m_nLeft);
    stTrue.y = static_cast<float>(box2.m_nTop);
    stTrue.w = static_cast<float>(box2.m_nWidth);
    stTrue.h = static_cast<float>(box2.m_nHeight);
    return box_iou(stPredict, stTrue);
#else
    return 0.0f;
#endif
}

void CYOLOV2Det::RestDetRet()
{
    for (int i = 0; i < MAX_OBJECT_SIZE; i++)
    {
        m_stDetectBBox[i] = tagDetBBox();
    }
}
