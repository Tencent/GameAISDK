/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef ACTION_H_
#define ACTION_H_
#include "Comm/Utils/TSingleton.h"
#include "Protobuf/common.pb.h"
#include "UI/Src/Action/SendAction.h"
#include "UI/Src/Communicate/DataComm.h"
#include "UI/Src/UITypes.h"


class CAction : public TSingleton<CAction>
{
public:
    CAction();
    ~CAction();
    /*!
     * @brief 初始化
     * @param[in] eTestMode
     * @return true表示成功，false表示失败
     */
    bool Initialize(ETestMode eTestMode);

    /*!
     * @brief UI动作
     * @param[in]stFramectx　图像帧信息
     * @param[in]stUIRegRst　识别结果信息
     * @param[in]state　配置参数信息
     * @param[in]eGameState　游戏状态
     * @return true表示成功，false表示失败
     */
    bool DoAction(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst, UIStateArray &state,
                  const enGameState eGameState);

    /*!
     * @brief 获取当前的游戏状态
     * @return游戏状态
     */
    enGameState GetGameState();

    /*!
     * @brief 获取是否与SDKTool调式
     */
    ETestMode GetTestMode();

    /*!
     * @brief 获取是否显示处理结果
     */
    bool IsShowResult();

    CSendAction* SendAction();
private:
    /*!
     * @brief 点击动作
     * @param[in]stFramectx 图像帧信息
     * @param[in]stSrcUIState　UI状态
     * @param[in]stDstActionState　点击位置
     * @return true表示成功，false表示失败
     */
    bool DoClickAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState, tagActionState &stDstActionState);

    /*!
     * @brief 拖拽动作
     * @param[in]stFramectx　图像帧信息
     * @param[in]stSrcUIState　UI状态
     * @param[in]stDstActionState1　拖拽起点
     * @param[in]stDstActionState2　拖拽终点
     * @return true表示成功，false表示失败
     */
    bool DoDragAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
                      tagActionState &stDstActionState1, tagActionState &stDstActionState2);

    /*!
     * @brief 脚本动作类型
     * @param[in]stFramectx
     * @param[in]stSrcUIState
     * @return true表示成功，false表示失败
     */
    bool DoScript(const tagFrameContext &stFramectx, tagUIState &stSrcUIState);

    /*!
     * @brief 边拖边拽动作类型
     * @param[in]stFramectx　图像帧信息
     * @param[in]stSrcUIState　UI状态
     * @param[in]stDstActionState　拖拽起点
     * @return true表示成功，false表示失败
     */
    bool DoDragCheckAction(const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
                           tagActionState &stDstActionState);

    /*!
     * @brief 空动作
     * @param[in]stFramectx　图像帧信息
     * @return true表示成功，false表示失败
     */
    bool DoNoneAction(const tagFrameContext &stFramectx);

    /*!
     * @brief 动作接口
     * @param[in]stFramectx
     * @param[in]stSrcUIState
     * @param[in]eGameState
     * @return true表示成功，false表示失败
     */
    bool DoAction(const tagFrameContext &stFramectx, tagUIState &stSrcUIState, enGameState eGameState);

private:
    int         m_nDragCount;
    enGameState m_eGameState;
    // GAMESTATEENUM m_eMsgState;
    // bool m_bDebugWithSDKTools;
    ETestMode m_eTestMode;
    bool      m_bShowResult;

    CSendAction   m_oSendAction;
    eUIActionType m_preActionType;
    tagUIState    m_prestSrcUIState;
};


// bool SendScriptUIAction(char *pszPkgBuff);
extern "C"
{
#ifdef LINUX
bool  SendScriptUIAction(char *pszPkgBuff);
bool  PyLOGD(char *pszLogContent);
bool  PyLOGI(char *pszLogContent);
bool  PyLOGW(char *pszLogContent);
bool  PyLOGE(char *pszLogContent);

#else
__declspec(dllexport)  bool __stdcall SendScriptUIAction(char *pszPkgBuff);
__declspec(dllexport)  bool PyLOGD(char *pszLogContent);
__declspec(dllexport)  bool PyLOGI(char *pszLogContent);
__declspec(dllexport)  bool PyLOGW(char *pszLogContent);
__declspec(dllexport)  bool PyLOGE(char *pszLogContent);
#endif
}
#endif // ACTION_H_
