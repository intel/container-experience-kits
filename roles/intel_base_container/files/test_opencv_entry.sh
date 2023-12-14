#!/bin/bash

TEST_POSTFIX="$1"

opencv_data_path="$HOME"/data/opencv_data_"$TEST_POSTFIX"
opencv_output_path="$HOME"/data/opencv_output_"$TEST_POSTFIX"
if [[ ! -d ${opencv_data_path} ]]
then
    mkdir -p "${opencv_data_path}"
fi
if [[ -d ${opencv_output_path} ]]
then
    rm -rf "${opencv_output_path}"
fi
mkdir -p "${opencv_output_path}"

cd "$opencv_data_path" || exit
if [[ -d opencv_extra ]]
then
    cd opencv_extra || exit
    git pull
else
    git clone --depth 1 https://github.com/opencv/opencv_extra.git opencv_extra
fi

export OPENCV_TEST_DATA_PATH=${opencv_data_path}/opencv_extra/testdata/
source /opt/intel/openvino/setupvars.sh

cd /opt/intel/nep/opencv_test/bin/ || exit
./opencv_perf_objdetect | tee "${opencv_output_path}"/opencv_test_output.txt
result="Failed"
if grep -n PASSED "${opencv_output_path}"/opencv_test_output.txt |grep "155 tests"
then
    result="Passed"
else
    result="Failed: Please check the result of opencv perf objdetect."
fi
echo "${result}" | tee "$HOME"/data/test_opencv_result_"$TEST_POSTFIX"
