#!/bin/bash

DLSTREAMER_VERSION="$1"
GPU_TYPE="$2"
NETWORK_TYPE="$3"

echo "dlstreamer version is : $DLSTREAMER_VERSION"
echo "gpu type is : $GPU_TYPE"
echo "network type is : $NETWORK_TYPE"


if [ "${DLSTREAMER_VERSION}" = "default" ]; then
    # the latest openvino 2022.3 lts release is 2022.3.1
    # default use openvino 2022.3.0 for dlsreamer 2022.3.0 compatiblity
    DLSTREAMER_VERSION=2022.3.0
fi
echo "openvino version is : $DLSTREAMER_VERSION"


if [ "${DLSTREAMER_VERSION}" = "2023.0.0" ]; then

    DLSTREAMER_PKG_DIR=dlstreamer_pkg

    mkdir -p $DLSTREAMER_PKG_DIR
    cd $DLSTREAMER_PKG_DIR || exit

    apt-get update; apt-get install -y software-properties-common jq

    curl -L -o /tmp/intel-sw-products.pub https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB
    gpg --dearmor < /tmp/intel-sw-products.pub > /usr/share/keyrings/intel-sw-products.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sw-products.gpg] https://apt.repos.intel.com/oneapi all main" >> /etc/apt/sources.list.d/intel-oneapi.list

    apt-get update

    curl -L -o ./libgstreamer-plugins-bad1.0-0_1.20.3-0ubuntu1_amd64.deb http://launchpadlibrarian.net/610729018/libgstreamer-plugins-bad1.0-0_1.20.3-0ubuntu1_amd64.deb
    curl -L -o ./gstreamer1.0-plugins-bad_1.20.3-0ubuntu1_amd64.deb http://launchpadlibrarian.net/610729015/gstreamer1.0-plugins-bad_1.20.3-0ubuntu1_amd64.deb
    apt-get install -y ./libgstreamer-plugins-bad1.0-0_1.20.3-0ubuntu1_amd64.deb
    apt-get install -y ./gstreamer1.0-plugins-bad_1.20.3-0ubuntu1_amd64.deb
    apt-mark hold libgstreamer-plugins-bad1.0-0
    apt-mark hold gstreamer1.0-plugins-bad

    if [ "${NETWORK_TYPE}" = "prc_network" ]; then
        curl -L -o ./intel-dlstreamer_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-bins_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-bins_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-cpp_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-cpp_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-cpu_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-cpu_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-dpcpp_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-dpcpp_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-env_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-env_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-ffmpeg_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-ffmpeg_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gpu_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gpu_2023.0.0.1341_amd64.deb

        curl -L -o ./intel-dlstreamer-gst_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-gstreamer1.0_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-gstreamer1.0_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-libav_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-libav_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-base_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-base_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-good_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-good_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-bad_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-bad_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-ugly_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-ugly_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-python3_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-python3_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-python3-plugin-loader_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-python3-plugin-loader_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-rtsp-server_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-rtsp-server_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-vaapi_1.22.5.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-vaapi_1.22.5.1341_amd64.deb

        curl -L -o ./intel-dlstreamer-opencl_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-opencl_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-opencv_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-opencv_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-openvino_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-openvino_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-vaapi_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-vaapi_2023.0.0.1341_amd64.deb
        curl -L -o ./python3-intel-dlstreamer_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/python3-intel-dlstreamer_2023.0.0.1341_amd64.deb

        #curl -L -o ./intel-dlstreamer-dev_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-dev_2023.0.0.1341_amd64.deb
        #curl -L -o ./intel-dlstreamer-samples_2023.0.0.1341_amd64.deb  https://hub.gitmirror.com/github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-samples_2023.0.0.1341_amd64.deb
    else
        curl -L -o ./intel-dlstreamer_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-bins_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-bins_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-cpp_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-cpp_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-cpu_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-cpu_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-dpcpp_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-dpcpp_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-env_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-env_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-ffmpeg_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-ffmpeg_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gpu_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gpu_2023.0.0.1341_amd64.deb

        curl -L -o ./intel-dlstreamer-gst_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-gstreamer1.0_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-gstreamer1.0_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-libav_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-libav_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-base_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-base_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-good_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-good_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-bad_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-bad_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-plugins-ugly_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-plugins-ugly_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-python3_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-python3_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-python3-plugin-loader_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-python3-plugin-loader_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-rtsp-server_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-rtsp-server_1.22.5.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-gst-vaapi_1.22.5.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-gst-vaapi_1.22.5.1341_amd64.deb

        curl -L -o ./intel-dlstreamer-opencl_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-opencl_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-opencv_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-opencv_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-openvino_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-openvino_2023.0.0.1341_amd64.deb
        curl -L -o ./intel-dlstreamer-vaapi_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-vaapi_2023.0.0.1341_amd64.deb
        curl -L -o ./python3-intel-dlstreamer_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/python3-intel-dlstreamer_2023.0.0.1341_amd64.deb

        #curl -L -o ./intel-dlstreamer-dev_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-dev_2023.0.0.1341_amd64.deb
        #curl -L -o ./intel-dlstreamer-samples_2023.0.0.1341_amd64.deb  https://github.com/dlstreamer/dlstreamer/releases/download/2023.0-release/intel-dlstreamer-samples_2023.0.0.1341_amd64.deb
    fi

    apt-get install -y ./*.deb

    pip install -r /opt/intel/dlstreamer/install_dependencies/requirements.txt

else
    # dlstreamer 2023.0 needs special workaround to downgrade VA libs to 2.17
    apt-get update; apt-get install -y software-properties-common

    curl -L -o /tmp/intel-sw-products.pub https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB
    gpg --dearmor < /tmp/intel-sw-products.pub > /usr/share/keyrings/intel-sw-products.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sw-products.gpg] https://apt.repos.intel.com/openvino/2022 jammy main" >> /etc/apt/sources.list.d/intel-dlstreamer.list
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sw-products.gpg] https://apt.repos.intel.com/oneapi all main" >> /etc/apt/sources.list.d/intel-oneapi.list

    rm -f /usr/share/keyrings/intel-graphics.gpg
    curl -L -o /tmp/intel-graphics.key https://repositories.intel.com/graphics/intel-graphics.key
    gpg --dearmor < /tmp/intel-graphics.key > /usr/share/keyrings/intel-graphics.gpg

    rm /etc/apt/sources.list.d/intel-gpu-jammy.list
    if [ "${GPU_TYPE}" = "Flex" ]; then
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu jammy flex" >> /etc/apt/sources.list.d/intel-gpu-jammy.list
    elif [ "${GPU_TYPE}" = "Arc" ] || [ "${GPU_TYPE}" = "iGPU" ]; then
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu jammy arc" >> /etc/apt/sources.list.d/intel-gpu-jammy.list
    else
        echo "Unknown GPU, no gpu stack workaround"
    fi

    apt-get update

    # Workaround as current Dlstreamer release depends on libva 2.17
    if [ "${GPU_TYPE}" == "Flex" ] || [ "${GPU_TYPE}" == "Arc" ] || [ "${GPU_TYPE}" == "iGPU" ]; then
    apt-mark unhold \
        libva2 \
        libva-drm2 \
        libva-wayland2 \
        libva-x11-2 \
        libva-glx2 \
        va-driver-all \
        intel-media-va-driver-non-free \
        libigfxcmrt7 \
        libigfxcmrt-dev

    apt-get install -y --allow-downgrades \
        libva2=2.17.0.2-44 \
        libva-drm2=2.17.0.2-44 \
        libva-wayland2=2.17.0.2-44 \
        libva-x11-2=2.17.0.2-44 \
        libva-glx2=2.17.0.2-44 \
        va-driver-all=2.17.0.2-44 \
        intel-media-va-driver-non-free=23.1.0+i553~22.04 \
        libigfxcmrt7=23.1.0+i553~22.04 \
        libigfxcmrt-dev=23.1.0+i553~22.04

    apt-mark hold \
        libva2 \
        libva-drm2 \
        libva-wayland2 \
        libva-x11-2 \
        libva-glx2 \
        va-driver-all \
        intel-media-va-driver-non-free \
        libigfxcmrt7 \
        libigfxcmrt-dev
    fi

    # Install dlstreamer
    apt-get install -y \
        intel-dlstreamer=2022.3.0.250 \
        python3-intel-dlstreamer=2022.3.0.250 \
        intel-dlstreamer-dpcpp=2022.3.0.250

    #    intel-dlstreamer-samples=2022.3.0.250

    pip install --upgrade --force-reinstall numpy

fi

/opt/intel/dlstreamer/install_dependencies/install_kafka_client.sh
/opt/intel/dlstreamer/install_dependencies/install_mqtt_client.sh
