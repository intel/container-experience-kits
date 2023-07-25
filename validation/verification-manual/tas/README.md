# Check Telemetry Aware Scheduler
A Health Metric Demo Policy (https://github.com/intel/platform-aware-scheduling/blob/master/telemetry-aware-scheduling/docs/health-metric-example.md) is deployed for Telemetry Aware Scheduler (TAS) when `tas_enable_demo_policy: true`, in `group_vars/all.yml` as shown below:
```
# Intel Telemetry Aware Scheduling
tas_enabled: true
tas_namespace: monitoring
# create and enable TAS demonstration policy: [true, false]
tas_enable_demo_policy: true
```
The Health Metric Demo Policy requires a Prometheus metric file to exist on the node and be read by Prometheus. For security reasons, BMRA does not deploy it in the /tmp directory, where every user has access. Instead, it is deployed in the `/opt/cek/tas-demo-policy/` directory.

To verify that the policy has been deployed, use the command:
```
# kubectl get taspolicies -n kube-system 
NAME          AGE
demo-policy   4h
```
Details of this policy, including the rules and associated metrics, can be described with following command:
```
# kubectl describe taspolicies demo-policy -n kube-system
```
To verify that the proper files exist on the worker node, use the following command:
```
# cat /opt/cek/tas-demo-policy/test.prom
node_health_metric 0
```
The node health metric value indicates the following:
* When `node_health_metric = 0`, then it allows scheduling of pods on this node (scheduleonmetric).
* When `node_health_metric = 1`, then pods will not be scheduled on this node (dontschedule).
* When `node_health_metric = 2`, then the descheduler deschedules pods from this node (deschedule).

## Check Scheduleonmetric Policy
Start by checking the logs to verify that `node_health_metric = 0` on worker nodes:
```
# kubectl logs pod/tas-telemetry-aware-scheduling-xxxx-yyyy -n kube-system --tail=20
  "Evaluating demo-policy" component="controller"
  "controller1 health_metric = 0" component="controller"
  "worker1 health_metric = 0" component="controller"
```
If it is not 0, set the `node_health_metric` to 0 (scheduleonmetric) on all worker nodes as follows:
``` 
# echo 'node_health_metric 0' > /opt/cek/tas-demo-policy/test.prom
```
The provided deployment manifest [tas-test.yml](tas-test.yml) can be used to deploy a pod that is susceptible to the demo scheduling policy. The content of the file is:
```
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tas-test
  namespace: kube-system
  labels:
    app: demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
        telemetry-policy: demo-policy
    spec:
      containers:
      - name: pod-tas-test
        image: ubuntu:focal
        imagePullPolicy: IfNotPresent
        command: [ "/bin/bash", "-c" ]
        args: [ "sleep inf" ]
        resources:
          limits:
            telemetry/scheduling: 1
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: demo-policy
                    operator: NotIn
                    values:
                      - violating
```
Note that the pod is deployed in the "kube-system" namespace, similar to the `demo-policy` that is being used. This is necessary for all of the functionality to be working.

To run the deployment:
```
# kubectl apply -f tas-test.yml
```
The pod should deploy successfully and end up in state “Running” as shown below:
```
# kubectl get pods -n kube-system | grep tas-test
  NAME                        READY   STATUS    RESTARTS   AGE
  tas-test-xxxx-yyyy          1/1     Running   0          2m
```
Delete the pod before continuing with the next test:
```
# kubectl delete -f tas-test.yml
```

## Check Dontschedule Policy
Set the `node_health_metric` to 1 (dontschedule) on all worker nodes as follows:
``` 
# echo 'node_health_metric 1' > /opt/cek/tas-demo-policy/test.prom
```

After a few seconds, check the logs to verify that the status has changed:
```
# kubectl logs pod/tas-telemetry-aware-scheduling-xxxx-yyyy -n kube-system --tail=20
  "Evaluating demo-policy" component="controller"
  "controller1 health_metric = 0" component="controller"
  "worker1 health_metric = 1" component="controller"
```
Deploy the [tas-test.yml](tas-test.yml) pod again:
```
# kubectl apply -f tas-test.yml
```
The pod should fail to schedule and end up in state “Pending” as shown below:
```
# kubectl get pods -n kube-system | grep tas-test
  NAME                        READY   STATUS    RESTARTS   AGE
  tas-test-xxxx-yyyy          0/1     Pending   0          3m
```
As `node_health_metric` is set to 1 (dontschedule), this is expected.
Delete the pod before continuing with the next test:
```
# kubectl delete -f tas-test.yml
```

## Check Deschedule Policy
To see the impact of the descheduling policy, use a component called descheduler. For more details, visit (https://github.com/intel/platform-aware-scheduling/blob/master/telemetry-aware-scheduling/docs/health-metric-example.md#seeing-the-impact).
**Descheduler require minimum 2 worker nodes.**

Start by setting `node_health_metric` to 0 (scheduleonmetric) on all worker nodes as follows:
``` 
# echo 'node_health_metric 0' > /opt/cek/tas-demo-policy/test.prom
```
Check the logs to verify that `node_health_metric = 0` on worker nodes:
```
# kubectl logs pod/tas-telemetry-aware-scheduling-xxxx-yyyy -n kube-system --tail=20
  "Evaluating demo-policy" component="controller"
  "controller1 health_metric = 0" component="controller"
  "worker1 health_metric = 0" component="controller"
  "worker2 health_metric = 0" component="controller"
```
Deploy the [tas-test.yml](tas-test.yml) pod again:
```
# kubectl apply -f tas-test.yml
```
The pod should deploy successfully and end up in state “running” as shown below:
```
# kubectl get pods -n kube-system -o wide | grep tas-test
  NAME        READY   STATUS    RESTARTS        AGE    IP               NODE          NOMINATED NODE   READINESS GATES
  tas-test    1/1     Running   0               44s    10.244.194.101   worker1       <none>           <none>
```
Set the `node_health_metric` to 2 (deschedule) on worker node that is currently running tas-test as follows:
``` 
# echo 'node_health_metric 2' > /opt/cek/tas-demo-policy/test.prom
```
After a few seconds, check the logs to verify that the status has changed for worker1, worker2 status should remained the same:
```
# kubectl logs pod/tas-telemetry-aware-scheduling-xxxx-yyyy -n kube-system --tail=20
  "Evaluating demo-policy" component="controller"
  "controller1 health_metric = 0" component="controller"
  "worker1 health_metric = 2" component="controller"
  health_metric violated in node worker1
  "worker1 violating demo-policy: health_metric Equals 2" component="controller"
  "Node worker1 violating demo-policy, " component="controller"
  "worker2 health_metric = 0" component="controller"
```

Use the provided desceduler policy [descheduler-policy.yml](descheduler-policy.yml) as a configuration file for the descheduler. The content of the file is:
```
---
apiVersion: "descheduler/v1alpha1"
kind: "DeschedulerPolicy"
strategies:
  "RemovePodsViolatingNodeAffinity":
    enabled: true
    params:
      nodeAffinityType:
        - "requiredDuringSchedulingIgnoredDuringExecution"
```

Then run the descheduler from the same controller node with following command:
```
# /opt/cek/sigs.k8s.io/descheduler/_output/bin/descheduler --policy-config-file <path to descheduler-policy.yml> --kubeconfig /etc/kubernetes/admin.conf
```

Now check the status of the pod deployed previously:
```
# kubectl get pods -n kube-system -o wide | grep tas-test
  NAME        READY   STATUS        RESTARTS        AGE    IP               NODE          NOMINATED NODE   READINESS GATES
  tas-test    1/1     Terminating   0               44s    10.244.194.101   worker1       <none>           <none>
  tas-test    1/1     Running       0               44s    10.244.194.101   worker2       <none>           <none>
```
The pod will be rescheduled onto a healthier node based on its TAS policy. Depending on how fast you check you might see the previous pod in state "Terminating"
