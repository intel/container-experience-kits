#!/bin/bash

# This script is used for developer to maintain this role in future,
# not used during CEK deployment.
# Developer can use this script on his dev machine, to get the package
# list for the latest gpu driver release, then paste gpu package vars.

echo "Get latest gpu package versions"

echo "gpu_kmd packages :"
#apt-cache madison intel-platform-vsec-dkms | head -n 1
#apt-cache madison intel-platform-cse-dkms | head -n 1
apt-cache madison intel-i915-dkms | head -n 1
apt-cache madison intel-fw-gpu | head -n 1

echo "gpu_umd_rt_packages :"
apt-cache madison intel-opencl-icd | head -n 1
apt-cache madison intel-level-zero-gpu | head -n 1
apt-cache madison level-zero | head -n 1
apt-cache madison intel-media-va-driver-non-free | head -n 1
apt-cache madison libmfx1 | head -n 1
apt-cache madison libmfxgen1 | head -n 1
apt-cache madison libvpl2 | head -n 1
apt-cache madison libegl-mesa0 | head -n 1
apt-cache madison libegl1-mesa | head -n 1
apt-cache madison libegl1-mesa-dev | head -n 1
apt-cache madison libgbm1 | head -n 1
apt-cache madison libgl1-mesa-dev | head -n 1
apt-cache madison libgl1-mesa-dri | head -n 1
apt-cache madison libglapi-mesa | head -n 1
apt-cache madison libgles2-mesa-dev | head -n 1
apt-cache madison libglx-mesa0 | head -n 1
apt-cache madison libigdgmm12 | head -n 1
apt-cache madison libxatracker2 | head -n 1
apt-cache madison mesa-va-drivers | head -n 1
apt-cache madison mesa-vdpau-drivers | head -n 1
apt-cache madison mesa-vulkan-drivers | head -n 1
apt-cache madison va-driver-all | head -n 1

echo "gpu_dev_packages :"
apt-cache madison libigc1 | head -n 1
apt-cache madison libigc-dev | head -n 1
apt-cache madison intel-igc-cm | head -n 1
apt-cache madison libigdfcl1 | head -n 1
apt-cache madison libigdfcl-dev | head -n 1
apt-cache madison libigfxcmrt7 | head -n 1
apt-cache madison libigfxcmrt-dev | head -n 1
apt-cache madison level-zero-dev | head -n 1
apt-cache madison libvpl-dev | head -n 1


echo "gpu_tool_packages :"
apt-cache madison xpu-smi | head -n 1
apt-cache madison libmetee | head -n 1
