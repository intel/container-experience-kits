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

import sys

def dpdk_link_port(filename1, filename2):
    print("dpdk_link_port : " + filename1 + " " + filename2)

    ret = 0

    with open(filename1, 'r+') as file1:
        with open(filename2, 'r+') as file2:
            append1 = []
            append2 = []

            file1.seek(0)
            lines1 = file1.readlines()
            #print(lines1)
            for line in lines1 :
                if 'srcmac' in line :
                    new_line = line.replace('srcmac', 'destmac')
                    append2 = append2 + [new_line]

            file2.seek(0)
            lines2 = file2.readlines()
            #print(lines2)
            for line in lines2 :
                if 'srcmac' in line :
                    new_line = line.replace('srcmac', 'destmac')
                    append1 = append1 + [new_line]

            #print(append1)
            #print(append2)
            for line in append1 :
                if line not in lines1 :
                    file1.write(line)

            for line in append2 :
                if line not in lines2 :
                    file2.write(line)

    return ret


# Usage :
#   cek_config_dpdk_link.py {filname1}  {filename2}
#
#   Examples :
#       dpdk_bind_port.py network_src.conf  network_dst.conf
#
#   Result :
#       If link success, return 0;
#       Else return error value (< 0);
#
#       If success, will :
#       1)Append src mac in file 1 to file 2 as dst mac.
#       2)Append src mac in file 2 to file 1 as dst mac.
#
#       Input file content may like this :
#       file 1:
#           dpdk_port1=0000:ca:00.0
#           dpdk_port2=0000:ca:00.1
#           dpdk_port1_srcmac=0x6c,0xfe,0x54,0x41,0x13,0x20
#           dpdk_port2_srcmac=0x6c,0xfe,0x54,0x41,0x13,0x21
#       file 2 :
#           dpdk_port1=0000:ca:00.0
#           dpdk_port2=0000:ca:00.1
#           dpdk_port1_srcmac=0x6c,0xfe,0x54,0x40,0xe6,0xe0
#           dpdk_port2_srcmac=0x6c,0xfe,0x54,0x40,0xe6,0xe1
#
#       After link, the file content may become :
#       file 1:
#           dpdk_port1=0000:ca:00.0
#           dpdk_port2=0000:ca:00.1
#           dpdk_port1_srcmac=0x6c,0xfe,0x54,0x41,0x13,0x20
#           dpdk_port2_srcmac=0x6c,0xfe,0x54,0x41,0x13,0x21
#           dpdk_port1_destmac=0x6c,0xfe,0x54,0x40,0xe6,0xe0
#           dpdk_port2_destmac=0x6c,0xfe,0x54,0x40,0xe6,0xe1
#       file 2 :
#           dpdk_port1=0000:ca:00.0
#           dpdk_port2=0000:ca:00.1
#           dpdk_port1_srcmac=0x6c,0xfe,0x54,0x40,0xe6,0xe0
#           dpdk_port2_srcmac=0x6c,0xfe,0x54,0x40,0xe6,0xe1
#           dpdk_port1_destmac=0x6c,0xfe,0x54,0x41,0x13,0x20
#           dpdk_port2_destmac=0x6c,0xfe,0x54,0x41,0x13,0x21
#

r = dpdk_link_port(sys.argv[1], sys.argv[2])
print("dpdk_link_port() return " + str(r))
sys.exit(r)
