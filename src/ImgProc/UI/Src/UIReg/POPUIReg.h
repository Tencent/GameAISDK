/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_UIREG_POPUIREG_H_
#define GAME_AI_SDK_IMGPROC_UI_UIREG_POPUIREG_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/Utils/TSingleton.h"
#include "opencv2/opencv.hpp"
#include "UI/Src/UICfg/POPUICfg.h"
#include "UI/Src/UIDefine.h"
#include "UI/Src/UIReg/UIReg.h"


struct tagPOPUIParam {
    int      nID;
    cv::Mat  oTemplImg;
    cv::Rect oSrcRect;
    float    fThreshold;

    tagPOPUIParam() {
        nID = 0;
        fThreshold = GAME_TEMPLATE_THRESHOLD;
    }
};


class CPOPUIReg : public TSingleton<CPOPUIReg>, public CUIReg {
  public:
    CPOPUIReg();
    ~CPOPUIReg();

    /*!
      * @brief 初始化
      * @param[in] pUICfg: 配置项
      * @return true表示成功，false表示失败
    */
    virtual bool Initialize(CUICfg *pUIReg);

    /*!
      * @brief　检测处理输入图像数据
      * @param[in] stFrameCtx: 输入帧信息
      * @param[out] stUIRegRst:　输出结果
      * @return -1 表示失败，否则返回匹配到的UI的ID
    */
    virtual int Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst);

    bool IsDevPOPUI();

    bool IsGamePOPUI();

  private:
    /*!
      * @brief 游戏弹框UI的识别参数
      * @param[in] pUICfg: 配置项
      * @return true表示成功，false表示失败
    */
    bool FillGamePOPUIRegParam(CUICfg *pUICfg);

    /*!
      * @brief 设备弹框UI的识别参数
      * @param[in] pUICfg: 配置项
      * @return true表示成功，false表示失败
    */
    bool FillDevPOPUIRegParam(CUICfg *pUICfg);

    bool FillPOPUIParam(const UIStateArray &oVecCfg, std::vector<tagPOPUIParam> *pstVecParam);

    /*!
      * @brief　检测处理输入图像数据
      * @param[in] frame
      * @param[in] stParam
      * @param[out] dstRect
      * @return -1 表示失败，否则返回匹配到的UI的ID
    */
    int  Predict(const cv::Mat &frame, std::vector<tagPOPUIParam> &stParam, cv::Rect &dstRect);

    /*!
      * @brief　判断前后帧是否相同
      * @param[in] frame
      * @return true表示成功，false表示失败
    */
    bool IsFrameSame(const cv::Mat &frame);

  private:
    std::vector<tagPOPUIParam> m_stGameParam;
    std::vector<tagPOPUIParam> m_stDevParam;

    UIStateArray m_oVecGameCfg;
    UIStateArray m_oVecDevCfg;
    cv::Mat      m_lastFrame;
    int          m_nFrameCount;

    bool m_bGamePOPUI;
    bool m_bDevPOPUI;
};

#endif  // GAME_AI_SDK_IMGPROC_UI_UIREG_POPUIREG_H_
