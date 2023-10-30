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

import re

def validate_nic_type(nic_type) :
    ret = False
    if re.match(r'^[A-Za-z0-9]+$', nic_type) :
        ret = True
    else :
        print("invalid nic_type : " + nic_type)
    return ret

def validate_bdf(bdf) :
    ret = False
    if re.match(r'^([0-9a-f]{4}:){0,1}[0-9a-f]{2,4}:[0-9a-f]{2}\.[0-9a-f]$', bdf) :
        ret = True
    else :
        print("invalid bdf : " + bdf)
    return ret

def validate_drv(drv) :
    ret = False
    nic_drvs = ["i40e", "ice", "iavf", "vfio-pci", "igb_uio"]
    if drv in nic_drvs :
        ret = True
    else :
        print("invalid drv : " + drv)
    return ret

def validate_dev(dev) :
    ret = False
    if re.match(r'^[A-Za-z0-9]+$', dev) :
        ret = True
    else :
        print("invalid dev : " + dev)
    return ret

def validate_conf_name(filename):
    ret = False
    if re.match(r'^/etc/network_[A-Za-z0-9]+.conf', filename):
        ret = True
    return ret
