# Check cAdvisor

cAdvisor (<https://github.com/google/cadvisor>) is a running daemon that collects, aggregates, processes, and exports information about running containers. Specifically, for each container it keeps resource isolation parameters, historical resource usage, histograms of complete historical resource usage and network statistics. This data is exported by container and machine-wide.

cAdvisor is deployed when `cadvisor_enabled: true` in `group_vars/all.yml`.

Collected data are exposed via cAdvisor exposed REST API (<https://github.com/google/cadvisor/blob/master/docs/api.md>).
In RA Deployment, the cAdvisor's API is not exposed to external net. To access it, one can use port-forward method to expose it:

```bash
kubectl port-forward -n cadvisor pod/cadvisor-xxxx --address localhost 8080
```

__NOTE__: cAdvisor is deployed as daemonset so check should be done for pod on each node to ensure all pods are configured properly.

To verify, that cAdvisor collects data of containers. One could check the specific container's stats collected:

1. Request container stats via cAdvisor REST API:

    ```bash
    CONTAINER_NAME="<absolute name of container>"
    curl "http://localhost:8080/api/v1.3/containers/${CONTAINER_NAME}"
    ```

    alternatively (docker only):

    ```bash
    CONTAINER_ID="<id of container>"
    curl "http://localhost:8080/api/v2.0/stats/${CONTAINER_ID}?type=docker"
    ```

    alternatively, to check all containers:

    ```bash
    curl "http://localhost:8080/api/v2.0/stats/?recursive=true"
    ```

    The response should not be empty.

## Perf Events configuration

cAdvisor can be configured to measure perf events. RA deployment supports setting up the sample perf events configuration via parameter `cadvisor_sample_perf_events_enabled` set to `true`.

Sample perf events configuration is supplied as json file [here](/roles/cadvisor_install/files/sample-perf-event.json)

To verify perf events configuration is applied correctly:

1. Request base container stats via cAdvisor REST API and check `LLC-load-misses` is being measured:

    ```bash
    curl "http://localhost:8080/api/v1.3/containers/" | grep "LLC-load-misses" 
    ```

    Output of grep should not be empty.
