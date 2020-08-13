/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskDataDeal.h"
using namespace std;

TaskDataDeal::TaskDataDeal()
{
    m_pCurImage = NULL;
}

TaskDataDeal::~TaskDataDeal()
{}

bool TaskDataDeal::Update()
{
    return true;
}

bool TaskDataDeal::SetCurImage(cv::Mat *poImage)
{
    if (NULL == poImage)
    {
        LOGE("input image is null, please check");
        return false;
    }

    m_pCurImage = poImage;
    return true;
}
