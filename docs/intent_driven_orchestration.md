# Intent Driven Orchestration (IDO)
Intent Driven Orchestration enables management of applications through their Service Level Objectives, while minimizing developer and administrator overhead.

This is achieved by doing orchestration based on intents in the form of objectives, which is done by the planner utilizing a set of actuators.

More information about IDO can be found here: [Intent Driven Orchestration (GitHub)](https://github.com/intel/intent-driven-orchestration)

## Ansible Configuration
IDO is available in the following profiles:
- on_prem
- regional_dc
- remote_fp
- build_your_own

Configure the Ansible host and generate the playbooks for any of these profiles using the steps described in the main readme file.

The installation of IDO has two dependencies:
- LinkerD
- Local Docker Registry

Update `group_vars/all.yml` to enable IDO and dependencies:
```yaml
# Istio must be disabled, as we will be enabling LinkerD
istio_service_mesh:
  enabled: false
  intel_preview:
    enabled: false
  tcpip_bypass_ebpf:
    enabled: false
  tls_splicing:
    enabled: false
  sgx_signer:
    enabled: false
(...)
linkerd_service_mesh:
  enabled: true
(...)
registry_enable: true
(...)
ido:
  enabled: true
# The demo workload is optional, but useful for testing.
# For this document, it is assumed that it has been enabled
  demo_workload: true
```

Prepare `inventory.ini` and `host_vars/<node>.yml` according to your environment, and proceed with the deployment as described in the main readme.

## Post Deployment
After successfully deploying, verify that IDO resources are available and running in the cluster:
```
# kubectl get all -n ido
NAME                     READY   STATUS    RESTARTS   AGE
pod/cpu-scale-actuator   1/1     Running   0          18h
pod/planner              1/1     Running   0          18h
pod/planner-mongodb      1/1     Running   0          18h
pod/rdt-actuator         1/1     Running   0          18h
pod/rmpod-actuator       1/1     Running   0          18h
pod/scaleout-actuator    1/1     Running   0          18h

NAME                                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)     AGE
service/cpu-scale-actuator-service   ClusterIP   None           <none>        33334/TCP   18h
service/planner-mongodb-service      ClusterIP   10.233.2.41    <none>        27017/TCP   18h
service/plugin-manager-service       ClusterIP   10.233.6.112   <none>        33333/TCP   18h
service/rdt-actuator-service         ClusterIP   None           <none>        33334/TCP   18h
service/rmpod-actuator-service       ClusterIP   None           <none>        33334/TCP   18h
service/scaleout-actuator-service    ClusterIP   None           <none>        33334/TCP   18h
```

_The content below assumes that `demo_workload: true` was configured in `host_vars`._

The demo steps provided in [Intent Driven Orchestration - Getting Started (GitHub)](https://github.com/intel/intent-driven-orchestration/blob/main/docs/getting_started.md#demo) will not work with this example workload, as the network service has been removed. The demo provided below will instead utilize deployment scaling to show the functionality of IDO.

The example workload and IDO resources related to the workload (KPIProfiles and Intent) are created in the default namespace.

Check the status of workload resources:
```
# kubectl get pods,deployments,intents,kpiprofiles
NAME                                          READY   STATUS    RESTARTS   AGE
pod/ido-example-deployment-5f476b97d4-55gnn   2/2     Running   0          18h

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ido-example-deployment   1/1     1            1           18h

NAME                                      INTENTS   PRIO   AGE
intent.ido.intel.com/ido-example-intent             0.01   18h

NAME                                    RESOLVED   AGE
kpiprofile.ido.intel.com/availability   true       18h
kpiprofile.ido.intel.com/p50latency     true       18h
kpiprofile.ido.intel.com/p95latency     true       18h
kpiprofile.ido.intel.com/p99latency     true       18h
kpiprofile.ido.intel.com/throughput     true       18h
```

In the above, `pod/ido-example-deployment-5f476b97d4-55gnn` is the sample workload (sample-function & linkerd-proxy), and `deployment.apps/ido-example-deployment` is the deployment that handles the workload/pod.

All of the KPIProfiles (`kpiprofile.ido.intel.com/*`) are prometheus queries towards the LinkerD prometheus instance running on the cluster.

Lastly the Intent (`intent.ido.intel.com/ido-example-intent`) is a set of objectives utilizing the data from the KPIProfiles. The intent is referencing the workload deployment mentioned above, which can also be seen below:
```
# kubectl get intent.ido.intel.com/ido-example-intent -o=yaml
apiVersion: ido.intel.com/v1alpha1
kind: Intent
metadata:
  creationTimestamp: "2023-09-27T17:49:48Z"
  generation: 1
  name: ido-example-intent
  namespace: default
  resourceVersion: "8591"
  uid: 5eaed99d-cee3-4230-a8ee-81c69171927a
spec:
  objectives:
  - measuredBy: default/p95latency
    name: ido-example-p95compliance
    value: 4
  - measuredBy: default/availability
    name: ido-example-availability
    value: 0.99
  - measuredBy: default/throughput
    name: ido-example-rps
    value: 0
  priority: 0.01
  targetRef:
    kind: Deployment
    name: default/ido-example-deployment
```

To test out IDO, modify the workload deployment to create additional replicas (5):
```
# kubectl scale deployment ido-example-deployment --replicas=5
deployment.apps/ido-example-deployment scaled
```

Now check if additional pods have been created:
```
# kubectl get pods,deployments
NAME                                          READY   STATUS    RESTARTS   AGE
pod/ido-example-deployment-5f476b97d4-55gnn   2/2     Running   0          18h
pod/ido-example-deployment-5f476b97d4-ddh8k   2/2     Running   0          38s
pod/ido-example-deployment-5f476b97d4-n9q9h   2/2     Running   0          38s
pod/ido-example-deployment-5f476b97d4-rxr6m   2/2     Running   0          38s
pod/ido-example-deployment-5f476b97d4-xk27g   2/2     Running   0          38s

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ido-example-deployment   5/5     5            5           18h
```

Wait a few minutes, and try to run the above command again. You should see that pods are being removed and that the deployment is being scaled back down. After 6-8 minutes the number of pods should be back down to 1 again:

```
# kubectl get pods,deployments
NAME                                          READY   STATUS    RESTARTS   AGE
pod/ido-example-deployment-5f476b97d4-xk27g   2/2     Running   0          8m43s

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ido-example-deployment   1/1     1            1           18h
```

You can check the logs for IDO to see that the deployment is being scaled down using `rmPod` utilizing `pod/rmpod-actuator` which is one of the IDO actuators running in the clusters:

```
# kubectl logs pod/planner -n ido | grep "Planner output for default/ido-example-intent was"
I0928 12:25:55.371232       1 intent_controller.go:165] Planner output for default/ido-example-intent was: []
I0928 12:26:40.372409       1 intent_controller.go:165] Planner output for default/ido-example-intent was: []
I0928 12:27:28.435086       1 intent_controller.go:165] Planner output for default/ido-example-intent was: [{rmPod map[name:ido-example-deployment-5f476b97d4-55gnn]}]
I0928 12:28:56.756055       1 intent_controller.go:165] Planner output for default/ido-example-intent was: [{rmPod map[name:ido-example-deployment-5f476b97d4-n9q9h]}]
I0928 12:30:25.926758       1 intent_controller.go:165] Planner output for default/ido-example-intent was: [{rmPod map[name:ido-example-deployment-5f476b97d4-rxr6m]}]
I0928 12:31:55.554513       1 intent_controller.go:165] Planner output for default/ido-example-intent was: [{rmPod map[name:ido-example-deployment-5f476b97d4-p9slf]}]
I0928 12:33:25.384619       1 intent_controller.go:165] Planner output for default/ido-example-intent was: []
I0928 12:34:10.368687       1 intent_controller.go:165] Planner output for default/ido-example-intent was: []
```
