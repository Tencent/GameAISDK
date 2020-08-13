/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/ImgProcess/CObjDet.h"

// **************************************************************************************
//          CObjDet Class Define
// **************************************************************************************

CObjDet::CObjDet()
{}

CObjDet::~CObjDet()
{}

int CObjDet::CheckPointer(IImgProcData *pData, IImgProcResult *pResult)
{
    // check data pointer
    if (NULL == pData)
    {
        LOGE("task ID %d: CObjDet -- IImgProcData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // check result pointer
    if (NULL == pResult)
    {
        LOGE("task ID %d: CObjDet -- IImgProcResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // check source image
    if (pData->m_oSrcImg.empty())
    {
        LOGE("task ID %d: CObjDet -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    return 1;
}

int CObjDet::SetROI(CObjDetData *pD, cv::Rect *pROI)
{
    if (-1 == pD->m_oROI.width && -1 == pD->m_oROI.height)
    {
        *pROI = m_oROI;
    }
    else
    {
        *pROI = pD->m_oROI;
    }

    // check ROI
    int nState = 0;
    nState = CheckROI(m_nTaskID, pD->m_oSrcImg, *pROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CObjDet -- ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CObjDet::SetResult(const cv::Rect &oROI, const std::vector<tagBBox> oVecBBoxes, CObjDetResult *pR)
{
    if (oVecBBoxes.empty())
    {
        // clear result
        pR->m_oVecBBoxes.clear();
        return 1;
    }

    // set detection result
    MergeBBox(oVecBBoxes, pR->m_oVecBBoxes, 0.25);

    for (int i = 0; i < static_cast<int>(pR->m_oVecBBoxes.size()); i++)
    {
        pR->m_oVecBBoxes[i].oRect.x += oROI.x;
        pR->m_oVecBBoxes[i].oRect.y += oROI.y;
    }

    sort(pR->m_oVecBBoxes.begin(), pR->m_oVecBBoxes.end(), LessScore);

    return 1;
}
