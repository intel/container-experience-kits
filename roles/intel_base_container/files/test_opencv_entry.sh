#!/bin/bash

git clone --depth 1 https://github.com/opencv/opencv_extra.git opencv_extra
export OPENCV_TEST_DATA_PATH=$HOME/opencv_extra/testdata/
source /opt/intel/openvino_2022/setupvars.sh

cd /opt/intel/nep/opencv_test/bin/ || exit
./opencv_perf_objdetect | tee /home/aibox/data/opencv_test_output.txt
result="Failed"
if grep -n PASSED /home/aibox/data/opencv_test_output.txt |grep "81 tests"
then
    result="Passed"
fi
echo ${result} | tee /home/aibox/data/test_opencv_result
