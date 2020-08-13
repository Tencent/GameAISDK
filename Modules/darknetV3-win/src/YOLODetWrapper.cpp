
/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <boost/python.hpp>
#include <boost/tuple/tuple.hpp>

#include "ObjDet.h"
#include "YOLOV2Det.h"


using namespace boost::python;
using namespace cv;

#define MAX_DETECT_RESULT 100


struct  tagDetRet
{
	int      nClass;
	float    fScore;
	int      x;
	int      y;
	int      nWidth;
	int      nHeight;
};


class YOLODetWrapper
{
public:
	YOLODetWrapper();
	~YOLODetWrapper();
	bool Initialize(char* pszNetFile, char *pszWeightFile);
	boost::python::list  Detect(int rows, int cols, PyObject* imgData);

private:
	CYOLOV2Det m_oDetector;

};


YOLODetWrapper::YOLODetWrapper()
{

}

YOLODetWrapper::~YOLODetWrapper()
{

}

bool YOLODetWrapper::Initialize(char* pszNetFile, char *pszWeightFile)
{
	if (NULL == pszNetFile)
	{
		printf("input netfile is null, please check\n");
		return false;
	}

	if(NULL == pszWeightFile)
	{
		printf("input weight file is null, please check \n");
		return false;
	}

	return m_oDetector.Initialize(pszNetFile, pszWeightFile);
}

boost::python::list  YOLODetWrapper::Detect(int rows, int cols, PyObject* pImageData)
{

	boost::python::list  retList = boost::python::list();
	unsigned char *pData = (unsigned char *)PyBytes_AsString(pImageData);

    cv::Mat oSrcImg(rows, cols, CV_8UC3, pData);

	if(NULL == pImageData || oSrcImg.empty())
	{
		printf("input param is invalid, please check");
		return retList;
	}

	tagDetBBox   *pstResult;
	int nNum = 0;
	int nRet =  m_oDetector.Detect(oSrcImg, pstResult, nNum);
	for(int i = 0; i < nNum; i++)
	{
		tagDetRet stDetRet;
		stDetRet.x = pstResult[i].m_nLeft;
		stDetRet.y = pstResult[i].m_nTop;
		stDetRet.nWidth = pstResult[i].m_nWidth;
		stDetRet.nHeight = pstResult[i].m_nHeight;
		stDetRet.nClass = pstResult[i].m_nClass;
		stDetRet.fScore = pstResult[i].m_fConfidence;
		retList.append<tagDetRet>(stDetRet);
	}
	
	return retList;
}


BOOST_PYTHON_MODULE(YOLODetWrapper)
{
	boost::python::class_<YOLODetWrapper>("YOLODetWrapper")
		.def("Initialize", &YOLODetWrapper::Initialize)
		.def("Detect", &YOLODetWrapper::Detect);

	boost::python::class_<tagDetRet>("tagDetRet")
			.def_readonly("classinfo", &tagDetRet::nClass)
			.def_readonly("fScore", &tagDetRet::fScore)
			.def_readonly("x", &tagDetRet::x)
			.def_readonly("y", &tagDetRet::y)
			.def_readonly("width", &tagDetRet::nWidth)
			.def_readonly("height", &tagDetRet::nHeight);	
}
