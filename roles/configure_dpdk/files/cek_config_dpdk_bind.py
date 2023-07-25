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
import re

import cek_config_dpdk_util as util

def dpdk_bind_port(nic_type, new_drv, port_offset, port_count) :
    print('dpdk_bind_port(' + nic_type + ' ' + new_drv + ' ' + port_offset + ' ' + port_count + ')')

    ret = 0
    idx1 = 0
    idx2 = 0
    nic_lines = None

    offset = int(port_offset)
    count  = int(port_count)
    if ( util.validate_nic_type(nic_type) and util.validate_drv(new_drv) and
         (offset >= 0) and (count > 0) ) :
        cmd = 'dpdk-devbind.py --status-dev net | grep ' + nic_type
        print('execute cmd : ' + cmd)
        result = os.popen(cmd)
        info_list = result.read()
        if result is not None :
            result.close()

        nic_lines = info_list.splitlines()
        idx1 = max(0, offset)
        idx2 = min(offset + count, len(nic_lines))
        print('bind range ' + str(idx1) + " : " + str(idx2) )
    else :
        print ("invalid input parameter, do nothing")
        return -1

    if idx1 >= idx2 :
        print("bind range is null, do nothing")
        return 0

    conf_filename = '/etc/network_env.conf'
    restore_conf_filename = '/etc/network_restore.conf'

    conf_port_lines = []
    conf_mac_lines = []
    conf_restore_lines = []

    # check whether conf files exsit
    append_conf = 0
    if os.path.exists(conf_filename) :
        conf_flag = 'r+'
        append_conf = 1
    else :
        conf_flag = 'w'

    append_restore_conf = 0
    if os.path.exists(restore_conf_filename):
        restore_conf_flag = 'r+'
        append_restore_conf = 1
    else :
        restore_conf_flag = 'w'

    with open(conf_filename, conf_flag) as conf :
        with open(restore_conf_filename, restore_conf_flag) as restore_conf :

            # read existing conf files
            if append_conf :
                conf.seek(0)
                lines = conf.readlines()
                for line in lines:
                    if re.match(r'^dpdk_port[0-9]*=', line) :
                        conf_port_lines.append(line)
                    elif re.match(r'^dpdk_port[0-9]*_srcmac=', line) :
                        conf_mac_lines.append(line)

            if append_restore_conf :
                restore_conf.seek(0)
                conf_restore_lines = restore_conf.readlines()

            # loop nic devices for procession
            idx = 0
            dpdk_idx = 1
            for idx in range(idx1, idx2) :
                nic_line = nic_lines[idx]
                bdf = nic_line[ : nic_line.find(' ')]
                print("bdf : " + bdf)

                # check whether bdf already in conf
                conf_exists = 0
                restore_line = ""
                conf_line_count = len(conf_restore_lines)
                for conf_line_idx in range(0, conf_line_count):
                    restore_line = conf_restore_lines[conf_line_idx]
                    if bdf in restore_line :
                        print("conf exists for " + bdf + " in line " + str(conf_line_idx) + " :")
                        print(restore_line)
                        conf_exists = 1
                        break

                if conf_exists :
                    # restore conf line example :
                    # 0000:ca:00.0 dpdk_port=1 if=ens25f0 curr_drv=vfio-pci prev_drv=ice prev_active=1
                    # 0000:ca:00.1 dpdk_port=2 if=ens25f1 curr_drv=vfio-pci prev_drv=ice prev_active=0
                    items = restore_line.split(' ')
                    dpdk_port_str = items[1]
                    dpdk_port = dpdk_port_str[dpdk_port_str.find("=")+1 : ]
                    dpdk_idx  = int(dpdk_port)

                    dev_str = items[2]
                    dev = dev_str[dev_str.find("=")+1 : ]

                    curr_drv_str = items[3]
                    curr_drv = curr_drv_str[curr_drv_str.find("=")+1 : ]

                    prev_drv_str = items[4]
                    prev_drv = prev_drv_str[prev_drv_str.find("=")+1 : ]

                    prev_act_str = items[5]
                    prev_act = int(prev_act_str[prev_act_str.find("=")+1 : ])

                    if curr_drv != new_drv :
                        # if driver change, rebind and update current conf line
                        if ( util.validate_bdf(bdf) and util.validate_drv(new_drv)) :
                            cmd = 'dpdk-devbind.py -u' + ' ' + bdf
                            print('execute cmd : ' + cmd)
                            ret = os.system(cmd)

                            cmd = 'dpdk-devbind.py --bind=' + new_drv + ' ' + bdf
                            print('execute cmd : ' + cmd)
                            ret = os.system(cmd)

                            curr_drv = new_drv

                            new_restore_line = bdf + \
                                                " dpdk_port=" + str(dpdk_idx) + \
                                                " if=" + dev + \
                                                " curr_drv=" + curr_drv + \
                                                " prev_drv=" + prev_drv + \
                                                " prev_active=" + str(prev_act) + "\n"
                            print("new restore line : " + new_restore_line)

                            conf_restore_lines[conf_line_idx] = new_restore_line
                    else :
                        print("no action for same conf")
                        ret = 0

                else :
                    # nic line examples :
                    # 0000:ca:00.0 'Ethernet Controller E810-C for QSFP 1592' drv=vfio-pci unused=ice
                    # 0000:ca:00.1 'Ethernet Controller E810-C for QSFP 1592' drv=vfio-pci unused=ice
                    # 0000:4b:00.0 'I350 Gigabit Network Connection 1521' if=ens9f0 drv=igb unused=vfio-pci *Active*
                    # 0000:4b:00.1 'I350 Gigabit Network Connection 1521' if=ens9f1 drv=igb unused=vfio-pci
                    items = nic_line.split(' ')
                    act = 0
                    dev_ready = 0
                    for item in items :
                        #print(item)
                        if 'if=' in item :
                            dev = item[item.find('=')+1 : ]
                            #print(dev)
                            dev_ready = 1
                        if 'drv=' in item :
                            drv = item[item.find('=')+1 : ]
                            #print(drv)
                        if '*Active*' in item :
                            act = 1
                            #print(act)

                    if dev_ready :
                        # get mac address
                        if util.validate_dev(dev) :
                            cmd = 'ifconfig ' + dev + ' | grep ether'
                            print('execute cmd : ' + cmd)
                            result2 = os.popen(cmd)
                            info_list2 = result2.read().split()
                            mac = '0x' + info_list2[1].replace(':', ',0x')
                            if result2 is not None :
                                result2.close()

                            # down dev before dpdk bind
                            cmd = 'ifconfig ' + dev + ' down'
                            print('execute cmd : ' + cmd)
                            ret = os.system(cmd)
                        else :
                            dev = ''
                            mac = 'unknown'
                    else :
                        dev = ''
                        mac = 'unknown'

                    if util.validate_bdf(bdf) and util.validate_drv(new_drv) :
                        # dpdk bind
                        cmd = 'dpdk-devbind.py -u' + ' ' + bdf
                        print('execute cmd : ' + cmd)
                        ret = os.system(cmd)

                        cmd = 'dpdk-devbind.py --bind=' + new_drv + ' ' + bdf
                        print('execute cmd : ' + cmd)
                        ret = os.system(cmd)

                        # append new conf lines
                        dpdk_idx = 1 + len(conf_port_lines)

                        new_port_line = "dpdk_port" + str(dpdk_idx) + "=" + bdf +"\n"
                        print("new conf line : " + new_port_line)

                        new_mac_line = "dpdk_port" + str(dpdk_idx) + "_srcmac=" + mac + "\n"
                        print("new mac line  : " + new_mac_line)


                        new_restore_line = bdf + \
                                            " dpdk_port=" + str(dpdk_idx) + \
                                            " if=" + dev + \
                                            " curr_drv=" + new_drv + \
                                            " prev_drv=" + drv + \
                                            " prev_active=" + str(act) + "\n"
                        print("new restore line : " + new_restore_line)

                        conf_port_lines.append(new_port_line)
                        conf_mac_lines.append(new_mac_line)
                        conf_restore_lines.append(new_restore_line)

            conf.seek(0)
            conf.writelines(conf_port_lines)
            conf.writelines(conf_mac_lines)

            restore_conf.seek(0)
            restore_conf.writelines(conf_restore_lines)

    return ret


# Usage :
#   cek_config_dpdk_bind.py nic_type drv_type port_offset port_count
#
#   Examples :
#       cek_dpdk_bind_port.py E810 vfio-pci 0 2
#       => bind E810 card port 0 and port 1 to vfio-pci driver
#
#       cek_dpdk_bind_port.py E810 vfio-pci 1 1
#       => bind E810 card port 1 to vfio-pci driver
#
#   Result :
#       If bind related nic port to dpdk success, return 0;
#       Else return error value (< 0);
#
#       If success, will generate below files for user.
#           /etc/network_env.conf and
#           /etc/network_restore.conf
#       /etc/network_env.conf content example as below :
#           dpdk_port1=0000:4b:00.0
#           dpdk_port2=0000:4b:00.1
#           dpdk_port1_srcmac=0xb4,0x96,0x91,0xb2,0xa6,0x48
#           dpdk_port2_srcmac=0xb4,0x96,0x91,0xb2,0xa6,0x49
#       /etc/network_restore.conf content example as below :
#           0000:ca:00.0 dpdk_port=1 if=ens25f0 curr_drv=vfio-pci prev_drv=ice prev_active=1
#           0000:ca:00.1 dpdk_port=2 if=ens25f1 curr_drv=vfio-pci prev_drv=ice prev_active=0
#

r = dpdk_bind_port(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
print("dpdk_bind_port() return " + str(r))
sys.exit(r)
