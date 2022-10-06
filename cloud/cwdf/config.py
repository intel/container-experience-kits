from schema import Schema, Or, Optional


config_schema = Schema({
    "cloudProvider": Or("aws"),
    Optional("awsConfig"): {
        Optional("region", default='eu-central-1'): str,
        Optional("profile", default='default'): str,
        Optional("vpc_cidr_block", default='10.0.0.0/16'): str,
        Optional("sg_whitelist_cidr_blocks", default=['0.0.0.0/0']): [str],
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
            Optional("kubernetes_version", default='1.22'): str,
            "subnets": [str],
            "node_groups": [{
                "name": str,
                Optional("instance_type", default='t3.medium'): str,
                Optional("vm_count", default=1): int
            }]
        }
    },
})
