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
import glob
import itertools
import os
from operator import itemgetter
from itertools import groupby

DOCUMENTATION = '''
---
module: calculate_isolcpu_
short_description: isolate CPU cores from each NUMA node an interface is attached too.
description:
   - algorithm:
       - find all the NUMA local cpus for each interface
options:
  interfaces: list of interfaces to calculate masks for.
'''


def select_cores(cpu_lists):
    isol_cores = select_isol_cores(cpu_lists)
    return {
        "isol_cores": sorted(isol_cores),
    }


def split_cpu_list(cpu_list):
    if cpu_list:
        ranges = cpu_list.split(',')
        bounds = ([int(b) for b in r.split('-')] for r in ranges)
        # include upper bound
        range_objects = (xrange(bound[0], bound[1] + 1 if len(bound) == 2 else bound[0] + 1) for bound
                         in bounds)
        return sorted(itertools.chain.from_iterable(range_objects))
    else:
        return []


def select_isol_cores(cpu_lists):
    isol_cores = set()
    for cpu_list in cpu_lists:
        # must make a copy because we pop and mutate
        cpu_list = cpu_list[:]
        # only mask cores if we have more than 4 CPUs
        if len(cpu_list) > 4:
            isol_cores.add(cpu_list.pop(0))
            isol_cores.update(cpu_list)
    return isol_cores


def get_numa_nodes():

    nodes_sysfs = glob.iglob("/sys/devices/system/node/node*")
    nodes = {}
    for node_sysfs in nodes_sysfs:
        num = os.path.basename(node_sysfs).replace("node", "")
        with open(os.path.join(node_sysfs, "cpulist")) as cpulist_file:
            cpulist = cpulist_file.read().strip()
        nodes[num] = split_cpu_list(cpulist)

    return nodes

def get_necessary_cores(needed_cores, cpu_list, threads_cpu):
    for port, cores in cpu_list.iteritems():
        total_cores = len(cores)/threads_cpu
        cpu_list[port] = cores[2:needed_cores + 2] + cores[total_cores + 2:total_cores + needed_cores + 2]
    return cpu_list

def main():

    module = AnsibleModule(
        argument_spec = {
            'interfaces': {'required': True, 'type': 'list'},
            'num_dp_cores': {'required': True, 'type': 'int'},
            'num_cp_cores': {'required': True, 'type': 'int'},
            'threads_per_cpu': {'required': True, 'type': 'int'},
        }
    )
    params = module.params

    numa_nodes = get_numa_nodes()
    all_cores = set(itertools.chain.from_iterable(numa_nodes.itervalues()))

    cpu_lists = {}
    for intf in params['interfaces']:
        try:
            with open("/sys/class/net/{}/device/local_cpulist".format(intf)) as cpu_list:
                cpu_lists[intf] = split_cpu_list(cpu_list.read().strip())
        except EnvironmentError as e:
            if os.path.basename(os.readlink("/sys/class/net/{}/device/driver".format(intf))) == "virtio_net":
                # virtual enviroment, use all cores
                cpu_lists[intf] = ",".join(sorted(all_cores))
            else:
                module.fail_json(msg=str(e))

    interface_cores = set(itertools.chain.from_iterable(cpu_lists.itervalues()))
    ansible_facts = select_cores(cpu_lists.itervalues())

    needed_cores = params['num_dp_cores'] + params['num_cp_cores']
    threads_cpu = params['threads_per_cpu']
    cpu_lists = get_necessary_cores(needed_cores, cpu_lists, threads_cpu)

    ansible_facts.update({
        "interface_numa_cpu_lists": cpu_lists
    })

    module.exit_json(changed=True, ansible_facts=ansible_facts)

# use this form to include ansible boilerplate so we can run unittests

#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

if __name__ == '__main__':
    main()
