#!/bin/bash

# set repo according to gpu type
curl -L -o /tmp/intel-graphics.key https://repositories.intel.com/graphics/intel-graphics.key
gpg --dearmor < /tmp/intel-graphics.key > /usr/share/keyrings/intel-graphics.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu jammy arc" >> /etc/apt/sources.list.d/intel-gpu-jammy.list
apt-get update

GPU_STACK_VERSION=20230714

if (("${GPU_STACK_VERSION}" == 20230714))
then

  echo "gpu stack version : 20230714"
  # install umd and runtime packages
  apt-get install -y --allow-downgrades \
    intel-opencl-icd=23.17.26241.33-647~22.04 \
    intel-level-zero-gpu=1.3.26241.33-647~22.04 \
    level-zero=1.11.0-647~22.04 \
    intel-media-va-driver-non-free=23.2.1-647~22.04 \
    libmfx1=23.2.1-647~22.04 \
    libmfxgen1=23.2.1-647~22.04 \
    libvpl2=2023.2.1.0-647~22.04 \
    libegl-mesa0=23.2.0.20230414.1+2061~u22.04 \
    libegl1-mesa=23.2.0.20230414.1+2061~u22.04 \
    libegl1-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libgbm1=23.2.0.20230414.1+2061~u22.04 \
    libgl1-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libgl1-mesa-dri=23.2.0.20230414.1+2061~u22.04 \
    libglapi-mesa=23.2.0.20230414.1+2061~u22.04 \
    libgles2-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libglx-mesa0=23.2.0.20230414.1+2061~u22.04 \
    libigdgmm12=22.3.5-647~22.04 \
    libxatracker2=23.2.0.20230414.1+2061~u22.04 \
    mesa-va-drivers=23.2.0.20230414.1+2061~u22.04 \
    mesa-vdpau-drivers=23.2.0.20230414.1+2061~u22.04 \
    mesa-vulkan-drivers=23.2.0.20230414.1+2061~u22.04 \
    va-driver-all=2.18.0.2-61~u22.04

  # install dev packages
  apt-get install -y --allow-downgrades \
    libigc1=1.0.13822.8-647~22.04 \
    libigc-dev=1.0.13822.8-647~22.04 \
    intel-igc-cm=1.0.176+i600~22.04 \
    libigdfcl1=1.0.13822.8-647~22.04 \
    libigdfcl-dev=1.0.13822.8-647~22.04 \
    libigfxcmrt7=23.2.1-647~22.04 \
    libigfxcmrt-dev=23.2.1-647~22.04 \
    level-zero-dev=1.11.0-647~22.04

  # install xpum packages
  # apt-get install -y --allow-downgrades \
  #  xpu-smi=1.2.13-24~22.04

else

  echo "gpu stack version : 20230526"
  # install umd and runtime packages
  apt-get install -y --allow-downgrades \
    intel-opencl-icd=23.13.26032.26-627~22.04 \
    intel-level-zero-gpu=1.3.26032.26-627~22.04 \
    level-zero=1.9.9-625~22.04 \
    intel-media-va-driver-non-free=23.1.6-622~22.04 \
    libmfx1=23.1.6-622~22.04 \
    libmfxgen1=23.1.5-622~22.04 \
    libvpl2=2023.1.3.0-622~22.04 \
    libegl-mesa0=23.2.0.20230414.1+2061~u22.04 \
    libegl1-mesa=23.2.0.20230414.1+2061~u22.04 \
    libegl1-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libgbm1=23.2.0.20230414.1+2061~u22.04 \
    libgl1-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libgl1-mesa-dri=23.2.0.20230414.1+2061~u22.04 \
    libglapi-mesa=23.2.0.20230414.1+2061~u22.04 \
    libgles2-mesa-dev=23.2.0.20230414.1+2061~u22.04 \
    libglx-mesa0=23.2.0.20230414.1+2061~u22.04 \
    libigdgmm12=22.3.5-622~22.04 \
    libxatracker2=23.2.0.20230414.1+2061~u22.04 \
    mesa-va-drivers=23.2.0.20230414.1+2061~u22.04 \
    mesa-vdpau-drivers=23.2.0.20230414.1+2061~u22.04 \
    mesa-vulkan-drivers=23.2.0.20230414.1+2061~u22.04 \
    va-driver-all=2.18.0.2-60~u22.04

  # install dev packages
  apt-get install -y --allow-downgrades \
    libigc1=1.0.13700.13-627~22.04 \
    libigc-dev=1.0.13700.13-627~22.04 \
    intel-igc-cm=1.0.176+i600~22.04 \
    libigdfcl1=1.0.13700.13-627~22.04 \
    libigdfcl-dev=1.0.13700.13-627~22.04 \
    libigfxcmrt7=23.1.6-622~22.04 \
    libigfxcmrt-dev=23.1.6-622~22.04 \
    level-zero-dev=1.9.9-625~22.04 \
    libvpl-dev=2023.1.3.0-622~22.04

  # include xpum packages
  # apt-get install -y --allow-downgrades \
  #  xpu-smi=1.2.3-13~u22.04

fi

# include test and tool packages
apt-get install -y --allow-downgrades \
  hwinfo \
  vainfo \
  clinfo \
  mesa-utils \
  vulkan-tools
