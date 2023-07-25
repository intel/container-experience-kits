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


## IPU pre-built images

Please ask Intel Support to get tarballs with 'imc' and 'mev-rl' images.
Insert those tarballs into directory /tmp/ipu on your ansible host


## IPU inventory preparation

Copy docs/ipu_inventory_example.ini to ipu_inventory.ini and update all relevant fields for your environment

ipu_host_machine ansible_host=<mgmt_if_ip> ip=<mgmt_if_ip> ansible_user=root ansible_password=<password>
ipu_link_partner ansible_host=<mgmt_if_ip> ip=<mgmt_if_ip> ansible_user=root ansible_password=<password> ipmi_ip=<ipmi_ip_for_ipu_host> ipmi_user=bmcuser ipma_password='<password>'

NOTE: If you need to connect 1GbE connection from IPU board to IPU host machine instead of IPU link partner (from any reason)
      then you need to change variable ipu_1gbe_connected_to_linkp inside inventory from true to false


## IPU group_vars

IPU deployment uses group_vars/all.yml from standard RA deployment.
So, if deployment is executed behind proxy then corresponding proxy configuration have to be done.


## IPU deployment

To start IPU deployment run following command

```
ansible-playbook -i ipu_inventory.ini playbooks/infra/prepare_ipu.yml  --flush-cache -vv 2>&1 | tee ipu_deployment.log
```

Here is summary of Successful deployment:

PLAY RECAP ***********************************************************************************************************
ipu_link_partner           : ok=49   changed=8    unreachable=1    failed=0    skipped=5    rescued=0    ignored=0
ipu_host_machine           : ok=13   changed=0    unreachable=0    failed=0    skipped=11   rescued=0    ignored=0
mev-acc-rl                 : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
mev-imc                    : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
*********************************************************************************************************************

NOTE: Unreachable=1 for ipu_link_partner is expected state. It is caused by ansible error and has no impact to deployment


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

MEV ACC mev-hw-b0-ci-ts.release.4988 mev-acc-rl -
mev-acc-rl login:


Finished deployment on IMC:

INFO: ######## System booted successfully! ########
MEV IMC MEV-HW-B0-CI-ts.release.4988 mev-imc /dev/ttyS0
mev-imc login:


### IPU post deployment accessibility

During IPU deployment updated version of inventory is generated:  ipu_inventory_mev.ini
It contains records for IMC and ACC and corresponding host groups.
That inventory can be used to install/configure additional software on IMC and ACC.

SSH config on ansible host is updated with records for IMC and ACC as well.
It allows to access IMC and ACC via ssh.

For IMC:

```
ssh mev-imc
```

For ACC:

```
ssh mev-acc-rl
```
