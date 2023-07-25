
# Cloud RA

  

Cloud RA allows for deploying Intel Container Experience Kits on managed Kubernetes infrastructure hosted by Azure or AWS (Amazon).

  
  

## Prerequisites

  

- Python 3.8+

- Azure CLI 2.50.0+ ([Install Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt))

- AWS CLI 2.12.7+ ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))

- Terraform 1.5.2+

- Docker 20.10.17+

-  `pip install -r requirements.txt`

-  `az login`

-  `aws configure`

  

## Managed Kubernetes deployment

  

### Automatic

  

All of the below steps expect you to be in the `container-experience-kits/cloud` directory.

  

Create deployment directory with `cwdf.yaml`, `sw.yaml` hardware and software configuration files:

  

```commandline

mkdir deployment

vim deployment/cwdf.yaml

vim deployment/sw.yaml

```

  

**Examples of `cwdf.yaml` for Azure and AWS:**

  

Azure:

```yaml
cloudProvider: azure
azureConfig:
  location: "West Europe"
  vpc_cidr_block: "10.21.0.0/16"
  extra_tags:
    Owner: "some_user"
  subnets:
    - name: "subnet_a"
      cidr_block: "10.21.1.0/24"
    - name: "subnet_b"
      cidr_block: "10.21.2.0/24"
    - name: "subnet_c"
      cidr_block: "10.21.3.0/24"
  sg_whitelist_cidr_blocks: []
  enable_proximity_placement: true
  aks:
    kubernetes_version: "1.26"
    cni: "kubenet" # Possible values are: kubenet, cilium
    enable_sgx: false # Requires DCsv series instances in one of node pools
    default_node_pool:
      subnet_name: "subnet_a"
      vm_count: 1
      vm_size: "Standard_D2_v3"
    additional_node_pools:
      - name: "large"
        subnet_name: "subnet_b"
        vm_count: 1
        vm_size: "Standard_D4_v3"
        kubelet_cpu_manager_policy: "static"
      - name: "burstable"
        subnet_name: "subnet_c"
        vm_count: 1
        vm_size: "Standard_B2ms"
```

AWS:

```yaml
cloudProvider: aws
awsConfig:
  profile: default
  region: eu-central-1
  vpc_cidr_block: "10.21.0.0/16"
  extra_tags:
    Owner: "some_user"
  subnets:
    - name: "subnet_a"
      az: eu-central-1a
      cidr_block: "10.21.1.0/24"
    - name: "subnet_b"
      az: eu-central-1b
      cidr_block: "10.21.2.0/24"
  sg_whitelist_cidr_blocks: []
  ecr_repositories: []
  eks:
    kubernetes_version: "1.26"
    subnets: ["subnet_a", "subnet_b"]
    custom_ami: "ubuntu" # Comment out this line to use Amazon Linux 2 OS
    node_groups:
      - name: "default"
        instance_type: "t3.large"
        vm_count: 3
```

  

**Example of `sw.yaml` for both Azure and AWS:**

  

The `sw.yaml` configuration is similar for both Azure and AWS, with the main difference being the values in `cloud_settings`.

  

Example `sw.yaml` file:

```yaml

ansible_host_ip: xxx.xxx.xxx.xxx  # This value can be ignored for automatic deployment

cloud_settings:

provider: azure  # Use the value from `profile` in the cwdf.yaml file

region: "West Europe"  # Use the value from `region` in the cwdf.yaml file

controller_ips:

- 127.0.0.1

exec_containers: []

replicate_from_container_registry: https://registry.hub.docker.com

replicate_to_container_registry: xxxxx  # This value can be ignored for automatic deployment

ssh_key: ../deployment/ssh/id_rsa  # Leave this value as is for automatic deployment

worker_ips: # These values can be ignored for automatic deployment

- xxx.xxx.xxx.xxx

- xxx.xxx.xxx.xxx

- xxx.xxx.xxx.xxx

```

  

Deploy

  

Deployment can be done with two tools. The first is Terraform, which is the default tool. The second is CloudCLI. CloudCLI is supported for both platforms (AWS, Azure).
Choosing a tool is possible with an optional argument:`--provisioner_tool=[terraform/cloudcli]` If the tool is not specified, Terraform is automatically chosen.
 Then run `deployer.py deploy` and pass the deployment directory as an argument:

```commandline

python deployer.py deploy --deployment_dir=deployment
or
python deployer.py deploy --deployment_dir=deployment --provisioner_tool=terraform

```

  

Along with the managed Kubernetes cluster an additional Ansible instance and container registry will be created.

  

Ansible instance will be available with Azure or AWS CLI, Ansible and kubectl pre-installed.

Kubectl will be also pre-configured and authorized against the managed Kubernetes cluster.

Once the deployment script has finished, the IP address of the Ansible instance is available under `ansible_host_ip` in the `sw.yaml` file.

The default user of the Ansible instance is `ubuntu`, and the SSH key can be found in `deployment/ssh/id_rsa`.

To access the Ansible instance, use:

```commandline

ssh -i deployment/ssh/id_rsa ubuntu@<ansible_host_ip>

```

  

On the Ansible instance, the `cwdf_deployment` folder in home directory contains ssh keys for EKS worker nodes and connection info for worker nodes and ECR registry.

  

After the deployment, discovery will run on each EKS worker node. Output will be written to `discovery_results` directory on local machine where `deployer.py` is running and then copied to Ansible host's `cwdf_deployment` directory.

  

Cleanup created resources:

```commandline

python deployer.py cleanup --deployment_dir=deployment

```

  

### Manual

  

Start by creating a directory for the deployment and generate SSH key for instances:

```commandline

mkdir deployment

mkdir deployment/ssh

ssh-keygen -f deployment/ssh

```

  

1. Create a `cwdf` hardware definition yaml file e.g. `cwdf.yaml`:

```commandline

cp cwdf_example.yaml deployment/cwdf.yaml

```

  

2. Then generate Terraform manifest using `cwdf.py`:

```commandline

python cwdf.py generate-terraform \

--cwdf_config=deployment/cwdf.yaml \

--ssh_public_key=deployment/ssh/id_rsa.pub \

--job_id=manual \

--create_ansible_host=True \

--create_container_registry=True \

> deployment/main.tf

```

  

3. Initialize Terraform and deploy resources in the deployment directory:

```commandline

terraform init

terraform apply

```
