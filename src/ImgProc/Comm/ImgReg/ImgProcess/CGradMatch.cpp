/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/ImgProcess/CGradMatch.h"

// **************************************************************************************
//          CGradMatch Factory Class Define
// **************************************************************************************

CGradMatchFactory::CGradMatchFactory()
{}

CGradMatchFactory::~CGradMatchFactory()
{}

IImgProc* CGradMatchFactory::CreateImgProc()
{
    return new CGradMatch();
}

// **************************************************************************************
//          CGradMatch Class Define
// **************************************************************************************

static const unsigned char SIMILARITY[256] = { 0, 4, 3, 4, 2, 4, 3, 4, 1, 4, 3, 4, 2, 4, 3, 4, \
                                               0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, \
                                               0, 3, 4, 4, 3, 3, 4, 4, 2, 3, 4, 4, 3, 3, 4, 4, \
                                               0, 1, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, \
                                               0, 2, 3, 3, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, \
                                               0, 2, 1, 2, 0, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, \
                                               0, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, \
                                               0, 3, 2, 3, 1, 3, 2, 3, 0, 3, 2, 3, 1, 3, 2, 3, \
                                               0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, \
                                               0, 4, 3, 4, 2, 4, 3, 4, 1, 4, 3, 4, 2, 4, 3, 4, \
                                               0, 1, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, \
                                               0, 3, 4, 4, 3, 3, 4, 4, 2, 3, 4, 4, 3, 3, 4, 4, \
                                               0, 2, 1, 2, 0, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, \
                                               0, 2, 3, 3, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, \
                                               0, 3, 2, 3, 1, 3, 2, 3, 0, 3, 2, 3, 1, 3, 2, 3, \
                                               0, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4 };

CGradMatch::CGradMatch()
{
    m_nFeatureNum = 16;
    m_oVecTmpls.clear();
    m_oVecGradTmpls.clear();
}

CGradMatch::~CGradMatch()
{}

int CGradMatch::Initialize(IImgProcParam *pParam)
{
    // check parameter pointer
    if (NULL == pParam)
    {
        LOGE("CGradMatch -- IImgProcParam pointer is NULL, please check");
        return -1;
    }

    // conver parameter pointer
    CGradMatchParam *pP = dynamic_cast<CGradMatchParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CGradMatch -- CGradMatchParam pointer is NULL, please check");
        return -1;
    }

    // parse parameters
    int nState = ParseParam(pP);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- parse parameters failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CGradMatch::Predict(IImgProcData *pData, IImgProcResult *pResult)
{
    int nState = 0;

    // convert pointer
    nState = CheckPointer(pData, pResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- check pointer failed, please check", m_nTaskID);
        return nState;
    }

    // convert data pointer
    CObjDetData *pD = dynamic_cast<CObjDetData*>(pData);
    if (NULL == pD)
    {
        LOGE("task ID %d: CGradMatch -- CObjDetData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // convert result pointer
    CObjDetResult *pR = dynamic_cast<CObjDetResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CGradMatch -- CObjDetResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // clear result
    pR->m_oVecBBoxes.clear();

    // set ROI
    cv::Rect oROI;
    nState = SetROI(pD, &oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- set ROI failed, please check", m_nTaskID);
        return nState;
    }

    // detect in ROI
    std::vector<tagBBox> oVecBBoxes;
    nState = Detect(pD->m_oSrcImg(m_oROI), m_oVecGradTmpls, oVecBBoxes);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- match template failed, please check", m_nTaskID);
        return nState;
    }

    // set result
    nState = SetResult(oROI, oVecBBoxes, pR);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- set result failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CGradMatch::Release()
{
    m_oVecTmpls.clear();
    m_oVecGradTmpls.clear();

    return 1;
}

// Compute gradient magnitude and gradient angle for color image
void CGradMatch::ColorGradient(const cv::Mat &oImg, cv::Mat &oMagnitude, cv::Mat &oAngle)
{
    int nRows = oImg.rows;
    int nCols = oImg.cols;

    cv::Mat oRedMagnitude(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oGreenMagnitude(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oBlueMagnitude(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oRedAngle(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oGreenAngle(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oBlueAngle(nRows, nCols, cv::DataType<float>::type);

    // Compute gradient magnitude and gradient angle for each channel
    std::vector<cv::Mat> oVecChannels; // BRG
    cv::split(oImg, oVecChannels);

    GrayGradient(oVecChannels[0], oBlueMagnitude, oBlueAngle);
    GrayGradient(oVecChannels[1], oGreenMagnitude, oGreenAngle);
    GrayGradient(oVecChannels[2], oRedMagnitude, oRedAngle);

    // Find max gradient magnitude in three channels
    for (int r = 0; r < nRows; r++)
    {
        const float *pRedMagnitude   = oRedMagnitude.ptr<float>(r);
        const float *pGreenMagnitude = oGreenMagnitude.ptr<float>(r);
        const float *pBlueMagnitude  = oBlueMagnitude.ptr<float>(r);

        const float *pRedAngle   = oRedAngle.ptr<float>(r);
        const float *pGreenAngle = oGreenAngle.ptr<float>(r);
        const float *pBlueAngle  = oBlueAngle.ptr<float>(r);

        float *pMagnitude = oMagnitude.ptr<float>(r);
        float *pAngle     = oAngle.ptr<float>(r);

        for (int c = 0; c < nCols; c++)
        {
            float fMaxMagnitude = 0.0;
            float fMaxAngle     = 0.0;

            if (pRedMagnitude[c] > pGreenMagnitude[c])
            {
                fMaxMagnitude = pRedMagnitude[c];
                fMaxAngle     = pRedAngle[c];
            }
            else
            {
                fMaxMagnitude = pGreenMagnitude[c];
                fMaxAngle     = pGreenAngle[c];
            }

            if (pBlueMagnitude[c] > fMaxMagnitude)
            {
                fMaxMagnitude = pBlueMagnitude[c];
                fMaxAngle     = pBlueAngle[c];
            }

            pMagnitude[c] = fMaxMagnitude;
            pAngle[c]     = fMaxAngle;
        }
    }
}

// Compute gradient magnitude and gradient angle for gray image
void CGradMatch::GrayGradient(const cv::Mat &oImg, cv::Mat &oMagnitude, cv::Mat &oAngle)
{
    int nRows = oImg.rows;
    int nCols = oImg.cols;

    cv::Mat oDx(nRows, nCols, cv::DataType<int16_t>::type);
    cv::Mat oDy(nRows, nCols, cv::DataType<int16_t>::type);
    cv::Sobel(oImg, oDx, CV_16S, 1, 0, 3, 1, 0, cv::BORDER_REPLICATE);
    cv::Sobel(oImg, oDy, CV_16S, 0, 1, 3, 1, 0, cv::BORDER_REPLICATE);

    ComputeMagnitude(oDx, oDy, oMagnitude);
    ComputeAngle(oDx, oDy, oAngle);
}

void CGradMatch::ComputeMagnitude(const cv::Mat &oDx, const cv::Mat &oDy, cv::Mat &oMagnitude)
{
    int nRows = oMagnitude.rows;
    int nCols = oMagnitude.cols;

    for (int r = 0; r < nRows; r++)
    {
        const int16_t *pDx = oDx.ptr<int16_t>(r);
        const int16_t *pDy = oDy.ptr<int16_t>(r);

        float *pMagnitude = oMagnitude.ptr<float>(r);

        for (int c = 0; c < nCols; c++)
        {
            pMagnitude[c] = sqrt(static_cast<float>(pDx[c] * pDx[c] + pDy[c] * pDy[c]));
        }
    }
}

void CGradMatch::ComputeAngle(const cv::Mat &oDx, const cv::Mat &oDy, cv::Mat &oAngle)
{
    int nRows = oAngle.rows;
    int nCols = oAngle.cols;

    for (int r = 0; r < nRows; r++)
    {
        const int16_t *pDx = oDx.ptr<int16_t>(r);
        const int16_t *pDy = oDy.ptr<int16_t>(r);

        float *pAngle = oAngle.ptr<float>(r);

        for (int c = 0; c < nCols; c++)
        {
            if (0 == pDx[c] && 0 == pDy[c])
            {
                pAngle[c] = 0;
            }
            else
            {
                pAngle[c] = static_cast<float>(atan2(static_cast<float>(pDy[c]),
                    static_cast<float>(pDx[c])) * 180 / CV_PI + 180);
            }
        }
    }
}

void CGradMatch::QuantAngle(const cv::Mat &oMagnitude, cv::Mat &oAngle, cv::Mat &oOrientation, int nWeakThreshold)
{
    int nRows = oOrientation.rows;
    int nCols = oOrientation.cols;

    cv::Mat oQuaOri(nRows, nCols, cv::DataType<uchar>::type);

    // Convert 0~360 angle into 0~15 orientation
    for (int r = 0; r < nRows; r++)
    {
        const float *pAngle  = oAngle.ptr<float>(r);
        uchar       *pQuaOri = oQuaOri.ptr<uchar>(r);

        for (int c = 0; c < nCols; c++)
        {
            pQuaOri[c] = (uchar)round(pAngle[c] * 16.0 / 360.0);
        }
    }

    // Zero out first and last rows
    uchar *pQuaOri_fr = oQuaOri.ptr<uchar>(0); // First row
    uchar *pQuaOri_lr = oQuaOri.ptr<uchar>(nRows - 1); // Last row

    for (int c = 0; c < nCols; c++)
    {
        pQuaOri_fr[c] = 0;
        pQuaOri_lr[c] = 0;
    }

    // Zero out first and last columns
    for (int r = 0; r < nRows; r++)
    {
        uchar *pQuaOri = oQuaOri.ptr<uchar>(r);
        pQuaOri[0]         = 0; // First column
        pQuaOri[nCols - 1] = 0; // Last column
    }

    // Mask 16 buckets into 8 quantized orientations
    // Diagonal buckets as the same orientation
    for (int r = 1; r < nRows - 1; r++)
    {
        uchar *pQuaOri = oQuaOri.ptr<uchar>(r);

        for (int c = 1; c < nCols - 1; c++)
        {
            pQuaOri[c] &= 7;
        }
    }

    oOrientation = cv::Mat::zeros(nRows, nCols, cv::DataType<uchar>::type);

    // Find significant orientation in 3x3 patch
    for (int r = 1; r < nRows - 1; r++)
    {
        const float *pMagnitude   = oMagnitude.ptr<float>(r);
        uchar       *pOrientation = oOrientation.ptr<uchar>(r);

        for (int c = 1; c < nCols - 1; c++)
        {
            if (pMagnitude[c] > nWeakThreshold)
            {
                int   nHist[8] = { 0, 0, 0, 0, 0, 0, 0, 0 }; // Orientation histogram
                uchar *pPatch3x3;

                pPatch3x3 = oQuaOri.ptr<uchar>(r - 1);
                nHist[pPatch3x3[c - 1]]++;
                nHist[pPatch3x3[c]]++;
                nHist[pPatch3x3[c + 1]]++;

                pPatch3x3 = oQuaOri.ptr<uchar>(r);
                nHist[pPatch3x3[c - 1]]++;
                nHist[pPatch3x3[c]]++;
                nHist[pPatch3x3[c + 1]]++;

                pPatch3x3 = oQuaOri.ptr<uchar>(r + 1);
                nHist[pPatch3x3[c - 1]]++;
                nHist[pPatch3x3[c]]++;
                nHist[pPatch3x3[c + 1]]++;

                // Find orientation with the most votes in 3x3 patch
                int nIdx     = -1;
                int nMaxVote = 0;

                for (int i = 0; i < 8; i++)
                {
                    if (nMaxVote < nHist[i])
                    {
                        nIdx     = i;
                        nMaxVote = nHist[i];
                    }
                }

                // Use one bit to represent one orientation
                if (nMaxVote >= NEIGHBOR_THRESHOLD)
                {
                    pOrientation[c] = 1 << nIdx;
                }
            }
        }
    }
}

void CGradMatch::SpreadOrientation(const cv::Mat &oOrientation, cv::Mat &oBinaryMat, int nT)
{
    int nRows = oOrientation.rows;
    int nCols = oOrientation.cols;

    // Zero-initialize binary mat
    oBinaryMat = cv::Mat::zeros(nRows, nCols, cv::DataType<uchar>::type);

    // Fill in spread gradient image
    uchar *pBinaryMat = oBinaryMat.data;

    for (int r = 0; r < nT; r++)
    {
        int nRowIdx = nRows - r;

        for (int c = 0; c < nT; c++)
        {
            // orientation(r, c)
            const uchar *pOrientation = oOrientation.data + r * oOrientation.step + c * oOrientation.elemSize();
            _OrUnaligned8u(pOrientation, static_cast<int>(oOrientation.step), pBinaryMat,
                           static_cast<int>(oBinaryMat.step), nCols - c, nRowIdx);
        }
    }
}

void CGradMatch::ComputeResponseMap(const cv::Mat &oBinaryMat, std::vector<cv::Mat> &oVecResponseMap)
{
    int nRows = oBinaryMat.rows;
    int nCols = oBinaryMat.cols;

    // Low significant 4 bits
    cv::Mat oLS4b(nRows, nCols, cv::DataType<uchar>::type);
    // High significant 4 bits
    cv::Mat oHS4b(nRows, nCols, cv::DataType<uchar>::type);

    for (int r = 0; r < nRows; r++)
    {
        const uchar *pBinaryMat = oBinaryMat.ptr<uchar>(r);

        uchar *pLS4b = oLS4b.ptr<uchar>(r);
        uchar *pHS4b = oHS4b.ptr<uchar>(r);

        for (int c = 0; c < nCols; c++)
        {
            // Get Low significant 4 bits of binary mat
            pLS4b[c] = pBinaryMat[c] & 15;
            // Get High significant 4 bits of binary mat
            // Right-shifted to be in [0, 16)
            pHS4b[c] = (pBinaryMat[c] & 240) >> 4;
        }
    }

    // Compute similarty for each orientation
    for (int nOriIdx = 0; nOriIdx < 8; nOriIdx++)
    {
        uchar *pResponseMap = oVecResponseMap[nOriIdx].ptr<uchar>(0);
        uchar *pLS4b        = oLS4b.ptr<uchar>(0);
        uchar *pHS4b        = oHS4b.ptr<uchar>(0);

        const uchar *pLow  = SIMILARITY + 32 * nOriIdx;
        const uchar *pHigh = pLow + 16;

        for (int i = 0; i < nRows * nCols; i++)
        {
            pResponseMap[i] = MAX(pLow[pLS4b[i]], pHigh[pHS4b[i]]);
        }
    }
}

void CGradMatch::Linearize(const cv::Mat &oResponseMap, cv::Mat &oLinearizedMap, int nT)
{
    int nRows = oResponseMap.rows;
    int nCols = oResponseMap.cols;

    int nIdx = 0;

    // Outer two for loops iterate over top-left T^2 starting pixels
    for (int r_start = 0; r_start < nT; r_start++)
    {
        for (int c_start = 0; c_start < nT; c_start++)
        {
            uchar *pLinearizedMap = oLinearizedMap.ptr<uchar>(nIdx);
            nIdx++;

            // Inner two loops copy every T-th pixel into the linear memory
            for (int r = r_start; r < (nRows - (nRows % nT)); r += nT)
            {
                const uchar *pResponseMap = oResponseMap.ptr<uchar>(r);

                for (int c = c_start; c < (nCols - (nCols % nT)); c += nT)
                {
                    *pLinearizedMap++ = pResponseMap[c];
                }
            }
        }
    }
}

void CGradMatch::SelectScatteredFeature(const std::vector<tagGradCandidate> &oVecCandidate,
    std::vector<tagGradFeature> &oVecGradFeature, int nFeatureNum, float fDist)
{
    oVecGradFeature.clear();

    float fDistSQR = MY_SQR(fDist);

    int i = 0; // Candidate index

    while (static_cast<int>(oVecGradFeature.size()) < nFeatureNum)
    {
        tagGradCandidate stCandidate = oVecCandidate[i];

        // Add if sufficient distance away from any previous chosen feature
        bool bKeep = true;

        for (int j = 0; (j < static_cast<int>(oVecGradFeature.size())) && bKeep; j++)
        {
            tagGradFeature stGradFeature = oVecGradFeature[j];
            bKeep = (MY_SQR(stCandidate.stGradFeature.nY - stGradFeature.nY) +
                     MY_SQR(stCandidate.stGradFeature.nX - stGradFeature.nX)) >= fDistSQR;
        }

        if (bKeep)
        {
            oVecGradFeature.push_back(stCandidate.stGradFeature);
        }

        if (++i == static_cast<int>(oVecCandidate.size()))
        {
            // Start back at beginning and relax required distance
            i        = 0;
            fDist   -= 1.0f;
            fDistSQR = MY_SQR(fDist);
        }
    }
}

void CGradMatch::ComputeSimilarity(const std::vector<cv::Mat> &oVecLinearizedMap,
    const tagGradTemplate &stGradTemplate, cv::Mat &oSimilarity, int nRows, int nCols, int nT)
{
    // Decimate input image size by factor of T
    int nW = nCols / nT;
    int nH = nRows / nT;

    // Feature dimensions, decimated by factor T and rounded up
    int nFeatureW = (stGradTemplate.nWidth - 1) / nT + 1;
    int nFeatureH = (stGradTemplate.nHeight - 1) / nT + 1;

    // Span is the range over which we can shift the template around the input image
    int nSpanX = nW - nFeatureW;
    int nSpanY = nH - nFeatureH;

    // Compute number of contiguous (in memory) pixels to check when sliding feature over image
    // This allows template to wrap around left/right border incorrectly, so any wrapped template matches
    // must be filtered out!
    int nTemplatePosition = (nSpanY - 1) * nW + nSpanX;

    int16_t *pSimilarity = oSimilarity.ptr<int16_t>(0);

    // Compute the similarity measure for this template by accumulating the contribution of each feature
    for (int i = 0; i < static_cast<int>(stGradTemplate.oVecGradFeature.size()); i++)
    {
        // Add the linear memory at the appropriate offset computed from the location of the feature in the template
        tagGradFeature stGradFeature = stGradTemplate.oVecGradFeature[i];

        if (stGradFeature.nX < 0 || stGradFeature.nX >= nCols || stGradFeature.nY < 0 || stGradFeature.nY >= nRows)
            continue;

        const uchar *pLinearizedMap = _AccessLinearMemory(oVecLinearizedMap, stGradFeature, nT, nW);

        // Do an aligned/unaligned add of pLinearizedMap and pSimilarity with nTemplatePosition elements

        // Process responses 16 at a time if vectorization possible
        // for (int j = 0 ; j < template_positions - 15; j += 16)
        // {
        //      __m128i responses = _mm_loadu_si128(reinterpret_cast<const __m128i*>(pLinearizedMap + j));
        //      __m128i* dst_ptr_sse = reinterpret_cast<__m128i*>(pSimilarity + j);
        //      *dst_ptr_sse = _mm_add_epi8(*dst_ptr_sse, responses);
        // }

        for (int j = 0; j < nTemplatePosition; j++)
            pSimilarity[j] += pLinearizedMap[j];
    }
}

// void CGradMatch::ShowTemplate(const tagGradTemplate &stGradTemplate)
// {
//     int nRows = stGradTemplate.nHeight;
//     int nCols = stGradTemplate.nWidth;
//
//     cv::Mat oDisplayImg = cv::Mat::zeros(nRows, nCols, cv::DataType<uchar>::type);
//
//     int nFeatureNum = static_cast<int>(stGradTemplate.oVecGradFeature.size());
//
//     for (int i = 0; i < nFeatureNum; i++)
//     {
//         int r = stGradTemplate.oVecGradFeature[i].nY;
//         int c = stGradTemplate.oVecGradFeature[i].nX;
//         oDisplayImg.ptr<uchar>(r)[c] = 255;
//     }
//
//     imshow("Gradient Template", oDisplayImg);
//     cvWaitKey(0);
// }

int CGradMatch::GetResponseMap(const cv::Mat &oImg, std::vector<cv::Mat> &oVecResponseMap, int nT)
{
    int nRows = oImg.rows;
    int nCols = oImg.cols;

    cv::Mat oMagnitude(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oAngle(nRows, nCols, cv::DataType<float>::type);
    cv::Mat oOrientation(nRows, nCols, cv::DataType<uchar>::type);
    cv::Mat oBinaryMat(nRows, nCols, cv::DataType<uchar>::type);

    // Compute gradient magnitude and gradient angle
    if (3 == oImg.channels())
    {
        ColorGradient(oImg, oMagnitude, oAngle);
    }
    else if (1 == oImg.channels())
    {
        GrayGradient(oImg, oMagnitude, oAngle);
    }
    else
    {
        LOGE("task ID %d: CGradMatch -- source image channel is invalid, please check", m_nTaskID);
        return -1;
    }

    // Quantize gradient angle according to gradient magnitude
    QuantAngle(oMagnitude, oAngle, oOrientation);

    // Convert into binary mat and spread orientation by TxT
    SpreadOrientation(oOrientation, oBinaryMat, nT);

    // Compute response map
    ComputeResponseMap(oBinaryMat, oVecResponseMap);

    return 1;
}

int CGradMatch::MatchTemplate(const std::vector<cv::Mat> &oVecLinearizedMap,
    const std::vector<tagGradTemplate> &oVecGradTempalte, std::vector<tagBBox> &oVecDetectBBox,
    int nRows, int nCols, int nT)
{
    // Compute match similarity with each template
    for (int i = 0; i < static_cast<int>(oVecGradTempalte.size()); i++)
    {
        tagGradTemplate stGradTemplate = oVecGradTempalte.at(i);
        cv::Mat         oSimilarity    = cv::Mat::zeros(nRows / nT, nCols / nT, cv::DataType<int16_t>::type);

        ComputeSimilarity(oVecLinearizedMap, stGradTemplate, oSimilarity, nRows, nCols, nT);

        // Select match result
        int nRawThreshold = static_cast<int>(2 *
            static_cast<int>(stGradTemplate.oVecGradFeature.size()) +
            (25.f / 100.f) * (2 * static_cast<int>(stGradTemplate.oVecGradFeature.size())) + 0.5f);

        for (int r = 0; r < oSimilarity.rows; r++)
        {
            int16_t *pSimilarity = oSimilarity.ptr<int16_t>(r);

            for (int c = 0; c < oSimilarity.cols; c++)
            {
                int nRawSimilarity = pSimilarity[c];

                if (nRawSimilarity > nRawThreshold)
                {
                    int   nOffset     = nT / 2 + (nT % 2 - 1);
                    int   nX          = c * nT + nOffset;
                    int   nY          = r * nT + nOffset;
                    float nSimilarity = (nRawSimilarity * 100.f) /
                        (4 * static_cast<int>(stGradTemplate.oVecGradFeature.size())) + 0.5f;

                    // Output BBox
                    if (nSimilarity / 100.f >= stGradTemplate.fThreshold)
                    {
                        if (nX + stGradTemplate.nWidth <= nCols && nY + stGradTemplate.nHeight <= nRows)
                        {
                            tagBBox stDetectBBox;
                            stDetectBBox.nClassID = stGradTemplate.nClassID;
                            stDetectBBox.fScore   = nSimilarity / 100.f;
                            stDetectBBox.fScale   = stGradTemplate.fScale;
                            snprintf(stDetectBBox.szTmplName, sizeof(stDetectBBox.szTmplName), "%s",
                                stGradTemplate.strTmplName.c_str());
                            stDetectBBox.oRect = cv::Rect(nX, nY, stGradTemplate.nWidth, stGradTemplate.nHeight);
                            oVecDetectBBox.push_back(stDetectBBox);
                        }
                    }
                }
            }
        }
    }

    return 1;
}

int CGradMatch::ParseParam(const CGradMatchParam *pParam)
{
    int nState = 0;

    // check task ID
    if (pParam->m_nTaskID < 0)
    {
        LOGE("CGradMatch -- task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    // set task ID
    m_nTaskID = pParam->m_nTaskID;

    // set ROI
    m_oROI = pParam->m_oROI;

    // compute scales for multi-scale matching
    std::vector<float> oVecScales;
    nState = ComputeScale(m_nTaskID, pParam->m_fMinScale, pParam->m_fMaxScale, pParam->m_nScaleLevel, &oVecScales);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- compute scale failed, please check", m_nTaskID);
        return nState;
    }

    int nLoc = static_cast<int>(pParam->m_strOpt.find("-featureNum"));
    if (-1 != nLoc)
    {
        std::string strFeatureNum;
        strFeatureNum = pParam->m_strOpt.substr(11, pParam->m_strOpt.length() - 11);
        m_nFeatureNum = std::stoi(strFeatureNum);
    }
    else
    {
        m_nFeatureNum = 16;
    }

    // load matching templates
    nState = LoadTemplate(m_nTaskID, pParam->m_oVecTmpls, oVecScales, m_oVecTmpls);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- load template failed, please check", m_nTaskID);
        return nState;
    }

    nState = MakeTemplate(m_oVecTmpls, m_oVecGradTmpls, m_nFeatureNum);
    if (1 != nState)
    {
        LOGE("task ID %d: CGradMatch -- make gradient template failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CGradMatch::MakeTemplate(const std::vector<tagTmpl> &oVecTmpls, std::vector<tagGradTemplate> &oVecGradTmpls,
    int nFeatureNum)
{
    for (int i = 0; i < static_cast<int>(oVecTmpls.size()); i++)
    {
        tagTmpl stTmpl = oVecTmpls.at(i);

        int nRows = stTmpl.oTmplImg.rows;
        int nCols = stTmpl.oTmplImg.cols;

        cv::Mat oMagnitude(nRows, nCols, cv::DataType<float>::type);
        cv::Mat oAngle(nRows, nCols, cv::DataType<float>::type);
        cv::Mat oOrientation(nRows, nCols, cv::DataType<uchar>::type);

        // Compute gradient magnitude and gradient angle
        if (3 == stTmpl.oTmplImg.channels())
        {
            ColorGradient(stTmpl.oTmplImg, oMagnitude, oAngle);
        }
        else if (1 == stTmpl.oTmplImg.channels())
        {
            GrayGradient(stTmpl.oTmplImg, oMagnitude, oAngle);
        }
        else
        {
            LOGE("task ID %d: CGradMatch -- template channel is invalid, please check", m_nTaskID);
            return -1;
        }

        QuantAngle(oMagnitude, oAngle, oOrientation, WEAK_THRESHOLD / 10);

        tagGradTemplate stGradTmpl;
        stGradTmpl.nClassID   = stTmpl.nClassID;
        stGradTmpl.fThreshold = stTmpl.fThreshold;
        stGradTmpl.fScale     = (static_cast<float>(stTmpl.oTmplImg.rows) /
            static_cast<float>(stTmpl.oRect.height) + static_cast<float>(stTmpl.oTmplImg.cols) /
            static_cast<float>(stTmpl.oRect.width)) / 2.0f;
        stGradTmpl.strTmplName = stTmpl.strTmplName;
        stGradTmpl.strTmplPath = stTmpl.strTmplPath;

        int nState = ExtractFeature(oMagnitude, oOrientation, stGradTmpl, nFeatureNum);
        if (1 != nState)
        {
            LOGE("task ID %d: CGradMatch -- extract feature failed, please check", m_nTaskID);
            return nState;
        }

        // ShowTemplate(stGradTmpl);

        oVecGradTmpls.push_back(stGradTmpl);
    }

    return 1;
}

int CGradMatch::ExtractFeature(const cv::Mat &oMagnitude, const cv::Mat &oOrientation,
    tagGradTemplate &stGradTemplate, int nFeatureNum, int nStrongThreshold)
{
    int nRows = oMagnitude.rows;
    int nCols = oMagnitude.cols;

    std::vector<tagGradCandidate> oVecCandidate;

    // Select obvious gradient candidate points
    for (int r = 0; r < nRows; r++)
    {
        const float *pMagnitude   = oMagnitude.ptr<float>(r);
        const uchar *pOrientation = oOrientation.ptr<uchar>(r);

        for (int c = 0; c < nCols; c++)
        {
            if (pMagnitude[c] > nStrongThreshold && pOrientation[c] > 0)
            {
                tagGradCandidate stCandidate(c, r, _GetLabel(pOrientation[c]), pMagnitude[c]);
                oVecCandidate.push_back(stCandidate);
            }
        }
    }

    if (static_cast<int>(oVecCandidate.size()) < nFeatureNum)
    {
        LOGE("task ID %d: CGradMatch -- not enough gradient feature, please check", m_nTaskID);
        return -1;
    }

    sort(oVecCandidate.begin(), oVecCandidate.end(), _LessScore);

    stGradTemplate.nHeight = nRows;
    stGradTemplate.nWidth  = nCols;

    if (nFeatureNum <= 0)
    {
        LOGE("task ID %d: CGradMatch -- feature number %d is invalid, please check", m_nTaskID, nFeatureNum);
        return -1;
    }

    // Use heuristic based on surplus of candidates in narrow outline for initial distance threshold
    float fDist = static_cast<float>(static_cast<int>(oVecCandidate.size()) / nFeatureNum + 1);

    SelectScatteredFeature(oVecCandidate, stGradTemplate.oVecGradFeature, nFeatureNum, fDist);

    return 1;
}

int CGradMatch::Detect(const cv::Mat &oSrcImg, const std::vector<tagGradTemplate> &oVecGradTmpls,
    std::vector<tagBBox> &oVecBBoxes)
{
    oVecBBoxes.clear();

    if (oVecGradTmpls.empty())
    {
        LOGE("task ID %d: CGradMatch -- gradient template vector is empty, please check", m_nTaskID);
        return -1;
    }

    int nT    = EXPAND_SIZE;
    int nRows = oSrcImg.rows;
    int nCols = oSrcImg.cols;

    // Initialize 8 response maps
    std::vector<cv::Mat> oVecResponseMap;

    for (int i = 0; i < 8; i++)
    {
        cv::Mat oResponseMap = cv::Mat::zeros(nRows, nCols, cv::DataType<uchar>::type);
        oVecResponseMap.push_back(oResponseMap);
    }

    // Compute the response map for each orientation
    GetResponseMap(oSrcImg, oVecResponseMap, nT);

    // Initialize 8 linearized map
    std::vector<cv::Mat> oVecLinearizedMap;

    for (int i = 0; i < 8; i++)
    {
        cv::Mat oLinearizedMap = cv::Mat::zeros(nT * nT, (nRows - nRows % nT) * (nCols - nCols % nT) /
            (nT * nT), cv::DataType<uchar>::type);
        oVecLinearizedMap.push_back(oLinearizedMap);
    }

    // Linearize response map
    for (int i = 0; i < 8; i++)
    {
        Linearize(oVecResponseMap[i], oVecLinearizedMap[i], nT);
    }

    MatchTemplate(oVecLinearizedMap, oVecGradTmpls, oVecBBoxes, nRows, nCols, nT);

    return 1;
}

// void CGradMatch::ShowDetectionResult(char *pszWindowName, const cv::Mat &oImg,
//     const std::vector<tagBBox> &oVecDetectBBox)
// {
//     cv::Mat oDisplayImg = oImg;
//
//     for (int i = 0; i < (int)oVecDetectBBox.size(); i++)
//     {
//         tagBBox stDetectBBox = oVecDetectBBox.at(i);
//
//         cv::Point oP1(stDetectBBox.m_nLeft, stDetectBBox.m_nTop);
//         cv::Point oP2(stDetectBBox.m_nLeft + stDetectBBox.m_nWidth,
//             stDetectBBox.m_nTop + stDetectBBox.m_nHeight);
//         cv::rectangle(oDisplayImg, oP1, oP2, cv::Scalar(255, 0, 255));
//     }
//
//     cv::imshow(pszWindowName, oDisplayImg);
//     cvWaitKey(1);
// }

void _OrUnaligned8u(const uchar *src, int src_stride, uchar *dst, int dst_stride, int cols, int rows)
{
    for (int r = 0; r < rows; r++)
    {
        int c = 0;
        if (src_stride % 16 == 0)
        {
            for (; c < cols - 15; c += 16)
            {
                __m128i val      = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + c));
                __m128i *dst_ptr = reinterpret_cast<__m128i*>(dst + c);
                *dst_ptr = _mm_or_si128(*dst_ptr, val);
            }

            for (; c < cols; c++)
                dst[c] |= src[c];
        }
        else
        {
            for (; c < cols; c++)
                dst[c] |= src[c];
        }

        // Advance to next row
        src += src_stride;
        dst += dst_stride;
    }
}

bool _LessConfidence(const tagBBox &stBBox1, const tagBBox &stBBox2)
{
    return stBBox1.fScore > stBBox2.fScore;
}

bool _LessScore(const tagGradCandidate &stCandidate1, const tagGradCandidate &stCandidate2)
{
    return stCandidate1.fScore > stCandidate2.fScore;
}

static inline int _GetLabel(int nQuant)
{
    switch (nQuant)
    {
    case 1:   return 0;

    case 2:   return 1;

    case 4:   return 2;

    case 8:   return 3;

    case 16:  return 4;

    case 32:  return 5;

    case 64:  return 6;

    case 128: return 7;

    default:
        LOGE("CGradMatch -- invalid value of quantized parameter, please check");
        return -1;
    }
}

const unsigned char* _AccessLinearMemory(const std::vector<cv::Mat> &oVecLinearizedMap,
    const tagGradFeature &stGradFeature, int nT, int nW)
{
    // Retrieve the TxT grid of linear memories associated with the feature label
    const cv::Mat oMemoryGrid = oVecLinearizedMap[stGradFeature.nLabel];

    if (nT * nT != oMemoryGrid.rows)
        return NULL;

    if (stGradFeature.nX < 0)
        return NULL;

    if (stGradFeature.nY < 0)
        return NULL;

    // The linear memory we want is at (nX%nT, nY%nT) in the TxT grid (stored as the rows of oMemoryGrid)
    int nGridX   = stGradFeature.nX % nT;
    int nGridY   = stGradFeature.nY % nT;
    int nGridIdx = nGridY * nT + nGridX;

    if (nGridIdx < 0)
        return NULL;

    if (nGridIdx >= oMemoryGrid.rows)
        return NULL;

    const uchar *pMemoryGrid = oMemoryGrid.ptr<uchar>(nGridIdx);

    // The feature is at (nX/nT, nY/nT) in the linear memory.
    // W is the "width" of the linear memory, the input image width decimated by T.
    int nLinearMemoryX = stGradFeature.nX / nT;
    int nLinearMemoryY = stGradFeature.nY / nT;

    int nOffset = nLinearMemoryY * nW + nLinearMemoryX;

    if (nOffset < 0)
        return NULL;

    if (nOffset >= oMemoryGrid.cols)
        return NULL;

    return pMemoryGrid + nOffset;
}
