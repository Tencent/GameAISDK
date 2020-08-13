/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <algorithm>
#include "UI/Src/UICfg/CommUICfg.h"

CCommUICfg::CCommUICfg()
{
    m_oVecState.clear();
    m_bOldCfg = false;
}

CCommUICfg::~CCommUICfg()
{}

bool CCommUICfg::Initialize(const char *pszRootDir, const char *pszCftPath, CJsonConfig *pConfig)
{
    // check parameters
    if (pConfig == NULL)
    {
        LOGE("Cannot create json config parser.");
        return false;
    }

    // check file exist
    char szPath[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(szPath, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, pszCftPath);
    if (!IsFileExist(szPath))
    {
        LOGE("file is not exist");
        return false;
    }

    // Load configure file.
    bool bRst = pConfig->loadFile(szPath);
    if (!bRst)
    {
        LOGE("Load file %s failed", szPath);
        return false;
    }

    // read configure
    LOGI("Load file %s success", szPath);
    bRst = ReadCfg(pszRootDir, pConfig);
    return bRst;
}

//
// Get template info from configure file.
//
bool CCommUICfg::ReadTemplateFromJson(const int nIndex, const int nTemplate,
                                      tagUIState *pstUIState, CJsonConfig *pConfig)
{
    // check parameters
    if (NULL == pstUIState)
    {
        LOGE("input point to UIState is NULL");
        return false;
    }

    char buf[TQC_PATH_STR_LEN] = {0};
    char key[TQC_PATH_STR_LEN] = {0};
    int  nLen                  = 0;
    bool bRst                  = false;

    // For consistent with the old format.
    if (nTemplate <= 0)
    {
        return true;
    }
    else if (nTemplate == 1)
    {
        // For template, we should set x, y, width and height of sample in
        // the image.
        // pUIState->bUseTempMatch = true;

        // For single template image, we use the default operator.
        pstUIState->tempOp = UI_TEMPLATE_AND;
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "x", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates x: %d", nIndex);
            // delete pConfig;
            return false;
        }

        pstUIState->szTemplState[0].stTemplParam.nSampleX = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "y", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates y: %d", nIndex);
            // delete pConfig;
            return false;
        }

        pstUIState->szTemplState[0].stTemplParam.nSampleY = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "w", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates w: %d", nIndex);
            // delete pConfig;
            return false;
        }

        pstUIState->szTemplState[0].stTemplParam.nSampleW = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "h", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates h: %d", nIndex);
            // delete pConfig;
            return false;
        }

        // We can search template in some region, not exact position of sample in
        // the image.
        pstUIState->szTemplState[0].stTemplParam.nSampleH = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "shift", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates shift: %d", nIndex);
            // delete pConfig;
            return false;
        }

        pstUIState->szTemplState[0].nShift = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "templateThreshold", buf, &nLen, DATA_STR);
        if (bRst)
        {
            pstUIState->szTemplState[0].stTemplParam.fThreshold = atof(buf);
        }
    }
    else
    {
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", nIndex, "templateOp", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates x: %d", nIndex);
            // delete pConfig;
            return false;
        }

        // All of the template images should be matched.
        if (strstr(buf, "and"))
        {
            pstUIState->tempOp = UI_TEMPLATE_AND;
        }
        // One of the template images is matched.
        else if (strstr(buf, "or"))
        {
            pstUIState->tempOp = UI_TEMPLATE_OR;
        }
        else
        {
            // Default template match operator is and
            pstUIState->tempOp = UI_TEMPLATE_AND;
        }

        // For template, we should set x, y, width and height of sample in the image.
        // pUIState->bUseTempMatch = true;
        for (int i = 0; i < nTemplate; i++)
        {
            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "x%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (!bRst)
            {
                LOGE("get state description failed. uiStates x: %d", nIndex);
                // delete pConfig;
                return false;
            }

            pstUIState->szTemplState[i].stTemplParam.nSampleX = atoi(buf);
            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "y%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (!bRst)
            {
                LOGE("get state description failed. uiStates y: %d", nIndex);
                // delete pConfig;
                return false;
            }

            pstUIState->szTemplState[i].stTemplParam.nSampleY = atoi(buf);
            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "w%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (!bRst)
            {
                LOGE("get state description failed. uiStates w: %d", nIndex);
                // delete pConfig;
                return false;
            }

            pstUIState->szTemplState[i].stTemplParam.nSampleW = atoi(buf);
            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "h%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (!bRst)
            {
                LOGE("get state description failed. uiStates h: %d", nIndex);
                // delete pConfig;
                return false;
            }

            // We can search template in some region, not exact position of sample in
            // the image.
            pstUIState->szTemplState[i].stTemplParam.nSampleH = atoi(buf);
            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "shift%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (!bRst)
            {
                LOGE("get state description failed. uiStates shift: %d", nIndex);
                // delete pConfig;
                return false;
            }

            memset(buf, 0, TQC_PATH_STR_LEN);
            memset(key, 0, TQC_PATH_STR_LEN);
            SNPRINTF(key, TQC_PATH_STR_LEN, "templateThreshold%d", (i + 1));
            bRst = pConfig->GetArrayValue("uiStates", nIndex, key, buf, &nLen, DATA_STR);
            if (bRst)
            {
                pstUIState->szTemplState[i].stTemplParam.fThreshold = atof(buf);
            }
        }
    }

    return true;
}
bool CCommUICfg::ReadDragCheckItem(const char *pszRootDir, const int nIndex,
                                   tagUIState *puiState, CJsonConfig *pConfig)
{
    // check parameters
    if (NULL == puiState)
    {
        LOGE("point to uiState is NULL");
        return false;
    }

    int  nLen;
    char buf[TQC_PATH_STR_LEN] = { 0 };

    memset(buf, 0, TQC_PATH_STR_LEN);
    bool bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionDir", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("Getting drag direction failed. uiStates action_dir: %d", nLen);
        // delete pConfig;
        return false;
    }

    // 0 for none, 1 for down, 2 for up, 3 for left, 4 for right
    if (strstr(buf, "down"))
        puiState->stDragCheckState.dragAction = 1;
    else if (strstr(buf, "up"))
        puiState->stDragCheckState.dragAction = 2;
    else if (strstr(buf, "left"))
        puiState->stDragCheckState.dragAction = 3;
    else if (strstr(buf, "right"))
        puiState->stDragCheckState.dragAction = 4;

    // Get start x position of drag operation.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "dragX", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get drag start x failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stDragPt.nPointX = atoi(buf);

    // Get start y position of drag operation.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "dragY", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get drag start y failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stDragPt.nPointY = atoi(buf);

    // Get length of drag operation by pixel.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "dragLen", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        puiState->stDragCheckState.dragLen = 80; // default is 80 pixels.
    }
    else
    {
        puiState->stDragCheckState.dragLen = atoi(buf);
    }

    // Get the count of max drag operation. We will count call of DoDragAndCheck.
    // If it exceeds the count of drag operation, we will change game state
    // to UI state.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "dragCount", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        puiState->stDragCheckState.dragCount = 400; // default is 400.
    }
    else
    {
        puiState->stDragCheckState.dragCount = atoi(buf);
    }

    // Get target image file.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "targetImg", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("Getting target image failed. uiStates action_dir: %d", nIndex);
        // delete pConfig;
        return false;
    }

    memset(puiState->stDragCheckState.strDragTargetFile, 0, TQC_PATH_STR_LEN);
    snprintf(puiState->stDragCheckState.strDragTargetFile, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, buf);
    cv::Mat oImage = cv::imread(puiState->stDragCheckState.strDragTargetFile);
    if (oImage.empty())
    {
        LOGE("UI %d read drage check image %s failed", puiState->nId, puiState->stDragCheckState.strDragTargetFile);
        return false;
    }

    puiState->stDragCheckState.targetImg[0] = oImage;
    // Get x position of target template image.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "targetX", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get target x failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stTargetRect.nPointX = atoi(buf);

    // Get y position of target template image.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "targetY", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get target y failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stTargetRect.nPointY = atoi(buf);

    // Get w position of target template image.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "targetW", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get target w failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stTargetRect.nWidth = atoi(buf);

    // Get h position of target template image.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "targetH", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get target h failed.");
        // delete pConfig;
        return false;
    }

    puiState->stDragCheckState.stTargetRect.nHeight = atoi(buf);

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "templateThreshold", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        puiState->stDragCheckState.fDragThreshold = GAME_TEMPLATE_THRESHOLD;
    }
    else
    {
        puiState->stDragCheckState.fDragThreshold = atoi(buf);
    }

    // uiState.tempOp = UI_TEMPLATE_AND;
    // uiState.nTemplate = 1;
    // uiState.szTemplState[0].stTemplParam.nSampleX = uiState.stDragCheckState.stTargetRect.nPointX;
    // uiState.szTemplState[0].stTemplParam.nSampleY = uiState.stDragCheckState.stTargetRect.nPointY;
    // uiState.szTemplState[0].stTemplParam.nSampleW = uiState.stDragCheckState.stTargetRect.nWidth;
    // uiState.szTemplState[0].stTemplParam.nSampleH = uiState.stDragCheckState.stTargetRect.nHeight;
    // uiState.actionType = UI_ACTION_DRAG_AND_CHECK;
    puiState->actionType = UI_ACTION_DRAG_AND_CHECK;
    // tagTmpl stTmpl;
    // stTmpl.oTmplImg = oImage;

    // CColorMatchParam oColorMatchParam;

    // oColorMatchParam.m_oVecTmpls.push_back(stTmpl);
    // uiState.stDragCheckState.targetMatch.Initialize(&oColorMatchParam)

    return true;
}

bool CCommUICfg::ReadClickItem(const int nIndex, tagUIState *puiState, CJsonConfig *pConfig)
{
    if (NULL == puiState)
    {
        LOGE("point to UIState is NULL");
        return false;
    }

    // (x, y) position of click.
    char buf[TQC_PATH_STR_LEN] = {0};
    int  nLen;

    puiState->actionType = UI_ACTION_CLICK;
    memset(buf, 0, TQC_PATH_STR_LEN);
    bool bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionX", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates actionX: %d", nIndex);
        // delete pConfig;
        return false;
    }

    puiState->stAction1.nActionX = atoi(buf);
    // uiState.x1Action = atoi(buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionY", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates actionY: %d", nIndex);
        // delete pConfig;
        return false;
    }

    puiState->stAction1.nActionY = atoi(buf);
    // uiState.y1Action = atoi(buf);

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionThreshold", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fActionThreshold = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdWPixel", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.nTmplExpdWPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdHPixel", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.nTmplExpdHPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdWRatio", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fROIExpdWRatio = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdHRatio", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fROIExpdHRatio = atof(buf);
    }

    LOGD("index: %d, id: %d, x: %d, y: %d, threshold: %f, EW: %d, EH: %d, EWRatio: %f, EHRatio: %f",
         nIndex, puiState->nId, puiState->stAction1.nActionX, puiState->stAction1.nActionY,
         puiState->stAction1.fActionThreshold, puiState->stAction1.nTmplExpdWPixel, puiState->stAction1.nTmplExpdHPixel,
         puiState->stAction1.fROIExpdWRatio, puiState->stAction1.fROIExpdHRatio);

    puiState->stAction2.nActionX = 0;
    puiState->stAction2.nActionY = 0;
    return true;
}

bool CCommUICfg::ReadDragItem(const int nIndex, tagUIState *puiState, CJsonConfig *pConfig)
{
    // check paramters
    if (NULL == puiState)
    {
        LOGE("point to UIState is NULL");
        return false;
    }

    puiState->actionType = UI_ACTION_DRAG;
    char buf[TQC_PATH_STR_LEN] = {0};
    int  nLen;
    // "actionX1"
    bool bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionX1", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get actionX1  failed. uiStates actionX1: %d", nIndex);
        delete pConfig;
        return false;
    }

    // uiState.x1Action = atoi(buf);
    puiState->stAction1.nActionX = atoi(buf);
    // "actionY1"
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionY1", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates actionY1: %d", nIndex);
        delete pConfig;
        return false;
    }
    puiState->stAction1.nActionY = atoi(buf);

    // actionThreshold1
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionThreshold1", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fActionThreshold = atof(buf);
    }

    // actionTmplExpdWPixel1
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdWPixel1", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.nTmplExpdWPixel = atoi(buf);
    }

    // actionTmplExpdHPixel1
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdHPixel1", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.nTmplExpdHPixel = atoi(buf);
    }

    // actionROIExpdWRatio1
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdWRatio1", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fROIExpdWRatio = atof(buf);
    }

    // actionROIExpdHRatio1
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdHRatio1", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction1.fROIExpdHRatio = atof(buf);
    }

    // actionX2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionX2", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates actionX2: %d", nIndex);
        delete pConfig;
        return false;
    }

    puiState->stAction2.nActionX = atoi(buf);
    // actionY2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionY2", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates actionY2: %d", nIndex);
        delete pConfig;
        return false;
    }

    puiState->stAction2.nActionY = atoi(buf);

    // actionThreshold2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionThreshold2", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction2.fActionThreshold = atof(buf);
    }

    // actionTmplExpdWPixel2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdWPixel2", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction2.nTmplExpdWPixel = atoi(buf);
    }

    // actionTmplExpdHPixel2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionTmplExpdHPixel2", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction2.nTmplExpdHPixel = atoi(buf);
    }

    // actionROIExpdWRatio2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdWRatio2", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction2.fROIExpdWRatio = atof(buf);
    }

    // actionROIExpdHRatio2
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionROIExpdHRatio2", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->stAction2.fROIExpdHRatio = atof(buf);
    }

    return true;
}


bool CCommUICfg::ReadScriptItem(const int nIndex, tagUIState *puiState, CJsonConfig *pConfig)
{
    // check paramters
    if (NULL == puiState)
    {
        LOGE("point to uiState is NULL");
        return false;
    }

    // process for "script" action
    puiState->actionType = UI_ACTION_SCRIPT;
    char buf[TQC_PATH_STR_LEN] = { 0 };
    int  nLen                  = 0;
    bool bRst                  = pConfig->GetArrayValue("uiStates", nIndex, "scriptPath", buf, &nLen, DATA_STR);
    memset(puiState->strScriptPath, 0, TQC_PATH_STR_LEN);
    memcpy(puiState->strScriptPath, buf, nLen);
    LOGI("read script path %s", puiState->strScriptPath);
    if (bRst)
    {
        Json::Value jsonUIStates = pConfig->GetJosnValue("uiStates");
        Json::Value jsonUITasks  = jsonUIStates[nIndex];
        puiState->jsonScriptParams["tasks"]  = jsonUITasks["tasks"];
        puiState->jsonScriptParams["extNum"] = puiState->nScrpitExtNum;
    }

    return true;
}


bool CCommUICfg::ReadCommItem(const char *pszRootDir, const int nIndex, tagUIState *puiState, CJsonConfig *pConfig)
{
    // check paramters
    if (NULL == puiState)
    {
        LOGE("point to uiState is NULL");
        return false;
    }

    int nTemplate = 0;

    char buf[TQC_PATH_STR_LEN] = { 0 };
    int  nLen                  = 0;
    // Description of UI state,This will be printed if being matched.
    bool bRst = pConfig->GetArrayValue("uiStates", nIndex, "desc", buf, &nLen, DATA_STR);

    if (!bRst)
    {
        LOGE("get state description failed. uiStates desc: %d", nIndex);
        delete pConfig;
        return false;
    }

    // ID of each UI state that cannot be duplicated.
    memset(puiState->strStateName, 0, TQC_PATH_STR_LEN);
    memcpy(puiState->strStateName, buf, nLen);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "id", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates id: %d", nIndex);
        delete pConfig;
        return false;
    }

    puiState->nId = atoi(buf);

    // ID of each UI state that cannot be duplicated.
    memset(puiState->strStateName, 0, TQC_PATH_STR_LEN);
    memcpy(puiState->strStateName, buf, nLen);

    // "delete"
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "delete", buf, &nLen, DATA_STR);
    if (bRst)
    {
        int nDel = atoi(buf);
        if (nDel == 1)
            puiState->bDelete = true;
    }

    // Match algorithm of UI state is feature poit match.
    // We will set minimun points that should be matched.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "keyPoints", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates keyPoints: %d", nIndex);
        delete pConfig;
        return false;
    }

    puiState->nMatched = atoi(buf);

    // Load sample image from the path of image.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "imgPath", buf, &nLen, DATA_STR);
    if (!bRst)
    {
        LOGE("get state description failed. uiStates imgPath: %d", nIndex);
        delete pConfig;
        return false;
    }

    // If feature point match cannot distinguish the same UI,
    // we can add a template match for some UI.
    memset(puiState->strSampleFile, 0, TQC_PATH_STR_LEN);
    SNPRINTF(puiState->strSampleFile, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst      = pConfig->GetArrayValue("uiStates", nIndex, "template", buf, &nLen, DATA_STR);
    nTemplate = atoi(buf);
    if (bRst && nTemplate > 0)
    {
        puiState->nTemplate = nTemplate;
        if (ReadTemplateFromJson(nIndex, nTemplate, puiState, pConfig) == false)
        {
            return false;
        }
    }

    // Set action during time.
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "during", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->nActionDuringTime = atoi(buf);
    }

    // "checkSameFrameCnt"
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "checkSameFrameCnt", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->nCheckSameFrameCnt = atoi(buf);
    }
    // "actionSleepTimeMs"
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("uiStates", nIndex, "actionSleepTimeMs", buf, &nLen, DATA_STR);
    if (bRst)
    {
        puiState->nActionSleepTimeMs = atoi(buf);
    }

    return true;
}


bool CCommUICfg::ReadCfg(const char *pszRootDir, CJsonConfig *pConfig)
{
    // check parameters
    if (NULL == pszRootDir || NULL == pConfig)
    {
        LOGE("input param is invalid, please check");
        return false;
    }

    int  nSize = pConfig->GetArraySize("uiStates");
    int  nLen  = 0;
    char buf[TQC_PATH_STR_LEN];
    bool bRst = false;

    // There is no UI state.
    if (nSize <= 0)
    {
        LOGE("There is no Hall UI state.");
        return true;
    }

    // Parse each UI state from json string.
    for (int i = 0; i < nSize; i++)
    {
        tagUIState uiState;
        bRst = ReadCommItem(pszRootDir, i, &uiState, pConfig);
        if (!bRst)
        {
            return false;
        }

        //  "actionType"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("uiStates", i, "actionType", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get state description failed. uiStates actionType: %d", i);
            return false;
        }

        // "click"
        if (strstr(buf, "click"))
        {
            bRst = ReadClickItem(i, &uiState, pConfig);
            if (!bRst)
            {
                return false;
            }
        }
        // "dragcheck"
        else if (strstr(buf, "dragcheck"))
        {
            // For drag-check operation, we do not set start point and end point.
            // But we should set the direction that drag will go to and the target
            // image.
            bRst = ReadDragCheckItem(pszRootDir, i, &uiState, pConfig);
            if (!bRst)
            {
                return false;
            }
        }
        // "drag"
        else if (strstr(buf, "drag"))
        {
            // For drag operation, we will set the start point and
            // end point. The drag is from (x1, y1) to (x2, y2).
            bRst = ReadDragItem(i, &uiState, pConfig);
            if (!bRst)
            {
                return false;
            }
        }
        // "script"
        else if (strstr(buf, "script"))
        {
            // process for "script" action
            bRst = ReadScriptItem(i, &uiState, pConfig);
            if (!bRst)
            {
                return false;
            }
        }

        // Load image from the path of sample image.
        // memset(buf, 0, TQC_PATH_STR_LEN);
        // SNPRINTF(buf, sizeof(buf), "%s/%s", pszRootDir, uiState.strSampleFile);
        cv::Mat origImg = cv::imread(uiState.strSampleFile);
        if (origImg.empty())
        {
            LOGE("Cannot open image file: %s", uiState.strSampleFile);
            return false;
        }

        uiState.sampleImg = origImg;
        // Saving the current UI state.
        // We will check each one of here to match some UI state.
        LOGI("load CommonUI: %d configure", uiState.nId);
        m_oVecState.push_back(uiState);
    }

    return true;
}

bool CCommUICfg::ReadStartState(std::vector<int> *pnVecStartID, CJsonConfig *pConfig)
{
    // check parameters
    if (NULL == pnVecStartID)
    {
        LOGE("pointer to start ID vector is None, please cechk");
        return false;
    }

    // "matchStartState"
    char buf[TQC_PATH_STR_LEN] = {0};
    int  nSize                 = pConfig->GetArraySize("matchStartState");
    int  nLen                  = 0;
    bool bRst                  = false;

    // There is no start state.
    if (nSize < 0)
    {
        LOGW("There is no matchStartState.");
        return true;
    }

    // Get the id of start states.
    for (int i = 0; i < nSize; i++)
    {
        // "matchStartState"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("matchStartState", i, "id", buf, &nLen, DATA_STR);
        if (!bRst)
        {
            LOGE("get start state description failed. matchStartState id: %d", i);

            return false;
        }

        pnVecStartID->push_back(atoi(buf));
    }

    return true;
}

UIStateArray CCommUICfg::GetState()
{
    return m_oVecState;
}
