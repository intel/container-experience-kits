# Check SST Configuration on 3rd and Next Gen. Intel Xeon Scalable Processors
On 3rd and Next Gen. Intel Xeon Scalable Processors there are several features available for Intel Speed Select Technology (SST). Below are examples for verifying Base Frequency (SST-BF), Core Power (SST-CP) and Performance Profile (SST-PP) with Turbo Frequency (SST-TF).

## Availability:
Depending on the processor generation, the available features are:
* 3rd Generation Intel Xeon Scalable Processors
  - SST-BF
  - SST-CP
* 3rd and Next Generation Intel Xeon Scalable Processors
  - SST-PP with SST-TF

## Check Intel SST-BF Configuration
To display Intel SST-BF properties, use the following command:
```
# intel-speed-select base-freq info -l 0 
Intel® Speed Select Technology
Executing on CPU model:106[0x6a]
 package-0
  die-0
    cpu-0
      speed-select-base-freq-properties
        high-priority-base-frequency(MHz):2400
        high-priority-cpu-mask:00000000,000030cc,cc0c0330
        high-priority-cpu-list:4,5,8,9,18,19,26,27,30,31,34,35,38,39,44,45
        low-priority-base-frequency(MHz):1800
        tjunction-temperature(C):105
        thermal-design-power(W):185
 package-1
  die-0
    cpu-48
      speed-select-base-freq-properties
        high-priority-base-frequency(MHz):2400
        high-priority-cpu-mask:000c0f3c,c3c00000,00000000
        high-priority-cpu-list:54,55,56,57,62,63,66,67,68,69,72,73,74,75,82,83
        low-priority-base-frequency(MHz):1800
        tjunction-temperature(C):105
        thermal-design-power(W):185
```

To help ensure that Intel SST-BF is enabled, check the base frequency of CPUs:
```
# cat /sys/devices/system/cpu/cpu0/cpufreq/base_frequency
1800000
# cat /sys/devices/system/cpu/cpu4/cpufreq/base_frequency
2400000
# cat /sys/devices/system/cpu/cpu5/cpufreq/base_frequency
2400000
```
CPUs 4 and 5 are configured as high priority CPUs and have a base frequency of 2.4 GHz.
CPU 0 is configured as normal priority and has a base frequency of 1.8 GHz.

## Check Intel SST-CP Configuration
Intel SST-CP enables a user to set up four Classes Of Service (CLOS) assign each CPU to a class.
To verify the correctness of CLOS 0, use the following command:
```
# intel-speed-select core-power get-config -c 0
Intel® Speed Select Technology
Executing on CPU model:106[0x6a]
 package-0
  die-0
    cpu-0
      core-power
        clos:0
        epp:0
        clos-proportional-priority:0
        clos-min:2400 MHz
        clos-max:Max Turbo frequency
        clos-desired:0 MHz
 package-1
  die-0
    cpu-48
      core-power
        clos:0
        epp:0
        clos-proportional-priority:0
        clos-min:2400 MHz
        clos-max:Max Turbo frequency
        clos-desired:0 MHz
```

To verify the CLOS assignment for CPUs 0, 4 and 5, use the following command:
```
# intel-speed-select -c 0,4-5 core-power get-assoc
Intel® Speed Select Technology
Executing on CPU model:106[0x6a]
 package-0
  die-0
    cpu-0
      get-assoc
        clos:3
 package-0
  die-0
    cpu-4
      get-assoc
        clos:0
 package-0
  die-0
    cpu-5
      get-assoc
        clos:0
```
To learn more about Intel SST-CP or Intel SST-CP classes of service, refer to: [https://www.kernel.org/doc/html/latest/admin-guide/pm/intel-speed-select.html#intel-r-speed-select-technology-core-power-intel-r-sst-cp]

## Check Intel SST-PP with Intel SST-TF
To verify the availability of Intel SST-PP and its features, use the following command:
```
# intel-speed-select –info
Intel(R) Speed Select Technology
Executing on CPU model:143[0x8f]
Platform: API version : 1
Platform: Driver version : 1
Platform: mbox supported : 1
Platform: mmio supported : 1
Intel(R) SST-PP (feature perf-profile) is supported
TDP level change control is unlocked, max level: 3
Intel(R) SST-TF (feature turbo-freq) is supported
Intel(R) SST-BF (feature base-freq) is supported
Intel(R) SST-CP (feature core-power) is supported
```

To verify that Intel SST-PP is unlocked in the BIOS:
```
# intel-speed-select perf-profile get-lock-status
Intel(R) Speed Select Technology
Executing on CPU model:143[0x8f]
Caching topology information
 package-0
  die-0
    cpu-0
      get-lock-status:unlocked
```

To confirm that the statuses of Intel SST-BF, Intel SST-CP, and Intel SST-TF are enabled or disabled, which must match the value of SST-PP in host_vars, and to check the properties of perf-level, use the following commands:
```
# intel-speed-select perf-profile info -l 0 2>&1 | grep 'speed-select'
        speed-select-turbo-freq:enabled
        speed-select-base-freq:enabled
        speed-select-core-power:enabled
        speed-select-base-freq-properties
        speed-select-turbo-freq-properties
          speed-select-turbo-freq-clip-frequencies
```
```
# intel-speed-select perf-profile get-config-levels
Intel(R) Speed Select Technology
Executing on CPU model:143[0x8f]
 package-0
  die-0
    cpu-0
      get-config-levels:3
```
**Note:** config-levels must be get-config-levels:3 (Intel SST-BF, Intel SST-CP, and Intel SST-TF ). get-config-levels: 0 means misconfiguration of setup in software or BIOS.

Set turbo status on and off to verify busy workload frequency ranges dynamically when Intel SST-PP is configured. For example, if CPUs 0,40,1,41,2,42,3,43,5,45,8,48,9,49,10,50,11,51,13,53 are defined in host_vars for Intel SST-PP to get 100 MHz boost, use the following commands for verification:

Start by disabling Turbo Boost:
```
# echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo
```
Now check the frequency of CPUs:
```
# turbostat -c 0,40,1,41,2,42,3,43,5,45,8,48,9,49,10,50,11,51,13,53 --show Package,Core,CPU,Bzy_MHz -i 1
Core    	CPU     	Bzy_MHz
-      	        -       	798
0       	0       	800
0       	40      	803
1       	1       	800
1       	41      	799
2       	2       	800
2       	42      	803
3       	3       	800
3       	43      	803
5       	5       	800
5       	45      	801
8       	8       	800
8       	48      	803
9       	9       	800
9       	49      	802
10      	10      	800
10      	50      	798
11      	11      	800
11      	51      	802
13      	13      	800
13      	53      	800
```

Enable Turbo Boost:
```
# echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo
```
Then check the frequency of CPUs again:
```
Core    	CPU     	Bzy_MHz
-       	-       	2888
0      	        0       	2896
0       	40      	2885
1       	1       	2884
1       	41      	2901
2       	2       	2899
2       	42      	2888
3       	3       	2900
3       	43      	2895
5      	        5       	2889
5       	45      	2900
8       	8       	2901
8       	48      	2898
9       	9       	2857
9       	49      	2900
10      	10      	2900
10      	50      	2838
11      	11      	2900
11      	51      	2900
13      	13      	2900
13      	53      	2902
14      	14      	2901
```
Note that improved performance in a frequency range can be observed dynamically as it jumps from approximately 800 to approximately 2900 in CPUs when Intel SST-PP is configured with turbo-freq.
