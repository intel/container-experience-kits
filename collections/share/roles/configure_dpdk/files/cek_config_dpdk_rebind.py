#
# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys

import cek_config_dpdk_util as util

def dpdk_rebind_port() :
    ret = 0

    restore_conf_filename = '/etc/network_restore.conf'
    if os.path.exists(restore_conf_filename) :
        print(restore_conf_filename + " exists.")

        with open(restore_conf_filename, 'r') as conf :
            # restore conf file content likes below :
            #   0000:ca:00.0 dpdk_port=1 if=ens25f0 curr_drv=vfio-pci prev_drv=ice prev_active=1
            #   0000:ca:00.1 dpdk_port=2 if=ens25f1 curr_drv=vfio-pci prev_drv=ice prev_active=0
            lines = conf.readlines()
            for line in lines :
                print(line)

                items = line.split(' ')

                bdf = items[0]

                dev_str = items[2]
                dev = dev_str[dev_str.find("=")+1 : ]

                curr_drv_str = items[3]
                curr_drv = curr_drv_str[curr_drv_str.find("=")+1 : ]

                # down dev before dpdk bind
                if dev != "" :
                    if util.validate_dev(dev) :
                        cmd = 'ifconfig ' + dev + ' down'
                        print('execute cmd : ' + cmd)
                        ret = os.system(cmd)

                # dpdk bind
                if util.validate_drv(curr_drv) and util.validate_bdf(bdf) :
                    cmd = 'dpdk-devbind.py --bind=' + curr_drv + ' ' + bdf
                    print('execute cmd : ' + cmd)
                    ret = os.system(cmd)

    else :
        print(restore_conf_filename + " does not exist.")

    return ret

# Usage :
#   cek_config_dpdk_rebind.py
#
#   Result :
#       It will check whether /etc/network_restore.conf exists.
#       If the restore conf file exists, it will rebind dpdk with NIC dev
#       according to the file content.
#
r = dpdk_rebind_port()
print("dpdk_rebind_port() return " + str(r))
sys.exit(r)
