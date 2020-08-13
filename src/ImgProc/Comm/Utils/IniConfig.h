/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef INI_CONFIG_H_
#define INI_CONFIG_H_

#include <fstream>
#include <string>


/*!
   @class : CIniConfig
   @brief : ini段键式配置文件读取/写入
 */
class CIniConfig
{
public:
    CIniConfig();
    virtual ~CIniConfig();

public:
    /*!
     * @brief 打开文件
     * @param[in] pszConfFilename ini格式配置文件路径
     * @return 0 成功， -1 文件名为空， -2 打开文件失败
     */
    int loadFile(const char *pszConfFilename);
    /*!
    * @brief 关闭文件
    */
    void closeFile();

public:
    /*!
     * @brief 读取字符串值
     * @param[in] pszSectionName section名
     * @param[in] pszKeyName key名
     * @param[in] pszDefaultStr 不存在时返回默认值
     * @param[in] pszRetValue 返回值缓存
     * @param[in] nRetLen 返回值缓存长度
     * @return >=0 成功， <0 失败
     */
    int getPrivateStr(const char *pszSectionName, const char *pszKeyName,
                      const char *pszDefaultStr, char *pszRetValue, const int nRetLen);

    /*!
     * @brief 返回所有的section名
     * @param[in] pszRetValue 返回值缓存
     * @param[in] nRetLen 返回值缓存长度
     * @return 0 成功， <0 失败
     */
    int getPrivateAllSection(char *pszRetValue, const int nRetLen);

    /*!
     * @brief 获取section名下所有的key名
     * @param[in] pszSectionName section名
     * @param[in] pszRetValue 返回值缓存
     * @param[in] nRetLen 返回值缓存长度
     * @return >=0 成功， <0 失败
     */
    int getPrivateAllKey(const char *pszSectionName, char *pszRetValue, const int nRetLen);

    /*！
     * @brief 获取int值
     * @param[in] pszSectionName section名
     * @param[in] pszKeyName key名
     * @param[in] nDefaultInt 若值不存在返回的默认值
     * @return int值
     */
    int getPrivateInt(const char *pszSectionName, const char *pszKeyName, const int nDefaultInt);

    /*!
     * @brief 获取bool值
     * @param[in] pszSectionName section名
     * @param[in] pszKeyName key名
     * @param[in] nDefaultInt 若值不存在返回的默认值
     * @return bool值
     */
    bool getPrivateBool(const char *pszSectionName, const char *pszKeyName, const int nDefaultInt);

public:
    /*!
     * @brief 从ini配置文件读取值
     * @param[in] pszSectionName section名
     * @param[in] pszKeyName key名
     * @param[in] pszDefaultStr 若值不存在返回默认值
     * @param[in] pszRetValue 返回值缓存
     * @param[in] nRetLen 返回值缓存长度
     * @return >=1 成功（实际返回值长度）， -1 返回值缓存不足
     */
    int getPrivateProfileString(const char *pszSectionName, const char *pszKeyName,
                                const char *pszDefaultStr, char *pszRetValue, const int nRetLen);

    int ProcessOperateOne(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
        char *pstrtmp, int  ntmp, char  *pszOneLine, const int nBufLen);
    int ProcessOperateTwo(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
        char *pstrtmp, int  ntmp, char  *pszOneLine, const int nBufLen, bool bApp, const char * pszSectionName);
    int ProcessOperateThree(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
        char *pstrtmp, int  ntmp, char  *pszOneLine, const int nBufLen);
    int ProcessOperateFour(const char *pszSectionName, const char *pszKeyName, const char *pszDefaultStr,
        char *pszRetValue, const int nRetLen, char *pstrtmp, int  ntmp, char  *pszOneLine, const int nBufLen);

private:
    std::string   m_strConfFileName; // 配置文件名
    std::ifstream m_ifStream; // 文件流
};

#endif // INI_CONFIG_H_
