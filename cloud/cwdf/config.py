from schema import Schema, Or, Optional


config_schema = Schema({
    "cloudProvider": Or("aws", "azure"),
    Optional("awsConfig"): {
        Optional("region", default='eu-central-1'): str,
        Optional("profile", default='default'): str,
        Optional("vpc_cidr_block", default='10.0.0.0/16'): str,
        Optional("sg_whitelist_cidr_blocks", default=['0.0.0.0/0']): [str],
        Optional("ansible_instance_type", default="t3.medium"): str,
        Optional("extra_tags", default={}): {str: str},
        "subnets": [{
            "name": str,
            "cidr_block": str,
            "az": str
        }],
        Optional("instance_profiles"): [{
            "name": str,
            Optional("instance_type", default='t3.medium'): str,
            "ami_id": str,
            "subnet": str,
            Optional("vm_count", default=1): int,
            Optional("root_volume_size", default=16): int,
            Optional("root_volume_type", default='gp2'): str
        }],
        Optional("eks"): {
            Optional("kubernetes_version", default='1.24'): Or("1.22", "1.23", "1.24"),
            "subnets": [str],
            Optional("install_ebs_csi_driver", default=True): bool,
            Optional("custom_ami", default=None): str,
            "node_groups": [{
                "name": str,
                Optional("instance_type", default='t3.medium'): str,
                Optional("vm_count", default=1): int
            }]
        },
        Optional("ecr_repositories", default=[]): [str]
    },
    Optional("azureConfig"): {
        Optional("location", default='West Europe'): str,
        Optional("vpc_cidr_block", default='10.0.0.0/16'): str,
        Optional("sg_whitelist_cidr_blocks", default=['0.0.0.0/0']): [str],
        Optional("extra_tags", default={}): {str: str},
        "subnets": [{
            "name": str,
            "cidr_block": str
        }],
        Optional("enable_proximity_placement", default=False): bool,
        Optional("ansible_instance_size", default="Standard_B2s"): str,
        Optional("aks"): {
            Optional("kubernetes_version", default='1.25'): Or("1.23", "1.24", "1.25"),
            Optional("cni", default="cilium"): Or("cilium", "cilium-ebpf", "kubenet"),
            Optional("enable_sgx", default=False): bool,
            "default_node_pool": {
                "subnet_name": str,
                Optional("vm_size", default='Standard_D2_v3'): str,
                Optional("vm_count", default=1): int,
                Optional("kubelet_cpu_manager_policy", default="none"): Or("none", "static")
            },
            Optional("additional_node_pools"): [{
                "name": str,
                "subnet_name": str,
                Optional("vm_size", default='Standard_D2_v3'): str,
                Optional("vm_count", default=1): int,
                Optional("kubelet_cpu_manager_policy", default="none"): Or("none", "static")
            }]
        }
    }
})
