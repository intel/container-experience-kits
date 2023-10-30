# System Utilization monitoring
Telemetry stack in RA project is consist of following components:

 1. **Elasticsearch and Kibana:** Elasticsearch along with Kibana, offers real-time indexing, searching, and visualization of logs from whole stack.
 2. **Prometheus:** Prometheus is an open-source monitoring system collecting and storing time-series data. It enables efficient querying and alerting for system metrics and application performance.
 3. **Grafana:** Grafana is a verstatile open-source dashboard and visualization platform. It seamlessly integrates with Prometheus and other data sources (influxdb, etc.). It provides customizable dashboards and realtime alerting.
 4. **Telegraf:** Telegraf serves as the data collector in our stack, efficiently gathering metrics and telemetry data from various sources. Its extensibility and plugin support make data collection flexible and powerful.
 5. **OpenTelemetry:** OpenTelemetry is an observability framework that automatically instruments your applications to capture distributed traces and metrics. It enhances end-to-end visibility, aiding in understanding system performance.

## How to work with monitoring stack:
## Telemetry 
Various dashboards are available for monitoring telemetry in the NEP stack with the possibility of creating new dashboards or editing existing ones.
Dashboards can be viewed by accessing Grafana.  This can be done in several ways:

1. By directly accessing Grafana through an open port:

	    https://<controller_IP>:30000
2. By creating an SSH tunnel with port forwarding (sometimes direct port access can be blocked by network management):

	    ssh -L 30000:localhost:30000 <instance_username>@<controller_IP>
	And in the browser open address:
	
	    https://localhost:30000

	In the basic settings, the user "admin" and the password "admin" are set for grafana.  We strongly recommend changing your password to a secure option.

Most cluster parameters can be monitored through Grafana.  Grafana provides several dashboards with options to monitor CPU resource usage, memory, disk usage, network usage, etc.

## Logging and Tracing
Logs can be accessed in several ways.

 1. By using Kibana. 
Same as Grafana you can access Kibana by two different ways:
	 - By directly accessing Kibana through an open port:

			https://<controller_IP>:30001
	 - By creating an SSH tunnel with port forwarding:

			ssh -L 30001:localhost:30001 <instance_username>@<controller_IP>
		And in the browser open address:
	
			https://localhost:30001
	- Username and login can be optain by these commands:
		Username:
		
			kubectl get secret -n monitoring elasticsearch-master-credentials -ojsonpath='{.data.username}' | base64 -d
		Password:	

		    kubectl get secret -n monitoring elasticsearch-master-credentials -ojsonpath='{.data.password}' | base64 -d
    
2. By using K8s log tool:
	It is still possible to detect the problem through kubernetes tools.
	For example using logs tool:

	    kubectl logs -n <namespace_name> <pod_name>

## Kubernetes dashboard

To enable deployment of the Kubernetes dashboard, it is necessary to check whether the variable "kube_dashboard" is in the "on" state.
For accessing kubernetes-dashboard follow [kubespray documentation](https://github.com/kubernetes-sigs/kubespray/blob/master/docs/getting-started.md#accessing-kubernetes-dashboard).