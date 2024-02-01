#!/bin/bash

GPU_STACK_VERSION="$1"
GPU_TYPE="$2"

echo "gpu stack version : $GPU_STACK_VERSION"
echo "gpu type is : $GPU_TYPE"

# set repo according to gpu type

curl -L -o /tmp/intel-graphics.key https://repositories.intel.com/graphics/intel-graphics.key
gpg --dearmor < /tmp/intel-graphics.key > /usr/share/keyrings/intel-graphics.gpg

if [ "${GPU_TYPE}" = "Flex" ]; then
  rm -f /etc/apt/sources.list.d/intel-gpu-jammy.list
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy/production/2328 unified" >> /etc/apt/sources.list.d/intel-gpu-jammy.list
  apt-get update

  echo "install server gpu stack"
  # install umd and runtime packages for server GPU
  apt-get install -y --allow-downgrades \
    intel-opencl-icd=23.22.26516.34-682~22.04 \
    intel-level-zero-gpu=1.3.26516.34-682~22.04 \
    level-zero=1.11.0-649~22.04 \
    intel-media-va-driver-non-free=23.2.4-682~22.04 \
    libmfx1=23.2.2-682~22.04 \
    libmfxgen1=23.2.4-682~22.04 \
    libvpl2=2023.3.0.0-682~22.04 \
    libegl-mesa0=24.0.0.20231114.1-2088~22.04 \
    libegl1-mesa=24.0.0.20231114.1-2088~22.04 \
    libegl1-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libgbm1=24.0.0.20231114.1-2088~22.04 \
    libgl1-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libgl1-mesa-dri=24.0.0.20231114.1-2088~22.04 \
    libglapi-mesa=24.0.0.20231114.1-2088~22.04 \
    libgles2-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libglx-mesa0=24.0.0.20231114.1-2088~22.04 \
    libigdgmm12=22.3.7-678~22.04 \
    libxatracker2=24.0.0.20231114.1-2088~22.04 \
    mesa-va-drivers=24.0.0.20231114.1-2088~22.04 \
    mesa-vdpau-drivers=24.0.0.20231114.1-2088~22.04 \
    mesa-vulkan-drivers=24.0.0.20231114.1-2088~22.04 \
    va-driver-all=2.20.0.2-75~u22.04

  # install dev packages for server GPU
  apt-get install -y --allow-downgrades \
    libigc1=1.0.14062.19-682~22.04 \
    libigc-dev=1.0.14062.19-682~22.04 \
    intel-igc-cm=1.0.202-682~22.04 \
    libigdfcl1=1.0.14062.19-682~22.04 \
    libigdfcl-dev=1.0.14062.19-682~22.04 \
    libigfxcmrt7=23.2.4-682~22.04 \
    libigfxcmrt-dev=23.2.4-682~22.04 \
    level-zero-dev=1.11.0-649~22.04 \
    libvpl-dev=2023.3.0.0-682~22.04

elif [[ "${GPU_TYPE}" = "Arc" || "${GPU_TYPE}" = "iGPU" ]]; then
  rm -f /etc/apt/sources.list.d/intel-gpu-jammy.list
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy client" >> /etc/apt/sources.list.d/intel-gpu-jammy.list
  apt-get update

  echo "install client gpu stack"
  # install umd and runtime packages for client GPU
  apt-get install -y --allow-downgrades \
    intel-opencl-icd=23.35.27191.42-775~22.04 \
    intel-level-zero-gpu=1.3.27191.42-775~22.04 \
    level-zero=1.14.0-744~22.04 \
    intel-media-va-driver-non-free=23.4.0-775~22.04 \
    libmfx1=23.2.2-775~22.04 \
    libmfxgen1=23.4.0-775~22.04 \
    libvpl2=2023.3.1.0-775~22.04 \
    libegl-mesa0=24.0.0.20231114.1-2088~22.04 \
    libegl1-mesa=24.0.0.20231114.1-2088~22.04 \
    libegl1-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libgbm1=24.0.0.20231114.1-2088~22.04 \
    libgl1-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libgl1-mesa-dri=24.0.0.20231114.1-2088~22.04 \
    libglapi-mesa=24.0.0.20231114.1-2088~22.04 \
    libgles2-mesa-dev=24.0.0.20231114.1-2088~22.04 \
    libglx-mesa0=24.0.0.20231114.1-2088~22.04 \
    libigdgmm12=22.3.12-742~22.04 \
    libxatracker2=24.0.0.20231114.1-2088~22.04 \
    mesa-va-drivers=24.0.0.20231114.1-2088~22.04 \
    mesa-vdpau-drivers=24.0.0.20231114.1-2088~22.04 \
    mesa-vulkan-drivers=24.0.0.20231114.1-2088~22.04 \
    va-driver-all=2.20.0.2-75~u22.04

  # install dev packages for client GPU
  apt-get install -y --allow-downgrades \
    libigc1=1.0.15136.24-775~22.04 \
    libigc-dev=1.0.15136.24-775~22.04 \
    intel-igc-cm=1.0.206-775~22.04 \
    libigdfcl1=1.0.15136.24-775~22.04 \
    libigdfcl-dev=1.0.15136.24-775~22.04 \
    libigfxcmrt7=23.4.0-775~22.04 \
    libigfxcmrt-dev=23.4.0-775~22.04 \
    level-zero-dev=1.14.0-744~22.04 \
    libvpl-dev=2023.3.1.0-775~22.04

else
  echo "Unknown GPU, no gpu stack will be installed"

fi

# install GPU type independent test and tool packages
apt-get install -y --allow-downgrades \
  hwinfo \
  vainfo \
  clinfo \
  mesa-utils \
  vulkan-tools \
  onevpl-tools
