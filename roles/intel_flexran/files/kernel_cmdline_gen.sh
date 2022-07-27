#! /bin/bash

threads_per_core=$(lscpu | grep "Thread(s) per core" | awk -F ':' '{print $2}' | xargs)
cores_per_socket=$(lscpu | grep "Core(s) per socket" | awk -F ':' '{print $2}' | xargs)
numa=$(lscpu | grep "NUMA node(s)" |awk -F ':' '{print $2}' | xargs)

# if cores_per_socket < 2, which means no cores available to isolate for realtime app.
# and isolcpus will results in 1-0, keep it here for test purpose. 

# On socket 0, core 0 and its sibling thread core will be kept for housekeeping
# all the other cores will be isolated
# No cores isolated from socket 1.
# NUMA node0 CPU(s):   0-27,56-83
# NUMA node1 CPU(s):   28-55,84-111
if [ "$numa" == "1" ] ; then
	if [ "$threads_per_core" == "2" ] ; then
		isolcpus="1-$(( cores_per_socket - 1 )),$(( cores_per_socket + 1 ))-$(( cores_per_socket * 2 - 1 ))"
		housekeeping="0,$cores_per_socket"

	else
		isolcpus="1-$(( cores_per_socket - 1 ))"
		housekeeping="0"
	fi
elif [ "$numa" == "2" ]; then
	if [ "$threads_per_core" == "2" ] ; then
		isolcpus="1-$(( cores_per_socket - 1 )),$(( cores_per_socket * 2 + 1 ))-$(( cores_per_socket * 3 - 1 ))"
		housekeeping="0,$(( cores_per_socket * 2 )),$(( cores_per_socket ))-$(( cores_per_socket * 2 - 1 )),$(( cores_per_socket * 3 ))-$(( cores_per_socket * 4 - 1 ))"

	else

		isolcpus="1-$(( cores_per_socket - 1 ))"
		housekeeping="0,$(( cores_per_socket ))-$(( cores_per_socket * 2 - 1 ))"
	fi
fi

flexran_kernel_cmdline="intel_iommu=on iommu=pt usbcore.autosuspend=-1 selinux=0 enforcing=0 nmi_watchdog=0 crashkernel=auto softlockup_panic=0 audit=0 cgroup_disable=memory tsc=nowatchdog intel_pstate=disable mce=off hugepagesz=1G hugepages=40 hugepagesz=2M hugepages=0 default_hugepagesz=1G kthread_cpus=$housekeeping irqaffinity=$housekeeping nohz=on nosoftlockup nohz_full=$isolcpus rcu_nocbs=$isolcpus rcu_nocb_poll skew_tick=1 isolcpus=$isolcpus"

echo "$flexran_kernel_cmdline"
