/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef UI_FRAMEWORK_H_
#define UI_FRAMEWORK_H_

#include <map>
#include <string>

#include "Comm/Utils/IniConfig.h"
#include "UI/Src/Communicate/DataComm.h"
#include "UI/Src/Communicate/DataManager.h"
#include "UI/Src/Communicate/PBMsgManager.h"
#include "UI/Src/GameState/UIState.h"


class CUIFrameWork
{
public:
    CUIFrameWork();
    ~CUIFrameWork();

    /*!
     * @brief 初始化
     * @param[in] pszRootPath: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pszCftPath: UI配置所在的相对路径
     * @return true表示成功，false表示失败
     */
    bool Initialize(const char *pszRootPath);
    /*!
     * @brief run
     * return 0表示成功，-1表示失败
     */
    int Run();

    /*!
     * @brief 释放资源
     */
    void Release();

    /*!
     * @brief 设置测试模式
     * @param[in] eTestMode
     */
    void SetTestMode(ETestMode eTestMode);

    /*!
     * @brief 设置数据管理器
     * @param[in] pDataMgr
     * @return true表示成功，false表示失败
     */
    bool SetDataMgr(CDataManager *pDataMgr);

    /*!
     * @brief 设置消息管理器
     * @param[in] pMsgMgr
     * @return true表示成功，false表示失败
     */
    bool SetMsgMgr(CPBMsgManager *pMsgMgr);

private:
    /*!
     * @brief 初始化数据管理器
     * @return true表示成功，false表示失败
     */
    bool InitDataMgr();

    /*!
     * @brief 初始化消息管理器
     * @return true表示成功，false表示失败
     */
    bool InitMsgMgr();

    /*!
     * @brief 初始化识别器
     * @param[in] pszRootPath: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pszUICfgPath: UI配置所在的相对路径
     * @return true表示成功，false表示失败
     */
    bool InitRecognizer(const char *pszRootPath, const char *pszUICfgPath);

    /*!
     * @brief 读取tbus的配置
     * @param[in] strConfigFileName
     * @param[in] strSectionName
     * @param[out] pMapValues
     * @return true表示成功，false表示失败
     */
    bool ReadTbusCfgFile(std::string strConfigFileName, std::string strSectionName,
                         std::map<std::string, std::string> *pMapValues);

    /*!
     * @brief 注册MC
     * @return true表示成功，false表示失败
     */
    bool RegisterToMC();

    /*!
     * @brief 反注册MC
     * @return true表示成功，false表示失败
     */
    bool UnRegisterFromMC();

    /*!
     * @brief 创建日志
     * @param[in]　strProgName 进程名
     * @return true or false
     */
    bool CreateLog(const char *strProgName);

    /*!
     * @brief 加载日志配置
     * @param[in] poCfg
     * @return true or false
     */
    bool LoadLogCfg(CIniConfig *poCfg);

    /*!
     * @brief 加载调试配置
     * @return true or false
     */
    bool LoadDebugCfg(CIniConfig *poCfg);

    /*!
     * @brief 加载配置
     * @return true or false
     */
    bool LoadPlatfromConfig();

    bool LoadTaskConfig(const char *pszRootPath);
private:
    CContext      *m_poCtx;
    ETestMode     m_eRunMode;           // UI以哪种模式运行，SDK，Video，SDKTool
    CDataManager  *m_pDataMgr;
    CPBMsgManager *m_pMsgMgr;
    enSourceType  m_eSrcType;
    enSourceType  m_eDstType;
    void          *m_pmsgThreadID;
    char          m_szVideoPath[TQC_PATH_STR_LEN];
    tagPicParams  m_stPicParams;
    int           m_nFrameCnt;
};
#endif // UI_FRAMEWORK_H_
