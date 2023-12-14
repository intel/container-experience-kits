#!/bin/bash

OPENCV_VERSION="$1"
NETWORK_TYPE="$2"

echo "opencv version is : $OPENCV_VERSION"
echo "network type is : $NETWORK_TYPE"

apt-get update

apt-get install -y git \
build-essential \
cmake \
ninja-build \
libgtk-3-dev  \
libx11-dev \
libtbb2  \
libssl-dev  \
libva-dev \
libmfx-dev \
libva-glx2 \
libgbm-dev \

if [ "${OPENCV_VERSION}" = "default" ]; then
    OPENCV_VERSION=4.7.0
fi
OPENCV_INSTALL_PREFIX=/usr/local

source /opt/intel/openvino/setupvars.sh

rm -rf ./opencv_src

if [ "${NETWORK_TYPE}" = "prc_network" ]; then
    echo "Download from gitCode"
    git clone -b "${OPENCV_VERSION}" --depth 1 --recurse-submodules https://gitcode.net/opencv/opencv opencv_src
else
    echo "Download from github"
    git clone -b "${OPENCV_VERSION}" --depth 1 --recurse-submodules https://github.com/opencv/opencv.git opencv_src
fi
sed -i "s/, device_fd//" ./opencv_src/modules/gapi/test/streaming/gapi_streaming_vpl_device_selector.cpp

mkdir -p opencv_src/build
cd opencv_src/build || exit

cmake -G Ninja -D BUILD_INFO_SKIP_EXTRA_MODULES=ON \
-D BUILD_EXAMPLES=OFF \
-D BUILD_JASPER=OFF \
-D BUILD_JAVA=OFF \
-D BUILD_JPEG=OFF \
-D BUILD_APPS_LIST=version \
-D BUILD_opencv_apps=OFF \
-D BUILD_opencv_java=OFF \
-D BUILD_OPENEXR=OFF \
-D BUILD_PNG=OFF \
-D BUILD_TBB=OFF \
-D BUILD_WEBP=OFF \
-D BUILD_ZLIB=OFF \
-D WITH_1394=OFF \
-D WITH_CUDA=OFF \
-D WITH_EIGEN=OFF \
-D WITH_OPENVINO=ON \
-D WITH_GAPI_ONEVPL=ON \
-D WITH_GPHOTO2=OFF \
-D WITH_FFMPEG=ON \
-D WITH_GSTREAMER=OFF \
-D OPENCV_GAPI_GSTREAMER=OFF \
-D WITH_GTK_2_X=OFF \
-D WITH_IPP=ON \
-D WITH_JASPER=OFF \
-D WITH_LAPACK=OFF \
-D WITH_MATLAB=OFF \
-D WITH_MFX=ON \
-D WITH_OPENCLAMDBLAS=OFF \
-D WITH_OPENCLAMDFFT=OFF \
-D WITH_OPENEXR=OFF \
-D WITH_OPENJPEG=OFF \
-D WITH_QUIRC=ON \
-D WITH_TBB=OFF \
-D WITH_TIFF=OFF \
-D WITH_VTK=OFF \
-D WITH_WEBP=OFF \
-D CMAKE_USE_RELATIVE_PATHS=ON \
-D CMAKE_SKIP_INSTALL_RPATH=ON \
-D ENABLE_BUILD_HARDENING=ON \
-D ENABLE_CONFIG_VERIFICATION=ON \
-D ENABLE_PRECOMPILED_HEADERS=OFF \
-D ENABLE_CXX11=ON \
-D INSTALL_PDB=OFF \
-D INSTALL_TESTS=OFF \
-D INSTALL_C_EXAMPLES=OFF \
-D INSTALL_PYTHON_EXAMPLES=OFF \
-D CMAKE_INSTALL_PREFIX=${OPENCV_INSTALL_PREFIX} \
-D OPENCV_SKIP_PKGCONFIG_GENERATION=ON \
-D OPENCV_SKIP_PYTHON_LOADER=OFF \
-D OPENCV_SKIP_CMAKE_ROOT_CONFIG=ON \
-D OPENCV_GENERATE_SETUPVARS=OFF \
-D OPENCV_BIN_INSTALL_PATH=bin \
-D OPENCV_INCLUDE_INSTALL_PATH=include \
-D OPENCV_LIB_INSTALL_PATH=lib \
-D OPENCV_CONFIG_INSTALL_PATH=cmake \
-D OPENCV_3P_LIB_INSTALL_PATH=3rdparty \
-D OPENCV_SAMPLES_SRC_INSTALL_PATH=samples \
-D OPENCV_DOC_INSTALL_PATH=doc \
-D OPENCV_OTHER_INSTALL_PATH=etc \
-D OPENCV_LICENSES_INSTALL_PATH=etc/licenses \
-D OPENCV_INSTALL_FFMPEG_DOWNLOAD_SCRIPT=ON \
-D BUILD_opencv_world=OFF \
-D BUILD_opencv_python2=OFF \
-D BUILD_opencv_python3=ON \
-D PYTHON3_PACKAGES_PATH=install/python/python3 \
-D PYTHON3_LIMITED_API=ON \
-D HIGHGUI_PLUGIN_LIST=all \
-D OPENCV_PYTHON_INSTALL_PATH=python \
-D CPU_BASELINE=SSE4_2 \
-D OPENCV_IPP_GAUSSIAN_BLUR=ON \
-D WITH_OPENVINO=ON \
-D VIDEOIO_PLUGIN_LIST=ffmpeg,mfx \
-D CMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined \
-D CMAKE_BUILD_TYPE=Release \
..
ninja
cmake --install .

mkdir -p ../../opencv_test/bin
cp -a bin/* ../../opencv_test/bin
