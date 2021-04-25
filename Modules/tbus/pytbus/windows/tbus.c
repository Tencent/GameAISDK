/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <Python.h>

#include "bus.h"

static PyObject * bus_init(PyObject *self, PyObject *args)
{
    int iRetVal;
    int iSelfAddr;
    char *pszCfgFile;

    if (!PyArg_ParseTuple(args, "is", &iSelfAddr, &pszCfgFile)) 
    {
        return NULL;
    }
    
    iRetVal = BusInit(iSelfAddr, pszCfgFile);
    
    return Py_BuildValue("i", iRetVal);
}

static PyObject * bus_exit(PyObject *self, PyObject *args)
{
    int iSelfAddr;

    if (!PyArg_ParseTuple(args, "i", &iSelfAddr)) 
    {
        return NULL;
    }
    
    BusExit(iSelfAddr);
    
    Py_RETURN_NONE;
}

static PyObject * bus_send_to(PyObject *self, PyObject *args)
{
    int iRetVal;
    int iPeerAddr;
    int iDataSize;
    char *pszDataBuf;
    
    if (!PyArg_ParseTuple(args, "iy#", &iPeerAddr, &pszDataBuf, &iDataSize)) 
    {
        return NULL; 
    }
    
    iRetVal = BusSendTo(iPeerAddr, pszDataBuf, iDataSize);
    
    return Py_BuildValue("i", iRetVal);
}

static PyObject * bus_recv_from(PyObject *self, PyObject *args)
{
    int iRetVal;
    int iPeerAddr;
    int iDataSize;
    char *pszDataBuf;
    PyObject *pRetObj;
    
    if (!PyArg_ParseTuple(args, "i", &iPeerAddr)) 
    {
        return NULL;  
    }
    
    iRetVal = BusRecvFrom(iPeerAddr, &pszDataBuf);
    if (iRetVal > 0)
    {
        return Py_BuildValue("y#", pszDataBuf, iRetVal);
    }
    else
    {
        Py_RETURN_NONE;
    }
}

static PyObject * bus_get_address(PyObject *self, PyObject *args)
{
    int iRetVal;
    int iAddress;
    char *pszAddress;
    
    if (!PyArg_ParseTuple(args, "s", &pszAddress))
    {
        return NULL;
    }
    
    iRetVal = BusGetAddress(pszAddress, &iAddress); 
    if (0 == iRetVal)
    {
        return Py_BuildValue("i", iAddress);
    }
    else
    {
        Py_RETURN_NONE;
    }
}

static PyMethodDef tbusMethods[] =  
{
    {"Init", bus_init, METH_VARARGS, "Init tbus channel."},
    {"Exit", bus_exit, METH_VARARGS, "Finish tbus channel."},
    {"SendTo", bus_send_to, METH_VARARGS, "Send data to tbus channel."},
    {"RecvFrom", bus_recv_from, METH_VARARGS, "Recv data from tbus channel"},
    {"GetAddress", bus_get_address, METH_VARARGS, "Get tbus address."},
    {NULL, NULL, 0, NULL},
};
  
static struct PyModuleDef tbusMoudle =
{
    PyModuleDef_HEAD_INIT,
    "tbus",
    NULL,
    -1,
    tbusMethods
};
  
void PyInit_tbus()
{
    PyModule_Create(&tbusMoudle);
}
