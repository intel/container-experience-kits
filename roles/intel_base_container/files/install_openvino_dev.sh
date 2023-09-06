#!/bin/bash

python3 -m venv venv_openvino_2022 --prompt openvino_2022_dev
export PATH="$HOME/venv_openvino_2022/bin:$PATH"
python3 -m pip install --upgrade pip
pip install "openvino-dev[onnx,tensorflow,pytorch]==2022.3.0"

