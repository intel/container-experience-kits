# Check Intel Server GPU Device and Driver
BMRA deploys the [intel-gpu/kernel](https://github.com/intel-gpu/kernel) project from GitHub for the latest Intel® Server GPU kernel driver for media processing. To verify that the devices and drivers are present in the system with the correct configuration, perform the following actions.
After installation, both GPU device and kernel must be inspected for the function readiness. First confirm the i915 driver presence and that the ASPEED device is ignored. The kernel option `915.force_probe=*` helps ensure the i915 driver probes for the SG1 device and `i915.enable_guc=2` helps ensure that the device is enabled for SR-IOV.
```
# lsmod | grep i915
i915_spi               24576  0
mtd                    77824  17 i915_spi
i915                 2609152  0
video                  53248  1 i915
i2c_algo_bit           16384  1 i915
drm_kms_helper        217088  1 i915
drm                   610304  3 drm_kms_helper,i915

# cat /proc/cmdline
BOOT_IMAGE=/boot/vmlinuz-5.4.48+ root=/dev/sda1 ro crashkernel=auto rhgb quiet i915.force_probe=* modprobe.blacklist=ast,snd_hda_intel i915.enable_guc=2
```

Verify the Intel Server GPU devices (4907) are present and using the i915 driver.
```
# lspci | grep -i VGA
02:00.0 VGA compatible controller: ASPEED Technology, Inc. ASPEED Graphics Family (rev 41)
1c:00.0 VGA compatible controller: Intel Corporation Device 4907 (rev 01)
21:00.0 VGA compatible controller: Intel Corporation Device 4907 (rev 01)
26:00.0 VGA compatible controller: Intel Corporation Device 4907 (rev 01)
2b:00.0 VGA compatible controller: Intel Corporation Device 4907 (rev 01)
```
```
# lspci -n -v -s 1c:00.0
1c:00.0 0300: 8086:4907 (rev 01) (prog-if 00 [VGA controller])
        Subsystem: 8086:35cf
        Flags: bus master, fast devsel, latency 0, IRQ 423, NUMA node 0
        Memory at a8000000 (64-bit, non-prefetchable) [size=16M]
        Memory at 387e00000000 (64-bit, prefetchable) [size=8G]
        Expansion ROM at <ignored> [disabled]
        Capabilities: [40] Vendor Specific Information: Len=0c <?>
        Capabilities: [70] Express Endpoint, MSI 00
        Capabilities: [ac] MSI: Enable+ Count=1/1 Maskable+ 64bit+
        Capabilities: [d0] Power Management version 3
        Capabilities: [100] Latency Tolerance Reporting
        Kernel driver in use: i915
        Kernel modules: i915
```
Confirm that the Intel Server GPU kernel drivers are present on the system.
```
# ls /dev/dri/ -l
total 0
crw-rw----. 1 root video 226,   0 Apr  8 10:15 card0
crw-rw----. 1 root video 226,   1 Apr  8 10:15 card1
crw-rw----. 1 root video 226,   2 Apr  8 10:15 card2
crw-rw----. 1 root video 226,   3 Apr  8 10:15 card3
crw-rw----. 1 root video 226, 128 Apr  8 10:15 renderD128
crw-rw----. 1 root video 226, 129 Apr  8 10:15 renderD129
crw-rw----. 1 root video 226, 130 Apr  8 10:15 renderD130
crw-rw----. 1 root video 226, 131 Apr  8 10:15 renderD131
```
You are now ready to deploy transcode workloads to utilize the hardware components. For more information, see the Open Visual Cloud GitHub site: [https://github.com/OpenVisualCloud/CDN-Transcode-Sample].
