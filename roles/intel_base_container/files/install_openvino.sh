#!/bin/bash

#curl -L -o openvino_2022.3.1.tgz \
#    https://storage.openvinotoolkit.org/repositories/openvino/packages/2022.3.1/linux/l_openvino_toolkit_ubuntu20_2022.3.1.9227.cf2c7da5689_x86_64.tgz

curl -L -o openvino_2022.3.0.tgz \
    https://storage.openvinotoolkit.org/repositories/openvino/packages/2022.3/linux/l_openvino_toolkit_ubuntu20_2022.3.0.9052.9752fafe8eb_x86_64.tgz
tar -xzvf openvino_2022.3.0.tgz
mv l_openvino_toolkit_ubuntu20_2022.3.0.9052.9752fafe8eb_x86_64 /opt/intel/openvino_2022.3.0
ln -s /opt/intel/openvino_2022.3.0 /opt/intel/openvino_2022
cd /opt/intel/openvino_2022 || exit
./install_dependencies/install_openvino_dependencies.sh

apt-get install -y libtbb2
