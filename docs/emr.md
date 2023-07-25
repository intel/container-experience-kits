# EMR platform configuration guide

This guide introdues how to enable RA on the Intel EMR platforms.

## BMRA configuration
### QAT Driver
Download the EMR QAT driver package and put it in the folder ``/tmp/emr_qat/`` folder on the ansible host machine. Then configure the QAT related operations in the files in the ``group_vars`` and ``host_vars`` referring to the security session in the below url
<https://networkbuilders.intel.com/solutionslibrary/network-and-edge-reference-system-architectures-portfolio-user-manual> 

### DPDK driver
To align with EMR BKC ingredient version, on the EMR platform we will use ```DPDK 22.11.1``` lts version.

## VMRA configuration
Not supported yet, to be done.

## Cloud RA configuration
Not supported yet, to be done.
