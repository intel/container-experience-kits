#!/bin/bash

VIDEO_IN=${1:-cars-on-highway.1920x1080.mp4}
VIDEO_OUT=${2:-cars-on-highway-annotated.mp4}

# shellcheck source=/dev/null
source /opt/intel/openvino_2022/setupvars.sh
# shellcheck source=/dev/null
source /opt/intel/dlstreamer/setupvars.sh

DET_MODEL=models/public/yolov5m/FP16/yolov5m.xml
DET_MODEL_PROC=models/public/yolov5m/yolov5m.json
DET_LABEL='labels-file=models/public/yolov5m/coco_80cl.txt'

CLS_MODEL=models/intel/vehicle-attributes-recognition-barrier-0039/FP16-INT8/vehicle-attributes-recognition-barrier-0039.xml
CLS_MODEL_PROC=models/intel/vehicle-attributes-recognition-barrier-0039/vehicle-attributes-recognition-barrier-0039.json

INC_DETECT="gvadetect pre-process-backend=vaapi-surface-sharing \
           model=${DET_MODEL} \
           model-proc=${DET_MODEL_PROC} \
           ${DET_LABEL} \
           ie-config=CACHE_DIR=./cl_cache \
           device=GPU ! "\

#INC_TRACK="gvatrack tracking-type=short-term-imageless ! "

INC_CLASSIFY="gvaclassify pre-process-backend=vaapi-surface-sharing \
           model=${CLS_MODEL} \
           model-proc=${CLS_MODEL_PROC} \
           ${CLS_LABEL} \
           inference-region=roi-list object-class=car \
           ie-config=CACHE_DIR=./cl_cache \
           device=GPU ! "

#INC_METAPUBLISH='gvametaconvert ! gvametapublish !'

INC_WATERMARK='meta_overlay device=GPU !'

set -x
# shellcheck disable=SC2086
gst-launch-1.0 filesrc location=${VIDEO_IN} ! \
           decodebin ! video/x-raw\(memory:VASurface\) ! \
           ${INC_DETECT} \
           ${INC_TRACK} \
           ${INC_CLASSIFY} \
           ${INC_METAPUBLISH} \
           ${INC_WATERMARK} \
           gvafpscounter ! \
           queue ! vaapih264enc bitrate=2048 ! h264parse ! \
           mp4mux ! filesink location=/tmp/${VIDEO_OUT}
