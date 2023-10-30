#!/bin/bash

OPENVINO_VERSION="$1"

echo "openvino version is : $OPENVINO_VERSION"

if [ "${OPENVINO_VERSION}" = "default" ]; then
    # the latest openvino 2022.3 lts release is 2022.3.1
    # default use openvino 2022.3.0 for dlsreamer 2022.3.0 compatiblity
    OPENVINO_VERSION=2022.3.0
fi
echo "openvino version is : $OPENVINO_VERSION"


if [ "${OPENVINO_VERSION}" = "2023.1.0" ]; then

    python3 -m venv venv_openvino_2023 --prompt openvino_2023_dev
    python3 -m pip install --upgrade pip
    pip install "openvino-dev[onnx,tensorflow,pytorch]==2023.1.0"
    ln -s "$HOME/venv_openvino_2023"  "$HOME/venv_openvino"

elif [ "${OPENVINO_VERSION}" = "2023.0.0" ]; then

    python3 -m venv venv_openvino_2023 --prompt openvino_2023_dev
    python3 -m pip install --upgrade pip
    pip install "openvino-dev[onnx,tensorflow,pytorch]==2023.0.0"
    ln -s "$HOME/venv_openvino_2023"  "$HOME/venv_openvino"

else

    python3 -m venv venv_openvino_2022 --prompt openvino_2022_dev
    python3 -m pip install --upgrade pip
    pip install "openvino-dev[onnx,tensorflow,pytorch]==2022.3.0"
    ln -s "$HOME/venv_openvino_2022"  "$HOME/venv_openvino"
fi
