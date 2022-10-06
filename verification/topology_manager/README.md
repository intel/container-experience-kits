# Check Topology Manager
Topology Manager supports its allocation policies via a Kubelet flag, `--topology-manager-policy`. There are four supported policies:
* **none:** Kubelet does not perform any topology alignment.
* **best-effort (default in BMRA deployment script):** Using resource availability reported by hint providers for each container in a guaranteed pod, the Topology Manager stores the preferred NUMA node affinity for that container. If the affinity is not preferred, Topology Manager stores this and admits the pod to the node anyway. The hint providers can then use this information when making the resource allocation decision.
* **restricted:** Using resource availability reported by hint providers for each container in a guaranteed pod, the Topology Manager stores the preferred NUMA node affinity for that container. If the affinity is not preferred, Topology Manager rejects this pod from the node. This results in a pod in a terminated state with a pod admission failure.
After the pod is in a terminated state, the Kubernetes scheduler will not attempt to reschedule the pod. We recommend you use a ReplicaSet or Deployment to trigger a redeploy of the pod. Alternatively, you could implement an external control loop to trigger a redeployment of pods that have the Topology Affinity error.
If the pod is admitted, the hint providers can then use this information when making the resource allocation decision.
* **single-numa-node:** Using resource availability reported by hint providers for each container in a guaranteed pod, the Topology Manager determines if a single NUMA node affinity is possible. If it is, Topology Manager stores this and the hint providers can then use this information when making the resource allocation decision. If this is not possible, however, then the Topology Manager rejects the pod from the node. This results in a pod in a terminated state with a pod admission failure.
After the pod is in a terminated state, the Kubernetes scheduler will not attempt to reschedule the pod. It is recommended to use a deployment with replicas to trigger a redeploy of the pod. An external control loop could be also implemented to trigger a redeployment of pods that have the Topology Affinity error.

To verify that Topology Manager is running, use the following command:
```
# journalctl | grep topology_manager
Sep 19 05:58:35 node1 kubelet[137442]: I0919 05:58:35.380933  137442 topology_manager.go:200] "Topology Admit Handler"
Sep 19 06:58:35 node1 kubelet[137442]: I0919 06:58:35.161388  137442 topology_manager.go:200] "Topology Admit Handler"
Sep 19 07:58:35 node1 kubelet[137442]: I0919 07:58:35.059673  137442 topology_manager.go:200] "Topology Admit Handler"
Sep 19 08:58:42 node1 kubelet[137442]: I0919 08:58:42.098158  137442 topology_manager.go:200] "Topology Admit Handler"
Sep 19 09:58:42 node1 kubelet[137442]: I0919 09:58:42.903203  137442 topology_manager.go:200] "Topology Admit Handler"
```

## Change Topology Manager Policy: Redeploy Kubernetes Playbook
This section describes one of two ways to change Topology Manager policy configuration after cluster deployment, by redeploying the Kubernetes playbook. It is only possible to use this method when BMRA has been deployed. For VMRA use the manual method mentioned below.
1. Update the `group_vars/all.yml` file.
```
# Enable Kubernetes built-in Topology Manager
topology_manager_enabled: true
# There are four supported policies: none, best-effort, restricted, single-numa-node.
topology_manager_policy: "single-numa-node"
```
2. Execute the ansible-playbook command to apply the new configuration cluster-wide.
```
# ansible-playbook -i inventory.ini playbooks/k8s/k8s.yml
```

## Change Topology Manager Policy: Manually Update Kubelet Flags
This section describes a method of changing Topology Manager policy configuration after cluster deployment, by manually updating Kubelet flags on a specific node. 
1. Log in to the worker node via SSH, for example:
```
# ssh <worker node name>
```
2. Edit the kubelet configuration in the `/etc/kubernetes/kubelet-config.yaml` file.
```
(...)
topologyManagerPolicy: single-numa-node
(...)
```
3. Restart the Kubelet service.
```
# systemctl restart kubelet
```
