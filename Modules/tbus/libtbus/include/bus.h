/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef BUS_H_
#define BUS_H_

#ifdef __cplusplus
extern "C" {
#endif

/*!
@brief bus 地址转换
@param[IN] pszAddress bus 地址xx.xx.xx.xx
@param[OUT] piAddr 转换后的bus 地址
@return 0 成功， 非0失败
*/
int BusGetAddress(const char *pszAddress, int *piAddr);


/*!
@brief bus 初始化
@param[IN] iSelfAddr 本进程bus地址
@param[IN] pszBusConfFileName 本进程bus地址
@return 0 成功， 非0失败
*/
int BusInit(int iSelfAddr, const char *pszBusConfFileName);


/*!
@brief bus 退出
@param[IN] iSelfAddr 本进程bus地址
@return None
*/
void BusExit(int iSelfAddr);

/*!
@brief 数据发送
@param[IN] iPeerAddr 对端bus地址
@param[IN] pData 待发送数据首地址
@param[IN] nDataSize 待发送数据长度
@return 0 成功， 非0失败
*/
int BusSendTo(int iPeerAddr, void *pData, int nDataSize);


/*!
@brief 数据接收
@param[IN] iPeerAddr 对端bus地址
@param[OUT] ppDataBuf 接收数据地址
@return 0未接收数据， >0 接收到数据
*/
int BusRecvFrom(int iPeerAddr, char **ppDataBuf);


#ifdef __cplusplus
}
#endif

#endif
