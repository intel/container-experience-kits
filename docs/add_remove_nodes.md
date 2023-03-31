# Adding and removing worker nodes

Note: adding new nodes currently will disturb current nodes in the cluster as
ansible-playbook limit option is not supported yet.

## Add new node(s)

Modify the inventory with the added new node(s), then run:

`ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml -e scale=true`

Alternatively, scale variable may accept any of the following values `{ yes, on, 1, true }`, case insensitive

## Remove node(s)

With the node(s) being removed still in the inventory, run:

`ansible-playbook -i inventory.ini playbooks/remove_node.yml -e node=NODE_NAME`

You may pass `-e node=NODE_NAME` or `-e node=NODE_NAME1,NODE_NAME2,...,NODE_NAMEn` or `-e node=NODES_GROUP_NAME` to the playbook to limit the execution to the node(s) being removed.
