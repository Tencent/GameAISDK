/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKDATADEAL_H_
#define GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKDATADEAL_H_

#include "GameRecognize/src/TaskMgr/TaskContext.h"

class TaskDataDeal {
  public:
    TaskDataDeal();
    ~TaskDataDeal();

    bool  SetCurImage(cv::Mat *oImage);

    bool Update();
  private:
    cv::Mat *m_pCurImage;
};
#endif  // GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_TASKMGR_TASKDATADEAL_H_
