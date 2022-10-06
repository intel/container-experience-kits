# Check the Kubernetes Cluster
Once deployment is complete, check the status of nodes in the cluster:
```
# kubectl get nodes -o wide
NAME         STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE           KERNEL-VERSION      CONTAINER-RUNTIME
node1        Ready    worker          12h   v1.24.3   10.166.30.64   <none>        Ubuntu 22.04 LTS   5.15.0-25-generic   docker://20.10.17
controller   Ready    control-plane   12h   v1.24.3   10.166.31.58   <none>        Ubuntu 22.04 LTS   5.15.0-25-generic   docker://20.10.17
```

Also check the status of pods running in the cluster. All should be in `Running` or `Completed` status:
```
# kubectl get pods --all-namespaces 
NAMESPACE                       NAME                                                              READY   STATUS      RESTARTS      AGE
cert-manager                    cert-manager-758558b8bd-pcfqz                                     1/1     Running     0             12h
cert-manager                    cert-manager-cainjector-6d4984d5f5-jtlsx                          1/1     Running     0             12h
cert-manager                    cert-manager-webhook-bf48fb88d-fpdb8                              1/1     Running     0             12h
intel-ethernet-operator         3e60ab2bf2a0e94cd94228eb615d3744dc6f4cbd5ec772ef7fcd0d740a428jf   0/1     Completed   0             11h
intel-ethernet-operator         clv-discovery-74pk4                                               1/1     Running     1 (11h ago)   11h
intel-ethernet-operator         fwddp-daemon-c5b4h                                                1/1     Running     1 (11h ago)   11h
intel-ethernet-operator         intel-ethernet-operator-controller-manager-69655db6cf-cgpfb       1/1     Running     1 (11h ago)   11h
intel-ethernet-operator         intel-ethernet-operator-controller-manager-69655db6cf-nlr9h       1/1     Running     1 (11h ago)   11h
intel-ethernet-operator         intel-ethernet-operators-c5brp                                    1/1     Running     1 (11h ago)   11h
intel-power                     controller-manager-5fc8f8f874-r6hs2                               1/1     Running     1 (11h ago)   11h
intel-power                     power-node-agent-qhh2x                                            2/2     Running     1 (11h ago)   11h
istio-system                    istio-ingressgateway-545d46d996-g4tns                             1/1     Running     1 (11h ago)   11h
istio-system                    istioctl-5bb557cb8b-zb75b                                         1/1     Running     1 (11h ago)   11h
istio-system                    istiod-59876b79cd-tqxq9                                           1/1     Running     1 (11h ago)   11h
kube-system                     bypass-tcpip-nrj8h                                                1/1     Running     0             11h
kube-system                     calico-node-dwn89                                                 1/1     Running     0             12h
kube-system                     container-registry-7b8b8b4446-rpfjg                               2/2     Running     0             12h
kube-system                     coredns-74d6c5659f-hrcss                                          1/1     Running     0             12h
kube-system                     dns-autoscaler-6656dfd4c6-skrbq                                   1/1     Running     0             12h
kube-system                     intel-qat-plugin-dv6w7                                            1/1     Running     0             11h
kube-system                     inteldeviceplugins-controller-manager-59b46b7949-swgtj            2/2     Running     1 (11h ago)   11h
kube-system                     kube-afxdp-device-plugin-e2e-5fpxc                                1/1     Running     0             11h
kube-system                     kube-apiserver-as09-16-wpr                                        1/1     Running     1 (11h ago)   12h
kube-system                     kube-controller-manager-as09-16-wpr                               1/1     Running     0             12h
kube-system                     kube-multus-ds-amd64-h5ft4                                        1/1     Running     1 (11h ago)   12h
kube-system                     kube-proxy-pgvsk                                                  1/1     Running     1 (11h ago)   12h
kube-system                     kube-scheduler-as09-16-wpr                                        1/1     Running     0             11h
kube-system                     kubernetes-dashboard-648989c4b4-xcdvt                             1/1     Running     1 (11h ago)   12h
kube-system                     kubernetes-metrics-scraper-84bbbc8b75-jpkdx                       1/1     Running     0             12h
kube-system                     node-feature-discovery-master-65ddb4669-dz6g7                     1/1     Running     0             12h
kube-system                     node-feature-discovery-worker-qblwf                               1/1     Running     0             12h
kube-system                     tas-telemetry-aware-scheduling-6f965ff445-fg7j7                   1/1     Running     1 (11h ago)   11h
modsec-tadk                     tadk-intel-tadkchart-7869548b67-r52z9                             1/1     Running     0             11h
monitoring                      kube-state-metrics-5d7b5d5bfc-rsvlk                               3/3     Running     1 (11h ago)   11h
monitoring                      node-exporter-zcw7q                                               2/2     Running     1 (11h ago)   11h
monitoring                      otel-telegraf-collector-579846745d-t2j64                          1/1     Running     1 (11h ago)   11h
monitoring                      prometheus-k8s-0                                                  4/4     Running     1 (11h ago)   11h
monitoring                      prometheus-operator-68d5d49646-xql4v                              2/2     Running     1 (11h ago)   11h
monitoring                      telegraf-w9z67                                                    2/2     Running     1 (11h ago)   11h
observability                   jaeger-7f8f665d7f-jnzh4                                           1/1     Running     0             11h
observability                   jaeger-agent-daemonset-xkvv2                                      1/1     Running     0             11h
observability                   jaeger-operator-5f45884b86-cl9ls                                  2/2     Running     1 (11h ago)   11h
olm                             catalog-operator-6587ff6f69-6p988                                 1/1     Running     1 (11h ago)   12h
olm                             olm-operator-6ccdf8f464-w5pv5                                     1/1     Running     1 (11h ago)   12h
olm                             operatorhubio-catalog-7g9db                                       1/1     Running     0             17h
olm                             packageserver-799bf4b7bf-b9l69                                    1/1     Running     1 (11h ago)   12h
olm                             packageserver-799bf4b7bf-n4t7q                                    1/1     Running     1 (11h ago)   12h
opentelemetry-operator-system   opentelemetry-operator-controller-manager-5656d6df74-7p8dl        2/2     Running     1 (11h ago)   11h
sriov-network-operator          sriov-device-plugin-bgtd7                                         1/1     Running     0             11h
sriov-network-operator          sriov-network-config-daemon-wqlcg                                 3/3     Running     1 (11h ago)   11h
sriov-network-operator          sriov-network-operator-69bbd699f8-xvqz6                           1/1     Running     1 (11h ago)   11h
```

