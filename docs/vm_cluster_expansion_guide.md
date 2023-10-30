# VM cluster expansion guide


VM cluster expansion means that we can add additional vm-work node(s) to existing VM cluster. They can be added on any existing vm_host machines or new vm_host machine(s) can be added as well. By default VM cluster expansion feature won't re-create existing VMs, which are in 'running' state. They will remain untouched during VM creation phase, nevertheless standard ansible deployment tasks will run on them as well. Corresponding ansible playbooks should be idempotent to ensure that running tasks again won't corrupt target system. Group vars for VM case contain new variable `vm_recreate_existing` with value set to `false`.
In order to expand VM cluster, the original VM cluster have to be up and running.

```
vm_recreate_existing: false
```

For VM cluster expansion deployment we should use the same ansible host, which was used for original VM cluster deployment.
Deployment configuration can't be changed except adding definitions for new VMs. Configuration of existing VMs have to remain the same.

**_NOTE:_** If you want to add new vm-work node to existing vm_host then the vm_host needs to have enough free available resources for it.

**_NOTE:_** VM cluster expansion deployment is not intended for any kind of configuration update on existing VMs.

**_NOTE:_** VM cluster reduction - removing vm-work node(s) from VM cluster - is not supported at all.


## Adding new vm-work to existing vm_host

To add new vm-work to existing vm-host you need to update vms definition in host_vars file for corresponding vm_host.
In example bellow we've added new vm-work node definition with name `vm-work-4`

```
vms:
  ...
  ...
  ...
  - type: "work"
    name: "vm-work-4"
    cpu_total: 16
    memory: 20480
    vxlan: 128
    pci:
      - "18:02.0"
      - "18:02.1"
      - "18:02.6"
      - "18:02.7"
      - "b1:01.3"
      - "b3:01.3"
```

New host_vars file needs to be created for added vm-work node. In our case host_vars/vm-work-4.yml.
Existing host_vars/vm-work-1.yml can be used as a template.


## Adding new vm_host machine with new vm-work

To add new vm_host machine you need to follow point 6 and point 8 in [README](README.md)
To be more precise we need to do three steps:
1) add new vm_host to inventory
  - Add vm_host info to section [all]
  - Add vm_host name to the end of section [vm_host]

2) create host_vars file for that vm_host from template host_vars/host-for-vms-2.yml
  - Update host specific params like `dataplane_interfaces` and `qat_devices`
  - Fill vms section with new vm-work node(s)

3) create new host_vars file for added vm-work node. In our case host_vars/vm-work-5.yml.
   Existing host_vars/vm-work-1.yml can be used as a template.


```
vms:
  - type: "work"
    name: "vm-work-5"
    cpu_total: 16
    memory: 20480
    vxlan: 128
    pci:
      - "18:02.0"
      - "18:02.1"
      - "18:02.6"
      - "18:02.7"
      - "b1:01.3"
      - "b3:01.3"
```



## Run VM cluster expansion deployment

Once we have prepared configuration for new VMs, we can run deployment via following command:

```
ansible-playbook -i inventory.ini playbooks/vm.yml -e scale=true
or
ansible-playbook -i inventory.ini playbooks/vm.yml -e scale=true --flush-cache -vv 2>&1 | tee vm_cluster_expansion.log
```



## Other options

If you want to update VM cluster including current VMs then `vm_recreate_existing` parameter can be switched to `true`
In that case all existing VMs will be destroyed and re-created again.

**_NOTE:_** All data, configurations and logs stored on VMs will be lost. Re-created VMs will get new IPs.
**_NOTE:_** If `vm_recreate_existing` is set to `true` then following two lists `vm_recreate_listed_vms` and `vm_keep_listed_vms` are not evaluated.

```
vm_recreate_existing: true
```


If you want to update just specific VM(s) then keep `vm_recreate_existing` parameter on `false` and use another configuration parameter
`vm_recreate_listed_vms` and insert VM names, which should be re-created, there. Default value for this paramater is empty list `[]`

```
vm_recreate_listed_vms: []
```

VMs to be re-created should be provided as list items E.g.:

```
vm_recreate_listed_vms:
  - vm-work-2
  - vm-1
```


If you want to keep existing VM, which is not in `running` state untouched from any reason then keep `vm_recreate_existing` parameter on `false`
and use another configuration parameter `vm_keep_listed_vms` and insert VM names, which should be kept, there. Default value for this paramater is empty list `[]`

```
vm_keep_listed_vms: []
```

VMs to be kept should be provided as list items E.g.:

```
vm_keep_listed_vms:
  - vm-work-3
  - vm-1
```

**_NOTE:_** If the same VM name appears in both lists `vm_recreate_listed_vms` and `vm_keep_listed_vms` then `vm_keep_listed_vms` has precedence and VM will be kept.
**_NOTE:_** Deployment procedure tries to start not running VMs, which were kept. Nevertheless subsequent ansible plays can fail if VM start was not successful or if they are in some inconsistent state.


To run those options use following command:

```
ansible-playbook -i inventory.ini playbooks/vm.yml
or
ansible-playbook -i inventory.ini playbooks/vm.yml --flush-cache -vv 2>&1 |tee vm_cluster_recreate.log
```
