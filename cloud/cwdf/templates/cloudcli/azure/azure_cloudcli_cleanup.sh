#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DATA_FILE="${SCRIPT_DIR}/azure_running_ids"


if test -f "$DATA_FILE";
then
# shellcheck source=/dev/null
    source "$DATA_FILE"
else
    echo "There is no azure_running_ids file."
    echo "Nothing to clean."
    echo "Exiting..."
    exit 0
fi

echo "Starting cleanup of CloudCLI CWDF (Azure) project..."

# Delete Ansible instance VM
echo "--------------------------------------------------"
echo "Delete Ansible instance VM"
az vm delete -y --name "$ANSIBLE_INSTANCE_NAME" --resource-group "$AZ_GROUP_NAME"

# Delete Ansible instance NIC
echo "--------------------------------------------------"
echo "Delete Ansible instance NIC"
az network nic delete --name "$NIC_NAME" --resource-group "$AZ_GROUP_NAME"

# Delete public IP
echo "--------------------------------------------------"
echo "Delete Ansible instance Public IP"
az network public-ip delete --name "$PUBLIC_IP_NAME" --resource-group "$AZ_GROUP_NAME"

# Delete Azure Container Registry
echo "--------------------------------------------------"
echo "Deleting Azure Container Registry"
az acr delete --name "$ACR_NAME" --resource-group "$AZ_GROUP_NAME" -y

# Delete AKS (Azure Kubernetes Service)
echo "--------------------------------------------------"
echo "Deleting Azure Kubernetes Service"
az aks delete --name "$AKS_NAME" --resource-group "$AZ_GROUP_NAME" -y

# Delete log-analytics workspace
echo "--------------------------------------------------"
echo "Deleting log-analytics workspace"
az monitor log-analytics workspace delete --ids "$AZ_MONITOR_ID" -y

# Delete network rule SSH
echo "--------------------------------------------------"
echo "Deleting network rule SSH"
az network nsg rule delete --ids "$RULE_SSH_ID"

# Delete network rule ICMP
echo "--------------------------------------------------"
echo "Deleting network rule ICMP"
az network nsg rule delete --ids "$RULE_ICMP_ID"

# Delete network security group
echo "--------------------------------------------------"
echo "Deleting network security group"
az network nsg delete --ids "$NSG_ID"

# Delete virtual network
echo "--------------------------------------------------"
echo "Deleting virtual network"
az network vnet delete --ids "$VNET_ID"

# Delete Azure group
echo "--------------------------------------------------"
echo "Deleting resource group"
az group delete -y --name "$AZ_GROUP_NAME"

rm "$DATA_FILE"

echo "--------------------------------------------------"
echo "Cleanup is done."
