# Check SST-BF Configuration on 2nd Gen. Intel Xeon Scalable Processor
Intel Speed Select Technology - Base Frequency (SST-BF) enables configuration of the base frequency across cores, allowing some cores to run at higher base frequency than others.

Three different configuration modes are supported through `sst_bf_mode`:
* **s:** Set high priority cores to 2700/2800 minimum and 2700/2800 maximum (both depending on CPU) and set normal priority cores to 2100 minimum and 2100 maximum.
* **m:** Set P1 on all cores (2300 minimum and 2300 maximum)
* **r:** Revert cores to minimum/Turbo (set all cores to 800 minimum and 3900 maximum)

To verify that SST-BF was configured as expected, use the following command:
```
# sst-bf.py -i
Name = 6252N
CPUs = 96
Base = 2300
     |------sysfs-------| 
Core | base   max   min | 
-----|------------------| 
   0 | 2100  2100  2100 | 
   1 | 2800  2800  2800 | 
   2 | 2800  2800  2800 | 
   3 | 2100  2100  2100 |
(...)
  94 | 2800  2800  2800 |
  95 | 2100  2100  2100 |
-----|------------------| 
```
The example output shown above is for SST-BF configured with mode "s".

To learn more about Intel SST-BF, visit [https://github.com/intel/CommsPowerManagement](https://github.com/intel/CommsPowerManagement/blob/master/sst_bf.md).
