/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "UI/Src/UICfg/POPUICfg.h"


CPOPUICfg::CPOPUICfg()
{
    m_bCheckCloseWhenPlaying = false;
    m_nCloseIconCounterMax   = 0;
    m_nCloseIconUICounterMax = 0;
    m_uiCloseIcons.clear();
    m_uiDeviceIcons.clear();
}


CPOPUICfg::~CPOPUICfg()
{}


bool CPOPUICfg::Initialize(const char *pszRootDir, const char *pszCfgFile)
{
    // check parameter valid
    if (NULL == pszRootDir || NULL == pszCfgFile)
    {
        LOGE("root dir or UIConfig dir is NULL, please check");
        return false;
    }

    int         nLen                  = 0;
    CJsonConfig *pConfig              = new CJsonConfig;
    bool        bCheckOpen            = false;
    int         nValue                = 0;
    char        buf[TQC_PATH_STR_LEN] = {0};
    // Cannot create json config parser.
    if (pConfig == NULL)
    {
        LOGE("Cannot create json config parser.");
        return false;
    }

    char szPath[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(szPath, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, pszCfgFile);
    // Check if UI config file exists.
    FILE *pFile = fopen(szPath, "r");
    if (pFile == NULL)
    {
        LOGE("UI states definition file is not exist: %s", szPath);
        delete pConfig;
        return false;
    }

    fclose(pFile);

    // Load UI config file.
    bool bRst = pConfig->loadFile(szPath);
    if (!bRst)
    {
        LOGE("Load file %s failed", szPath);
        delete pConfig;
        return false;
    }

    // Check if we should check pop UI when playing game:"checkCloseIconsWhenPlaying"
    // m_bCheckCloseWhenPlaying = false;
    bRst = pConfig->GetConfValue("checkCloseIconsWhenPlaying", reinterpret_cast<char*>(&bCheckOpen),
                                 &nLen, DATA_BOOL);
    if (!bRst)
    {
        m_bCheckCloseWhenPlaying = true;
    }
    else
    {
        m_bCheckCloseWhenPlaying = bCheckOpen;
    }

    // Get close icon check interval:"closeIconsCounter"
    bRst = pConfig->GetConfValue("closeIconsCounter", reinterpret_cast<char*>(&nValue), &nLen, DATA_INT);
    if (!bRst)
    {
        m_nCloseIconCounterMax   = GAME_UI_DIALOG_CHECK_INTERVAL_AI;
        m_nCloseIconUICounterMax = GAME_UI_DIALOG_CHECK_INTERVAL_UI;
    }
    else
    {
        m_nCloseIconCounterMax   = nValue;
        m_nCloseIconUICounterMax = nValue / 8;
    }

    // Check if interval is valid. If not, use the default value.
    if (m_nCloseIconCounterMax < GAME_UI_DIALOG_CHECK_INTERVAL_AI)
    {
        m_nCloseIconCounterMax = GAME_UI_DIALOG_CHECK_INTERVAL_AI;
    }

    if (m_nCloseIconUICounterMax < GAME_UI_DIALOG_CHECK_INTERVAL_UI)
    {
        m_nCloseIconUICounterMax = GAME_UI_DIALOG_CHECK_INTERVAL_UI;
    }

    // If enable this option, we do not check close icon when playing game.
    if (m_bCheckCloseWhenPlaying)
    {
        LOGI("Enable check of close icon when playing game.");
    }
    else
    {
        LOGI("Disable check of close icon when playing game.");
    }

    bRst = ReadGameCloseIcons(pszRootDir, pConfig);
    bRst = ReadDeviceCloseIcons(pszRootDir, pConfig);
    // if (bRst == false)
    // {
    //   return false;
    // }
    return true;
}

bool CPOPUICfg::ReadDeviceCloseIcons(const char *pszRootDir, CJsonConfig *pConfig)
{
    // Check if we should detect Devices Icons when playing game.
    // Check if we should detect Devices Icons when playing game.
    char buf[TQC_PATH_STR_LEN] = {0};
    int  nLen                  = 0;
    bool bCheckOpen            = false;

    // get size of configure: "devicesCloseIcons"
    int nSize = pConfig->GetArraySize("devicesCloseIcons");

    // Parse each close icon.
    for (int i = 0; i < nSize; i++)
    {
        tagUIState uiState;

        // uiState.bUseTempMatch = true;
        uiState.nTemplate = 1;
        uiState.tempOp    = UI_TEMPLATE_AND;

        // Description of UI state.
        // This will be printed if being matched.
        memset(buf, 0, TQC_PATH_STR_LEN);
        bool bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "desc", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons desc");
            delete pConfig;
            return false;
        }

        // ID of each close icon that cannot be duplicated.
        memset(uiState.strStateName, 0, TQC_PATH_STR_LEN);
        memcpy(uiState.strStateName, buf, nLen);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "id"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "id", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons id");
            delete pConfig;
            return false;
        }

        // Close icon uses template match algorithm. we should set x, y, width and height
        // of the sample in the image.
        uiState.nId = atoi(buf);

        // "actionSleepTimeMs"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "actionSleepTimeMs", buf, &nLen, DATA_STR);
        if (bRst)
        {
            uiState.nActionSleepTimeMs = atoi(buf);
        }

        memset(buf, 0, TQC_PATH_STR_LEN);
        // "height"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "height", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons height");
            delete pConfig;
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleH = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "width"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "width", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons width");
            delete pConfig;
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleW = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "x"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "x", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons x");
            delete pConfig;
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleX = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "y"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "y", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons y");
            delete pConfig;
            return false;
        }

        // Load sample image from the path of image.
        uiState.szTemplState[0].stTemplParam.nSampleY = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "imgPath"
        bRst = pConfig->GetArrayValue("devicesCloseIcons", i, "imgPath", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. devicesCloseIcons imgPath");
            delete pConfig;
            return false;
        }

        // There is no action, because devices icon always uses click action.

        memset(uiState.strSampleFile, 0, TQC_PATH_STR_LEN);
        SNPRINTF(uiState.strSampleFile, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, buf);
        // memcpy(uiState.strSampleFile, buf, nLen);
        LOGI("load POPUI(Device) %d configure", uiState.nId);
        m_uiDeviceIcons.push_back(uiState);
    }

    return true;
}

bool CPOPUICfg::ReadGameCloseIcons(const char *pszRootDir, CJsonConfig *pConfig)
{
    char buf[TQC_PATH_STR_LEN] = {0};
    int  nLen                  = 0;
    // get size of configure "closeIcons"
    int  nSize                 = pConfig->GetArraySize("closeIcons");

    // Parse each close icon.
    for (int i = 0; i < nSize; i++)
    {
        tagUIState uiState;

        // uiState.bUseTempMatch = true;
        uiState.nTemplate = 1;
        uiState.tempOp    = UI_TEMPLATE_AND;

        // Description of UI state.
        // This will be printed if being matched.
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "desc"
        bool bRst = pConfig->GetArrayValue("closeIcons", i, "desc", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons desc");
            return false;
        }

        // ID of each close icon that cannot be duplicated.
        memset(uiState.strStateName, 0, TQC_PATH_STR_LEN);
        memcpy(uiState.strStateName, buf, nLen);

        memset(buf, 0, TQC_PATH_STR_LEN);
        // "id"
        bRst = pConfig->GetArrayValue("closeIcons", i, "id", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons id");
            return false;
        }
        uiState.nId = atoi(buf);

        // "actionSleepTimeMs"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "actionSleepTimeMs", buf, &nLen, DATA_STR);
        if (bRst)
        {
            uiState.nActionSleepTimeMs = atoi(buf);
        }

        // Close icon uses template match algorithm. we should set x, y, width and height
        // of the sample in the image.
        // "height"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "height", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons height");
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleH = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        // "width"
        bRst = pConfig->GetArrayValue("closeIcons", i, "width", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons width");
            return false;
        }
        uiState.szTemplState[0].stTemplParam.nSampleW = atoi(buf);

        // "x"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "x", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons x");
            return false;
        }
        uiState.szTemplState[0].stTemplParam.nSampleX = atoi(buf);

        // "y"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "y", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons y");
            return false;
        }
        // Load sample image from the path of image.
        uiState.szTemplState[0].stTemplParam.nSampleY = atoi(buf);

        // "imgPath"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "imgPath", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("Get state description failed. closeIcons imgPath");
            return false;
        }

        memset(uiState.strSampleFile, 0, TQC_PATH_STR_LEN);
        // memcpy(uiState.strSampleFile, buf, nLen);
        SNPRINTF(uiState.strSampleFile, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, buf);

        // check sample file valid
        cv::Mat oImage = cv::imread(uiState.strSampleFile);
        if (!oImage.empty())
        {
            uiState.sampleImg = oImage;
        }

        // "templateThreshold"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("closeIcons", i, "templateThreshold", buf, &nLen, DATA_STR);
        if (bRst)
        {
            uiState.szTemplState[0].stTemplParam.fThreshold = atof(buf);
        }

        // There is no action, because close icon always uses click action.

        LOGI("load POPUI(Game) %d configure", uiState.nId);
        m_uiCloseIcons.push_back(uiState);
    }
    return true;
}

UIStateArray CPOPUICfg::GetGameCloseIcons()
{
    return m_uiCloseIcons;
}

UIStateArray CPOPUICfg::GetDeviceCloseIcons()
{
    return m_uiDeviceIcons;
}

bool CPOPUICfg::CheckWhenPlaying()
{
    return m_bCheckCloseWhenPlaying;
}

int CPOPUICfg::GetUICounterMax()
{
    return m_nCloseIconUICounterMax;
}

int CPOPUICfg::GetRunCounterMax()
{
    return m_nCloseIconCounterMax;
}
