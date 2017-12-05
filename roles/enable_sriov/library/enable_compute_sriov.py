#!/usr/bin/python

# Copyright (c) 2016-2017, Intel Corporation.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import os
import sys
import random
#from ansible.module_utils.basic import *

id_dict = {
    'common':'/sys/class/net/%s/device/{}',
    'vendor_id':'vendor',
    'device_id':'device',
    'virt_id':'virtfn0/device',}

def enable_vf(sriov_intf, num_vfs):
    """Enable a number of virtual_functions on network interface"""
    with open(id_dict['common'].format('sriov_numvfs') %sriov_intf, 'w') as fp:
        fp.write(str(num_vfs))

def get_interface_id(sriov_intf, get_id):
    """Find and return: Vendor id, device id, virtual function id"""
    with open(id_dict['common'].format(id_dict[get_id]) %sriov_intf) as fp:
        return_id = (fp.read().lstrip('0x').rstrip())
    return return_id

def set_vf_address(module, sriov_intf, num_vfs):
    """Set mac address for VF"""
    for vf_num in xrange(num_vfs):
        set_command = "ip link set {} vf {} mac {}".format(sriov_intf, vf_num, spawn_mac())
        module.run_command(set_command)

def spawn_mac():
    """Generate mac address"""
    mac = [ 0x52, 0x54, 0x00,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def main():
    """Enable SR-IOV on interface, create VFs and set mac address for each. Return vendor/device id """
    module = AnsibleModule(
        argument_spec={
                'sriov_intf': {'required': True, 'type': 'str'},
                'num_vfs': {'required': True, 'type': 'int'}
        }
    )

    #Get parameters from ansible.
    params = module.params
    sriov_intf = params['sriov_intf']
    num_vfs = int(params['num_vfs'])

    enable_vf(sriov_intf, num_vfs)
    set_vf_address(module, sriov_intf, num_vfs)

    sriov_vendor_id = get_interface_id(sriov_intf, 'vendor_id')
    sriov_device_id = get_interface_id(sriov_intf, 'device_id')
    sriov_virt_id = get_interface_id(sriov_intf, 'virt_id')
    ansible_facts = {
        "sriov_vendor_id": sriov_vendor_id,
        "sriov_device_id": sriov_device_id,
        "sriov_virt_id": sriov_virt_id,
    }
    module.exit_json(Changed=True, ansible_facts=ansible_facts)

#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
if __name__ == '__main__':
    main()
