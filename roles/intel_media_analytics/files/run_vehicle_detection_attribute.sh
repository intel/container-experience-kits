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

INC_DETECT_CMD=(
    "gvadetect"
    "pre-process-backend=vaapi-surface-sharing"
    "model=${DET_MODEL}"
    "model-proc=${DET_MODEL_PROC}"
    "${DET_LABEL}"
    "ie-config=CACHE_DIR=./cl_cache"
    "device=GPU"
)

#INC_TRACK_CMD=(
#    "gvatrack"
#    "tracking-type=short-term-imageless"
#)


if [[ -n "${CLS_LABEL}" ]];
then
INC_CLASSIFY_CMD=(
    "gvaclassify"
    "pre-process-backend=vaapi-surface-sharing"
    "model=${CLS_MODEL}"
    "model-proc=${CLS_MODEL_PROC}"
    "${CLS_LABEL}"
    "inference-region=roi-list"
    "object-class=car"
    "ie-config=CACHE_DIR=./cl_cache"
    "device=GPU"
)
else
INC_CLASSIFY_CMD=(
    "gvaclassify"
    "pre-process-backend=vaapi-surface-sharing"
    "model=${CLS_MODEL}"
    "model-proc=${CLS_MODEL_PROC}"
    "inference-region=roi-list"
    "object-class=car"
    "ie-config=CACHE_DIR=./cl_cache"
    "device=GPU"
)
fi

#INC_METAPUBLISH_PIPLINE=(
#    'gvametaconvert' !
#    'gvametapublish'
#)

INC_WATERMARK_CMD=(
    "meta_overlay"
    "device=GPU"
)

FULL_PIPELINE=(
    "filesrc" "location=${VIDEO_IN}" !
    "decodebin" !
    "video/x-raw(memory:VASurface)" !
    "${INC_DETECT_CMD[@]}" !
#    "${INC_TRACK_CMD[@]}" !
    "${INC_CLASSIFY_CMD[@]}" !
#    "${INC_METAPUBLISH_PIPELINE[@]}" !
    "${INC_WATERMARK_CMD[@]}" !
    "gvafpscounter" !
    "queue" !
    "vaapih264enc" "bitrate=2048" !
    "h264parse" !
    "mp4mux" !
    "filesink" "location=/tmp/${VIDEO_OUT}"
)

set -x
gst-launch-1.0 "${FULL_PIPELINE[@]}"
