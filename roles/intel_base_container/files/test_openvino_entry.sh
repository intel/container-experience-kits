#!/bin/bash

source /opt/intel/openvino_2022/setupvars.sh

echo "---------------- Build benchmark_app ----------------"
cd /opt/intel/openvino_2022/samples/cpp || exit
./build_samples.sh

cd "$HOME"/openvino_cpp_samples_build/intel64/Release || exit

echo "---------------- Check Avaliable OpenVINO devices ----------------"
./benchmark_app -h | grep Available

echo "---------------- Check OpenVINO inference ----------------"

DATA_PATH=$HOME/data
mkdir -p "${DATA_PATH}"/models/

if [[ ! -f "${DATA_PATH}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin ]]
then
    echo "---------------- Download ResNet50 model ----------------"
    mkdir -p "${DATA_PATH}"/models/intel/resnet50-binary-0001/FP16-INT1/

    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin \
        --output "${DATA_PATH}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin

    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml \
        --output "${DATA_PATH}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml

fi
./benchmark_app -m "${DATA_PATH}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml -d GPU | tee /home/aibox/data/openvino_test_output.txt
result="Failed"
pass_count=0
if [[ $(grep -n "Throughput:" /home/aibox/data/openvino_test_output.txt | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
fi
if [[ $(grep -n "Median:" /home/aibox/data/openvino_test_output.txt | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
fi
if [[ $(grep -n "Average:" /home/aibox/data/openvino_test_output.txt | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
fi
if [[ $(grep -n "Min:" /home/aibox/data/openvino_test_output.txt | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
fi
if [[ $(grep -n "Max:" /home/aibox/data/openvino_test_output.txt | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
fi

if [[ ${pass_count} -eq 5 ]]
then
    result="Passed"
fi

echo ${result} | tee /home/aibox/data/test_openvino_result

