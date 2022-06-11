# Check the Kubernetes Cluster
Once deployment is complete, check the status of nodes in the cluster:
```
# kubectl get nodes -o wide
NAME        STATUS    ROLES                 AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                               KERNEL-VERSION          CONTAINER-RUNTIME
node1       Ready     worker                60m   v1.22.3   10.166.30.34   <none>        Red Hat Enterprise Linux 8.5 (Ootpa)   4.18.0-348.el8.x86_64   docker://20.10.12
controller  Ready     control-plane,master  61m   v1.22.3   10.166.31.41   <none>        Red Hat Enterprise Linux 8.5 (Ootpa)   4.18.0-348.el8.x86_64   docker://20.10.12
```

Also check the status of pods running in the cluster. All should be in `Running` or `Completed` status:
```
# kubectl get pods --all-namespaces 
NAMESPACE                NAME                                                     READY   STATUS             RESTARTS       AGE
cert-manager             cert-manager-56b686b465-5qxxt                            1/1     Running            0              21m
cert-manager             cert-manager-cainjector-75c94654d-tztfg                  1/1     Running            0              21m
cert-manager             cert-manager-webhook-69bd5c9d75-m7rhf                    1/1     Running            0              21m
intel-power              controller-manager-f584c9458-52wdq                       1/1     Running            0              11m
intel-power              power-node-agent-2pm84                                   2/2     Running            0              11m
istio-system             istio-ingressgateway-88cc46fd6-n9pfn                     1/1     Running            0              5m31s
istio-system             istiod-576d9f454-w9nvt                                   1/1     Running            0              5m37s
kmra                     kmra-apphsm-85fb47f7f9-8rjb4                             2/2     Running            0              14m
kmra                     kmra-ctk-5558c9954b-zc6zv                                0/1     Running            7 (2m7s ago)   14m
kmra                     kmra-pccs-675f458576-597lq                               2/2     Running            0              14m
kube-system              bypass-tcpip-5v2vh                                       1/1     Running            0              5m45s
kube-system              bypass-tcpip-nrjxj                                       1/1     Running            0              5m45s
kube-system              calico-kube-controllers-684bcfdc59-8sczm                 1/1     Running            2 (22m ago)    23m
kube-system              calico-node-865wh                                        1/1     Running            2 (21m ago)    23m
kube-system              calico-node-gb5wz                                        1/1     Running            1 (22m ago)    23m
kube-system              container-registry-55d455b586-z5shr                      2/2     Running            0              19m
kube-system              coredns-8474476ff8-p67xp                                 1/1     Running            1 (22m ago)    22m
kube-system              coredns-8474476ff8-pkvxs                                 1/1     Running            1 (22m ago)    22m
kube-system              dns-autoscaler-5ffdc7f89d-g9225                          1/1     Running            1 (22m ago)    22m
kube-system              intel-qat-plugin-flncg                                   1/1     Running            0              10m
kube-system              intel-sgx-aesmd-shhfk                                    1/1     Running            0              14m
kube-system              intel-sgx-plugin-r2jg9                                   1/1     Running            0              14m
kube-system              inteldeviceplugins-controller-manager-6475d97999-d5r8b   2/2     Running            0              17m
kube-system              kube-apiserver-ar09-09-cyp                               1/1     Running            0              18m
kube-system              kube-controller-manager-ar09-09-cyp                      1/1     Running            2 (22m ago)    29m
kube-system              kube-multus-ds-amd64-kq44m                               1/1     Running            1 (21m ago)    23m
kube-system              kube-multus-ds-amd64-xllwr                               1/1     Running            1 (21m ago)    23m
kube-system              kube-proxy-64dqd                                         1/1     Running            1 (22m ago)    29m
kube-system              kube-proxy-pxdzs                                         1/1     Running            2 (21m ago)    29m
kube-system              kube-scheduler-ar09-09-cyp                               1/1     Running            0              6m23s
kube-system              kubernetes-dashboard-548847967d-slhpt                    1/1     Running            1 (22m ago)    22m
kube-system              kubernetes-metrics-scraper-6d49f96c97-fn2rc              1/1     Running            1 (22m ago)    22m
kube-system              nginx-proxy-ar09-01-cyp                                  1/1     Running            2 (21m ago)    29m
kube-system              node-feature-discovery-controller-5bb85dfdbb-pb8m4       1/1     Running            0              18m
kube-system              node-feature-discovery-worker-7g5l2                      1/1     Running            0              18m
kube-system              tas-telemetry-aware-scheduling-688d74f657-dpr6c          1/1     Running            0              6m29s
minio-operator           console-6c9557b87d-tkf4s                                 1/1     Running            0              5m9s
minio-operator           minio-operator-7885bb8d4-2flpf                           1/1     Running            0              5m9s
minio-operator           minio-operator-7885bb8d4-ddccf                           1/1     Running            0              5m9s
minio-operator           minio-operator-7885bb8d4-hwqxz                           1/1     Running            0              5m9s
minio-operator           minio-operator-7885bb8d4-zwv6b                           1/1     Running            0              5m9s
minio-tenant             minio-tenant-ss-0-0                                      1/1     Running            0              4m28s
monitoring               node-exporter-7bc74                                      2/2     Running            0              7m23s
monitoring               node-exporter-wbxn2                                      2/2     Running            0              7m23s
monitoring               prometheus-k8s-0                                         4/4     Running            0              7m21s
monitoring               prometheus-operator-bf54b8f56-hcc72                      2/2     Running            0              7m25s
monitoring               telegraf-67nbn                                           2/2     Running            0              5m49s
sriov-network-operator   sriov-device-plugin-z8bjj                                1/1     Running            0              12m
sriov-network-operator   sriov-network-config-daemon-rkmg2                        3/3     Running            0              17m
sriov-network-operator   sriov-network-operator-98db5fcbf-6nzcg                   1/1     Running            0              17m
sriov-network-operator   sriov-network-operator-bb8ff65d9-2td74                   1/1     Running            0              40h
```

