#!/bin/bash

TEST_POSTFIX="$1"

source /opt/intel/openvino/setupvars.sh

openvino_dev_output_path="$HOME"/data/openvino_dev_output_"$TEST_POSTFIX"
mtcnn_path=${openvino_dev_output_path}/models/public/mtcnn
result="Failed"

if [[ -d ${openvino_dev_output_path} ]]
then
    rm -rf "${openvino_dev_output_path}"
fi
mkdir -p "${openvino_dev_output_path}"

# Download and convert mtcnn models, which is also the input for opencv_ffmpeg test.
if [[ -d ${mtcnn_path} ]]
then
    rm -rf "${mtcnn_path}"
fi

timeout 120 omz_downloader --name mtcnn -o "${openvino_dev_output_path}"/models
cd "${mtcnn_path}" || exit
if [[ $(find . -name "*caffemodel" -size +10k -o -name "*prototxt" -size +1k | wc -l) -ne 6 ]]
then
    echo ""
    echo "[Warning] !!!The models download failed, please rerun the case."
    exit 1
fi

omz_converter --name mtcnn -d "${openvino_dev_output_path}"/models
cd "${mtcnn_path}" || exit
if [[ $(find . -name "*bin" -size +10k | wc -l) -eq 6 ]]
then
    result="Passed"
else
    result="Failed: The converted file does not match expectations."
    find . -name "*bin" -exec ls -l {} \;
fi
echo "${result}" | tee "$HOME"/data/test_openvino_dev_result_"$TEST_POSTFIX"
