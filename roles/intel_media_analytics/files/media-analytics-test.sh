#!/bin/bash

source /opt/intel/oneapi/setvars.sh
source /opt/intel/openvino/setupvars.sh
source /opt/intel/dlstreamer/setupvars.sh

VIDEO_IN=${1:-cars-on-highway.1920x1080.mp4}
VIDEO_OUT=${2:-cars-on-highway-annotated.mp4}

DET_MODEL=models/public/yolov5m/FP16/yolov5m.xml
DET_MODEL_PROC=models/public/yolov5m/yolov5m.json

gst-launch-1.0 -e filesrc location="${VIDEO_IN}" ! \
qtdemux ! \
h264parse ! \
vaapih264dec ! \
video/x-raw\(memory:VASurface\) ! \
gvadetect \
pre-process-backend=vaapi-surface-sharing \
pre-process-config=VAAPI_FAST_SCALE_LOAD_FACTOR=1 \
model=${DET_MODEL} \
model-proc=${DET_MODEL_PROC} \
device=GPU ! \
meta_overlay ! \
gvafpscounter ! \
vaapih264enc ! \
h264parse ! \
mp4mux ! \
filesink \
location=/tmp/"${VIDEO_OUT}"
