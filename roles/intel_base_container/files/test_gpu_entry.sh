#!/bin/bash

result="Failed"
pass_count=0
echo "---------------------Check glxinfo -------------------"
glxinfo | grep OpenGL
if glxinfo | grep OpenGL | grep "Intel" | grep "Graphics"
then
    (( pass_count+=1 )) || true
else
    echo "glxinfo: Failed"
fi

echo "---------------------Check clinfo ------------------- "
clinfo  | grep Device
if clinfo  | grep Device | grep "Intel" | grep "Graphics"
then
    (( pass_count+=1 )) || true
else
    echo "clinfo: Failed"
fi

echo "---------------------Check vulkaninfo ----------------- "
vulkaninfo | grep deviceName
if vulkaninfo | grep deviceName | grep "Intel" | grep "Graphics"
then
    (( pass_count+=1 )) || true
else
    echo "vulkaninfo: Failed"
fi

echo "---------------------Check vainfo --------------------"
vainfo | grep Driver
if vainfo | grep Driver | grep "Intel" | grep "Graphics"
then
    (( pass_count+=1 )) || true
else
    echo "vainfo: Failed"
fi

if [[ ${pass_count} -eq 4 ]]
then
    result="Passed"
fi

echo ${result} | tee /home/aibox/data/test_gpu_result
