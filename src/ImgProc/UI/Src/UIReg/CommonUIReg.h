/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_UIREG_COMMONUIREG_H_
#define GAME_AI_SDK_IMGPROC_UI_UIREG_COMMONUIREG_H_
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/ImgReg/ImgProcess/CORBMatch.h"
#include "opencv2/opencv.hpp"
#include "UI/Src/UICfg/GameOverCfg.h"
#include "UI/Src/UIDefine.h"
#include "UI/Src/UIReg/UIReg.h"


struct tagTmplateParam {
    int      nID;
    cv::Mat  oTmplImg;
    cv::Rect oSrcRect;
    float    fThreshold;

    tagTmplateParam() {
        nID = 0;
        fThreshold = GAME_TEMPLATE_THRESHOLD;
    }
};

struct tagCommonRegParam {
    int                          nUID;
    int                          nKeyPtThr;  // key point number
    cv::Mat                      oUIImg;
    _eTemplateOp                 eTmplOp;
    std::vector<tagTmplateParam> stVecTmplParam;
    tagCommonRegParam() {
        nUID = -1;
        nKeyPtThr = 100;
        eTmplOp = UI_TEMPLATE_NONE;
    }
};


class CCommonUIReg {
  public:
    CCommonUIReg();
    ~CCommonUIReg();

    /*!
      * @brief 初始化
      * @param[in] pUICfg: 配置项
      * @return true表示成功，false表示失败
    */
    virtual bool Initialize(const UIStateArray &oVecCfg);

    /*!
      * @brief　检测处理输入图像数据
      * @param[in] stFrameCtx: 输入帧信息
      * @param[out] stUIRegRst:　输出结果
      * @return -1 表示失败，否则返回匹配到的UI的ID
    */
    virtual int Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst);

  private:
    /*!
      * @brief 填充识别参数
      * @param[in] oVecCfg
      * @return true表示成功，false表示失败
    */
    bool FillRegParam(const UIStateArray &oVecCfg);

    /*!
      * @brief　检测处理输入图像数据
      * @param[in] frame
      * @param[in] stParam
      * @param[out] dstRect
      * @return -1 表示失败，否则返回匹配到的UI的ID
    */
    int Predict(const cv::Mat &frame, const std::vector<tagCommonRegParam> &stParam,
        cv::Rect &dstRect);

    /*!
      * @brief　模板匹配检测处理输入图像数据
      * @param[in] frame
      * @param[in] stParam
      * @return true表示成功，false表示失败
    */
    bool CheckMatch(const cv::Mat &frame, const tagCommonRegParam &stRegParam);

    int FindMatch(const std::vector<float> &nKPTVecMatch, const std::vector<bool> &bTmplVecMatch);

    bool ChecSameImage(int nIndex, const tagFrameContext &stFrameCtx);
    /*!
      * @brief　查找特征点匹配的匹配结果
      * @param[in] bKPTVecMatch
      * @return UI的ID
    */
    // int FindKTMatchIndex(const std::vector<int> &nKPTVecMatch);

    /*!
      * @brief　查找最佳模板匹配：模板数最多的那个UI
      * @param[in] bTmplVecMatch
      * @param[in] stParam
      * @return UI的ID
    */
    // int FindTmplMatchIndex(const std::vector<bool> &bTmplVecMatch,
    // const std::vector<tagCommonRegParam> &stParam);

  private:
    std::vector<tagCommonRegParam> m_stVecParam;
    UIStateArray                   m_oVecCfg;
    std::vector<CORBMatch>         m_oVecOrbMatch;
    int                            m_nTmplMatchIndex;
    std::vector<int>               m_nVecUseTemplMatch;
    cv::Mat                        m_oPreFrame;
    int                            m_nPreUID;
    int                            m_nSameFrameCnt;
};
#endif  // GAME_AI_SDK_IMGPROC_UI_UIREG_COMMONUIREG_H_
