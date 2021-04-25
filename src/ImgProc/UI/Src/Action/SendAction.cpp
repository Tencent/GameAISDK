/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Utils/TqcLog.h"
#include "UI/Src/Action/SendAction.h"
#include "UI/Src/Communicate/PBMsgManager.h"

extern CPBMsgManager g_pbMsgMgr;
extern cv::Mat       g_uiFrame;

CSendAction::CSendAction() {
    m_bShowResult = false;
    m_eTestMode = SDK_TEST;
    m_eMsgState = PB_STATE_NONE;
    m_eGameState = GAME_REG_STATE_NONE;
}

CSendAction::~CSendAction() {
}
void CSendAction::PaintAction(cv::Mat oFrame, cv::Point actionPoint1, cv::Point actionPoint2,
    int nActionID, GAMESTATEENUM eMsgState) {
    // 检查输入参数的合法性
    if (oFrame.empty()) {
        return;
    }

    // 第一个坐标点
    std::string strPtRest;
    if (actionPoint1.x > 0 && actionPoint1.y) {
        cv::circle(oFrame, cv::Point(actionPoint1.x, actionPoint1.y), 5, cv::Scalar(0, 255, 0), 3);
        char szUIName[TQC_PATH_STR_LEN] = { 0 };
        SNPRINTF(szUIName, TQC_PATH_STR_LEN, "UI:%d", nActionID);
        cv::putText(oFrame, cv::String(szUIName), cv::Point(actionPoint1.x, actionPoint1.y),
            cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 0, 0), 3);

        char szPointRest[TQC_PATH_STR_LEN] = { 0 };
        SNPRINTF(szPointRest, TQC_PATH_STR_LEN, "Pt1(%d, %d)", actionPoint1.x, actionPoint1.y);
        strPtRest = strPtRest + std::string(szPointRest);
    }

    // 第二个坐标点
    if (actionPoint2.x > 0 && actionPoint2.y) {
        cv::circle(oFrame, cv::Point(actionPoint2.x, actionPoint2.y), 5, cv::Scalar(0, 255, 0), 3);
        char szUIName[TQC_PATH_STR_LEN] = { 0 };
        SNPRINTF(szUIName, TQC_PATH_STR_LEN, "UI:%d,", nActionID);
        cv::putText(oFrame, cv::String(szUIName), cv::Point(actionPoint2.x, actionPoint2.y),
            cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 0, 0), 3);

        char szPointRest[TQC_PATH_STR_LEN] = { 0 };
        SNPRINTF(szPointRest, TQC_PATH_STR_LEN, "Pt2(%d, %d)", actionPoint2.x, actionPoint2.y);
        strPtRest = strPtRest + std::string(szPointRest);
    }

    // 当前的UI状态:"ui"/"game start"/"match over"/"none"
    std::string strTips;

    /* PB_STATE_NONE, PB_STATE_UI, PB_STATE_START,PB_STATE_OVER,*/
    switch (eMsgState) {
    case PB_STATE_UI:
        strTips = "ui";
        break;

    case PB_STATE_START:
        strTips = "game start";
        break;

    case PB_STATE_OVER:
        strTips = "match over";
        break;

    case PB_STATE_NONE:
        strTips = "none";
        break;

    default:
        break;
    }

    strPtRest = strPtRest + strTips;
    cv::putText(oFrame, cv::String(strPtRest), cv::Point(static_cast<int>(oFrame.cols / 4),
        static_cast<int>(oFrame.rows / 4)), cv::FONT_HERSHEY_SIMPLEX, 1,
        cv::Scalar(0, 255, 255), 3);

    // cv::imshow("UI", oFrame);
    // cv::waitKey(1);
}

bool CSendAction::SendClickAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
    tagActionState &stDstActionState) {
    // 打包点击协议包
    tagMessage  uiMsg;
    tagUIAction *pUIState = uiMsg.mutable_stuiaction();

    // GAMESTATEENUM uiState = PB_STATE_NONE;
    pUIState->set_nuiid(stSrcUIState.nId);
    GAMESTATEENUM uiState = MapState(m_eGameState, stSrcUIState.nId);

    pUIState->set_egamestate(uiState);

    // 根据源图像大小和处理图像大小，计算源图像对应的点击位置
    int nActionX = stDstActionState.nActionX;
    int nActionY = stDstActionState.nActionY;
    if (nActionX >= 0 && nActionY >= 0) {
        cv::Point dstPt;
        cv::Size  srcImgSize = cv::Size(stFramectx.oFrame.cols, stFramectx.oFrame.rows);
        cv::Size  ProcessImgSize = cv::Size(g_uiFrame.cols, g_uiFrame.rows);
        RestoreActionPoint(cv::Point(nActionX, nActionY), srcImgSize, ProcessImgSize, dstPt);
        nActionX = dstPt.x;
        nActionY = dstPt.y;
    }

    // 封装点击协议包
    tagUIUnitAction *pUIUnitAction = pUIState->add_stuiunitaction();
    pUIUnitAction->set_euiaction(PB_UI_ACTION_CLICK);
    pUIUnitAction->set_nduringtimems(stSrcUIState.nActionDuringTime);
    pUIUnitAction->set_nsleeptimems(stSrcUIState.nActionSleepTimeMs);
    tagUIPoint *pPoint = pUIUnitAction->mutable_stclickpoint();
    pPoint->set_nx(nActionX);
    pPoint->set_ny(nActionY);

    LOGI("UI: %d, x=%d y=%d, during=%d, %s", stSrcUIState.nId, nActionX, nActionY,
        stSrcUIState.nActionDuringTime, stSrcUIState.strStateName);

    cv::Mat oFrame = stFramectx.oFrame;
    int     nFrameSeq = stFramectx.nFrameSeq;
    // 封装图像信息(帧序号，图像长，宽)，如果是SDKTool运行模式，需要封装源图像数据
    {
        int             nImgSize = oFrame.total() * oFrame.elemSize();
        tagSrcImageInfo *pImg = pUIState->mutable_stsrcimageinfo();

        pImg->set_uframeseq(nFrameSeq);
        pImg->set_nwidth(oFrame.cols);
        pImg->set_nheight(oFrame.rows);

        if (m_eTestMode == SDKTOOL_TEST) {
            pImg->set_byimagedata(oFrame.data, nImgSize);
        }
    }

    uiMsg.set_emsgid(MSG_UI_ACTION);
    // 发送点击消息
    SendActionMsg(stFramectx, cv::Point(nActionX, nActionY), cv::Point(-1, -1),
        stSrcUIState.nId, uiState, uiMsg,
        stSrcUIState.nActionSleepTimeMs);
    return true;
}

GAMESTATEENUM CSendAction::MapState(const enGameState eGameState, const int nID) {
    // 检查输入参数的合法性
    if (nID < 0) {
        return PB_STATE_NONE;
    }

    switch (eGameState) {
        // in hall state, set message UI state as PB_STATE_UI
    case GAME_REG_STATE_HALL:
        m_eMsgState = PB_STATE_UI;
        return PB_STATE_UI;

    case GAME_REG_STATE_START:
        // game start state check: game start UI
        // 1) fisrt game start state, set message UI state as PB_STATE_START
        // 2) 2nd or later game start state, set message UI state as PB_STATE_UI
        if (PB_STATE_START != m_eMsgState) {
            m_eMsgState = PB_STATE_START;
            return PB_STATE_START;
        } else if (PB_STATE_START == m_eMsgState) {
            return PB_STATE_UI;
        } else {
            LOGE("msg state is %d, game sate is %d", m_eMsgState, m_eGameState);
            return PB_STATE_NONE;
        }

    case GAME_REG_STATE_RUN:
        // game run state check: pop UI
        return PB_STATE_UI;

    case GAME_REG_STATE_OVER:
        // game over state check: game over UI
        // 1) fisrt game over state, set message UI state as PB_STATE_OVER
        // 2) 2nd or later game over state, set message UI state as PB_STATE_UI
        if (PB_STATE_OVER != m_eMsgState) {
            m_eMsgState = PB_STATE_OVER;
            return PB_STATE_OVER;
        } else if (PB_STATE_OVER == m_eMsgState) {
            return PB_STATE_UI;
        } else {
            LOGE("msg state is %d, game sate is %d", m_eMsgState, m_eGameState);
            return PB_STATE_NONE;
        }

    default:
        LOGE("invalid game sate is %d", m_eGameState);
        return PB_STATE_NONE;
    }
}

bool CSendAction::SendActionMsg(const tagFrameContext &stFramectx, const cv::Point pt1,
    const cv::Point pt2, const int uID, GAMESTATEENUM eMsgState, tagMessage &uiMsg,
    const int nSleepTimeMS) {
    std::string strState;

    uiMsg.SerializeToString(&strState);

    // Send game state msg to ManageCenter
    // If we need to debug with sdk tool, we should send msg to it.
    enPeerName peerAddr = PEER_MC;

    if (m_eTestMode == SDKTOOL_TEST) {
        peerAddr = PEER_SDK_TOOLS;
    }

    // send data
    if (SDKTOOL_TEST == m_eTestMode || SDK_TEST == m_eTestMode) {
        LOGI("test mode is %d, message length is %zd, peerAddr %d", m_eTestMode,
            strState.length(), peerAddr);
        bool bRst = g_pbMsgMgr.SendData(reinterpret_cast<void*>
            (const_cast<char*>(strState.c_str())), strState.length(), peerAddr);
        if (!bRst) {
            LOGE("Send game state failed.");
        }
    }

    // 显示处理结果，并把显示图像存储在目录"../result"
    if (m_bShowResult) {
        cv::Mat oDisplay;
        g_uiFrame.copyTo(oDisplay);
        PaintAction(oDisplay, pt1, pt2, uID, eMsgState);
        cv::imshow("UI", oDisplay);
        cv::waitKey(1);
        char szRstImgName[TQC_PATH_STR_LEN] = { 0 };
        SNPRINTF(szRstImgName, TQC_PATH_STR_LEN, "../result/Cnt%d_Seq%d.jpg",
            stFramectx.nFrameCount, stFramectx.nFrameSeq);
        cv::imwrite(szRstImgName, oDisplay);
    }

    TqcOsSleep(nSleepTimeMS);
    LOGI("send frame data, frameIndex=%d", stFramectx.nFrameSeq);
    return true;
}

bool CSendAction::SendDragAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
    const tagActionState &stDstActionState1, const tagActionState &stDstActionState2) {
    // 打包拖拽包
    tagMessage  uiMsg;
    tagUIAction *pUIState = uiMsg.mutable_stuiaction();

    // GAMESTATEENUM uiState = PB_STATE_NONE;
    pUIState->set_nuiid(stSrcUIState.nId);
    GAMESTATEENUM uiState = MapState(m_eGameState, stSrcUIState.nId);
    pUIState->set_egamestate(uiState);
    tagUIUnitAction *pUIUnitAction = pUIState->add_stuiunitaction();
    pUIUnitAction->set_euiaction(PB_UI_ACTION_DRAG);
    pUIUnitAction->set_nduringtimems(stSrcUIState.nActionDuringTime);
    pUIUnitAction->set_nsleeptimems(stSrcUIState.nActionSleepTimeMs);

    // 根据源图像大小和处理图像大小，计算源图像对应的点击位置
    cv::Point dstPt;
    cv::Size  srcImgSize = cv::Size(stFramectx.oFrame.cols, stFramectx.oFrame.rows);
    cv::Size  ProcessImgSize = cv::Size(g_uiFrame.cols, g_uiFrame.rows);

    // 计算起始点1的点击位置
    int nActionX1 = stDstActionState1.nActionX;
    int nActionY1 = stDstActionState1.nActionY;
    if (nActionX1 >= 0 || nActionY1 >= 0) {
        RestoreActionPoint(cv::Point(nActionX1, nActionY1), srcImgSize, ProcessImgSize, dstPt);
        nActionX1 = dstPt.x;
        nActionY1 = dstPt.y;
    }

    tagUIPoint *pPoint = pUIUnitAction->add_stdragpoints();
    pPoint->set_nx(nActionX1);
    pPoint->set_ny(nActionY1);

    // 计算起始点2的点击位置
    int nActionX2 = stDstActionState2.nActionX;
    int nActionY2 = stDstActionState2.nActionY;
    if (nActionX2 >= 0 || nActionY2 >= 0) {
        RestoreActionPoint(cv::Point(nActionX2, nActionY2), srcImgSize, ProcessImgSize, dstPt);
        nActionX2 = dstPt.x;
        nActionY2 = dstPt.y;
    }

    pPoint = pUIUnitAction->add_stdragpoints();
    pPoint->set_nx(nActionX2);
    pPoint->set_ny(nActionY2);

    LOGW("UI: %d, (%d, %d)->(%d, %d), during=%d, %s",
        stSrcUIState.nId, nActionX1, nActionY1, nActionX2, nActionY2,
        stSrcUIState.nActionDuringTime, stSrcUIState.strStateName);

    cv::Mat oDisplay = stFramectx.oFrame.clone();
    cv::Mat oFrame = stFramectx.oFrame;
    int     nFrameSeq = stFramectx.nFrameSeq;
    // 封装图像信息(帧序号，图像长，宽)，如果是SDKTool运行模式，需要封装源图像数据
    {
        int             nImgSize = oFrame.total() * oFrame.elemSize();
        tagSrcImageInfo *pImg = pUIState->mutable_stsrcimageinfo();

        pImg->set_uframeseq(nFrameSeq);
        pImg->set_nwidth(oFrame.cols);
        pImg->set_nheight(oFrame.rows);

        if (SDKTOOL_TEST == m_eTestMode) {
            pImg->set_byimagedata(oFrame.data, nImgSize);
        }
    }
    uiMsg.set_emsgid(MSG_UI_ACTION);
    cv::Point pt1 = cv::Point(stDstActionState1.nActionX, stDstActionState1.nActionY);
    cv::Point pt2 = cv::Point(stDstActionState2.nActionX, stDstActionState2.nActionY);
    // 发送拖拽消息
    SendActionMsg(stFramectx, pt1, pt2, stSrcUIState.nId, uiState, uiMsg,
        stSrcUIState.nActionSleepTimeMs);
    return true;
}

void CSendAction::ReadActionJsonValue(const Json::Value &josnValue, tagActionState &stState1,
    tagActionState &stState2) {   // 读取第一个点的配置
    int   nPoint1X = josnValue["point1X"].asInt();
    int   nPoint1Y = josnValue["point1Y"].asInt();
    float fThreshold1 = 0.7f;
    // 读取模板匹配的阈值
    Json::Value jsonThreahold1 = josnValue["actionThreshold1"];

    if (!jsonThreahold1.empty()) {
        fThreshold1 = jsonThreahold1.asFloat();
    }

    // 读取以点为中心，水平方向扩展的区域，左右分别扩展"actionTmplExpdWPixel1"
    int         nTmplExpdWPixel1 = 25;
    Json::Value jsonTmplExpdWPixel = josnValue["actionTmplExpdWPixel1"];
    if (!jsonTmplExpdWPixel.empty()) {
        nTmplExpdWPixel1 = jsonTmplExpdWPixel.asInt();
    }

    // 读取以点为中心，竖直方向扩展的区域，左右分别扩展"actionTmplExpdHPixel1"
    int         nTmplExpdHPixel1 = 25;
    Json::Value jsonTmplExpdHPixel = josnValue["actionTmplExpdHPixel1"];
    if (!jsonTmplExpdHPixel.empty()) {
        nTmplExpdHPixel1 = jsonTmplExpdHPixel.asInt();
    }

    // ROI扩展区域，水平方向扩展1280 * "actionROIExpdWRatio1"
    float       fROIExpdWRatio1 = 0.275f;
    Json::Value jsonROIExpdWRatio1 = josnValue["actionROIExpdWRatio1"];
    if (!jsonROIExpdWRatio1.empty()) {
        fROIExpdWRatio1 = jsonROIExpdWRatio1.asFloat();
    }

    // ROI扩展区域，竖直方向扩展 height * "actionROIExpdWRatio1"
    float       fROIExpdHRatio1 = 0.275f;
    Json::Value jsonROIExpdHRatio1 = josnValue["actionROIExpdHRatio1"];
    if (!jsonROIExpdHRatio1.empty()) {
        fROIExpdHRatio1 = jsonROIExpdHRatio1.asFloat();
    }

    // 读取第二个点的配置
    int nPoint2X = josnValue["point2X"].asInt();
    int nPoint2Y = josnValue["point2Y"].asInt();

    // 读取模板匹配的阈值
    float       fThreshold2 = 0.7f;
    Json::Value jsonThreahold2 = josnValue["actionThreshold2"];

    if (!jsonThreahold2.empty()) {
        fThreshold2 = jsonThreahold2.asFloat();
    }

    // 读取以点为中心，水平方向扩展的区域，左右分别扩展"actionTmplExpdWPixel2"
    int         nTmplExpdWPixel2 = 25;
    Json::Value jsonTmplExpdWPixe2 = josnValue["actionTmplExpdWPixel2"];
    if (!jsonTmplExpdWPixe2.empty()) {
        nTmplExpdWPixel2 = jsonTmplExpdWPixe2.asInt();
    }

    // 读取以点为中心，竖直方向扩展的区域，左右分别扩展"actionTmplExpdHPixel2"
    int         nTmplExpdHPixel2 = 25;
    Json::Value jsonTmplExpdHPixe2 = josnValue["actionTmplExpdHPixel2"];
    if (!jsonTmplExpdHPixe2.empty()) {
        nTmplExpdHPixel2 = jsonTmplExpdHPixe2.asInt();
    }

    // ROI扩展区域，水平方向扩展1280 * "actionROIExpdWRatio1"
    float       fROIExpdWRatio2 = 0.275f;
    Json::Value jsonROIExpdWRatio2 = josnValue["actionROIExpdWRatio2"];
    if (!jsonROIExpdWRatio2.empty()) {
        fROIExpdWRatio2 = jsonROIExpdWRatio2.asFloat();
    }

    // ROI扩展区域，竖直方向扩展 height * "actionROIExpdHRatio2"
    float       fROIExpdHRatio2 = 0.275f;
    Json::Value jsonROIExpdHRatio2 = josnValue["actionROIExpdHRatio2"];
    if (!jsonROIExpdHRatio2.empty()) {
        fROIExpdHRatio2 = jsonROIExpdHRatio2.asFloat();
    }

    stState1 = tagActionState(nPoint1X, nPoint1Y, fThreshold1, nTmplExpdWPixel1, nTmplExpdHPixel1,
        fROIExpdWRatio1, fROIExpdHRatio1);
    stState2 = tagActionState(nPoint2X, nPoint2Y, fThreshold2, nTmplExpdWPixel2, nTmplExpdHPixel2,
        fROIExpdWRatio2, fROIExpdHRatio2);
}

void CSendAction::RestoreActionPoint(const cv::Point inPoint, const cv::Size inImgSize,
    const cv::Size outImgSize, cv::Point &outPoint) {
    // 检查输入参数的合法性
    outPoint.x = inPoint.x;
    outPoint.y = inPoint.y;
    if (inImgSize.width <= 0) {
        LOGE("image size width %d is invalid, please check", inImgSize.width);
        return;
    }

    // 根据输入图像和处理图像的尺寸，调整点的坐标值
    float fScaleW = static_cast<float>(outImgSize.width) / static_cast<float>(inImgSize.width);
    float fScaleH = fScaleW;

    if (inPoint.x >= 0 && inPoint.y >= 0) {
        outPoint.x = static_cast<int>(inPoint.x * fScaleW);
        outPoint.y = static_cast<int>(inPoint.y * fScaleH);
    }
}

void CSendAction::SetTestMode(const ETestMode eTestMode) {
    m_eTestMode = eTestMode;
}

void CSendAction::SetGameState(const enGameState eGameState) {
    m_eGameState = eGameState;
}

void CSendAction::SetShowResult(const bool bShowResult) {
    m_bShowResult = bShowResult;
}
