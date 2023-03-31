#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DATA_FILE="${SCRIPT_DIR}/aws_running_ids"


if test -f "$DATA_FILE";
then
# shellcheck source=/dev/null
    source "$DATA_FILE"
else
    echo "There is no aws_running_ids file."
    echo "Nothing to clean."
    echo "Exiting..."
    exit 0
fi

echo "Starting cleanup of AWS project..."

# Delete ECR
echo "--------------------------------------------------"
echo "Delete Amazon Elastic Container Registry"
aws ecr delete-repository \
    --repository-name "$ECR_REPOSITORY_NAME" \
    --output text

# Delete node groups
echo "--------------------------------------------------"
echo "Delete Node Groups"
for node_group in $(aws eks list-nodegroups --cluster-name "$EKS_CLUSTER_NAME" | jq .nodegroups[] | tr -d '"')
do
    aws eks delete-nodegroup \
        --cluster-name "$EKS_CLUSTER_NAME" \
        --nodegroup-name "$node_group" \
        --output text
    aws eks wait nodegroup-deleted \
        --cluster-name "$EKS_CLUSTER_NAME" \
        --nodegroup-name "$node_group"
done

# Delete launch template
echo "--------------------------------------------------"
echo "Delete Launch Template"
aws ec2 delete-launch-template \
    --launch-template-name "$EKS_LAUNCH_TEMPLATE_NAME" \
    --output text

# Delete EKS cluster
echo "--------------------------------------------------"
echo "Delete Amazon Elastic Kubernetes Service cluster"
aws eks delete-cluster \
    --name "$EKS_CLUSTER_NAME" \
    --output text
aws eks wait cluster-deleted \
    --name "$EKS_CLUSTER_NAME"

# Detach role policies
echo "--------------------------------------------------"
echo "Detach Role Policies"
aws iam detach-role-policy --role-name "$IAM_CLUSTER_ROLE_NAME" --policy-arn "$IAM_EKS_POLICY_ARN"
aws iam detach-role-policy --role-name "$IAM_NODEGROUP_ROLE_NAME" --policy-arn "$IAM_EKS_POLICY_ARN"
aws iam detach-role-policy --role-name "$IAM_NODEGROUP_ROLE_NAME" --policy-arn "$IAM_EKS_WORKERNODE_POLICY_ARD"
aws iam detach-role-policy --role-name "$IAM_NODEGROUP_ROLE_NAME" --policy-arn "$IAM_EKS_CONTAINER_REGISTRY_READONLY_POLICY_ARD"
aws iam detach-role-policy --role-name "$IAM_NODEGROUP_ROLE_NAME" --policy-arn "$IAM_EKS_CNI_POLICY"

# Delete roles
echo "--------------------------------------------------"
echo "Delete Roles"
aws iam delete-role --role-name "$IAM_NODEGROUP_ROLE_NAME"
aws iam delete-role --role-name "$IAM_CLUSTER_ROLE_NAME"

# Delete Ansible instance
echo "--------------------------------------------------"
echo "Delete Ansible instance"
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --output text
aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID"
    
# Detach internet gateways
echo "--------------------------------------------------"
echo "Detach Internet gateway"
aws ec2 detach-internet-gateway --internet-gateway-id "$VPC_IGW" --vpc-id "$VPC_ID"

# Delete internet gateway
echo "--------------------------------------------------"
echo "Delete Internet gateway"
aws ec2 delete-internet-gateway --internet-gateway-id "$VPC_IGW"

# Delete security group
echo "--------------------------------------------------"
echo "Delete Security group"
aws ec2 delete-security-group --group-id "$SECURITY_GROUP_ID"

# Delete subnets
echo "--------------------------------------------------"
echo "Delete subnets"
for subnet in $(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" | jq ".Subnets[].SubnetId" | tr -d '"'); 
do
    aws ec2 delete-subnet --subnet-id "$subnet"
done

# Delete route table
echo "--------------------------------------------------"
echo "Delete Internet gateway"
aws ec2 delete-route-table --route-table-id "$ROUTE_TABLE_ID"

# Delete VPC
echo "--------------------------------------------------"
echo "Delete VPC"
aws ec2 delete-vpc --vpc-id "$VPC_ID"

# Delete SSH key
echo "--------------------------------------------------"
echo "Delete SSH Key Pair"
aws ec2 delete-key-pair --key-name "$KEYPAIR_NAME"

rm "$DATA_FILE"

echo "--------------------------------------------------"
echo "Cleanup is done."
