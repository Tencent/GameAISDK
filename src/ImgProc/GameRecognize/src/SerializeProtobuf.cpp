/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "GameRecognize/src/SerializeProtobuf.h"

extern std::string g_strBaseDir;

CSerialFrameResult::CSerialFrameResult()
{
    m_oMapSerRegRst.clear();

    m_oMapSerRegRst[TYPE_FIXOBJREG]       = &CSerialFrameResult::SerialFixObjReg;
    m_oMapSerRegRst[TYPE_STUCKREG]        = &CSerialFrameResult::SerialStuckReg;
    m_oMapSerRegRst[TYPE_PIXREG]          = &CSerialFrameResult::SerialPixReg;
    m_oMapSerRegRst[TYPE_DEFORMOBJ]       = &CSerialFrameResult::SerialDeformReg;
    m_oMapSerRegRst[TYPE_NUMBER]          = &CSerialFrameResult::SerialNumberReg;
    m_oMapSerRegRst[TYPE_FIXBLOOD]        = &CSerialFrameResult::SerialFixBloodReg;
    m_oMapSerRegRst[TYPE_KINGGLORYBLOOD]  = &CSerialFrameResult::SerialKingGloryBloodReg;
    m_oMapSerRegRst[TYPE_MAPREG]          = &CSerialFrameResult::SerialMapReg;
    m_oMapSerRegRst[TYPE_MULTCOLORVAR]    = &CSerialFrameResult::SerialMultColorVarReg;
    m_oMapSerRegRst[TYPE_SHOOTBLOOD]      = &CSerialFrameResult::SerialShootBloodReg;
    m_oMapSerRegRst[TYPE_SHOOTHURT]       = &CSerialFrameResult::SerialShootHurtReg;
    m_oMapSerRegRst[TYPE_MAPDIRECTIONREG] = &CSerialFrameResult::SerialMapDirectionReg;
}

CSerialFrameResult::~CSerialFrameResult()
{}

/*!
 * @brief 序列化ShootBloodReg结果字段
 * @param[out] pstPBResult
 * @param[in] pShootBloodRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialShootBloodReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pShootBloodRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                      nSize;
    CShootGameBloodRegResult *pGBloodRegResult = dynamic_cast<CShootGameBloodRegResult*>(pRegResult);
    if (NULL == pGBloodRegResult)
    {
        LOGE("pGBloodRegResult is NULL");
        return -1;
    }

    tagShootGameBloodRegResult *pstShootGameBloodRegResult = pGBloodRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultShootBloodRegRes = pstPBResult->add_stpbresultres();
        pstPBResultShootBloodRegRes->set_nflag(pstShootGameBloodRegResult[nIdx].nState);
        pstPBResultShootBloodRegRes->set_fnum(pstShootGameBloodRegResult[nIdx].stBlood.fPercent);

        tagPBRect *pPBRect = pstPBResultShootBloodRegRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstShootGameBloodRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial ShootBloodRegResult");
            return -1;
        }

        pPBRect = pstPBResultShootBloodRegRes->mutable_stpbrect();
        if (-1 == SerialRect(pPBRect, pstShootGameBloodRegResult[nIdx].stBlood.oRect))
        {
            LOGE("Serial rect failed when serial ShootBloodRegResult");
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 序列化ShootHurtReg结果字段
 * @param[out] pstPBResult
 * @param[in] pShootHurtRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialShootHurtReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pShootHurtRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                     nSize;
    CShootGameHurtRegResult *pShootHurtRegResult = dynamic_cast<CShootGameHurtRegResult*>(pRegResult);
    if (NULL == pShootHurtRegResult)
    {
        LOGE("pShootHurtRegResult is NULL");
        return -1;
    }

    tagShootGameHurtRegResult *pstShootGameHurtRegResult = pShootHurtRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultShootHurtRegRes = pstPBResult->add_stpbresultres();
        pstPBResultShootHurtRegRes->set_nflag(pstShootGameHurtRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultShootHurtRegRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstShootGameHurtRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial ShootHurtRegResult");
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 序列化MapReg结果字段
 * @param[out] pstPBResult
 * @param[in] pMapRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialMapReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pMapRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int           nSize;
    CMapRegResult *pMapRegResult = dynamic_cast<CMapRegResult*>(pRegResult);
    if (NULL == pMapRegResult)
    {
        LOGE("pMapRegResult is NULL");
        return -1;
    }

    tagMapRegResult *pstMapRegResult = pMapRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultMapRegRes = pstPBResult->add_stpbresultres();
        pstPBResultMapRegRes->set_nflag(pstMapRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultMapRegRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstMapRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial MapRegResult");
            return -1;
        }

        tagPBPoint *pPBPoint = pstPBResultMapRegRes->mutable_stpbviewanglepoint();
        pPBPoint->set_nx(pstMapRegResult[nIdx].oViewAnglePoint.x);
        pPBPoint->set_ny(pstMapRegResult[nIdx].oViewAnglePoint.y);

        pPBPoint = pstPBResultMapRegRes->mutable_stpbmylocpoint();
        pPBPoint->set_nx(pstMapRegResult[nIdx].oMyLocPoint.x);
        pPBPoint->set_ny(pstMapRegResult[nIdx].oMyLocPoint.y);

        for (int nIdxn = 0; nIdxn < pstMapRegResult[nIdx].nFreindsPointNum; ++nIdxn)
        {
            tagPBPoint *pPBPoint = pstPBResultMapRegRes->add_stpbpoints();
            pPBPoint->set_nx(pstMapRegResult[nIdx].szFriendsLocPoints[nIdxn].x);
            pPBPoint->set_ny(pstMapRegResult[nIdx].szFriendsLocPoints[nIdxn].y);
        }
    }

    return 0;
}

/*!
 * @brief 序列化MapDirectionReg结果字段
 * @param[out] pstPBResult
 * @param[in] pMapRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialMapDirectionReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pMapRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                    nSize;
    CMapDirectionRegResult *pMapRegResult = dynamic_cast<CMapDirectionRegResult*>(pRegResult);
    if (NULL == pMapRegResult)
    {
        LOGE("pMapRegResult is NULL");
        return -1;
    }

    tagMapDirectionRegResult *pstMapRegResult = pMapRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultMapRegRes = pstPBResult->add_stpbresultres();
        pstPBResultMapRegRes->set_nflag(pstMapRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultMapRegRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstMapRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial MapRegResult");
            return -1;
        }

        tagPBPoint *pPBPoint = pstPBResultMapRegRes->mutable_stpbviewanglepoint();
        pPBPoint->set_nx(pstMapRegResult[nIdx].oViewAnglePoint.x);
        pPBPoint->set_ny(pstMapRegResult[nIdx].oViewAnglePoint.y);

        pPBPoint = pstPBResultMapRegRes->mutable_stpbmylocpoint();
        pPBPoint->set_nx(pstMapRegResult[nIdx].oMyLocPoint.x);
        pPBPoint->set_ny(pstMapRegResult[nIdx].oMyLocPoint.y);
    }

    return 0;
}

/*!
 * @brief 序列化MultColorVarReg结果字段
 * @param[out] pstPBResult
 * @param[in] pMultColorVarRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialMultColorVarReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pMultColorVarRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                    nSize;
    CMultColorVarRegResult *pMultColorVarRegResult = dynamic_cast<CMultColorVarRegResult*>(pRegResult);
    if (NULL == pMultColorVarRegResult)
    {
        LOGE("pMultColorVarRegResult is NULL");
        return -1;
    }

    tagMultColorVarRegResult *pstMultColorVarRegResult = pMultColorVarRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultMultColorVarRes = pstPBResult->add_stpbresultres();
        pstPBResultMultColorVarRes->set_nflag(pstMultColorVarRegResult[nIdx].nState);

        for (int nIdxn = 0; nIdxn < DIRECTION_SIZE; ++nIdxn)
        {
            pstPBResultMultColorVarRes->add_fcolormeanvars(pstMultColorVarRegResult[nIdx].colorMeanVar[nIdxn]);
        }
    }

    return 0;
}

/*!
 * @brief 序列化KingGloryBlood结果字段
 * @param[out] pstPBResult
 * @param[in] pKingGloryBloodRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialKingGloryBloodReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pKingGloryBloodRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                      nSize;
    CKingGloryBloodRegResult *pKingGloryBloodRegResult = dynamic_cast<CKingGloryBloodRegResult*>(pRegResult);
    if (NULL == pKingGloryBloodRegResult)
    {
        LOGE("pKingGloryBloodRegResult is NULL");
        return -1;
    }

    tagKingGloryBloodRegResult *pstKingGloryBloodRegResult = pKingGloryBloodRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultKingGloryBloodRes = pstPBResult->add_stpbresultres();
        pstPBResultKingGloryBloodRes->set_nflag(pstKingGloryBloodRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultKingGloryBloodRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstKingGloryBloodRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial KingGloryBloodRegResult");
            return -1;
        }

        for (int nIdxn = 0; nIdxn < pstKingGloryBloodRegResult[nIdx].nBloodNum; ++nIdxn)
        {
            tagPBBlood *pPBBlood = pstPBResultKingGloryBloodRes->add_stpbbloods();
            pPBBlood->set_nlevel(pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].nLevel);
            pPBBlood->set_fscore(pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].fScore);
            pPBBlood->set_fpercent(pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].fPercent);
            pPBBlood->set_nclassid(pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].nClassID);
            pPBBlood->set_strname(pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].szName);

            pPBRect = pPBBlood->mutable_stpbrect();
            if (-1 == SerialRect(pPBRect, pstKingGloryBloodRegResult[nIdx].szBloods[nIdxn].oRect))
            {
                LOGE("Serial rect failed when serial KingGloryBloodRegResult");
                return -1;
            }
        }
    }

    return 0;
}

/*!
 * @brief 序列化FixbloodReg结果字段
 * @param[out] pstPBResult
 * @param[in] pFixBloodRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialFixBloodReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pFixBloodRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                nSize;
    CFixBloodRegResult *pFixBloodRegResult = dynamic_cast<CFixBloodRegResult*>(pRegResult);
    if (NULL == pFixBloodRegResult)
    {
        LOGE("pFixBloodRegResult is NULL");
        return -1;
    }

    tagFixBloodRegResult *pstFixBloodRegResult = pFixBloodRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultFixBloodRes = pstPBResult->add_stpbresultres();
        pstPBResultFixBloodRes->set_nflag(pstFixBloodRegResult[nIdx].nState);
        pstPBResultFixBloodRes->set_fnum(pstFixBloodRegResult[nIdx].fPercent);

        tagPBRect *pPBRect = pstPBResultFixBloodRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstFixBloodRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial FixBloodRegResult");
            return -1;
        }

        pPBRect = pstPBResultFixBloodRes->mutable_stpbrect();
        if (-1 == SerialRect(pPBRect, pstFixBloodRegResult[nIdx].oRect))
        {
            LOGE("Serial rect failed when serial FixBloodRegResult");
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 序列化FixObj结果字段
 * @param[out] pstPBResult
 * @param[in] pFixObjRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialFixObjReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pFixObjRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    CFixObjRegResult *pFixObjRegResult = dynamic_cast<CFixObjRegResult*>(pRegResult);
    if (NULL == pFixObjRegResult)
    {
        LOGE("pFixObjRegResult is NULL");
        return -1;
    }

    int                nSize;
    tagFixObjRegResult *pstFixObjRegResult = pFixObjRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultFixObjRes = pstPBResult->add_stpbresultres();
        pstPBResultFixObjRes->set_nflag(pstFixObjRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultFixObjRes->mutable_stpbroi();
        if (-1 == SerialRect(pPBRect, pstFixObjRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial FixobjRegResult");
            return -1;
        }

        for (int nIdxn = 0; nIdxn < pstFixObjRegResult[nIdx].nBBoxNum; ++nIdxn)
        {
            tagPBBox *pPBBox = pstPBResultFixObjRes->add_stpbboxs();
            pPBBox->set_strtmplname(pstFixObjRegResult[nIdx].szBBoxes[nIdxn].szTmplName);
            pPBBox->set_nclassid(pstFixObjRegResult[nIdx].szBBoxes[nIdxn].nClassID);
            pPBBox->set_fscore(pstFixObjRegResult[nIdx].szBBoxes[nIdxn].fScore);
            pPBBox->set_fscale(pstFixObjRegResult[nIdx].szBBoxes[nIdxn].fScale);

            pPBRect = pPBBox->mutable_stpbrect();
            if (-1 == SerialRect(pPBRect, pstFixObjRegResult[nIdx].szBBoxes[nIdxn].oRect))
            {
                LOGE("Serial rect failed when serial FixObjRegResult");
                return -1;
            }
        }
    }

    return 0;
}

/*!
 * @brief 序列化PixReg结果字段
 * @param[out] pstPBResult
 * @param[in] pPixRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialPixReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pPixRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int           nSize;
    CPixRegResult *pPixRegResult = dynamic_cast<CPixRegResult*>(pRegResult);
    if (NULL == pPixRegResult)
    {
        LOGE("pPixRegResult is NULL");
        return -1;
    }

    tagPixRegResult *pstPixRegResult = pPixRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultPixRes = pstPBResult->add_stpbresultres();
        pstPBResultPixRes->set_nflag(pstPixRegResult[nIdx].nState);

        for (int nIdxn = 0; nIdxn < pstPixRegResult[nIdx].nPointNum; ++nIdxn)
        {
            tagPBPoint *pPBPoint = pstPBResultPixRes->add_stpbpoints();
            pPBPoint->set_nx(pstPixRegResult[nIdx].szPoints[nIdxn].x);
            pPBPoint->set_ny(pstPixRegResult[nIdx].szPoints[nIdxn].y);
        }

        // int nImageSize = pstPixRegResult[nIdx].oDstImg.total() * pstPixRegResult[nIdx].oDstImg.elemSize();
        // pstPBResultPixRes->set_byimage(pstPixRegResult[nIdx].oDstImg.data, nImageSize);
    }

    return 0;
}

/*!
 * @brief 序列化StuckReg结果字段
 * @param[out] pstPBResult
 * @param[in] pStuckRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialStuckReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pStuckRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int             nSize;
    CStuckRegResult *pStuckRegResult = dynamic_cast<CStuckRegResult*>(pRegResult);
    if (NULL == pStuckRegResult)
    {
        LOGE("pStuckRegResult is NULL");
        return -1;
    }

    tagStuckRegResult *pstStuckRegResult = pStuckRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBResultStuckRes = pstPBResult->add_stpbresultres();
        pstPBResultStuckRes->set_nflag(pstStuckRegResult[nIdx].nState);

        tagPBRect *pPBRect = pstPBResultStuckRes->mutable_stpbrect();
        if (-1 == SerialRect(pPBRect, pstStuckRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial StuckRegResult");
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 序列化BumberReg结果字段
 * @param[out] pstPBResult
 * @param[in] pNumRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialNumberReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pNumRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int           nSize;
    CNumRegResult *pNumRegResult = dynamic_cast<CNumRegResult*>(pRegResult);
    if (NULL == pNumRegResult)
    {
        LOGE("pNumRegResult is NULL");
        return -1;
    }

    tagNumRegResult *pstNumRegResult = pNumRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBNumRegResult = pstPBResult->add_stpbresultres();
        pstPBNumRegResult->set_nflag(pstNumRegResult[nIdx].nState);
        pstPBNumRegResult->set_fnum(pstNumRegResult[nIdx].fNum);

        tagPBRect *pPBRect = pstPBNumRegResult->mutable_stpbrect();
        if (-1 == SerialRect(pPBRect, pstNumRegResult[nIdx].oROI))
        {
            LOGE("Serial rect failed when serial NumberRegResult");
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 序列化DeformReg结果字段
 * @param[out] pstPBResult
 * @param[in] pDeformRegResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialDeformReg(tagPBResult *pstPBResult, IRegResult *pRegResult)
{
    if (pRegResult == NULL)
    {
        LOGE("pDeformRegResult is NULL");
        return -1;
    }

    if (pstPBResult == NULL)
    {
        LOGE("pstPBResult is NULL");
        return -1;
    }

    int                 nSize;
    CDeformObjRegResult *pDeformRegResult = dynamic_cast<CDeformObjRegResult*>(pRegResult);
    if (NULL == pDeformRegResult)
    {
        LOGE("pDeformRegResult is NULL");
        return -1;
    }

    tagDeformObjRegResult *pstDeformRegResult = pDeformRegResult->GetResult(&nSize);

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBResultRes *pstPBDeformObjRes = pstPBResult->add_stpbresultres();
        pstPBDeformObjRes->set_nflag(pstDeformRegResult[nIdx].nState);

        for (int nIdxn = 0; nIdxn < pstDeformRegResult[nIdx].nBBoxNum; ++nIdxn)
        {
            tagPBBox *pPBBox = pstPBDeformObjRes->add_stpbboxs();
            pPBBox->set_strtmplname(pstDeformRegResult[nIdx].szBBoxes[nIdxn].szTmplName);
            pPBBox->set_nclassid(pstDeformRegResult[nIdx].szBBoxes[nIdxn].nClassID);
            pPBBox->set_fscore(pstDeformRegResult[nIdx].szBBoxes[nIdxn].fScore);
            pPBBox->set_fscale(pstDeformRegResult[nIdx].szBBoxes[nIdxn].fScale);

            tagPBRect *pPBRect = pPBBox->mutable_stpbrect();
            if (-1 == SerialRect(pPBRect, pstDeformRegResult[nIdx].szBBoxes[nIdxn].oRect))
            {
                LOGE("Serial rect failed when serial DeformRegResult");
                return -1;
            }
        }
    }

    return 0;
}

bool SetRegType(tagPBResult *pstPBResult, const EREGTYPE eRegType)
{
    switch (eRegType)
    {
    case TYPE_FIXOBJREG:
    {
        pstPBResult->set_eregtype(TYPE_FIXOBJREG);
        break;
    }

    case TYPE_PIXREG:
    {
        pstPBResult->set_eregtype(TYPE_PIXREG);
        break;
    }

    case TYPE_STUCKREG:
    {
        pstPBResult->set_eregtype(TYPE_STUCKREG);
        break;
    }

    case TYPE_NUMBER:
    {
        pstPBResult->set_eregtype(TYPE_NUMBER);
        break;
    }

    case TYPE_DEFORMOBJ:
    {
        pstPBResult->set_eregtype(TYPE_DEFORMOBJ);
        break;
    }

    case TYPE_FIXBLOOD:
    {
        pstPBResult->set_eregtype(TYPE_FIXBLOOD);
        break;
    }

    case TYPE_KINGGLORYBLOOD:
    {
        pstPBResult->set_eregtype(TYPE_KINGGLORYBLOOD);
        break;
    }

    case TYPE_MAPREG:
    {
        pstPBResult->set_eregtype(TYPE_MAPREG);
        break;
    }

    case TYPE_MAPDIRECTIONREG:
    {
        pstPBResult->set_eregtype(TYPE_MAPDIRECTIONREG);
        break;
    }

    case TYPE_MULTCOLORVAR:
    {
        pstPBResult->set_eregtype(TYPE_MULTCOLORVAR);
        break;
    }

    case TYPE_SHOOTBLOOD:
    {
        pstPBResult->set_eregtype(TYPE_SHOOTBLOOD);
        break;
    }

    case TYPE_SHOOTHURT:
    {
        pstPBResult->set_eregtype(TYPE_SHOOTHURT);
        break;
    }

    default:
    {
        LOGE("wrong REGTYPE: %d", eRegType);
        return false;
    }
    }

    return true;
}
/*!
 * @brief 序列化tagFrameResult结构
 * @param[out] strJosnBuf
 * @param[in] stFrameResult
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::Serialize(std::string *pstrDataBuf, const tagFrameResult &stFrameResult)
{
    if (stFrameResult.oFrame.empty())
    {
        LOGE("image of FrameResult is empty, init failed");
        return -1;
    }

    // 将外层消息赋值，具体可参考protobuf协议文件结构
    tagPBAgentMsg stPBAgentMsg;
    stPBAgentMsg.set_eagentmsgid(MSG_SEND_RESULT);
    tagPBResultValue *pstPBResultValue = stPBAgentMsg.mutable_stpbresultvalue();
    pstPBResultValue->set_nframeseq(stFrameResult.nframeSeq);
    pstPBResultValue->set_ndeviceindex(stFrameResult.ndeviceIndex);
    pstPBResultValue->set_nwidth(stFrameResult.oFrame.cols);
    pstPBResultValue->set_nheight(stFrameResult.oFrame.rows);
    pstPBResultValue->set_strjsondata(stFrameResult.strJsonData);
    int nImageSize = stFrameResult.oFrame.total() * stFrameResult.oFrame.elemSize();
    pstPBResultValue->set_byimgdata(stFrameResult.oFrame.data, nImageSize);

    std::map<int, CTaskResult> *mapTaskResult = const_cast<std::map<int, CTaskResult>*>(&stFrameResult.mapTaskResult);

    // 对于每个taskID对应的结果做序列化操作，不同的任务类型执行不同的序列化逻辑
    for (std::map<int, CTaskResult>::iterator pIter = mapTaskResult->begin(); pIter != mapTaskResult->end(); ++pIter)
    {
        EREGTYPE   eRegType    = pIter->second.GetType();
        IRegResult *pRegResult = pIter->second.GetInstance(eRegType);

        if (eRegType == TYPE_REFER_LOCATION || eRegType == TYPE_REFER_BLOODREG)
        {
            continue;
        }

        tagPBResult *pstPBResult = pstPBResultValue->add_stpbresult();
        pstPBResult->set_ntaskid(pIter->first);

        if (!SetRegType(pstPBResult, eRegType))
        {
            return -1;
        }

        int nRst = (this->*m_oMapSerRegRst[eRegType])(pstPBResult, pRegResult);
        if (-1 == nRst)
        {
            return -1;
        }
    }

    stPBAgentMsg.SerializeToString(pstrDataBuf);
    return 0;
}

/*!
 * @brief 序列化Rect结构
 * @param[out] pPBRect
 * @param[in] oRect
 * @return 0表示成功，-1表示失败
 */
int CSerialFrameResult::SerialRect(tagPBRect *pPBRect, const cv::Rect &oRect)
{
    if (pPBRect == NULL)
    {
        LOGE("pPBRect is NULL");
        return -1;
    }

    pPBRect->set_nx(oRect.x);
    pPBRect->set_ny(oRect.y);
    pPBRect->set_nw(oRect.width);
    pPBRect->set_nh(oRect.height);

    return 0;
}

CUnSerialSrcImg::CUnSerialSrcImg()
{}

CUnSerialSrcImg::~CUnSerialSrcImg()
{}

/*!
 * @brief tagSrcImgInfo结构体的反序列化
 * @param[out] pSrcImgInfo
 * @param[in] pDataBuf
 * @param[in] nSize
 * @return 0表示成功，-1表示失败，1表示没有收到数据
 */
int CUnSerialSrcImg::UnSerialize(tagSrcImgInfo *pSrcImgInfo, char *pDataBuf, int nSize)
{
    if (pSrcImgInfo == NULL)
    {
        LOGE("pSrcImgInfo is empty");
        return -1;
    }

    if (pDataBuf == NULL)
    {
        LOGE("databuf is empty");
        return -1;
    }

    if (nSize < 0)
    {
        LOGE("wrong size");
        return -1;
    }

    tagMessage stMessage;
    stMessage.ParseFromArray(pDataBuf, nSize);
    EMSGIDENUM eMsgID = stMessage.emsgid();
    if (eMsgID != MSG_SRC_IMAGE_INFO)
    {
        return 1;
    }

    int nWidth  = stMessage.stsrcimageinfo().nwidth();
    int nHeight = stMessage.stsrcimageinfo().nheight();
    pSrcImgInfo->uFrameSeq    = stMessage.stsrcimageinfo().uframeseq();
    pSrcImgInfo->uDeviceIndex = stMessage.stsrcimageinfo().udeviceindex();
    pSrcImgInfo->strJsonData  = stMessage.stsrcimageinfo().strjsondata();

    std::string strData = stMessage.stsrcimageinfo().byimagedata();
    pSrcImgInfo->oSrcImage.create(nHeight, nWidth, CV_8UC3);
    memcpy(pSrcImgInfo->oSrcImage.data, strData.c_str(), strData.length());

//    imshow("src", stSrcImgInfo.oSrcImage);
//    waitKey(0);

    return 0;
}

CUnSerialTaskMsg::CUnSerialTaskMsg()
{
    m_oMapUnSerRegParam[TYPE_STUCKREG]        = &CUnSerialTaskMsg::UnSerialTaskMsgAgentStuckElmts;
    m_oMapUnSerRegParam[TYPE_FIXOBJREG]       = &CUnSerialTaskMsg::UnSerialTaskMsgAgentFixObjElmts;
    m_oMapUnSerRegParam[TYPE_PIXREG]          = &CUnSerialTaskMsg::UnSerialTaskMsgAgentPixElmts;
    m_oMapUnSerRegParam[TYPE_DEFORMOBJ]       = &CUnSerialTaskMsg::UnSerialTaskMsgAgentDeformElmts;
    m_oMapUnSerRegParam[TYPE_NUMBER]          = &CUnSerialTaskMsg::UnSerialTaskMsgAgentNumberElmts;
    m_oMapUnSerRegParam[TYPE_FIXBLOOD]        = &CUnSerialTaskMsg::UnSerialTaskMsgAgentFixBloodElmts;
    m_oMapUnSerRegParam[TYPE_KINGGLORYBLOOD]  = &CUnSerialTaskMsg::UnSerialTaskMsgAgentKGBloodElmts;
    m_oMapUnSerRegParam[TYPE_MAPREG]          = &CUnSerialTaskMsg::UnSerialTaskMsgAgentMapRegElmts;
    m_oMapUnSerRegParam[TYPE_MULTCOLORVAR]    = &CUnSerialTaskMsg::UnSerialTaskMsgAgentMltClVarElmts;
    m_oMapUnSerRegParam[TYPE_SHOOTBLOOD]      = &CUnSerialTaskMsg::UnSerialTaskMsgAgentShootBloodElmts;
    m_oMapUnSerRegParam[TYPE_SHOOTHURT]       = &CUnSerialTaskMsg::UnSerialTaskMsgAgentShootHurtElmts;
    m_oMapUnSerRegParam[TYPE_MAPDIRECTIONREG] = &CUnSerialTaskMsg::UnSerialTaskMsgAgentMpDRegElmts;
}

CUnSerialTaskMsg::~CUnSerialTaskMsg()
{}

/*!
 * @brief CTaskMessage类的反序列化
 * @param[out] pTaskMsg
 * @param[in] pDataBuf
 * @param[in] nSize
 * @return 0表示成功，-1表示失败，1表示没有收到数据
 */
int CUnSerialTaskMsg::UnSerialize(CTaskMessage *pTaskMsg, char *pDataBuf, int nSize)
{
    if (pTaskMsg == NULL)
    {
        LOGE("pTaskMsg is empty");
        return -1;
    }

    if (pDataBuf == NULL)
    {
        LOGE("databuf is empty");
        return -1;
    }

    if (nSize < 0)
    {
        LOGE("wrong size");
        return -1;
    }

    tagMessage stMessage;
    stMessage.ParseFromArray(pDataBuf, nSize);
    EMSGIDENUM eMsgID = stMessage.emsgid();
    if (eMsgID != MSG_GAMEREG_INFO)
    {
        return 1;
    }

    tagPBAgentMsg stPBAgentMsg = stMessage.stpbagentmsg();
    EAgentMsgID   eAgentMsgID  = stPBAgentMsg.eagentmsgid();
    pTaskMsg->SetMsgType(eAgentMsgID);

    // 总共有六种类型的消息，对于不同类型的消息，做不同处理
    switch (eAgentMsgID)
    {
    case MSG_RECV_GROUP_ID:
    {
        tagCmdMsg   *pstCmdMsg   = pTaskMsg->GetInstance(MSG_RECV_GROUP_ID);
        tagAgentMsg *pstAgentMsg = dynamic_cast<tagAgentMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskMsgAgent(pstAgentMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg Agent failed");
            return -1;
        }

        break;
    }

    case MSG_RECV_TASK_FLAG:
    {
        tagCmdMsg      *pstCmdMsg      = pTaskMsg->GetInstance(MSG_RECV_TASK_FLAG);
        tagTaskFlagMsg *pstTaskFlagMsg = dynamic_cast<tagTaskFlagMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskMsgFlag(pstTaskFlagMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg Flag failed");
            return -1;
        }

        break;
    }

    case MSG_RECV_ADD_TASK:
    {
        tagCmdMsg   *pstCmdMsg     = pTaskMsg->GetInstance(MSG_RECV_ADD_TASK);
        tagAgentMsg *pstAddTaskMsg = dynamic_cast<tagAgentMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskMsgAgent(pstAddTaskMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg ADD task failed");
            return -1;
        }

        break;
    }

    case MSG_RECV_DEL_TASK:
    {
        tagCmdMsg     *pstCmdMsg     = pTaskMsg->GetInstance(MSG_RECV_DEL_TASK);
        tagDelTaskMsg *pstDelTaskMsg = dynamic_cast<tagDelTaskMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskMsgDEL(pstDelTaskMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg DEL task failed");
            return -1;
        }

        break;
    }

    case MSG_RECV_CHG_TASK:
    {
        tagCmdMsg   *pstCmdMsg     = pTaskMsg->GetInstance(MSG_RECV_CHG_TASK);
        tagAgentMsg *pstChgTaskMsg = dynamic_cast<tagAgentMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskMsgAgent(pstChgTaskMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg CHG task failed");
            return -1;
        }

        break;
    }

    case MSG_RECV_CONF_TASK:
    {
        tagCmdMsg      *pstCmdMsg      = pTaskMsg->GetInstance(MSG_RECV_CONF_TASK);
        tagConfTaskMsg *pstConfTaskMsg = dynamic_cast<tagConfTaskMsg*>(pstCmdMsg);
        if (-1 == UnSerialTaskConf(pstConfTaskMsg, stPBAgentMsg))
        {
            LOGE("UnSerial TaskMsg Conf task failed");
            return -1;
        }

        break;
    }

    default:
    {
        LOGE("wrong recvmsg type: %d", eAgentMsgID);
        return -1;
    }
    }

    return 0;
}

/*!
 * @brief 任务相关数据的反序列化
 * @param[out] pstAgentMsg
 * @param[in] stPBAgentMsg
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgent(tagAgentMsg *pstAgentMsg, const tagPBAgentMsg &stPBAgentMsg)
{
    if (pstAgentMsg == NULL)
    {
        LOGE("pstAgentMsg is NULL");
        return -1;
    }

    tagPBAgentTaskValue stPBAgentTaskValue = stPBAgentMsg.stpbagenttaskvalue();
    pstAgentMsg->uGroupID = stPBAgentTaskValue.ugroupid();
    int nSize = stPBAgentTaskValue.stpbagenttasktsks_size();

    // 对于不同类型的任务参数，做不同的反序列化操作
    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBAgentTaskTsk stPBAgentTaskTsk = stPBAgentTaskValue.stpbagenttasktsks(nIdx);
        int               nTaskID          = stPBAgentTaskTsk.ntaskid();
        pstAgentMsg->mapTaskParams[nTaskID] = CTaskParam();
        pstAgentMsg->mapTaskParams[nTaskID].SetTaskID(nTaskID);
        EREGTYPE eTaskType = stPBAgentTaskTsk.etype();
        pstAgentMsg->mapTaskParams[nTaskID].SetType(eTaskType);
        pstAgentMsg->mapTaskParams[nTaskID].SetSkipFrame(stPBAgentTaskTsk.nskipframe());

        IRegParam *pBaseParam = pstAgentMsg->mapTaskParams[nTaskID].GetInstance(eTaskType);
        int       nRst        = (this->*m_oMapUnSerRegParam[eTaskType])(pBaseParam, stPBAgentTaskTsk);
        if (-1 == nRst)
        {
            return -1;
        }
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的FixObj数据字段的反序列化
 * @param[out] poFixObjRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentFixObjElmts(IRegParam *pBaseParam,
                                                      const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poFixObjRegParam is NULL");
        return -1;
    }

    int             nSize            = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CFixObjRegParam *pFixObjRegParam = dynamic_cast<CFixObjRegParam*>(pBaseParam);
    if (NULL == pFixObjRegParam)
    {
        LOGE("poFixObjRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagFixObjRegElement   stFixObjRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stFixObjRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in FixObj elements");
            return -1;
        }

        stFixObjRegElement.strAlgorithm = stPBAgentTaskElement.stralgorithm();
        stFixObjRegElement.fMinScale    = stPBAgentTaskElement.fminscale();
        stFixObjRegElement.fMaxScale    = stPBAgentTaskElement.fmaxscale();
        stFixObjRegElement.nScaleLevel  = stPBAgentTaskElement.nscalelevel();
        stFixObjRegElement.nMaxBBoxNum  = stPBAgentTaskElement.nmaxbboxnum();

        if (-1 == UnSerialTemplate(&stFixObjRegElement.oVecTmpls, stPBAgentTaskElement.stpbtemplates()))
        {
            LOGE("UnSerial Template failed in fixobj element");
            return -1;
        }

        pFixObjRegParam->m_oVecElements.push_back(stFixObjRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的PixReg数据字段的反序列化
 * @param[out] poPixRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentPixElmts(IRegParam *pBaseParam,
                                                   const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poPixRegParam is NULL");
        return -1;
    }

    int          nSize         = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CPixRegParam *pPixRegParam = dynamic_cast<CPixRegParam*>(pBaseParam);
    if (NULL == pPixRegParam)
    {
        LOGE("pPixRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPixRegElement      stPixRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stPixRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in FixObj elements");
            return -1;
        }

        stPixRegElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();
        stPixRegElement.strCondition = stPBAgentTaskElement.strcondition();

        pPixRegParam->m_oVecElements.push_back(stPixRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的StuckReg数据字段的反序列化
 * @param[out] poPixRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentStuckElmts(IRegParam *pBaseParam,
                                                     const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poStuckRegParam is NULL");
        return -1;
    }

    int            nSize           = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CStuckRegParam *pStuckRegParam = dynamic_cast<CStuckRegParam*>(pBaseParam);
    if (NULL == pStuckRegParam)
    {
        LOGE("pStuckRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagStuckRegElement    stStuckRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stStuckRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in FixObj elements");
            return -1;
        }

        stStuckRegElement.fThreshold    = stPBAgentTaskElement.fthreshold();
        stStuckRegElement.fIntervalTime = stPBAgentTaskElement.fintervaltime();

        pStuckRegParam->m_oVecElements.push_back(stStuckRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的NumberReg数据字段的反序列化
 * @param[out] poPixRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentNumberElmts(IRegParam *pBaseParam,
                                                      const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poNumRegParam is NULL");
        return -1;
    }

    int          nSize         = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CNumRegParam *pNumRegParam = dynamic_cast<CNumRegParam*>(pBaseParam);
    if (NULL == pNumRegParam)
    {
        LOGE("pNumRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagNumRegElement      stNumRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        stNumRegElement.nScaleLevel = stPBAgentTaskElement.nscalelevel();
        stNumRegElement.fMinScale   = stPBAgentTaskElement.fminscale();
        stNumRegElement.fMaxScale   = stPBAgentTaskElement.fmaxscale();
        stNumRegElement.oAlgorithm  = stPBAgentTaskElement.stralgorithm();

        if (-1 == UnSerialRect(&stNumRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("UnSerial ROI failed in NumReg element");
            return -1;
        }

        if (-1 == UnSerialTemplate(&stNumRegElement.oVecTmpls, stPBAgentTaskElement.stpbtemplates()))
        {
            LOGE("UnSerial Template failed in NumReg element");
            return -1;
        }

        pNumRegParam->m_oVecElements.push_back(stNumRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的DeformReg数据字段的反序列化
 * @param[out] poPixRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentDeformElmts(IRegParam *pBaseParam,
                                                      const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poDeformRegParam is NULL");
        return -1;
    }

    int                nSize            = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CDeformObjRegParam *pDeformRegParam = dynamic_cast<CDeformObjRegParam*>(pBaseParam);
    if (NULL == pDeformRegParam)
    {
        LOGE("pDeformRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagDeformObjRegElement stDeformRegElement;
        tagPBAgentTaskElement  stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stDeformRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in Deform elements");
            return -1;
        }

        stDeformRegElement.fThreshold    = stPBAgentTaskElement.fthreshold();
        stDeformRegElement.strCfgPath    = g_strBaseDir + stPBAgentTaskElement.strcfgpath();
        stDeformRegElement.strWeightPath = g_strBaseDir + stPBAgentTaskElement.strweightpath();
        stDeformRegElement.strNamePath   = g_strBaseDir + stPBAgentTaskElement.strnamepath();
        if (!stPBAgentTaskElement.strmaskpath().empty())
        {
            stDeformRegElement.strMaskPath = g_strBaseDir + stPBAgentTaskElement.strmaskpath();
        }

        pDeformRegParam->m_oVecElements.push_back(stDeformRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的FixBlood数据字段的反序列化
 * @param[out] poFixBloodRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentFixBloodElmts(IRegParam *pBaseParam,
                                                        const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poFixBloodRegParam is NULL");
        return -1;
    }

    int               nSize              = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CFixBloodRegParam *pFixBloodRegParam = dynamic_cast<CFixBloodRegParam*>(pBaseParam);
    if (NULL == pFixBloodRegParam)
    {
        LOGE("pFixBloodRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagFixBloodRegParam   stFixBloodRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stFixBloodRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in FixBlood elements");
            return -1;
        }

        stFixBloodRegElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();
        stFixBloodRegElement.strCondition = stPBAgentTaskElement.strcondition();
        stFixBloodRegElement.nBloodLength = stPBAgentTaskElement.nbloodlength();
        stFixBloodRegElement.nMaxPointNum = stPBAgentTaskElement.nmaxpointnum();

        pFixBloodRegParam->m_oVecElements.push_back(stFixBloodRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的KingGloryBlood数据字段的反序列化
 * @param[out] poKingGloryBloodRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentKGBloodElmts(IRegParam *pBaseParam,
                                                       const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poKingGloryBloodRegParam is NULL");
        return -1;
    }

    int                     nSize                    = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CKingGloryBloodRegParam *pKingGloryBloodRegParam = dynamic_cast<CKingGloryBloodRegParam*>(pBaseParam);
    if (NULL == pKingGloryBloodRegParam)
    {
        LOGE("pKingGloryBloodRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagKingGloryBloodRegParam stKingGloryBloodRegElement;
        tagPBAgentTaskElement     stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stKingGloryBloodRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in KingGloryBlood elements");
            return -1;
        }

        stKingGloryBloodRegElement.strCfgPath    = g_strBaseDir + stPBAgentTaskElement.strcfgpath();
        stKingGloryBloodRegElement.strWeightPath = g_strBaseDir + stPBAgentTaskElement.strweightpath();
        stKingGloryBloodRegElement.strNamePath   = g_strBaseDir + stPBAgentTaskElement.strnamepath();
        if (!stPBAgentTaskElement.strmaskpath().empty())
        {
            stKingGloryBloodRegElement.strMaskPath = g_strBaseDir + stPBAgentTaskElement.strmaskpath();
        }

        stKingGloryBloodRegElement.fThreshold   = stPBAgentTaskElement.fthreshold();
        stKingGloryBloodRegElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();
        stKingGloryBloodRegElement.nBloodLength = stPBAgentTaskElement.nbloodlength();
        stKingGloryBloodRegElement.nMaxPointNum = stPBAgentTaskElement.nmaxpointnum();
        stKingGloryBloodRegElement.fMinScale    = stPBAgentTaskElement.fminscale();
        stKingGloryBloodRegElement.fMaxScale    = stPBAgentTaskElement.fmaxscale();
        stKingGloryBloodRegElement.nScaleLevel  = stPBAgentTaskElement.nscalelevel();

        if (-1 == UnSerialTemplate(&stKingGloryBloodRegElement.oVecTmpls, stPBAgentTaskElement.stpbtemplates()))
        {
            LOGE("UnSerial Template failed in KingGloryBlood element");
            return -1;
        }

        pKingGloryBloodRegParam->m_oVecElements.push_back(stKingGloryBloodRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的MapReg数据字段的反序列化
 * @param[out] poMapRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentMapRegElmts(IRegParam *pBaseParam,
                                                      const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poMapRegParam is NULL");
        return -1;
    }

    int          nSize         = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CMapRegParam *pMapRegParam = dynamic_cast<CMapRegParam*>(pBaseParam);
    if (NULL == pMapRegParam)
    {
        LOGE("pMapRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagMapRegParam        stMapRegElement;
        tagPBAgentTaskElement stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stMapRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in MapReg elements");
            return -1;
        }

        stMapRegElement.strMyLocCondition      = stPBAgentTaskElement.strmyloccondition();
        stMapRegElement.strFriendsLocCondition = stPBAgentTaskElement.strfriendscondition();
        stMapRegElement.strViewLocCondition    = stPBAgentTaskElement.strviewloccondition();
        stMapRegElement.strMapTempPath         = g_strBaseDir + stPBAgentTaskElement.strmappath();

        if (!stPBAgentTaskElement.strmaskpath().empty())
        {
            stMapRegElement.strMapMaskPath = g_strBaseDir + stPBAgentTaskElement.strmaskpath();
        }

        stMapRegElement.nMaxPointNum = stPBAgentTaskElement.nmaxpointnum();
        stMapRegElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();

        pMapRegParam->m_oVecElements.push_back(stMapRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的MapDirectionReg数据字段的反序列化
 * @param[out] poMapRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentMpDRegElmts(IRegParam *pBaseParam,
                                                      const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poMapRegParam is NULL");
        return -1;
    }

    int                   nSize         = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CMapDirectionRegParam *pMapRegParam = dynamic_cast<CMapDirectionRegParam*>(pBaseParam);
    if (NULL == pMapRegParam)
    {
        LOGE("pMapRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagMapDirectionRegParam stMapRegElement;
        tagPBAgentTaskElement   stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stMapRegElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in MapReg elements");
            return -1;
        }

        stMapRegElement.strMyLocCondition   = stPBAgentTaskElement.strmyloccondition();
        stMapRegElement.strViewLocCondition = stPBAgentTaskElement.strviewloccondition();

        if (!stPBAgentTaskElement.strmaskpath().empty())
        {
            stMapRegElement.strMapMaskPath = g_strBaseDir + stPBAgentTaskElement.strmaskpath();
        }

        stMapRegElement.nMaxPointNum = stPBAgentTaskElement.nmaxpointnum();
        stMapRegElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();
        stMapRegElement.nDilateSize  = stPBAgentTaskElement.ndilatesize();
        stMapRegElement.nErodeSize   = stPBAgentTaskElement.nerodesize();
        stMapRegElement.nRegionSize  = stPBAgentTaskElement.nregionsize();

        pMapRegParam->m_oVecElements.push_back(stMapRegElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的KingGloryBlood数据字段的反序列化
 * @param[out] poMultColorVarRegParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentMltClVarElmts(IRegParam *pBaseParam,
                                                        const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poMultColorVarRegParam is NULL");
        return -1;
    }

    int                   nSize                  = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CMultColorVarRegParam *pMultColorVarRegParam = dynamic_cast<CMultColorVarRegParam*>(pBaseParam);
    if (NULL == pMultColorVarRegParam)
    {
        LOGE("pMultColorVarRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagMultColorVarRegElement stMultColorVarElement;
        tagPBAgentTaskElement     stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        stMultColorVarElement.strImageFilePath = g_strBaseDir + stPBAgentTaskElement.strimgfilepath();

        pMultColorVarRegParam->m_oVecElements.push_back(stMultColorVarElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的ShootGameBlood数据字段的反序列化
 * @param[out] poShootBloodParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentShootBloodElmts(IRegParam *pBaseParam,
                                                          const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poShootBloodParam is NULL");
        return -1;
    }

    int                     nSize                    = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CShootGameBloodRegParam *pShootGameBloodRegParam = dynamic_cast<CShootGameBloodRegParam*>(pBaseParam);
    if (NULL == pShootGameBloodRegParam)
    {
        LOGE("pShootGameBloodRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagShootGameBloodRegParam stShootGameBloodElement;
        tagPBAgentTaskElement     stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stShootGameBloodElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in ShootGameBlood elements");
            return -1;
        }

        stShootGameBloodElement.nBloodLength = stPBAgentTaskElement.nbloodlength();
        stShootGameBloodElement.nMaxPointNum = stPBAgentTaskElement.nmaxpointnum();
        stShootGameBloodElement.fMinScale    = stPBAgentTaskElement.fminscale();
        stShootGameBloodElement.fMaxScale    = stPBAgentTaskElement.fmaxscale();
        stShootGameBloodElement.nScaleLevel  = stPBAgentTaskElement.nscalelevel();
        stShootGameBloodElement.nFilterSize  = stPBAgentTaskElement.nfiltersize();

        if (-1 == UnSerialTemplate(&stShootGameBloodElement.oVecTmpls, stPBAgentTaskElement.stpbtemplates()))
        {
            LOGE("UnSerial Template failed in ShootGameBlood element");
            return -1;
        }

        pShootGameBloodRegParam->m_oVecElements.push_back(stShootGameBloodElement);
    }

    return 0;
}

/*!
 * @brief 任务设置，任务添加，任务修改数据的MapReg数据字段的反序列化
 * @param[out] poShootHurtParam
 * @param[in] stPBAgentTaskTsk
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgAgentShootHurtElmts(IRegParam *pBaseParam,
                                                         const tagPBAgentTaskTsk &stPBAgentTaskTsk)
{
    if (pBaseParam == NULL)
    {
        LOGE("poShootHurtParam is NULL");
        return -1;
    }

    int                    nSize                   = stPBAgentTaskTsk.stpbagenttaskelements_size();
    CShootGameHurtRegParam *pShootGameHurtRegParam = dynamic_cast<CShootGameHurtRegParam*>(pBaseParam);
    if (NULL == pShootGameHurtRegParam)
    {
        LOGE("pShootGameHurtRegParam is NULL");
        return -1;
    }

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagShootGameHurtRegParam stShootGameHurtElement;
        tagPBAgentTaskElement    stPBAgentTaskElement = stPBAgentTaskTsk.stpbagenttaskelements(nIdx);

        if (-1 == UnSerialRect(&stShootGameHurtElement.oROI, stPBAgentTaskElement.stpbrect()))
        {
            LOGE("unSerialize rect when unSerialize ROI in ShootHurt elements");
            return -1;
        }

        stShootGameHurtElement.fThreshold = stPBAgentTaskElement.fthreshold();

        pShootGameHurtRegParam->m_oVecElements.push_back(stShootGameHurtElement);
    }

    return 0;
}

/*!
 * @brief Rect类型的反序列化
 * @param[out] pRect
 * @param[in] stPBRect
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialRect(cv::Rect *oRect, const tagPBRect &stPBRect)
{
    oRect->x      = stPBRect.nx();
    oRect->y      = stPBRect.ny();
    oRect->width  = stPBRect.nw();
    oRect->height = stPBRect.nh();
    return 0;
}

/*!
 * @brief 模板template数据的反序列化
 * @param[out] pVecTmpls
 * @param[in] stPBTemplates
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTemplate(std::vector<tagTmpl> *oVecTmpls, const tagPBTemplates &stPBTemplates)
{
    int nSize = stPBTemplates.stpbtemplates_size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagTmpl       stTmpl;
        tagPBTemplate stPBTemplate = stPBTemplates.stpbtemplates(nIdx);

        stTmpl.strTmplPath = g_strBaseDir + stPBTemplate.strpath();
        stTmpl.strTmplName = stPBTemplate.strname();
        stTmpl.fThreshold  = stPBTemplate.fthreshold();
        stTmpl.nClassID    = stPBTemplate.nclassid();

        if (-1 == UnSerialRect(&stTmpl.oRect, stPBTemplate.stpbrect()))
        {
            LOGE("UnSerialize rect failed when unSerialize template");
            return -1;
        }

        oVecTmpls->push_back(stTmpl);
    }

    return 0;
}

/*!
 * @brief 任务标识数据的反序列化
 * @param[out] pstFlagMsg
 * @param[int] stPBAgentMsg
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgFlag(tagTaskFlagMsg *pstFlagMsg, const tagPBAgentMsg &stPBAgentMsg)
{
    if (pstFlagMsg == NULL)
    {
        LOGE("pstFlagMsg is NULL");
        return -1;
    }

    int nSize = stPBAgentMsg.stpbtaskflagmaps_size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        tagPBTaskFlagMap stPBTaskFlagMap = stPBAgentMsg.stpbtaskflagmaps(nIdx);
        pstFlagMsg->mapTaskFlag[stPBTaskFlagMap.ntaskid()] = stPBTaskFlagMap.bflag();
    }

    return 0;
}

/*!
 * @brief 删除任务数据的反序列化
 * @param[out] pstDelMsg
 * @param[in] stPBAgentMsg
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskMsgDEL(tagDelTaskMsg *pstDelMsg, const tagPBAgentMsg &stPBAgentMsg)
{
    if (pstDelMsg == NULL)
    {
        LOGE("pstDelMsg is NULL");
        return -1;
    }

    int nSize = stPBAgentMsg.ndeltaskids_size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        pstDelMsg->nVecTask.push_back(stPBAgentMsg.ndeltaskids(nIdx));
    }

    return 0;
}

/*!
 * @brief 配置文件任务数据的反序列化
 * @param[out] pstConfTaskMsg
 * @param[in] stPBAgentMsg
 * @return 0表示成功，-1表示失败
 */
int CUnSerialTaskMsg::UnSerialTaskConf(tagConfTaskMsg *pstConfTaskMsg, const tagPBAgentMsg &stPBAgentMsg)
{
    if (pstConfTaskMsg == NULL)
    {
        LOGE("pstConfTaskMsg is NULL");
        return -1;
    }

    int nSize = stPBAgentMsg.strconffilename_size();

    for (int nIdx = 0; nIdx < nSize; ++nIdx)
    {
        pstConfTaskMsg->strVecConfName.push_back(stPBAgentMsg.strconffilename(nIdx));
    }

    return 0;
}

CRegisterToMCMsg::CRegisterToMCMsg()
{}

CRegisterToMCMsg::~CRegisterToMCMsg()
{}

int CRegisterToMCMsg::SerialRegisterMsg(std::string *pstrDataBuf)
{
    tagMessage stMessage;

    stMessage.set_emsgid(MSG_SERVICE_REGISTER);

    tagServiceRegister *pstServiceRegister = stMessage.mutable_stserviceregister();
    pstServiceRegister->set_eregistertype(PB_SERVICE_REGISTER);
    pstServiceRegister->set_eservicetype(PB_SERVICE_TYPE_REG);

    stMessage.SerializeToString(pstrDataBuf);
    return 0;
}

int CRegisterToMCMsg::SerialUnRegisterMsg(std::string *pstrDataBuf)
{
    tagMessage stMessage;

    stMessage.set_emsgid(MSG_SERVICE_REGISTER);

    tagServiceRegister *pstServiceRegister = stMessage.mutable_stserviceregister();
    pstServiceRegister->set_eregistertype(PB_SERVICE_UNREGISTER);
    pstServiceRegister->set_eservicetype(PB_SERVICE_TYPE_REG);

    stMessage.SerializeToString(pstrDataBuf);
    return 0;
}

int CRegisterToMCMsg::SerialTaskReportMsg(std::string *pstrDataBuf, bool bState)
{
    tagMessage stMessage;

    stMessage.set_emsgid(MSG_TASK_REPORT);

    tagTaskReport *pstTaskReport = stMessage.mutable_sttaskreport();
    if (bState)
    {
        pstTaskReport->set_etaskstatus(PB_TASK_INIT_SUCCESS);
    }
    else
    {
        pstTaskReport->set_etaskstatus(PB_TASK_INIT_FAILURE);
    }

    stMessage.SerializeToString(pstrDataBuf);
    return 0;
}
/*! @} */
