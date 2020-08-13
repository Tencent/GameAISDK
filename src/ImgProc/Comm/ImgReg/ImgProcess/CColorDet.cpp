/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/ImgProcess/CColorDet.h"

// **************************************************************************************
//          CColorDetFactory Class Define
// **************************************************************************************

CColorDetFactory::CColorDetFactory()
{}

CColorDetFactory::~CColorDetFactory()
{}

IImgProc* CColorDetFactory::CreateImgProc()
{
    return new CColorDet();
}

// **************************************************************************************
//          CColorDet Class Define
// **************************************************************************************

CColorDet::CColorDet()
{
    m_nFilterSize  = 1; // filter size of erode and dilate operation
    m_nMaxPointNum = 512; // the number of max points
    m_nRedLower    = 0; // lower red value
    m_nRedUpper    = 255; // upper red value
    m_nGreenLower  = 0; // lower green value
    m_nGreenUpper  = 255; // upper green value
    m_nBlueLower   = 0; // lower blue value
    m_nBlueUpper   = 255; // upper blue value
}

CColorDet::~CColorDet()
{}

int CColorDet::Initialize(IImgProcParam *pParam)
{
    // check parameter pointer
    if (NULL == pParam)
    {
        LOGE("CColorDet -- IImgProcParam pointer is NULL, please check");
        return -1;
    }

    // conver parameter pointer
    CColorDetParam *pP = dynamic_cast<CColorDetParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CColorDet -- CColorDetParam pointer is NULL, please check");
        return -1;
    }

    // parse parameters
    int nState = ParseParam(pP);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorDet -- parse parameters failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CColorDet::Predict(IImgProcData *pData, IImgProcResult *pResult)
{
    if (NULL == pData)
    {
        LOGE("task ID %d: CColorDet -- IImgProcData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: CColorDet -- IImgProcResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CPixDetData *pD = dynamic_cast<CPixDetData*>(pData);
    if (NULL == pD)
    {
        LOGE("task ID %d: CColorDet -- CPixDetData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CPixDetResult *pR = dynamic_cast<CPixDetResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CColorDet -- CPixDetResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (pD->m_oSrcImg.empty())
    {
        LOGE("task ID %d: CColorDet -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // set ROI
    cv::Rect oROI;
    if (-1 == pD->m_oROI.width && -1 == pD->m_oROI.height)
    {
        oROI = m_oROI;
    }
    else
    {
        oROI = pD->m_oROI;
    }

    int nState;

    // check ROI
    nState = CheckROI(m_nTaskID, pD->m_oSrcImg, oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorDet -- ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    // detect in ROI
    cv::Mat oDstImg;
    std::vector<cv::Point> oVecPoints;
    nState = Detect(pD->m_oSrcImg(oROI), oDstImg, oVecPoints);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorDet -- detect color failed, please check", m_nTaskID);
        return nState;
    }

    // set detection result
    pR->m_oDstImg = cv::Mat::zeros(pD->m_oSrcImg.rows, pD->m_oSrcImg.cols, cv::DataType<uchar>::type);
    oDstImg.copyTo(pR->m_oDstImg(oROI));

    for (int i = 0; i < static_cast<int>(oVecPoints.size()); i++)
    {
        cv::Point oPt;
        oPt.x = oVecPoints[i].x + oROI.x;
        oPt.y = oVecPoints[i].y + oROI.y;

        pR->m_oVecPoints.push_back(oPt);
    }

    // cv::imshow("src", pD->m_oSrcImg);
    // cv::imshow("dst", pR->m_oDstImg);
    // cvWaitKey(0);

    return 1;
}

int CColorDet::Release()
{
    return 1;
}

int CColorDet::ParseParam(const CColorDetParam *pParam)
{
    if (pParam->m_nTaskID < 0)
    {
        LOGE("CColorDet -- task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    m_nTaskID = pParam->m_nTaskID;

    if (pParam->m_nMaxPointNum <= 0)
    {
        LOGE("task ID %d: CColorDet -- max point number %d is invalid, please check",
            m_nTaskID, pParam->m_nMaxPointNum);
        return -1;
    }

    if (pParam->m_nFilterSize < 0)
    {
        LOGE("task ID %d: CColorDet -- filter size %d is invalid, please check",
            m_nTaskID, pParam->m_nFilterSize);
        return -1;
    }

    if (pParam->m_nRedLower > 255 || pParam->m_nRedLower < 0)
    {
        LOGE("task ID %d: CColorDet -- lower red %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nRedLower);
        return -1;
    }

    if (pParam->m_nRedUpper > 255 || pParam->m_nRedUpper < 0)
    {
        LOGE("task ID %d: CColorDet -- upper red %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nRedUpper);
        return -1;
    }

    if (pParam->m_nGreenLower > 255 || pParam->m_nGreenLower < 0)
    {
        LOGE("task ID %d: CColorDet -- lower green threshold %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nGreenLower);
        return -1;
    }

    if (pParam->m_nGreenUpper > 255 || pParam->m_nGreenUpper < 0)
    {
        LOGE("task ID %d: CColorDet -- upper green threshold %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nGreenUpper);
        return -1;
    }

    if (pParam->m_nBlueLower > 255 || pParam->m_nBlueLower < 0)
    {
        LOGE("task ID %d: CColorDet -- lower blue threshold %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nBlueLower);
        return -1;
    }

    if (pParam->m_nBlueUpper > 255 || pParam->m_nBlueUpper < 0)
    {
        LOGE("task ID %d: CColorDet -- upper blue threshold %d is not in 0~255, please check",
            m_nTaskID, pParam->m_nBlueUpper);
        return -1;
    }

    m_oROI = pParam->m_oROI;

    m_nFilterSize  = pParam->m_nFilterSize;
    m_nMaxPointNum = pParam->m_nMaxPointNum;
    m_nRedLower    = pParam->m_nRedLower;
    m_nRedUpper    = pParam->m_nRedUpper;
    m_nGreenLower  = pParam->m_nGreenLower;
    m_nGreenUpper  = pParam->m_nGreenUpper;
    m_nBlueLower   = pParam->m_nBlueLower;
    m_nBlueUpper   = pParam->m_nBlueUpper;

    return 1;
}

int CColorDet::Detect(const cv::Mat &oSrcImg, cv::Mat &oDstImg, std::vector<cv::Point> &oVecPoints)
{
    oVecPoints.clear();

    int nRows = oSrcImg.rows;
    int nCols = oSrcImg.cols;

    oDstImg = cv::Mat::zeros(nRows, nCols, cv::DataType<uchar>::type);

    // split BGR channels
    std::vector<cv::Mat> oVecChannels;
    cv::split(oSrcImg, oVecChannels);

    // find points that satisfies the condition
    for (int r = 0; r < nRows; r++)
    {
        uchar *pBlueImg  = oVecChannels[0].ptr<uchar>(r);
        uchar *pGreenImg = oVecChannels[1].ptr<uchar>(r);
        uchar *pRedImg   = oVecChannels[2].ptr<uchar>(r);

        uchar *pDst = oDstImg.ptr<uchar>(r);

        for (int c = 0; c < nCols; c++)
        {
            bool bResBlue  = CompareValue(pBlueImg[c], m_nBlueLower, m_nBlueUpper);
            bool bResGreen = CompareValue(pGreenImg[c], m_nGreenLower, m_nGreenUpper);
            bool bResRed   = CompareValue(pRedImg[c], m_nRedLower, m_nRedUpper);

            if (bResBlue && bResGreen && bResRed)
            {
                pDst[c] = 255;
            }
        }
    }

    // filter some isolated points
    if (m_nFilterSize > 0)
    {
        cv::Mat element = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(m_nFilterSize, m_nFilterSize));

        cv::erode(oDstImg, oDstImg, element);
        cv::dilate(oDstImg, oDstImg, element);
    }

    // select points with stride
    int nCount = 0;
    for (int y = 0; y < PIX_DET_STRIDE; y++)
    {
        for (int x = 0; x < PIX_DET_STRIDE; x++)
        {
            for (int r = y; r < nRows; r += PIX_DET_STRIDE)
            {
                uchar *pDst = oDstImg.ptr<uchar>(r);

                for (int c = x; c < nCols; c += PIX_DET_STRIDE)
                {
                    if (pDst[c] > 127)
                    {
                        oVecPoints.push_back(cv::Point(c, r));
                        nCount++;
                    }

                    if (nCount > m_nMaxPointNum)
                    {
                        LOGD("task ID %d: CColorDet -- the number of color points is larger than max point number %d",
                            m_nTaskID, m_nMaxPointNum);
                        break;
                    }
                }
            }
        }
    }

    // cv::imshow("src", oSrcImg);
    // cv::imshow("dst", oDstImg);
    // cvWaitKey(0);

    return 1;
}

bool CColorDet::CompareValue(uchar uValue, int nLower, int nUpper)
{
    if (uValue >= nLower && uValue <= nUpper)
    {
        return true;
    }
    else
    {
        return false;
    }
}
