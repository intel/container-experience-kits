# Deployment of Ingress-nginx as Cluster Ingress Controller

This section describes how to leverage Ingress resources in Cluster

## Ingress Controller description

Ingress Controller is application within a Kubernetes cluster that enable Ingress resources to function. It's not automatically deployed with a Kubernetes cluster, and each variant can vary in implementation based on intended use, such as load balancing algorithms for Ingress resources.

## Ingress resource description

Ingress refers to an Ingress Resource, a Kubernetes API object which allows access to Services within a cluster. They are managed by an Ingress Controller.

Ingress resources enable the following functionality:

- Load balancing, extended through the use of Services
- Content-based routing, using hosts and paths
- TLS/SSL termination, based on hostnames

For additional information, please read the official Kubernetes Ingress Documentation.

## Ingress-Nginx as controller in RA deployment

The deployment of ingress-nginx on reference architecture cluster has following specifics:

- There's no support for LoadBalancer type of services
- External connection point for ingress resources is provided by NodePorts 30123 & 30124 reachable via localhost of each node in cluster

## Validation of Ingress resource

Sample resource files can be found at [sample_deployment.yaml](sample_deployment.yaml) and [sample_ingress.yaml](sample_ingress.yaml)

1. Deploy sample workload with ingress resource:

    ```bash
    $ kubectl apply -f sample_deployment.yaml
    deployment.apps/http-svc created
    service/http-svc created

    $ kubectl apply -f sample_ingress.yaml
    ingress.networking.k8s.io/example-ingress created
    ```

2. Check deployment, service and ingress resources status:

    ```bash
    $ kubectl get pods 
    NAME                       READY   STATUS    RESTARTS   AGE
    http-svc-68dd884bb-wds72   1/1     Running   0          20s

    $ kubectl get svc http-svc
    NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
    http-svc   ClusterIP   10.233.6.129   <none>        80/TCP    27m

    $ kubectl get ingress
    NAME              CLASS   HOSTS   ADDRESS   PORTS   AGE
    example-ingress   nginx   *                 80      25s
    ```

3. Reach new exposed port from ingress from node:

    ```bash
    $ curl http://127.0.0.1:30123/echo-server/


    Hostname: http-svc-68dd884bb-wds72

    Pod Information:
            node name:      am09-05-cyp
            pod name:       http-svc-68dd884bb-wds72
            pod namespace:  default
            pod IP: 10.244.39.42

    Server values:
            server_version=nginx: 1.14.2 - lua: 10015

    Request Information:
            client_address=10.244.39.50
            method=GET
            real path=/
            query=
            request_version=1.1
            request_scheme=http
            request_uri=http://127.0.0.1:8080/

    Request Headers:
            accept=*/*
            host=127.0.0.1:30123
            user-agent=curl/7.81.0
            x-forwarded-for=10.166.31.87
            x-forwarded-host=127.0.0.1:30123
            x-forwarded-port=80
            x-forwarded-proto=http
            x-forwarded-scheme=http
            x-real-ip=10.166.31.87
            x-request-id=32daf99bb22f84ae5da6c7d4d233d31c
            x-scheme=http

    Request Body:
            -no body in request-
    ```
