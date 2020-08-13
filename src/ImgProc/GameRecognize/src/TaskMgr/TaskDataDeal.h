/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_DATA_DEAL_H_
#define TASK_DATA_DEAL_H_

#include "GameRecognize/src/TaskMgr/TaskContext.h"

class TaskDataDeal
{
public:
    TaskDataDeal();
    ~TaskDataDeal();
    /*!
    * @brief ���õ�ǰͼ��
    * @param[in] ��ǰͼ��
    */
    bool  SetCurImage(cv::Mat *oImage);

    bool Update();

private:
    cv::Mat *m_pCurImage;

};
#endif // TASK_DATA_DEAL_H_
