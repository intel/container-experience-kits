# FQDN Deployment

CEK can also be deployed through FQDNs instead of IPs. Make sure the FQDN is stable before deploying it.

## BMRA

An example of inventory.ini is as under

```bash
[all]
controller.xy.example.com ansible_host=controller.xy.example.com ansible_user=USER ansible_password=USER
node.xy.example.com ansible_host=node.xy.example.com ansible_user=USER ansible_password=USER
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3

[vm_host]

[kube_control_plane]
controller.xy.example.com

[etcd]
controller.xy.example.com

[kube_node]
node.xy.example.com

[k8s_cluster:children]
kube_control_plane
kube_node

[all:vars]
ansible_python_interpreter=/usr/bin/python3
 
```

> Note: In host_vars, please use complete FQDN such as **node.xy.example.com.yml**
        also use complete FQDN name when updating lists in host_vars or group_vars such as in example mentioned under

```bash
# Intel Kubernetes Power Manager
intel_power_manager:
  enabled: true   # enable intel_power_manager
  # The performance profile is available for nodes that has CPU max MHz > 3500.0000 - use 'lscpu' command to see your node details
  power_profiles: [performance, balance-performance, balance-power]       # the list of PowerProfiles that will be available on the nodes
                                                                          # possible PowerProfiles are: performance, balance_performance, balance_power
  power_nodes:                                                          # list of nodes that should be considered during Operator work and profiles deployment
     - node.xy.example.com
    # - node2
  build_image_locally: false
  deploy_example_pods: false                                      # deploy example Pods that will utilize special resources
  global_shared_profile_enabled: false                            # deploy custom Power Profile with user defined frequencies that can be applied to all power nodes
                                                                  # to make use of Shared Profile fill Shared Workload settings in host vars
  max_shared_frequency: 1500                                      # max frequency that will be applied for cores by Shared Workload
  min_shared_frequency: 1000                                      # min frequency that will be applied for cores by Shared Workload
```

##  VMRA

 An example of inventory.ini is as under

```bash
[all]
host-for-vms.xy.example.com ansible_host=host-for-vms.xy.example.com ansible_user=USER ansible_password=USER
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3

[vm_host]
host-for-vms.xy.example.com

[kube_control_plane]
#host-for-vms-ctrl-1

[etcd]
#host-for-vms-ctrl-1

[kube_node]
#host-for-vms-work-1

[k8s_cluster:children]
kube_control_plane
kube_node

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

> Note: In host_vars, please use complete FQDN such as host-for-vms.xy.example.com.yml and in host_vars/host-for-vms.xy.example.com.yml VM's names for (workers & controllers) can also be renamed as mentioned below. VM's will be build-up with name selected by user.

```bash
vms:
  - type: "ctrl"
    name: "host-for-vms-ctrl-1"
    cpu_total: 8
    memory: 20480
    vxlan: 120

  - type: "work"
    name: "host-for-vms-work-1"
    cpu_total: 16
    memory: 61440
    vxlan: 120
    pci:
#      - "18:02.0"
#      - "18:02.1"
#      - "18:02.6"
#      - "18:02.7"
```

> Note: In host_vars, please update VM's names (workers & controllers) as updated in **host_vars/host-for-vms.xy.example.com.yml** such as **host_vars/host-for-vms.xy.example.com host-for-vms-ctrl-1.yml host-for-vms-work-1.yml**
