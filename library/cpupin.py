#!/usr/bin/env python3
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: cpupin

short_description: cpupin module get the available resources from host server and do the CPU
                   pinning for VMs

version_added: "1.0"

description: cpupin module get the available resources from host server and do the CPU pinning for
             VMs. By default it selects CPUs from single NUMA node and do NUMA allignment for VMs
             With option alloc_all it selects all available CPUs from all NUMA nodes.
             It reserves configured amount of CPUs for host OS.

options:
    name: 
        description: Name of the VM machine
        required: true
        type: str
    number:
        description: Number of CPUs to be reserved for VM.
        required: false
        type: int
    numa:
        description: NUMA node to be used for CPUs reservation
        required: false
        type: int
    cpus:
        description: List of vCPUs that should be pinned for the purpose of running VM.
        required: false
        type: string
    number_host_os:
        description: Number of CPUs to be reserved for host OS.
        required: false
        type: int
    alloc_all:
        description: Option to enable reservation of all available CPUs from all NUMA nodes for
                     single VM.
        required: false
        type: boolean
    pinning:
        description: Do the actual cpu-pinning
        required: true
        type: boolean

author:
    - Lumir Jasiok (lumirx.jasiok@intel.com)
'''

EXAMPLES = r'''
# Module is used in two modes:
# 1. CPU allocation - pinning: false
#    In this mode all user inputs are validated and requested CPUs are selected.
#    By default it reserve 16 CPUs/Threads for host OS

# Allocate eight CPUs/Threads from randomly selected NUMA node for VM named vm-ctrl-1
- name: Allocate 8 VCPUs
  cpupin:
    name: vm-ctrl-1
    number: 8
    pinning: false

# Allocate eight CPUs/Threads from randomly selected NUMA node for VM named vm-ctrl-1
# and reserve only 8 CPUs/Threads for host OS
- name: Allocate 8 VCPUs
  cpupin:
    name: vm-ctrl-1
    number: 8
    number_host_os: 8
    pinning: false

# Allocate sixteen CPUs/Threads from NUMA node 0 for VM named vm-work-1
- name: Allocate 16 VCPUs from NUMA node 0
  cpupin:
    name: vm-work-1
    number: 16
    numa: 0
    pinning: false

# Allocate eight manually selected CPUs in a range specified in parameter 'cpus', which
# are available on numa: 0 for VM named vm-ctrl-1
# Manually selested CPU ranges have to consist of 4 CPUs and 4 corresponding Threads.
# It meens that 4 cores are selected.
- name: Allocate manually selected CPUs in a range specified in parameter 'cpus'
  cpupin:
    name: vm-ctrl-1
    cpus: 8-11,64-67
    numa: 0
    number: 8
    pinning: false

# Allocate all CPUs/Threads from NUMA node with the highest number of available CPUs
# for VM named vm-ctrl-1
- name: Allocate all CPUs from NUMA with the highest number of CPUs
  cpupin:
    name: vm-ctrl-1
    number: 0
    pinning: false

# Allocate all CPUs/Threads from selected NUMA node 1 for VM named vm-ctrl-1
- name: Allocate all CPUs from selected NUMA node
  cpupin:
    name: vm-ctrl-1
    numa: 1
    number: 0
    pinning: false

# Allocate all CPUs/Threads from all NUMA nodes for VM named vm-ctrl-1
- name: Allocate all CPUs from all NUMA nodes
  cpupin:
    name: vm-ctrl-1
    number: 0
    alloc_all: true
    pinning: false

# 2. CPU pinning - pinning: true
#    In this mode allocated CPUs from previous step are pinned to VM.
#    It is expected that output from CPU Allocation phase is automatically gathered
#    and passed as input to Pinning phase. Due to that inputs validation is not done.

# Pin CPUs/Threads from list prepared by CPU Allocattion phase for VM named vm-ctrl-1
- name: Pin pre-allocated CPUs from CPU Allocattion phase
  cpupin:
    name: vm-ctrl-1
    cpus: 8-11,64-67
    numa: 0
    alloc_all: false
    pinning: true
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return
# values.
name:
    description: Name of the VM
    type: str
    returned: always
    sample: vm-ctrl-1
cpus:
    description: CPUs that has been allocated/pinned for the VM
    type: list
    returned: always
    sample: [8, 9, 10, 11]
numa:
    description: Number of NUMA node that has been used
    type: int
    returned: always
    sample: 0
number:
    description: Number of CPUs that has been requested for CPU allocation
    type: int
    returned: always
    sample: 8
number_host_os:
    description: Number of CPUs that has been reserved for host OS
    type: int
    returned: always
    sample: 16
alloc_all:
    description: Was the alloc_all requested? If yes then NUMA allignment is skipped.
    type: boolean
    returned: always
    sample: false
pinning: 
    description: Was the actual pinning requested?
    type: boolean
    returned: always
    sample: false
'''
