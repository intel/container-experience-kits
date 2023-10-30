#!/bin/bash

DLSTREAMER_VERSION="$1"
GPU_TYPE="$2"

echo "dlstreamer version is : $DLSTREAMER_VERSION"
echo "gpu type is : $GPU_TYPE"

apt-get install -y software-properties-common

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

/opt/intel/dlstreamer/install_dependencies/install_kafka_client.sh
/opt/intel/dlstreamer/install_dependencies/install_mqtt_client.sh
