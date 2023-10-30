#!/bin/bash

TEST_POSTFIX="$1"

source /opt/intel/openvino/setupvars.sh

echo "---------------- Build benchmark_app ----------------"
cd /opt/intel/openvino/samples/cpp || exit
./build_samples.sh

cd "$HOME"/openvino_cpp_samples_build/intel64/Release || exit

echo "---------------- Check Avaliable OpenVINO devices ----------------"
./benchmark_app -h | grep Available

echo "---------------- Check OpenVINO inference ----------------"

openvino_data_path="$HOME"/data/openvino_data_"$TEST_POSTFIX"
openvino_output_path="$HOME"/data/openvino_output_"$TEST_POSTFIX"
if [[ -d "${openvino_output_path}" ]]
then
    rm -rf "${openvino_output_path}"
fi
mkdir -p "${openvino_output_path}"

output_result="${openvino_output_path}"/openvino_test_output.txt
bin_file="${openvino_data_path}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin
if [[ ! -f ${bin_file} ]] || [[ $(md5sum "${bin_file}" | awk '{print $1}') != "e2823d2a2548a8c03ae9920659175c58" ]]
then
    if [[ -d "${openvino_data_path}"/models ]]
    then
        rm -rf "${openvino_data_path}"/models
    fi
    mkdir -p "${openvino_data_path}"/models/intel/resnet50-binary-0001/FP16-INT1/
    echo "---------------- Download ResNet50 model ----------------"
    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin \
        --output "${openvino_data_path}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.bin
    curl -L https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml \
        --output "${openvino_data_path}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml
fi

./benchmark_app -m "${openvino_data_path}"/models/intel/resnet50-binary-0001/FP16-INT1/resnet50-binary-0001.xml -d GPU | tee "${output_result}"
result="Failed"
pass_count=0
if [[ $(grep -n "Throughput:" "${output_result}" | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
else
    result_failed_txt="No Throughput value."
fi
if [[ $(grep -n "Median:" "${output_result}" | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
else
    result_failed_txt="No Median value. ${result_failed_txt}"
fi
if [[ $(grep -n "Average:" "${output_result}" | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
else
    result_failed_txt="No Average value. ${result_failed_txt}"
fi
if [[ $(grep -n "Min:" "${output_result}" | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
else
    result_failed_txt="No Min value. ${result_failed_txt}"
fi
if [[ $(grep -n "Max:" "${output_result}" | awk '{if($(NF-1)>0) {print "Passed"} else {print "Failed"}}') == "Passed" ]]
then
    (( pass_count+=1 )) || true
else
    result_failed_txt="No Max value. ${result_failed_txt}"
fi

if [[ ${pass_count} -eq 5 ]]
then
    result="Passed"
else
    result="Failed: ${result_failed_txt}"
fi

echo "${result}" | tee "${HOME}"/data/test_openvino_result_"$TEST_POSTFIX"
