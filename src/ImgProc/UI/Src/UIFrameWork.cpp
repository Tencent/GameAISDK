/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifdef LINUX
#include <unistd.h>
#elif WINDOWS
#include <io.h>
#endif

#include "Protobuf/common.pb.h"
#include "UI/Src/Action/Action.h"
#include "UI/Src/Communicate/DataManager.h"
#include "UI/Src/Communicate/PBMsgManager.h"
#include "UI/Src/GameState/HallState.h"
#include "UI/Src/UICfg/GameOverCfg.h"
#include "UI/Src/UICfg/GameStartCfg.h"
#include "UI/Src/UICfg/HallCfg.h"
#include "UI/Src/UICfg/POPUICfg.h"
#include "UI/Src/UIFrameWork.h"
#include "UI/Src/UIReg/GameOverReg.h"
#include "UI/Src/UIReg/GameStartReg.h"
#include "UI/Src/UIReg/HallReg.h"
#include "UI/Src/UIReg/POPUIReg.h"


extern bool          g_bExit;
extern CDataManager  g_dataMgr;
extern CPBMsgManager g_pbMsgMgr;
cv::Mat              g_uiFrame;

void RunMsgThread(void *pArgs) {
    ETestMode *pMode = reinterpret_cast<ETestMode*>(pArgs);

    // 如果不是从tbus收帧，退出
    if (g_dataMgr.GetSrcType() != DATA_SRC_TBUS) {
        return;
    }

    // 循环从tbus收数据
    do {
        // 收到exit信号后，退出
        if (g_bExit) {
            LOGI("Msg Thread Exist");
            break;
        }

        // 运行SDKTool模式，从SDKTool收消息
        if (SDKTOOL_TEST == *pMode) {
            if (!g_pbMsgMgr.ReceiveMsg(MsgHandler, "SDKToolAddr"))
                break;
        } else if (SDK_TEST == *pMode) {
            if (!g_pbMsgMgr.ReceiveMsg(MsgHandler, "MCAddr"))
                break;
        } else {
            LOGE("input mode %d is invalid", *pMode);
            break;
        }
    } while (1);
}

CUIFrameWork::CUIFrameWork() {
    m_pDataMgr = NULL;
    m_pMsgMgr = NULL;
    m_pmsgThreadID = NULL;

    m_eSrcType = DATA_SRC_TBUS;
    m_eDstType = DATA_SRC_TBUS;
    memset(m_szVideoPath, 0, sizeof(m_szVideoPath));

    m_poCtx = NULL;
    m_nFrameCnt = -1;
    // 默认为运行AI SDK模式
    m_eRunMode = SDK_TEST;
}

CUIFrameWork::~CUIFrameWork() {
    if (NULL != m_pmsgThreadID) {
        // 关闭线程
        TqcCloseThread(m_pmsgThreadID);
    }

    if (NULL != m_poCtx) {
        delete m_poCtx;
        m_poCtx = NULL;
    }
}

bool CUIFrameWork::Initialize(const char *pszRootPath, const char *pszUserPath) {
    // 加载平台配置文件(cfg/platform/UI.ini)
    bool bRst = LoadPlatfromConfig(pszRootPath);

    if (!bRst) {
        LOGE("load platform config failed");
        return false;
    }

    // 加载游戏配置文件(cfg/task/ui/UIConfig.json)
    bRst = LoadTaskConfig(pszUserPath);
    if (!bRst) {
        LOGE("load task config failed");
        return false;
    }

    // 初始化识别器（大厅识别器，开始识别器，结束识别器，弹框UI识别器）
    bRst = InitRecognizer(pszUserPath, UI_TASK_CFG_FILE);
    if (!bRst) {
        LOGE("init recognize failed");
        return false;
    }

    // 初始化消息管理模块
    bRst = InitMsgMgr(pszRootPath);
    if (!bRst) {
        LOGE("init message manager failed, please check");
        return false;
    }

    // 初始化数据管理模块
    bRst = InitDataMgr();
    if (!bRst) {
        LOGE("init data manager failed, please check");
        return false;
    }

    // 初始化执行动作模块
    bRst = CAction::getInstance()->Initialize(m_eRunMode, pszRootPath);
    if (!bRst) {
        LOGE("init action failed, please check");
        return false;
    }

    // 创建并启动收消息的线程
    m_pmsgThreadID = TqcOsCreateThread(reinterpret_cast<void*>(RunMsgThread),
        reinterpret_cast<void*>(&m_eRunMode));
    if (NULL == m_pmsgThreadID) {
        LOGE("create thread failed, please check");
        return false;
    }

    // Context 初始维护的状态为大厅状态
    m_poCtx = new CContext(CHallState::getInstance());
    return true;
}

int CUIFrameWork::Run() {
    // 向MC注册
    bool bRst = RegisterToMC();

    if (!bRst) {
        LOGE("register to MC failed");
        return -1;
    }

    switch (m_eRunMode) {
    case SDK_TEST:
        LOGI("================please check, run with AI SDK mode================");
        break;

    case VIDEO_TEST:
        LOGI("================please check, run with VIDEO TEST mode================");
        break;

    case IMG_TEST:
        LOGI("================please check, run with IMG TEST  mode================");
        break;

    case SDKTOOL_TEST:
        LOGI("================please check, run with SDK TOOL TEST  mode================");
        break;
    }

    // 循环收帧，处理
    while (!g_bExit) {
        // 获取一帧图像,如果收不到图像帧，则退出
        cv::Mat oFrame;
        if (!m_pDataMgr->GetNextFrame(&oFrame)) {
            break;
        }

        // 如果收到的图像帧无效则退出
        if (oFrame.empty()) {
            LOGE("frame is empty");
            break;
        }
        LOGI("recv frame width %d, height %d", oFrame.cols, oFrame.rows);
        // 构造输入参数(frame, seq, frameCount)
        g_uiFrame = oFrame;
        tagFrameContext stFrameCtx;
        stFrameCtx.oFrame = oFrame;
        stFrameCtx.nFrameSeq = m_pDataMgr->GetFrameSeq();
        m_nFrameCnt++;
        stFrameCtx.nFrameCount = m_nFrameCnt;
        LOGI("recv frame data, frameIndex=%d", stFrameCtx.nFrameSeq);

        // 处理图像帧，并在其内部维护状态的改变
        m_poCtx->Process(stFrameCtx);
    }

    // 向MC反注册
    bRst = UnRegisterFromMC();
    if (!bRst) {
        LOGE("un register from MC failed");
        return -1;
    }

    return 0;
}

void CUIFrameWork::Release() {
}

void CUIFrameWork::SetTestMode(ETestMode eTestMode) {
    // 设置运行模式，一般由外部调用
    m_eRunMode = eTestMode;
}

bool CUIFrameWork::InitDataMgr() {
    // 检查输入参数的合法性
    if (m_pDataMgr == NULL) {
        LOGE("There is invalid pointer of pData");
        return false;
    }

    // 数据源为tbus
    if (DATA_SRC_TBUS == m_eSrcType) {
        return m_pDataMgr->InitializeFromData(m_eSrcType, m_eDstType, NULL);
    } else if (DATA_SRC_VIDEO == m_eSrcType) {
        return m_pDataMgr->InitializeFromData(m_eSrcType, m_eDstType, &m_szVideoPath);
    } else if (DATA_SRC_PICTURE == m_eSrcType) {
        return m_pDataMgr->InitializeFromData(m_eSrcType, m_eDstType, &m_stPicParams);
    }

    return true;
}

bool CUIFrameWork::InitMsgMgr(const char* pszUserCfgPath) {
    stTBUSInitParams stTBusParam;
    bool             bRes = false;

    // 检查输入参数的合法性
    if (NULL == m_pMsgMgr) {
        LOGE("There is invalid pointer of pMsgMgr");
        return false;
    }

    char tbusCfgFile[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(tbusCfgFile, TQC_PATH_STR_LEN, "%s/%s", pszUserCfgPath, TBUS_CONFIG_FILE);

    char szUIAddr[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(szUIAddr, TQC_PATH_STR_LEN, "%s", UI_TBUS_ADDR_NAME);

    // 读取tbus配置文件
    std::map<std::string, std::string> mapValue;
    std::string                        strconffile(tbusCfgFile);
    bool                               bRst = ReadTbusCfgFile(tbusCfgFile, "BusConf", &mapValue);
    if (bRst) {
        memcpy(stTBusParam.szConfigFile, tbusCfgFile, strlen(tbusCfgFile));
        stTBusParam.mapStrAddr = mapValue;
        stTBusParam.strSelfAddr = szUIAddr;
        // 初始化消息管理模块
        bRes = m_pMsgMgr->Initialize(reinterpret_cast<void*>(&stTBusParam));
        if (!bRes) {
            LOGE("cdata manager initialize faild");
            return false;
        }

        return true;
    } else {
        LOGE("read config file failed");
        return false;
    }
}

bool CUIFrameWork::InitRecognizer(const char *pszRootPath, const char *pszUICfgPath) {
    // 初始化大厅配置
    CHallCfg *pHallCfg = CHallCfg::getInstance();
    bool     bRst = pHallCfg->Initialize(pszRootPath, pszUICfgPath);

    if (!bRst) {
        LOGE("read hall cfg failed");
        return false;
    }

    // 初始化大厅识别器
    CHallReg *pHallReg = CHallReg::getInstance();
    bRst = pHallReg->Initialize(pHallCfg);
    if (!bRst) {
        LOGE("initialize hall reg failed");
        return false;
    }

    // 初始化游戏开始配置
    CGameStartCfg *pGameStartCfg = CGameStartCfg::getInstance();
    bRst = pGameStartCfg->Initialize(pszRootPath, pszUICfgPath);
    if (!bRst) {
        LOGE("read game start cfg failed");
        return false;
    }

    // 初始化游戏开始识别器
    CGameStartReg *pGameStartReg = CGameStartReg::getInstance();
    bRst = pGameStartReg->Initialize(pGameStartCfg);
    if (!bRst) {
        LOGE("initialize game start reg failed");
        return false;
    }

    // 初始化游戏结束配置
    CGameOverCfg *pGameOvercfg = CGameOverCfg::getInstance();
    bRst = pGameOvercfg->Initialize(pszRootPath, pszUICfgPath);
    if (!bRst) {
        LOGE("read game over cfg failed");
        return false;
    }

    // 初始化游戏结束识别器
    CGameOverReg *pGameOverReg = CGameOverReg::getInstance();
    bRst = pGameOverReg->Initialize(pGameOvercfg);
    if (!bRst) {
        LOGE("initialize game over reg failed");
        return false;
    }

    // 初始化弹框UI的配置
    CPOPUICfg *pPOPUICfg = CPOPUICfg::getInstance();
    bRst = pPOPUICfg->Initialize(pszRootPath, pszUICfgPath);
    if (!bRst) {
        LOGE("read pop ui cfg failed");
        return false;
    }

    // 初始化弹框UI的识别器
    CPOPUIReg *pPoPUIReg = CPOPUIReg::getInstance();
    bRst = pPoPUIReg->Initialize(pPOPUICfg);
    if (!bRst) {
        LOGE("initialize pop ui cfg failed");
        return false;
    }

    return true;
}

bool CUIFrameWork::ReadTbusCfgFile(std::string strConfigFileName,
    std::string strSectionName, std::map<std::string, std::string> *pMapValues) {
    std::ifstream inConfigFile(strConfigFileName.c_str());

    // 检查文件是否能正常打开
    if (!inConfigFile.is_open()) {
        LOGE("open config file %s failed", strConfigFileName.c_str());
        return false;
    }

    // 文件指针定位到文件起始位
    inConfigFile.seekg(0, std::ios::beg);

    // 8*1024,1行的最大
    const int LINE_BUFFER_LEN = 8192;
    char szOneLine[LINE_BUFFER_LEN + 1];
    char szKey[LINE_BUFFER_LEN + 1];
    char szString[LINE_BUFFER_LEN + 1];
    szOneLine[LINE_BUFFER_LEN] = '\0';
    szKey[LINE_BUFFER_LEN] = '\0';
    szString[LINE_BUFFER_LEN] = '\0';

    bool bFind = false;

    while (inConfigFile) {
        inConfigFile.getline(szOneLine, LINE_BUFFER_LEN);
        // 整理
        StrTrim(szOneLine);

        // 注释
        if (szOneLine[0] == ';' || szOneLine[0] == '#') {
            continue;
        }

        if (false == bFind) {
            // 找匹配的Section
            if (szOneLine[0] == '[' && szOneLine[strlen(szOneLine) - 1] == ']') {
                // 去掉'[',']'
                memmove(szOneLine, szOneLine + 1, strlen(szOneLine) - 1);
                szOneLine[strlen(szOneLine) - 2] = '\0';
                // 整理
                StrTrim(szOneLine);

                if (StrCaseIgnoreCmp(szOneLine, strSectionName.c_str()) == 0) {
                    bFind = true;
                } else {
                    bFind = false;
                }
            }
        }


        // 找key
        if (bFind == true) {
            char *str = strstr(szOneLine, "=");

            if (str != NULL) {
                char *snext = str + 1;
                *str = '\0';
                strncpy(szKey, szOneLine, LINE_BUFFER_LEN);
                strncpy(szString, snext, LINE_BUFFER_LEN);
                std::string strKey(szKey);
                std::string strValue(szString);
                pMapValues->insert(std::pair<std::string, std::string>(szKey, strValue));
                printf("strKey %s\n", strKey.c_str());
                printf("strValue %s \n", strValue.c_str());
            }
        }
    }

    return true;
}

bool CUIFrameWork::SetDataMgr(CDataManager *pDataMgr) {
    // 检查输入参数的合法性
    if (NULL == pDataMgr) {
        LOGE("input pDataMgr is NULL, please check");
        return false;
    }
    // 设置数据管理器
    m_pDataMgr = pDataMgr;
    return true;
}

bool CUIFrameWork::SetMsgMgr(CPBMsgManager *pMsgMgr) {
    // 检查输入参数的合法性
    if (NULL == pMsgMgr) {
        LOGE("input MsgMgr is NULL, please check");
        return false;
    }

    // 设置消息管理器
    m_pMsgMgr = pMsgMgr;
    return true;
}

bool CUIFrameWork::RegisterToMC() {
    // 检查输入参数的合法性
#if !NO_TBUS
    if (m_pMsgMgr == NULL) {
        LOGE("There is no msg manager.");
        return false;
    }

    tagUIState  state;
    std::string strState;

    // 打包注册协议包
    // std::string strState;
    tagMessage         uiMsg;
    tagServiceRegister *pUIState = uiMsg.mutable_stserviceregister();

    pUIState->set_eregistertype(PB_SERVICE_REGISTER);
    pUIState->set_eservicetype(PB_SERVICE_TYPE_UI);

    uiMsg.set_emsgid(MSG_SERVICE_REGISTER);
    uiMsg.SerializeToString(&strState);

    // 发送注册消息
    bool bRst = m_pMsgMgr->SendData(reinterpret_cast<void*>(const_cast<char*>(strState.c_str())),
        strState.length(), PEER_MC);
    if (!bRst) {
        LOGE("Register UI failed.");
        return bRst;
    } else {
        LOGI("Register UI process to MC.");
    }

    // 打包初始化消息包
    tagMessage    uiTaskMsg;
    tagTaskReport *pUITask = uiTaskMsg.mutable_sttaskreport();

    pUITask->set_etaskstatus(PB_TASK_INIT_SUCCESS);

    uiTaskMsg.set_emsgid(MSG_TASK_REPORT);
    uiTaskMsg.SerializeToString(&strState);

    // 发送初始化成功消息
    bRst = m_pMsgMgr->SendData(reinterpret_cast<void*>(const_cast<char*>(strState.c_str())),
        strState.length(), PEER_MC);
    if (!bRst) {
        LOGE("Report UI status failed.");
        return bRst;
    } else {
        LOGI("UI initialization is OK.");
    }
#endif

    LOGI("Register UI process to MC OK.");
    return true;
}

bool CUIFrameWork::UnRegisterFromMC() {
#if !NO_TBUS
    tagUIState  state;
    std::string strState;

    // 打包反注册协议包
    tagMessage         uiMsg;
    tagServiceRegister *pUIState = uiMsg.mutable_stserviceregister();

    pUIState->set_eregistertype(PB_SERVICE_UNREGISTER);
    pUIState->set_eservicetype(PB_SERVICE_TYPE_UI);

    uiMsg.set_emsgid(MSG_SERVICE_REGISTER);
    uiMsg.SerializeToString(&strState);

    // 发送反注册消息
    bool bRst = m_pMsgMgr->SendData(reinterpret_cast<void*>(const_cast<char*>(strState.c_str())),
        strState.length(), PEER_MC);
    if (!bRst) {
        LOGE("UnRegister UI failed.");
        return bRst;
    }
#endif  // !NO_TBUS

    LOGI("Unregister UI process from MC.");
    return true;
}

bool CUIFrameWork::LoadLogCfg(CIniConfig *poCfg) {
    // 检查输入参数的合法性
    if (NULL == poCfg) {
        LOGE("platform config is NULL");
        return false;
    }

    // 读取日志路径
    char pLogPath[TQC_PATH_STR_LEN] = { 0 };
    if (-1 == poCfg->getPrivateStr("LOG", "Path", DEFAULT_UI_LOG_FILE, pLogPath,
        TQC_PATH_STR_LEN)) {
        LOGE("get log path failed: %s", pLogPath);
        return false;
    }

    // 读取日志级别
    char pLogLevel[TQC_PATH_STR_LEN] = { 0 };
    if (-1 == poCfg->getPrivateStr("LOG", "Level", "ERROR", pLogLevel, TQC_PATH_STR_LEN)) {
        LOGE("get log level failed: %s", pLogLevel);
        return false;
    }

    // 解析日志级别(DEBUG|INFO|WARN|ERROR)
    std::string strLogLevel(pLogLevel);
    int         nLogLevel = FACE_ERROR;
    if (strLogLevel == "DEBUG") {
        g_logLevel = FACE_DEBUG;
    } else if (strLogLevel == "INFO") {
        g_logLevel = FACE_INFO;
    } else if (strLogLevel == "WARN") {
        g_logLevel = FACE_WARNING;
    } else if (strLogLevel == "ERROR") {
        g_logLevel = FACE_ERROR;
    } else {
        LOGW("log level is wrong");
    }

    // 创建日志
    bool bRst = CreateLog(pLogPath);
    if (!bRst) {
        LOGE("create log failed");
        return false;
    }

    return true;
}

bool CUIFrameWork::LoadDebugCfg(CIniConfig *poCfg) {
    // 读取调试配置
    bool bTestFlag = poCfg->getPrivateBool("DEBUG", "Flag", 0);

    if (bTestFlag) {
        std::string strTestMode;
        char        pTestMode[64];
        if (-1 == poCfg->getPrivateStr("DEBUG", "Mode", "video", pTestMode, 64)) {
            LOGW("key of 'Mode' is needed in 'DEBUG'");
            return false;
        }

        strTestMode = pTestMode;
        // 运行模式: SDKTool, video, image
        if ("video" == strTestMode) {
            // 读取"video"配置:视频文件路径
            char pTestVideo[64] = { 0 };
            if (-1 == poCfg->getPrivateStr("DEBUG", "Video", "./test/sendMC.mp4", pTestVideo, 64)) {
                LOGW("get video failed %s", pTestVideo);
                return false;
            }

            int nRst = -1;
#ifdef LINUX
            nRst = access(pTestVideo, 0);
#elif WINDOWS
            nRst = _access(pTestVideo, 0);
#endif
            if (-1 == nRst) {
                // 判断文件是否存在
                LOGE("video file %s not exists", pTestVideo);
                return false;
            } else {
                memcpy(m_szVideoPath, pTestVideo, strlen(pTestVideo));
                // 设置运行模式为视频模式
                m_eSrcType = DATA_SRC_VIDEO;
            }
        } else if ("image" == strTestMode) {
            // 读取"image"配置: 文件或文件夹名称，前缀，后缀，开始序号，结束序号
            memset(m_stPicParams.filePath, 0, sizeof(m_stPicParams.filePath));
            memset(m_stPicParams.fileName, 0, sizeof(m_stPicParams.fileName));
            memset(m_stPicParams.fileSuffix, 0, sizeof(m_stPicParams.fileSuffix));
            m_stPicParams.nStart = 0;
            m_stPicParams.nEnd = 0;

            if (-1 == poCfg->getPrivateStr("DEBUG", "ImageDir", "./test/", m_stPicParams.filePath,
                sizeof(m_stPicParams.filePath))) {
                LOGW("get DEBUG|ImagesDir value failed please check");
                return false;
            }

            if (-1 == poCfg->getPrivateStr("DEBUG", "PreName", "", m_stPicParams.fileName,
                sizeof(m_stPicParams.fileName))) {
                LOGW("get DEBUG|PreName value failed please check");
                return false;
            }

            if (-1 == poCfg->getPrivateStr("DEBUG", "Suffix", "jpg", m_stPicParams.fileSuffix,
                sizeof(m_stPicParams.fileSuffix))) {
                LOGW("get DEBUG|Suffix value failed please check");
                return false;
            }

            char szBuf[TQC_PATH_STR_LEN] = { 0 };
            if (-1 == poCfg->getPrivateStr("DEBUG", "Start", "0", szBuf,
                sizeof(szBuf))) {
                LOGW("get DEBUG|Start value failed please check");
                return false;
            }

            m_stPicParams.nStart = atoi(szBuf);

            memset(szBuf, 0, sizeof(szBuf));
            if (-1 == poCfg->getPrivateStr("DEBUG", "End", "0", szBuf,
                sizeof(szBuf))) {
                LOGW("get DEBUG|End value failed please check");
                return false;
            }

            m_stPicParams.nEnd = atoi(szBuf);
            // 设置运行模式为图片模式
            m_eSrcType = DATA_SRC_PICTURE;
        } else if ("SDKTool" == strTestMode) {
            // 设置运行模式为SDKTool模式
            m_eRunMode = SDKTOOL_TEST;
        }
    }

    return true;
}

bool CUIFrameWork::LoadPlatfromConfig(const char* pszUserCfgPath) {
    // 读取平台配置文件
    CIniConfig oPlatformCfg;
    char szPath[256];
    sprintf(szPath, "%s/%s", pszUserCfgPath, UI_PLATFORM_CFG);
    int        nRst = oPlatformCfg.loadFile(szPath);

    if (nRst != 0) {
        LOGE("load file %s failed", szPath);
        return false;
    }

    // 读取平台配置中的日志配置模块
    bool bRst = LoadLogCfg(&oPlatformCfg);
    if (!bRst) {
        LOGE("load LOG config failed");
        return false;
    }

    // 读取平台配置中的调试模块
    bRst = LoadDebugCfg(&oPlatformCfg);
    if (!bRst) {
        LOGE("load DEBUG config failed");
        return false;
    }

    return true;
}

bool CUIFrameWork::LoadTaskConfig(const char *pszRootPath) {
    // 检查输入参数的合法性
    if (NULL == pszRootPath) {
        LOGE("input param szRootPath is NULL, please check");
        return false;
    }

    CJsonConfig *pConfig = new CJsonConfig();
    if (NULL == pConfig) {
        LOGE("new json config failed");
        return false;
    }

    char szPath[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(szPath, TQC_PATH_STR_LEN, "%s/%s", pszRootPath, UI_TASK_CFG_FILE);

    // 检查游戏UI配置文件是否存在
    if (!IsFileExist(szPath)) {
        LOGE("file %s is not exist", szPath);
        delete pConfig;
        pConfig = NULL;
        return false;
    }

    // 加载游戏UI配置文件
    bool bRst = pConfig->loadFile(szPath);
    if (!bRst) {
        LOGE("Load file %s failed", szPath);
        delete pConfig;
        pConfig = NULL;
        return false;
    }

    LOGI("Load file %s success", szPath);

    // 读取 "debugWithSDKTools" 配置项
    bool bCheckOpen = false;
    int  nLen = 0;
    bRst = pConfig->GetConfValue(
        "debugWithSDKTools", reinterpret_cast<char*>(&bCheckOpen), &nLen, DATA_BOOL);
    if (bRst && bCheckOpen) {
        // 如果读取成功，且为true设置当前的运行模式为 SDKTOOL_TEST
        m_eRunMode = SDKTOOL_TEST;
    }

    delete pConfig;
    pConfig = NULL;

    return true;
}
bool CUIFrameWork::CreateLog(const char *strProgName) {
    // 初始化日志模块
    CLog *pLog = CLog::getInstance();

    // 创建命名为strProgName的日志文件，默认日志级别是7，即(ERROR/WARN/RUN)都开启
    // 通过g_logLevel控制日志级别
    int  nResult = pLog->init(strProgName, 7);

    if (nResult) {
        LOGE("Create log file failed: %s.", strProgName);
        return false;
    }
    return true;
}
