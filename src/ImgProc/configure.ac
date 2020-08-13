#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT(SDK, 1.0, xxx@tencent.com)
AM_INIT_AUTOMAKE(SDK, 1.0)
AC_CONFIG_SRCDIR([GameRecognize/src/IniConfClass.cpp])
AC_CONFIG_HEADERS([config.h])

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC

# Checks for libraries.
# FIXME: Replace `main' with a function in `-lX11':
GAMEREGLIBFLAG=
UIRECOGNIZELIBFLAG=
SPACE=' '
# AC_CHECK_LIB([X11], [main], [X11LIB=-lX11])
# GAMEREGLIBFLAG+=$X11LIB
# GAMEREGLIBFLAG+=$SPACE
# UIRECOGNIZELIBFLAG+=$X11LIB
# UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lboost_system':
AC_CHECK_LIB([boost_system], [main], [BOOSTSYSTEMLIB=-lboost_system], [
echo "Error! boost_system is needed"
exit -1]
)
GAMEREGLIBFLAG+=$BOOSTSYSTEMLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$BOOSTSYSTEMLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lboost_thread':
AC_CHECK_LIB([boost_thread], [main], BOOSTTHREADLIB=-lboost_thread, [
echo "Error! boost_thread is needed"
exit -1
])
GAMEREGLIBFLAG+=$BOOSTTHREADLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$BOOSTTHREADLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-ldl':
AC_CHECK_LIB([dl], [main], [DLLIB=-ldl], [
echo "Error! dl is needed"
exit -1
])
GAMEREGLIBFLAG+=$DLLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$DLLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_core':
AC_CHECK_LIB([opencv_core], [main], [OPENCVCORELIB=-lopencv_core], [
echo "Error! opencv_core is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVCORELIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVCORELIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_features2d':
AC_CHECK_LIB([opencv_features2d], [main], [OPENCVFEATURES2DLIB=-lopencv_features2d], [
echo "Error! opencv_features2d is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVFEATURES2DLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVFEATURES2DLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_highgui':
AC_CHECK_LIB([opencv_highgui], [main], [OPENCVHIGHGUILIB=-lopencv_highgui], [
echo "Error! opencv_highgui is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVHIGHGUILIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVHIGHGUILIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_imgcodecs':
AC_CHECK_LIB([opencv_imgcodecs], [main], [OPENCVIMGCEDECSLIB=-lopencv_imgcodecs])
GAMEREGLIBFLAG+=$OPENCVIMGCEDECSLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVIMGCEDECSLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_imgproc':
AC_CHECK_LIB([opencv_imgproc], [main], [OPENCVIMGPROCLIB=-lopencv_imgproc], [
echo "Error! opencv_imgproc is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVIMGPROCLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVIMGPROCLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_photo':
AC_CHECK_LIB([opencv_photo], [main], [OPENCVPHOTOLIB=-lopencv_photo], [
echo "Error! opencv_photo is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVPHOTOLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVPHOTOLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_video':
AC_CHECK_LIB([opencv_video], [main], [OPENCVVIDEOLIB=-lopencv_video], [
echo "Error! opencv_video is needed"
exit -1
])
GAMEREGLIBFLAG+=$OPENCVVIDEOLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVVIDEOLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lopencv_videoio':
AC_CHECK_LIB([opencv_videoio], [main], [OPENCVVIDEOIOLIB=-lopencv_videoio])
GAMEREGLIBFLAG+=$OPENCVVIDEOIOLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$OPENCVVIDEOIOLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lprotobuf':
AC_CHECK_LIB([protobuf], [main], [PROTOBUFLIB=-lprotobuf], [
echo "Error! protobuf is needed"
exit -1
])
GAMEREGLIBFLAG+=$PROTOBUFLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$PROTOBUFLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-lpthread':
AC_CHECK_LIB([pthread], [main], [PTHREADLIB=-lpthread], [
echo "Error! pthread is needed"
exit -1
])
GAMEREGLIBFLAG+=$PTHREADLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$PTHREADLIB
UIRECOGNIZELIBFLAG+=$SPACE
# FIXME: Replace `main' with a function in `-ltbus':
AC_CHECK_LIB([tbus], [main], [TBUSLIB=-ltbus], [
echo "Error! tbus is needed"
exit -1
])
GAMEREGLIBFLAG+=$TBUSLIB
GAMEREGLIBFLAG+=$SPACE
UIRECOGNIZELIBFLAG+=$TBUSLIB
UIRECOGNIZELIBFLAG+=$SPACE
AC_SUBST([GAMEREGLIBFLAG])
AC_SUBST([UIRECOGNIZELIBFLAG])
# Checks for header files.
AC_CHECK_HEADERS([stdlib.h])

CXXFLAGS=-g

LIBDARKNET=-ldarknetV3_CPU
GPUDEF=
AC_ARG_ENABLE(
    [GPU],
    AS_HELP_STRING(--enable-GPU, support GPU),
    [
        LIBDARKNET=-ldarknetV3_GPU
        GPUDEF=GPU
    ],
    [
        LIBDARKNET=-ldarknetV3_CPU
        GPUDEF=CPU
    ]
)
AC_SUBST([LIBDARKNET])
AC_SUBST([GPUDEF])

# Checks for typedefs, structures, and compiler characteristics.
AC_CHECK_HEADER_STDBOOL
AC_C_INLINE
AC_TYPE_INT16_T
AC_TYPE_SIZE_T
AC_TYPE_UINT64_T

# Checks for library functions.
AC_CHECK_FUNCS([memset sqrt])

# AC_CONFIG_FILES([Makefile])
AC_OUTPUT([
    Makefile
    GameRecognize/Makefile
    UI/Makefile
])
