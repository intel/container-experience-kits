#!/bin/bash

NETWORK_TYPE="$1"

source /opt/intel/openvino_2022/setupvars.sh
source /opt/intel/dlstreamer/setupvars.sh

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/oneapi/compiler/2023.2.1/linux/lib:/opt/intel/oneapi/compiler/2023.2.1/linux/compiler/lib/intel64_lin

DATA_PATH=$HOME/data

if [[ ! -d "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/FP16 ]]
then
    mkdir -p "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/FP16/
    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/person-vehicle-bike-detection-2004/FP16/person-vehicle-bike-detection-2004.xml \
        --output "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/FP16/person-vehicle-bike-detection-2004.xml

    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/person-vehicle-bike-detection-2004/FP16/person-vehicle-bike-detection-2004.bin \
        --output "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/FP16/person-vehicle-bike-detection-2004.bin
    if [ "${NETWORK_TYPE}" = "prc_network" ]; then
        echo "Download .proc file from gitmirror"
        curl -L https://raw.gitmirror.com/dlstreamer/dlstreamer/2022.3-release/samples/gstreamer/model_proc/intel/person-vehicle-bike-detection-2004.json \
            --output "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/person-vehicle-bike-detection-2004.json
    else
        echo "Download .proc file from github"
        curl -L https://raw.githubusercontent.com/dlstreamer/dlstreamer/2022.3-release/samples/gstreamer/model_proc/intel/person-vehicle-bike-detection-2004.json \
            --output "${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/person-vehicle-bike-detection-2004.json
    fi
fi

if [[ ! -f "${DATA_PATH}"/videos/car-detection.mp4 ]]
then
    mkdir -p "${DATA_PATH}"/videos/
    curl -L https://storage.openvinotoolkit.org/test_data/videos/car-detection.mp4 \
        --output "${DATA_PATH}"/videos/car-detection.mp4
fi

if [[ -d "${DATA_PATH}"/videos/dump_yuv ]]
then
    rm -rf "${DATA_PATH}"/videos/dump_yuv
fi
if [[ -d "${DATA_PATH}"/videos/dump_jpg ]]
then
    rm -rf "${DATA_PATH}"/videos/dump_jpg
fi
mkdir -p "${DATA_PATH}"/videos/dump_yuv
mkdir -p "${DATA_PATH}"/videos/dump_jpg


gst-launch-1.0 -e filesrc location="${DATA_PATH}"/videos/car-detection.mp4 ! \
qtdemux ! h264parse ! vaapih264dec ! video/x-raw\(memory:VASurface\) ! \
gvadetect pre-process-backend=vaapi-surface-sharing pre-process-config=VAAPI_FAST_SCALE_LOAD_FACTOR=1 \
model="${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/FP16/person-vehicle-bike-detection-2004.xml \
model-proc="${DATA_PATH}"/models/intel/person-vehicle-bike-detection-2004/person-vehicle-bike-detection-2004.json \
device=GPU ! \
meta_overlay ! \
gvafpscounter ! \
vaapih264enc ! h264parse ! mp4mux ! filesink location="${DATA_PATH}"/videos/output_person-vehicle-bike-detection-2004.mp4

gst-discoverer-1.0 "${DATA_PATH}"/videos/output_person-vehicle-bike-detection-2004.mp4 | tee "${DATA_PATH}"/dlstreamer_test_output.txt

result="Failed"
pass_count=0
if grep -n "Bitrate" "${DATA_PATH}"/dlstreamer_test_output.txt | awk -F: '{print $3}'
then
    (( pass_count+=1 )) || true
fi

if grep -n "H.264" "${DATA_PATH}"/dlstreamer_test_output.txt
then
    (( pass_count+=1 )) || true
fi

if [[ ${pass_count} -eq 2 ]]
then
    result="Passed"
fi

echo "${result}" | tee "${DATA_PATH}"/test_dlstreamer_result
