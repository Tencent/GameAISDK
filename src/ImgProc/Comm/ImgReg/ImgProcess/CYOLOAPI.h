/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CYOLOAPI_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CYOLOAPI_H_

#include <string>
#include <vector>

#ifdef LINUX
#include <boost/thread/mutex.hpp>
#include "Comm/ImgReg/ImgProcess/CObjDet.h"
#include "Comm/Os/TqcOs.h"
#include "GameRecognize/src/FrameWorkDefine.h"
#include "Modules/darknetV3/include/darknet.h"
#endif

#ifdef WINDOWS
#include "Comm/ImgReg/ImgProcess/CObjDet.h"
#include "GameRecognize/src/FrameWorkDefine.h"
extern "C" {
#include "Modules/darknetV3-win/src/parser.h"
}

#include "Modules/darknetV3-win/src/blas.h"
#include "Modules/darknetV3-win/src/cuda.h"
#include "Modules/darknetV3-win/src/utils.h"
#endif



// **************************************************************************************
//          tagYoloNetWork Structure Define
// **************************************************************************************

struct tagYoloNetWork {
    bool         bState;
#ifdef WINDOWS
    network stNet;
#endif

#ifdef LINUX
    network      *pNet;
#endif
    LockerHandle Mutex;

    tagYoloNetWork() {
#ifdef LINUX
        pNet = NULL;
#endif
        bState = true;
        Mutex = NULL;
    }

    ~tagYoloNetWork() {
        // TqcOsDeleteMutex(Mutex);
    }

    bool IsFree() {
        TqcOsAcquireMutex(Mutex);
        bool bTmp = bState;
        if (bState) {
            bState = false;
        }

        TqcOsReleaseMutex(Mutex);
        return bTmp;
    }

    void SetFree() {
        TqcOsAcquireMutex(Mutex);
        bState = true;
        TqcOsReleaseMutex(Mutex);
    }
};

// **************************************************************************************
//          CYOLO Class Define
// **************************************************************************************

class CYOLO {
  public:
    CYOLO();
    ~CYOLO();

    int Initialize(char *pszCfgFile, char *pszWeightFile, char *pszNameFile,
        float fThreshold = 0.5f);

    int Predict(const cv::Mat &oSrcImg, std::vector<tagBBox> &oVecBBoxes);

    int Release();

  private:
    char                        **m_pszNames;
    float                       m_fThreshold;
    std::vector<tagYoloNetWork> m_oVecNets;
};

// **************************************************************************************
//          CYOLOAPIParam Class Define
// **************************************************************************************

class CYOLOAPIParam {
  public:
    CYOLOAPIParam() {
        m_nTaskID = -1;
        m_nMaskValue = 127;
        m_fThreshold = 0.5f;
        m_oROI = cv::Rect(-1, -1, -1, -1);
        m_strCfgPath = "";
        m_strWeightPath = "";
        m_strNamePath = "";
        m_strMaskPath = "";
    }
    virtual ~CYOLOAPIParam() {}

  public:
    int         m_nTaskID;
    int         m_nMaskValue;
    float       m_fThreshold;
    cv::Rect    m_oROI;
    std::string m_strCfgPath;
    std::string m_strWeightPath;
    std::string m_strNamePath;
    std::string m_strMaskPath;
};

// **************************************************************************************
//          CYOLOAPIData Class Define
// **************************************************************************************

class CYOLOAPIData {
  public:
    CYOLOAPIData() {}
    virtual ~CYOLOAPIData() {}

  public:
    cv::Mat m_oSrcImg;
};

// **************************************************************************************
//          CYOLOAPIResult Class Define
// **************************************************************************************

class CYOLOAPIResult {
  public:
    CYOLOAPIResult() {}
    virtual ~CYOLOAPIResult() {}

  public:
    std::vector<tagBBox> m_oVecBBoxes;
};

// **************************************************************************************
//          CYOLOAPI Class Define
// **************************************************************************************

class CYOLOAPI {
  public:
    CYOLOAPI();
    ~CYOLOAPI();

    // interface
    int Initialize(const CYOLOAPIParam &oParam);
    int Predict(const CYOLOAPIData &oData, CYOLOAPIResult &oResult);
    int Release();

  private:
    int      m_nTaskID;
    int      m_nMaskValue;
    cv::Rect m_oROI;
    cv::Mat  m_oMask;
    CYOLO    m_oYOLO;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CYOLOAPI_H_
