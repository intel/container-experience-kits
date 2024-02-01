# IPU setup user guide

This guide introduces how to enable Intel(R) Infrastructure Processing Unit (Intel(R) IPU) inside RA environment.
IPU consist of two main blocks: Integrated Management Complex (IMC) and Acceleration Compute Complex (ACC)


## IPU physical setup - Config L

Two physical machines are needed for this setup 'IPU host' and 'IPU link partner'
Both machines are connected to management network
IPU board has five different connection points:
 - IPU board is inserted into PCIe slot on Xeon IPU host
 - IPU board is connected with IPU host via power connection
 - IPU board is connected via 1GbE connection to IPU link partner host
 - IPU board is connected via serial Mini USB connection to IPU link partner host
 - IPU board is connected via high speed connection to CVL NIC on IPU link partner host

IPU host needs to have Baseboard Management Controller (BMC) interface configured and connected to network to be usable via
Intelligent Platform Management Interface (IPMI) tool


## IPU host and IPU linkp OS

Currently supported OSes are Rocky 9.1, Rocky 9.2 and Fedora


## IPU pre-built images

Please ask Intel Support to get tarballs with IPU pre-built images.
Insert those tarballs into directory /tmp/ipu on your ansible host
E.g.: EthProgrammer-2.0.1.zip
      hw-flash.6330.tgz
      hw-ssd.6330.tgz
      hw-p4-programs.6330.tgz
      Intel_IPU_SDK-6330.tgz
      hw-workbench.6330.tgz


## IPU inventory preparation

Copy docs/ipu_inventory_example.ini to ipu_inventory.ini and update all relevant fields for your environment

ipu_host_machine ansible_host=<mgmt_if_ip> ip=<mgmt_if_ip> ansible_user=root ansible_password=<password>
ipu_link_partner ansible_host=<mgmt_if_ip> ip=<mgmt_if_ip> ansible_user=root ansible_password=<password> ipmi_ip=<ipmi_ip_for_ipu_host> ipmi_user=bmcuser ipma_password='<password>'

NOTE: If you need to connect 1GbE connection from IPU board to IPU host machine instead of IPU link partner (from any reason)
      then you need to change variable ipu_1gbe_connected_to_linkp inside inventory from true to false
      In that case you need to provide ipmi credentials in inventory record for ipu_host_machine
      and run deployment under root user or any other user with paswordless sudo on ansible_host
```
ipu_host_machine ansible_host=<mgmt_if_ip> ip=<mgmt_if_ip> ansible_user=root ansible_password=<password> ipmi_ip=<ipmi_ip_for_ipu_host> ipmi_user=bmcuser ipma_password='<password>'
```

NOTE: If you do not specify ipmi credentials at all then power cycle will be replaced with reboot.
      Reboot is sufficient in some cases but does not reinitialize IPU card reliably. If IMC and ACC does not come up properly then
      manual power cycle (power off, wait at least 10 secs, power on) needs to be done.

Here is error message when IMC and ACC are not initialized properly
```
TASK [ipu/flash_ipu_nvm : wait for ssh connection to IPU-IMC] ****************************************************************************************
task path: /root/final_ipu/cek/roles/ipu/flash_ipu_nvm/tasks/main.yml:116
fatal: [ae07-06-wp-ipu6-linkp]: FAILED! => {
    "changed": false,
    "elapsed": 301
}

MSG:

Timeout when waiting for search string OpenSSH in 100.0.0.100:22
```

Once power cycle is done, wait for ssh connection to ipu_host_machine.
Once the ssh connection is ready you can continue with ansible script via:
```
ansible-playbook -i ipu_inventory.ini playbooks/infra/prepare_ipu.yml --start-at-task "wait for ssh connection to IPU-IMC" --flush-cache -vv 2>&1 | tee ipu_deployment_cont.log
```

NOTE: If ansible script failed during ipmi related operations from any reason E.g.: wrong/missing ipmi credentials then fix configuration and
      run deployment from point before power cycle/reboot handling again via:
```
ansible-playbook -i ipu_inventory.ini playbooks/infra/prepare_ipu.yml --start-at-task "IPU images are flashed" --flush-cache -vv 2>&1 | tee ipu_deployment_power.log
```


## IPU group_vars

IPU deployment uses group_vars/all.yml from standard RA deployment.
So, if deployment is executed behind proxy then corresponding proxy configuration have to be done.

To prepare needed deployment environment please follow listed steps from [README](README.md):
step 1. (basic)
step 2. section b)
step 3.
step 4. (tested with icx/cvl)
step 7. (k8s)
step 8. proxy and mirror settings if needed


## IPU deployment

To start IPU deployment run following command

```
ansible-playbook -i ipu_inventory.ini playbooks/infra/prepare_ipu.yml  --flush-cache -vv 2>&1 | tee ipu_deployment.log
```

Here is summary of Successful deployment:

PLAY RECAP ***********************************************************************************************************
ipu_link_partner           : ok=72   changed=34   unreachable=0    failed=0    skipped=6    rescued=0    ignored=0
ipu_host_machine           : ok=14   changed=6    unreachable=0    failed=0    skipped=12   rescued=0    ignored=0
ipu-acc                    : ok=28   changed=21   unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
ipu-imc                    : ok=11   changed=5    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
*********************************************************************************************************************

NOTE: Unreachable=1 for ipu_link_partner can appear as expected state. It is caused by ansible error and has no impact to deployment
PLAY RECAP ***********************************************************************************************************
ipu_link_partner           : ok=71   changed=34   unreachable=1    failed=0    skipped=5    rescued=0    ignored=0
*********************************************************************************************************************


### IPU deployment progress monitoring

IPU deployment progress can be monitored via remote console for IPU host and via minicom connections to IMC and ACC from IPU link partner machine
minicom tool is installed in initial phase of deployment. So, it is available after approximately one minute.

```
minicom IMC
then press enter
```

```
minicom ACC
then press enter
```

NOTE: To escape from minicom use 'Ctrl-a q' and then enter
      To get minicom help use 'Ctrl-a z'


Finished deployment on ACC:

Rocky Linux 9.2 (Blue Onyx)
Kernel 5.15.120_ipu_acc on an aarch64

ipu-acc login:


Finished deployment on IMC:

+-------------------+
| Intel IPU SDK     |
| Version: 1.0.0    |
| Complex: IMC      |
+-------------------+
  Built on   : Wed Sep  6 03:38:07 UTC 2023
  Build host : Linux x86_64
  Source rev : 49f2e2588be2401c2025bce28e1a43d32119ee39
  Build      : ci-ts.release.6330
  ---
  IMC uBoot  : 2023.07
  IMC Kernel : 5.15.120

ipu-imc login:


### IPU post deployment accessibility

During IPU deployment updated version of inventory is generated:  ipu_inventory_mev.ini
It contains records for IMC and ACC and corresponding host groups.
That inventory can be used to install/configure additional software on IMC and ACC.

SSH config on ansible host is updated with records for IMC and ACC as well.
It allows to access IMC and ACC via ssh.

For IMC:

```
ssh ipu-imc
```

For ACC:

```
ssh ipu-acc
```


### IPU/IPDK Networking recipe verification

IPU setup scripts prepare IPU/IPDK Networking recipe including one custom P4 program for l2-fwd_lem.
Here are steps how to validate that setup works correctly:

1. login to ipu-imc to check ports

```
ssh ipu-imc cli_client -q -c
```

Output:
Warning: Permanently added 'ae07-06-wp-ipu6-linkp,10.166.30.171' (ECDSA) to the list of known hosts.
Warning: Permanently added 'ipu-imc' (ECDSA) to the list of known hosts.
No IP address specified, defaulting to localhost
fn_id: 0x4   host_id: 0x4   is_vf: no  vsi_id: 0x2   vport_id 0x0   is_created: yes  is_enabled: yes mac addr: 00:00:00:00:03:18
promiscuous mode: 00
fn_id: 0x4   host_id: 0x4   is_vf: no  vsi_id: 0x8   vport_id 0x1   is_created: yes  is_enabled: yes mac addr: 00:08:00:01:03:18
promiscuous mode: 00
fn_id: 0x4   host_id: 0x4   is_vf: no  vsi_id: 0x9   vport_id 0x2   is_created: yes  is_enabled: yes mac addr: 00:09:00:02:03:18
promiscuous mode: 00
fn_id: 0x4   host_id: 0x4   is_vf: no  vsi_id: 0xa   vport_id 0x3   is_created: yes  is_enabled: yes mac addr: 00:0a:00:03:03:18
promiscuous mode: 00
fn_id: 0x5   host_id: 0x5   is_vf: no  vsi_id: 0x3   vport_id 0x0   is_created: yes  is_enabled: yes mac addr: 00:00:00:00:03:19
promiscuous mode: 00
fn_id: 0x5   host_id: 0x5   is_vf: no  vsi_id: 0x5   vport_id 0x1   is_created: yes  is_enabled: yes mac addr: 00:05:00:01:03:19
promiscuous mode: 00
fn_id: 0x5   host_id: 0x5   is_vf: no  vsi_id: 0x6   vport_id 0x2   is_created: yes  is_enabled: yes mac addr: 00:06:00:02:03:19
promiscuous mode: 00
fn_id: 0x5   host_id: 0x5   is_vf: no  vsi_id: 0x7   vport_id 0x3   is_created: yes  is_enabled: yes mac addr: 00:07:00:03:03:19
promiscuous mode: 00
fn_id: 0xc   host_id: 0x4   is_vf: no  vsi_id: 0x4   vport_id 0x0   is_created: yes  is_enabled: no mac addr: 00:00:00:00:03:20
promiscuous mode: 00
fn_id: 0xc   host_id: 0x4   is_vf: no  vsi_id: 0xb   vport_id 0x1   is_created: yes  is_enabled: yes mac addr: 00:0b:00:01:03:20
promiscuous mode: 00
fn_id: 0xc   host_id: 0x4   is_vf: no  vsi_id: 0xc   vport_id 0x2   is_created: yes  is_enabled: yes mac addr: 00:0c:00:02:03:20
promiscuous mode: 00

server finished responding =======================

The first four lines correspond to four NICs inside ACC. The fourth one is used for sending traffic to ACC.
Its mac address is 00:0a:00:03:03:18 and vsi_id: 0xa -> it is 10 in decimal. Once we want to use it inside br0 rule we need to add constant 16 to it.
So, final port value inside rule is 26.



2. login to ipu-acc and check NIC name which holds mac address found in step 1

[root@ipu-acc ~]# ip a show enp0s1f0d3
5: enp0s1f0d3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0a:00:03:03:18 brd ff:ff:ff:ff:ff:ff


3. login to ipu-acc and start tcpdump with NIC name found in step 2. In our case enp0s1f0d3.

```
ssh ipu-acc tcpdump -xni enp0s1f0d3 -vv -s0 -e
```


4. login to ipu_linkp run scapy there and send 100 packets to ACC

```
ssh ae07-06-wp-ipu6-linkp scapy
enter
sendp(Ether(dst="00:00:00:00:03:43", src="9e:ba:ce:98:d9:d3")/Raw(load="0"*50), iface='ens785f0', count=100)
enter
```
....................................................................................................
Sent 100 packets.
>>>


5. on ipu-acc you will see 100 packets received

01:19:46.679164 9e:ba:ce:98:d9:d3 > 00:00:00:00:03:43, ethertype Loopback (0x9000), length 64: Loopback, skipCount 12336 (invalid)
        0x0000:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0010:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0020:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0030:  3030
01:19:46.679264 9e:ba:ce:98:d9:d3 > 00:00:00:00:03:43, ethertype Loopback (0x9000), length 64: Loopback, skipCount 12336 (invalid)
        0x0000:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0010:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0020:  3030 3030 3030 3030 3030 3030 3030 3030
        0x0030:  3030
