/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef COLOR_MATCH_H_
#define COLOR_MATCH_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CObjDet.h"

// **************************************************************************************
//          CColorMatch Parameter Class Define
// **************************************************************************************

class CColorMatchParam : public CObjDetParam
{
public:
    CColorMatchParam()
    {
        m_nScaleLevel = 1;
        m_fMinScale   = 1.0;
        m_fMaxScale   = 1.0;
        m_strOpt        = "-matchMethod CCOEFF_NORMED";
        m_oVecTmpls.clear();
    }
    virtual ~CColorMatchParam() {}

public:
    int                  m_nScaleLevel; // scale level for multi-scale matching
    float                m_fMinScale; // min scale
    float                m_fMaxScale; // max scale
    std::string          m_strOpt; // method optional
    std::vector<tagTmpl> m_oVecTmpls; // matching templates
};

// **************************************************************************************
//          CColorMatch Factory Class Define
// **************************************************************************************

class CColorMatchFactory : public IObjDetFactory
{
public:
    CColorMatchFactory();
    ~CColorMatchFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CColorMatch Class Define
// **************************************************************************************

class CColorMatch : public CObjDet
{
public:
    CColorMatch();
    ~CColorMatch();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

private:
    int ParseParam(const CColorMatchParam *pParam);
    int MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls, std::vector<tagBBox> &oVecBBoxes);

private:
    std::string          m_strMethod; // name of matching method
    std::vector<tagTmpl> m_oVecTmpls; // matching templates
};

#endif /* COLOR_MATCH_H_ */
