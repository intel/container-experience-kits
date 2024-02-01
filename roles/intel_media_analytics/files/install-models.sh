#!/bin/bash

MODEL_PATH=${HOME}/models

cd "${HOME}" || exit
rm -rf yolov5-v6.2

git clone --branch v6.2 --depth 1 https://github.com/ultralytics/yolov5 yolov5-v6.2

pip install -r yolov5-v6.2/requirements.txt
pip install onnx==1.12.0 torch==1.13.0 torchvision==0.14.0 openvino-dev==2022.3

mkdir -p "${MODEL_PATH}"/public/yolov5m/
curl -L --output "${HOME}"/cars-on-highway.1920x1080.mp4 "https://www.pexels.com/video/854671/download/?h=1080&w=1920"
curl -L --output "${MODEL_PATH}"/public/yolov5m/yolov5m.pt \
    https://github.com/ultralytics/yolov5/releases/download/v6.2/yolov5m.pt
cd yolov5-v6.2 && python3 export.py --weights "${MODEL_PATH}"/public/yolov5m/yolov5m.pt \
    --imgsz 640 --batch 1 --include onnx
mo --input_model "${MODEL_PATH}"/public/yolov5m/yolov5m.onnx --model_name yolov5m \
    --scale 255 --reverse_input_channels \
    --output /model.24/m.0/Conv,/model.24/m.1/Conv,/model.24/m.2/Conv \
    --data_type FP16 \
    --output_dir "${MODEL_PATH}"/public/yolov5m/FP16
curl -L --output "${MODEL_PATH}"/public/yolov5m/yolov5m.json \
    https://raw.githubusercontent.com/dlstreamer/dlstreamer/2022.3-release/samples/gstreamer/model_proc/public/yolo-v5.json
curl -L --output "${MODEL_PATH}"/public/yolov5m/coco_80cl.txt \
    https://github.com/dlstreamer/dlstreamer/blob/2022.3-release/samples/labels/coco_80cl.txt?raw=true
