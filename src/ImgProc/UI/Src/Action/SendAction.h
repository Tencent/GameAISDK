/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef SEND_ACTION_H_
#define SEND_ACTION_H_

#include "Protobuf/common.pb.h"
#include "UI/Src/Communicate/DataComm.h"
#include "UI/Src/UITypes.h"

class CSendAction
{
public:
    CSendAction();
    ~CSendAction();
    /*!
     * @brief 发送点击动作协议包
     * @param[in]stFramectx
     * @param[in]stSrcUIState
     * @param[in]stDstActionState
     * @return true表示成功，false表示失败
     */
    bool SendClickAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
                         tagActionState &stDstActionState);

    /*!
     * @brief 发送点击动作协议包
     * @param[in]eGameState
     * @param[in]nID
     * @return转换后的状态
     */
    GAMESTATEENUM MapState(const enGameState eGameState, const int nID);

    /*!
     * @brief 发送协议包
     * @param[in]stFramectx
     * @param[in]pt1
     * @param[in]pt2
     * @param[in]uID
     * @param[in]stDstActionState
     * @param[in]eMsgState
     * @param[in]uiMsg
     * @param[in]nSleepTimeMS:发送完动作后的等待时间
     * @return true表示成功，false表示失败
     */
    bool SendActionMsg(const tagFrameContext &stFramectx, const cv::Point pt1, const cv::Point pt2, const int uID,
                       GAMESTATEENUM eMsgState, tagMessage &uiMsg, const int nSleepTimeMS = 100);

    /*!
     * @brief 发送拖拽动作协议包
     * @param[in]stFramectx　图像帧信息
     * @param[in]stSrcUIState　UI状态
     * @param[in]stDstActionState1　拖拽起点
     * @param[in]stDstActionState2　拖拽终点
     * @return true表示成功，false表示失败
     */
    bool SendDragAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
                        const tagActionState &stDstActionState1, const tagActionState &stDstActionState2);

    /*!
     * @brief 读取动作参数
     * @param[in]josnValue
     * @param[out]stState1
     * @param[out]stDstActionState1　拖拽起点
     * @param[out]stState2　拖拽终点
     * @return true表示成功，false表示失败
    */
    void ReadActionJsonValue(const Json::Value &josnValue, tagActionState &stState1, tagActionState &stState2);
    /*!
     * @brief 读取动作参数
     * @param[in]inPoint
     * @param[in]inImgSize
     * @param[in]outImgSize
     * @param[out]outPoint
    */
    void RestoreActionPoint(const cv::Point inPoint, const cv::Size inImgSize,
                            const cv::Size outImgSize, cv::Point &outPoint);

    /*!
     * @brief 动作结果绘制
     * @param[in]oFrame　图像帧
     * @param[in]actionPoint1　第一个点击位置(点击动作时，只需要这一个位置，第二个点击位置无效
       拖拽动作时，第一个点击位置表示拖拽的起点，第二个点击位置表示拖拽的终点)
     * @param[in]actionPoint2　第二个点击位置(点击动作时，只需要这一个位置)
     * @param[in]nActionID　游戏状态
     */
    void PaintAction(cv::Mat oFrame, cv::Point actionPoint1, cv::Point actionPoint2, int nActionID,
                     GAMESTATEENUM eMsgState = PB_STATE_NONE);
    /*!
     * @brief 设置运行模式
     * @param[in]eTestMode
     */
    void SetTestMode(const ETestMode eTestMode);

    /*!
     * @brief 设置游戏状态
     * @param[in]eTestMode
     */
    void SetGameState(const enGameState eGameState);

    /*!
     * @brief 设置是否线上游戏结果
     * @param[in]eTestMode
     */
    void SetShowResult(const bool bShowResult);

private:
    ETestMode     m_eTestMode;
    GAMESTATEENUM m_eMsgState;
    enGameState   m_eGameState;

    bool m_bShowResult;
};

#endif // SEND_ACTION_H_
