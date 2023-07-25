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

def dpdk_unbind_port() :

    ret = 0
    conf_filename = '/etc/network_env.conf'
    restore_conf_filename = '/etc/network_restore.conf'

    with open(restore_conf_filename, 'r') as restore_conf :
        lines = restore_conf.readlines()
        for line in lines :
            # network_restore.conf conent likes below :
            #   0000:ca:00.0 dpdk_port=1 if=ens25f0 curr_drv=vfio-pci prev_drv=ice prev_active=1
            #   0000:ca:00.1 dpdk_port=2 if=ens25f1 curr_drv=vfio-pci prev_drv=ice prev_active=0
            print(line)
            items = line.split(' ')

            bdf = items[0]

            dev_str = items[2]
            dev = dev_str[dev_str.find("=")+1 : ]

            #curr_drv_str = items[2]
            #curr_drv = curr_drv_str[curr_drv_str.find("=")+1 : ]

            prev_drv_str = items[4]
            prev_drv = prev_drv_str[prev_drv_str.find("=")+1 : ]

            if 'pre_active=1' in items[4]:
                act = 1
            else :
                act = 0

            if util.validate_drv(prev_drv) and util.validate_bdf(bdf) :
                cmd = 'dpdk-devbind.py -u ' + bdf
                print('execute cmd : ' + cmd)
                ret = os.system(cmd)

                cmd = 'dpdk-devbind.py --bind=' + prev_drv + ' ' + bdf
                print('execute cmd : ' + cmd)
                ret = os.system(cmd)

            if dev != "" :
                if act and util.validate_dev(dev) :
                    cmd = 'ifconfig ' + dev + ' up'
                    print('execute cmd : ' + cmd)

    os.remove(conf_filename)
    os.remove(restore_conf_filename)

    return ret


# Usage :
#   cek_config_dpdk_unbind.py
#
#   Result :
#       If will read /etc/network_restore.conf, to resotre nic
#       to previous status before calling cek_config_dpdk_bind.py.
#       After status restore, the /etc/network_restore.conf file
#       will be removed.
#

r = dpdk_unbind_port()
print("dpdk_unbind_port() return " + str(r))
sys.exit(r)
