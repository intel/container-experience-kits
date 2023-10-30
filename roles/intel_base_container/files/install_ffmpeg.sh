#!/bin/bash

FFMPEG_VERSION="$1"
NETWORK_TYPE="$2"

echo "ffmpeg version is : $FFMPEG_VERSION"
echo "network type is : $NETWORK_TYPE"

apt-get update
apt-get install -y \
  autoconf \
  automake \
  build-essential \
  cmake \
  git-core \
  libass-dev \
  libfreetype6-dev \
  libgnutls28-dev \
  libmp3lame-dev \
  libsdl2-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  meson \
  ninja-build \
  pkg-config \
  texinfo \
  yasm \
  zlib1g-dev \
  nasm \
  libnuma-dev \
  libfdk-aac-dev \
  libopus-dev \
  libdav1d-dev \
  libmfx-dev \
  libvpl-dev \

FFMPEG_BUILD_DIR=ffmpeg_build
FFMPEG_UPSTREAM_VERSION=9b6d191
FFMPEG_PATCH_VERSION=2023q2
FFMPEG_INSTALL_PREFIX=/usr/local

mkdir -p $FFMPEG_BUILD_DIR

cd $FFMPEG_BUILD_DIR || exit

if [ "${NETWORK_TYPE}" = "prc_network" ]; then
    echo "Download from gitee mirror"
    git clone https://gitee.com/mirrors/ffmpeg.git ffmpeg_src
else
    echo "Download from github"
    git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg_src
fi

cd ffmpeg_src || exit
git checkout $FFMPEG_UPSTREAM_VERSION -b $FFMPEG_PATCH_VERSION

cd .. || exit
if [ "${NETWORK_TYPE}" = "prc_network" ]; then
    echo "Download from ghproxy mirror"
    curl -L https://ghproxy.com/github.com/intel/cartwheel-ffmpeg/archive/refs/tags/$FFMPEG_PATCH_VERSION.tar.gz -o cartwheel-patch.tar.gz
else
    echo "Download from github"
    curl -L https://github.com/intel/cartwheel-ffmpeg/archive/refs/tags/$FFMPEG_PATCH_VERSION.tar.gz -o cartwheel-patch.tar.gz
fi
mkdir -p cartwheel-patch
tar xvzf cartwheel-patch.tar.gz --strip-components 1 -C cartwheel-patch

cd ./ffmpeg_src || exit
git config user.email "builder@intel.com"
git config user.name  "builder"
git am ../cartwheel-patch/patches/*.patch
./configure --prefix=${FFMPEG_INSTALL_PREFIX} --enable-shared --enable-vaapi --enable-libvpl
make -j8
make install
