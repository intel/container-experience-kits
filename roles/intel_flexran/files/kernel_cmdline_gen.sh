#! /bin/bash

threads_per_core=$(lscpu | grep "Thread(s) per core" | awk -F ':' '{print $2}' | xargs)
cores_per_socket=$(lscpu | grep "Core(s) per socket" | awk -F ':' '{print $2}' | xargs)
socket=$(lscpu | grep "Socket(s)" |awk -F ':' '{print $2}' | xargs)


# On socket 0, core 0-1 and its sibling thread core will be kept for housekeeping.
# On socket 1, the first two cores and its sibling will be kept for housekeeping
# all the other cores will be isolated

# Set isolcpus and housekeeping
if [ "$socket" == "1" ] ; then
	if [ "$threads_per_core" == "2" ] ; then
		isolcpus="2-$(( cores_per_socket - 1 )),$(( cores_per_socket + 2 ))-$(( cores_per_socket * 2 - 1 ))"
		housekeeping="0-1,$(( cores_per_socket ))-$(( cores_per_socket + 1 ))"
	else
		isolcpus="2-$(( cores_per_socket - 1 ))"
		housekeeping="0-1"
	fi
elif [ "$socket" == "2" ]; then
	if [ "$threads_per_core" == "2" ] ; then
		isolcpus="2-$(( cores_per_socket - 1 )),$(( cores_per_socket + 2 ))-$(( cores_per_socket * 2 - 1 )),$(( cores_per_socket * 2 + 2 ))-$(( cores_per_socket * 3 - 1 )),$(( cores_per_socket * 3 + 2 ))-$(( cores_per_socket * 4 - 1 ))"
		housekeeping="0-1,$(( cores_per_socket ))-$(( cores_per_socket + 1 )),$(( cores_per_socket * 2 ))-$(( cores_per_socket * 2 + 1 )),$(( cores_per_socket * 3 ))-$(( cores_per_socket * 3 + 1 ))"
	else
		isolcpus="2-$(( cores_per_socket - 1 )),$(( cores_per_socket + 2 ))-$(( cores_per_socket * 2 - 1 ))"
		housekeeping="0-1,$(( cores_per_socket ))-$(( cores_per_socket + 1 ))"
	fi
fi

# Set hugepage size
if [ "$cores_per_socket" -lt "32" ] ; then
        pagesize="40"
else
        pagesize="60"
fi

flexran_kernel_cmdline="hugepagesz=1G hugepages=$pagesize hugepagesz=2M hugepages=0 default_hugepagesz=1G nmi_watchdog=0 softlockup_panic=0 intel_iommu=on iommu=pt vfio_pci.enable_sriov=1 vfio_pci.disable_idle_d3=1 rcu_nocbs=$isolcpus irqaffinity=$housekeeping isolcpus=managed_irq,domain,$isolcpus kthread_cpus=$housekeeping nohz_full=$isolcpus crashkernel=auto enforcing=0 quiet rcu_nocb_poll rhgb selinux=0 mce=off audit=0 pci=realloc pci=assign-busses rdt=l3cat skew_tick=1 nosoftlockup nohz=on"
echo "$flexran_kernel_cmdline"
