#!/bin/bash

source /opt/intel/openvino_2022/setupvars.sh

test_data_path="/home/aibox/test_data/"
mtcnn_path="/home/aibox/data/models/public/mtcnn"
result="Failed"

if [[ ! -d /home/aibox/data/models ]]
then
    mkdir -p /home/aibox/data/models
fi

# Download and convert mtcnn models, which is also the input for opencv_ffmpeg test.
if [[ -d /home/aibox/data/models/public/mtcnn ]]
then
    rm -rf /home/aibox/data/models/public/mtcnn
fi

timeout 120 omz_downloader --name mtcnn -o /home/aibox/data/models
cd ${mtcnn_path} || exit
check_download_md5=$(find . -name "*caffemodel" -o -name "*prototxt" | sort -k 2 | xargs md5sum)
if [[ $(grep -E "caffemodel|prototxt" ${test_data_path}/test_base_devel_md5.txt | sort -k 2) != "${check_download_md5}" ]]
then
    echo ""
    echo "[Warning] !!!The models download failed, please rerun the case."
    exit 1
fi

omz_converter --name mtcnn -d /home/aibox/data/models
cd ${mtcnn_path} || exit
current_md5=$(find . -name "*bin" -o -name "*mapping" -o -name "*caffemodel" -o -name "*prototxt" | sort -k 2 | xargs md5sum)
echo "Current files md5:"
find . -name "*bin" -o -name "*mapping" -o -name "*caffemodel" -o -name "*prototxt" | sort -k 2 | xargs md5sum

if [[ $(cat ${test_data_path}/test_base_devel_md5.txt) == "${current_md5}" ]]
then
    result="Passed"
fi
echo ${result} | tee /home/aibox/data/test_base_devel_result
