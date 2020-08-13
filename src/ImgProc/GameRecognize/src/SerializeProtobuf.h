/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef SERIALIZE_PROTOBUF_H_
#define SERIALIZE_PROTOBUF_H_

#include <map>
#include <string>
#include <vector>
#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskManager.h"
#include "Protobuf/common.pb.h"

/*!
 * @class CSerialFrameResult
 * @brief 图像识别结果数据的序列化
 */
class CSerialFrameResult
{
public:
    CSerialFrameResult();
    ~CSerialFrameResult();

    /*!
     * @brief 序列化tagFrameResult结构
     * @param[out] strJosnBuf
     * @param[in] stFrameResult
     * @return 0表示成功，-1表示失败
     */
    int Serialize(std::string *pstrDataBuf, const tagFrameResult &stFrameResult);

private:

    /*!
     * @brief 序列化FixObj结果字段
     * @param[out] pstPBResult
     * @param[in] pFixObjRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialFixObjReg(tagPBResult *pstPBResult, IRegResult *pFixObjRegResult);

    /*!
     * @brief 序列化PixReg结果字段
     * @param[out] pstPBResult
     * @param[in] pPixRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialPixReg(tagPBResult *pstPBResult, IRegResult *pPixRegResult);

    /*!
     * @brief 序列化BumberReg结果字段
     * @param[out] pstPBResult
     * @param[in] pNumRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialNumberReg(tagPBResult *pstPBResult, IRegResult *pNumRegResult);

    /*!
     * @brief 序列化DeformReg结果字段
     * @param[out] pstPBResult
     * @param[in] pDeformRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialDeformReg(tagPBResult *pstPBResult, IRegResult *pDeformRegResult);

    /*!
     * @brief 序列化StuckReg结果字段
     * @param[out] pstPBResult
     * @param[in] pStuckRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialStuckReg(tagPBResult *pstPBResult, IRegResult *pStuckRegResult);

    /*!
     * @brief 序列化FixbloodReg结果字段
     * @param[out] pstPBResult
     * @param[in] pFixBloodRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialFixBloodReg(tagPBResult *pstPBResult, IRegResult *pFixBloodRegResult);

    /*!
     * @brief 序列化KingGloryBlood结果字段
     * @param[out] pstPBResult
     * @param[in] pKingGloryBloodRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialKingGloryBloodReg(tagPBResult *pstPBResult, IRegResult *pKingGloryBloodRegResult);

    /*!
     * @brief 序列化MapReg结果字段
     * @param[out] pstPBResult
     * @param[in] pMapRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialMapReg(tagPBResult *pstPBResult, IRegResult *pMapRegResult);

    /*!
     * @brief 序列化MapDirectionReg结果字段
     * @param[out] pstPBResult
     * @param[in] pMapRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialMapDirectionReg(tagPBResult *pstPBResult, IRegResult *pMapRegResult);

    /*!
     * @brief 序列化MultColorVarReg结果字段
     * @param[out] pstPBResult
     * @param[in] pMultColorVarRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialMultColorVarReg(tagPBResult *pstPBResult, IRegResult *pMultColorVarRegResult);
    /*!
     * @brief 序列号ShootBloodReg结果字段
     * @param[out] pstPBResult
     * @param[in] pShootBloodRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialShootBloodReg(tagPBResult *pstPBResult, IRegResult *pShootBloodRegResult);

    /*!
     * @brief 序列化ShootHurtReg结果字段
     * @param[out] pstPBResult
     * @param[in] pShootHurtRegResult
     * @return 0表示成功，-1表示失败
     */
    int SerialShootHurtReg(tagPBResult *pstPBResult, IRegResult *pShootHurtRegResult);
/*================================================通用类型数据=======================================================*/
    /*!
     * @brief 序列化Rect结构
     * @param[out] pPBRect
     * @param[in] oRect
     * @return 0表示成功，-1表示失败
     */
    int SerialRect(tagPBRect *pPBRect, const cv::Rect &oRect);
private:
    typedef int (CSerialFrameResult::*mFun)(tagPBResult *pstPBResult, IRegResult *pRegResult);
    std::map<EREGTYPE, mFun> m_oMapSerRegRst;
};

/*!
 * @class CUnSerialSrcImg
 * @brief 图像数据的反序列化
 */
class CUnSerialSrcImg
{
public:
    CUnSerialSrcImg();
    ~CUnSerialSrcImg();

    /*!
     * @brief tagSrcImgInfo结构体的反序列化
     * @param[out] pSrcImgInfo
     * @param[in] pDataBuf
     * @param[in] nSize
     * @return 0表示成功，-1表示失败，1表示没有收到数据
     */
    int UnSerialize(tagSrcImgInfo *pSrcImgInfo, char *pDataBuf, int nSize);
};

/*!
 * @class CUnSerialTaskMsg
 * @brief Task任务数据的反序列化
 */
class CUnSerialTaskMsg
{
public:
    CUnSerialTaskMsg();
    ~CUnSerialTaskMsg();

    /*!
     * @brief CTaskMessage类的反序列化
     * @param[out] pTaskMsg
     * @param[in] pDataBuf
     * @param[in] nSize
     * @return 0表示成功，-1表示失败，1表示没有收到数据
     */
    int UnSerialize(CTaskMessage *pTaskMsg, char *pDataBuf, int nSize);

private:
/*======================================任务设置，任务添加，任务修改相关数据============================================*/
    /*!
     * @brief 任务相关数据的反序列化
     * @param[out] pstAgentMsg
     * @param[in] stPBAgentMsg
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgent(tagAgentMsg *pstAgentMsg, const tagPBAgentMsg &stPBAgentMsg);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的FixObj数据字段的反序列化
     * @param[out] poFixObjRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentFixObjElmts(IRegParam *poFixObjRegParam,
                                        const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的PixReg数据字段的反序列化
     * @param[out] poPixRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentPixElmts(IRegParam *poPixRegParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的StuckReg数据字段的反序列化
     * @param[out] poPixRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentStuckElmts(IRegParam *poStuckRegParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);
    /*!
     * @brief 任务设置，任务添加，任务修改数据的NumberReg数据字段的反序列化
     * @param[out] poPixRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentNumberElmts(IRegParam *poNumRegParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的DeformReg数据字段的反序列化
     * @param[out] poPixRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentDeformElmts(IRegParam *poDeformRegParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的FixBlood数据字段的反序列化
     * @param[out] poFixBloodRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentFixBloodElmts(IRegParam *poFixBloodRegParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的KingGloryBlood数据字段的反序列化
     * @param[out] poKingGloryBloodRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentKGBloodElmts(IRegParam *poKingGloryBloodRegParam,
                                         const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的KingGloryBlood数据字段的反序列化
     * @param[out] poMultColorVarRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentMltClVarElmts(IRegParam *poMultColorVarRegParam,
                                          const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的MapReg数据字段的反序列化
     * @param[out] poMapRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentMapRegElmts(IRegParam *poMapRegParam,
                                        const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的MapDirectionReg数据字段的反序列化
     * @param[out] poMapRegParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentMpDRegElmts(IRegParam *poMapRegParam,
                                        const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的ShootGameBlood数据字段的反序列化
     * @param[out] poShootBloodParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentShootBloodElmts(IRegParam *poShootBloodParam,
                                            const tagPBAgentTaskTsk &stPBAgentTaskTsk);

    /*!
     * @brief 任务设置，任务添加，任务修改数据的MapReg数据字段的反序列化
     * @param[out] poShootHurtParam
     * @param[in] stPBAgentTaskTsk
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgAgentShootHurtElmts(IRegParam *poShootHurtParam,
                                           const tagPBAgentTaskTsk &stPBAgentTaskTsk);

/*================================================任务标识数据=======================================================*/
    /*!
     * @brief 任务标识数据的反序列化
     * @param[out] pstFlagMsg
     * @param[int] stPBAgentMsg
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgFlag(tagTaskFlagMsg *pstFlagMsg, const tagPBAgentMsg &stPBAgentMsg);

/*================================================删除任务数据=======================================================*/
    /*!
     * @brief 删除任务数据的反序列化
     * @param[out] pstDelMsg
     * @param[in] stPBAgentMsg
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskMsgDEL(tagDelTaskMsg *pstDelMsg, const tagPBAgentMsg &stPBAgentMsg);

/*================================================配置文件数据======================================================*/
    /*!
     * @brief 配置文件任务数据的反序列化
     * @param[out] pstConfTaskMsg
     * @param[in] stPBAgentMsg
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTaskConf(tagConfTaskMsg *pstConfTaskMsg, const tagPBAgentMsg &stPBAgentMsg);

/*================================================通用类型数据=======================================================*/
    /*!
     * @brief Rect类型的反序列化
     * @param[out] pRect
     * @param[in] stPBRect
     * @return 0表示成功，-1表示失败
     */
    int UnSerialRect(cv::Rect *pRect, const tagPBRect &stPBRect);

    /*!
     * @brief 模板template数据的反序列化
     * @param[out] pVecTmpls
     * @param[in] stPBTemplates
     * @return 0表示成功，-1表示失败
     */
    int UnSerialTemplate(std::vector<tagTmpl> *pVecTmpls, const tagPBTemplates &stPBTemplates);

private:
    typedef int (CUnSerialTaskMsg::*mFun)(IRegParam *pBaseParam, const tagPBAgentTaskTsk &stPBAgentTaskTsk);
    std::map<EREGTYPE, mFun> m_oMapUnSerRegParam;
};

/*!
 * @class CRegisterToMCMsg
 * @brief MC的注册与反注册消息的序列化
 */
class CRegisterToMCMsg
{
public:
    CRegisterToMCMsg();
    ~CRegisterToMCMsg();

public:
    /*!
     * @brief 序列化注册信息
     * @param pstrDataBuf，序列化后的结果
     * @return 0表示成功，-1表示失败
     */
    int SerialRegisterMsg(std::string *pstrDataBuf);

    /*!
     * @brief 序列化反注册信息
     * @param pstrDataBuf，序列化后的结果
     * @return 0表示成功，-1表示失败
     */
    int SerialUnRegisterMsg(std::string *pstrDataBuf);

    /*!
     * @brief 序列化发送给MC的reger初始化成功或失败的消息
     * @param pstrDataBuf，序列化后的结果
     * @param bState，成功或失败
     * @return 0表示成功，-1表示失败
     */
    int SerialTaskReportMsg(std::string *pstrDataBuf, bool bState);
};

#endif // SERIALIZE_PROTOBUF_H_
/*!@}*/
