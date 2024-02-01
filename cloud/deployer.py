import json
import os
import random
import shutil
import string
import subprocess  # nosec B404 # subprocess is set to shell=False

import click
import paramiko
import yaml

from azure.identity import AzureCliCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

import cwdf_util
import sw_deployment.sw_deployment_tool as sw_deployment

from ssh_connector import SSHConnector, SSHHostKey


def subprocess_run(*args, **kwargs):
    return subprocess.run(*args, **kwargs)  # pylint: disable=W1510


def generate_ssh_keys(ssh_dir, public_key_path, private_key_path):
    key_length = 2048
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        keypair = paramiko.RSAKey.generate(key_length)
        keypair.write_private_key_file(private_key_path)
        with open(public_key_path, 'w') as f:
            f.write(f'ssh-rsa {keypair.get_base64()}')
        os.chmod(private_key_path, 0o600)


def authenticate_aks(deployment_dir):
    proc = subprocess_run(["terraform", "output", "-json"], cwd=deployment_dir, capture_output=True)
    terraform_output = json.loads(proc.stdout)
    resource_group_name = terraform_output.get("resource_group_name", {}).get("value")
    aks_cluster_name = terraform_output.get("aks_cluster_name", {}).get("value")
    if not resource_group_name or not aks_cluster_name:
        return
    click.echo("Running az aks get-credentials...")
    proc = subprocess_run(["az", "aks", "get-credentials", f"-n={aks_cluster_name}", f"-g={resource_group_name}"], universal_newlines=True)
    if proc.returncode != 0:
        click.secho("Unable to setup kubectl. Ignoring...", err=True, bold=True, fg="red")


@click.group()
def cli():
    pass


@click.command()
@click.option('--deployment_dir', help='Path to deployment directory', required=True)
@click.option('--provisioner_tool', help='Select the tool that will be used for provisioning.', default='terraform')
def deploy(deployment_dir, provisioner_tool):
    config_path = os.path.join(deployment_dir, "cwdf.yaml")
    sw_config_path = os.path.join(deployment_dir, "sw.yaml")

    # Verify config file exists
    if not os.path.exists(config_path):
        click.echo("Config file does not exist.", err=True)
        return None
    if not os.path.exists(sw_config_path):
        click.echo("Software config file does not exist.", err=True)
        return None

    click.echo("Beginning deployment...")

    with open(config_path, 'r') as f:
        cwdf_user_config = f.read()

    # Generate SSH keys for instances
    ssh_dir = os.path.join(os.path.abspath(deployment_dir), "ssh")
    public_key_path = os.path.join(ssh_dir, "id_rsa.pub")
    private_key_path = os.path.join(ssh_dir, "id_rsa")
    generate_ssh_keys(ssh_dir, public_key_path, private_key_path)
    with open(public_key_path, 'r') as f:
        ssh_public_key = f.read()
    with open(private_key_path, 'r') as f:
        f.read()

    # Create lock file if not exists
    # Lock file is intended to contain info not to break previous deployment in future
    # For now only job id is stored there to preserve previous deployment
    lock_path = os.path.join(deployment_dir, "tbd.lock")
    with open(lock_path, 'a+') as f:
        f.seek(0)
        lock_str = f.read()
        try:
            lock = json.loads(lock_str)
        except ValueError:
            lock = None

        if lock is not None and "job_id" in lock:
            job_id = lock["job_id"]
        else:
            # Random 8 digit identifier
            job_id = ''.join(random.choices(string.digits, k=8))  # nosec B311 # pseudo-random generator is not used for security purposes
            lock = json.dumps({"job_id": job_id})
            f.write(lock)

    click.echo("Job ID: " + job_id)

    provisioning_output = None
    if provisioner_tool == "terraform":
        provisioning_output = terrafrom_provisioning(deployment_dir, cwdf_user_config, job_id, ssh_public_key)
    elif provisioner_tool == "cloudcli":
        provisioning_output = cloudcli_provisioning(deployment_dir, cwdf_user_config, job_id, public_key_path)
    else:
        return

    ansible_host_ip = provisioning_output["ansible_host_public_ip"]["value"]
    click.echo("Ansible Host is accessible on: " + ansible_host_ip)
    click.echo("-------------------")
    cr_url = provisioning_output["cr_url"]["value"]
    click.echo("Container Registry URL:")
    click.echo(cr_url)
    click.echo("-------------------")

    workers = []
    cloud_provider = provisioning_output["cloud_provider"]["value"]
    if cloud_provider == "azure":
        subscription_id = provisioning_output["subscription_id"]["value"]
        aks_scale_sets_rg = provisioning_output["aks_scale_sets_rg"]["value"]

        credential = AzureCliCredential()
        network_client = NetworkManagementClient(credential, subscription_id)
        compute_client = ComputeManagementClient(credential, subscription_id)
        scale_sets = compute_client.virtual_machine_scale_sets.list(aks_scale_sets_rg)
        scale_set_names = list(map(lambda ss: ss.name, scale_sets))

        for scale_set_name in scale_set_names:
            nics = network_client.network_interfaces.list_virtual_machine_scale_set_network_interfaces(
                aks_scale_sets_rg,
                scale_set_name
            )
            for nic in nics:
                workers.append({
                    "id": nic.id,
                    "private_ip": nic.ip_configurations[0].private_ip_address,
                    "public_ip": ""
                })
    elif cloud_provider == "aws":
        workers = provisioning_output["k8s_worker_instances"]["value"]

    click.echo("Worker nodes:")
    click.echo("-------------------")
    workers_ip = []
    for worker in workers:
        workers_ip.append(worker["private_ip"])
        click.echo("Worker " + worker["id"])
        click.echo("Private ip: " + worker["private_ip"])
        click.echo("Public ip: " + worker["public_ip"])
        click.echo("-------------------")
    ssh_username = provisioning_output["k8s_worker_username"]["value"]
    rsa_ssh_host_key_raw = provisioning_output["ansible_host_ssh_host_key_rsa"]["value"].split(' ')[1]
    ecdsa_ssh_host_key_raw = provisioning_output["ansible_host_ssh_host_key_ecdsa"]["value"].split(' ')[1]
    ecdsa_ssh_host_key_type = provisioning_output["ansible_host_ssh_host_key_ecdsa"]["value"].split(' ')[0]
    ed25519_ssh_host_key_raw = provisioning_output["ansible_host_ssh_host_key_ed25519"]["value"].split(' ')[1]
    rsa_ssh_host_key = SSHHostKey("ssh-rsa", rsa_ssh_host_key_raw)
    ecdsa_ssh_host_key = SSHHostKey(ecdsa_ssh_host_key_type, ecdsa_ssh_host_key_raw)
    ed25519_ssh_host_key = SSHHostKey("ssh-ed25519", ed25519_ssh_host_key_raw)
    click.echo("Opening SSH connection to Ansible host...")
    ssh = SSHConnector(ip_address=ansible_host_ip,
                       username='ubuntu',
                       host_keys=[rsa_ssh_host_key, ecdsa_ssh_host_key, ed25519_ssh_host_key],
                       priv_key=private_key_path,
                       try_loop=True)
    click.echo("Opened SSH connection.")
    click.echo("Waiting for cloud init to complete on Ansible host...")
    _, stdout, stderr = ssh.exec_command("cloud-init status --wait")
    stdout.channel.recv_exit_status()
    click.echo("Cloud init done.")

    # Make deployment output yaml file
    cwdf_output = {
        "cr_url": cr_url,
        "k8s_worker_instances": workers
    }
    cwdf_output_filename = os.path.join(deployment_dir, "cwdf_output.yaml")
    with open(cwdf_output_filename, 'w') as f:
        yaml.dump(cwdf_output, f)

    ssh.copy_file(cwdf_output_filename, destination_path="/home/ubuntu/cwdf_deployment/")
    click.echo("Transferring SSH keys to Ansible machine...")
    ssh.copy_file(private_key_path, destination_path='/tmp/id_rsa')
    ssh.exec_command("sudo mv /tmp/id_rsa /home/ubuntu/cwdf_deployment/ssh/id_rsa")
    ssh.exec_command("sudo chmod 600 /home/ubuntu/cwdf_deployment/ssh/id_rsa")
    click.echo("Successfully transferred SSH key to ~/cwdf_deployment/ssh/id_rsa")
    click.echo("Transferring discovery to Ansible instance...")
    ssh.copy_file("discovery", destination_path="/home/ubuntu/cwdf_deployment/", recursive=True)
    ssh.copy_file("ssh_connector.py", destination_path="/home/ubuntu/cwdf_deployment/discovery")
    click.echo("Successfully transferred discovery to ~/cwdf_deployment/discovery")
    click.echo("Running discovery on EKS workers...")
    discovery_results_path = os.path.join(deployment_dir, "discovery_results")
    if not os.path.exists(discovery_results_path):
        os.makedirs(discovery_results_path)
    for worker in workers:
        _, stdout, stderr = ssh.exec_command(
            f"python3 /home/ubuntu/cwdf_deployment/discovery/discover.py {worker['private_ip']} ec2-user /home/ubuntu/cwdf_deployment/ssh/id_rsa"
        )
        if stdout.channel.recv_exit_status() != 0:
            click.echo(f"Error while running discovery on {worker['private_ip']}:", err=True)
            click.echo(stderr.read(), err=True)
        else:
            filename = os.path.join(discovery_results_path, worker['private_ip'].replace(".", "-") + ".json")
            with open(filename, 'w') as f:
                f.write(stdout.read().decode("utf-8"))
    click.echo("Wrote to discovery_results directory.")
    click.echo("Copying to Ansible instance...")
    ssh.copy_file(discovery_results_path, destination_path="/home/ubuntu/cwdf_deployment/", recursive=True)
    click.echo("Copied discovery results to Ansible host.")

    configuration = yaml.safe_load(cwdf_user_config)
    ssh.close_connection()

    click.echo("-------------------")
    click.echo('Running SW deployment')

    with open(file=sw_config_path, mode='r', encoding='utf-8') as file:
        sw_configuration = yaml.load(file, Loader=yaml.FullLoader)
    sw_configuration['ansible_host_ip'] = ansible_host_ip
    sw_configuration['ansible_ssh_rsa_host_key'] = rsa_ssh_host_key_raw
    sw_configuration['ansible_ssh_ecdsa_host_key'] = ecdsa_ssh_host_key_raw
    sw_configuration['ansible_ssh_ed25519_host_key'] = ed25519_ssh_host_key_raw
    sw_configuration['worker_ips'] = workers_ip
    sw_configuration['ssh_user'] = ssh_username
    sw_configuration['ssh_key'] = os.path.join('..', private_key_path)
    sw_configuration['replicate_to_container_registry'] = cr_url

    if cloud_provider == "aws":
        if "eks" in configuration['awsConfig']:
            sw_configuration['custom_ami'] = configuration['awsConfig']['eks']['custom_ami']

    with open(file=sw_config_path, mode="w", encoding='utf-8') as file:
        yaml.dump(sw_configuration, file)

    sw_deployment.start_deploy(config=sw_config_path)


def terrafrom_provisioning(deployment_dir, cwdf_user_config, job_id, ssh_public_key):
    tf_manifest, _ = cwdf_util.compose_terraform(cwdf_user_config, job_id, ssh_public_key)
    manifest_path = os.path.join(deployment_dir, 'deploy.tf')
    with open(manifest_path, 'w') as f:
        f.write(tf_manifest)

    click.echo("Initializing Terraform...")
    proc = subprocess_run(["terraform", "init", "-upgrade"], cwd=deployment_dir, universal_newlines=True)
    if proc.returncode != 0:
        click.secho("Error while initializing Terraform", err=True, bold=True, fg="red")
        return

    # Setup ~/.kube/config if in AKS environment to prevent helm provider errors
    authenticate_aks(deployment_dir)

    click.echo("Building Terraform plan...")
    proc = subprocess_run(
        ["terraform", "plan", "-out=outfile", "-detailed-exitcode"],
        cwd=deployment_dir, universal_newlines=True
    )
    if proc.returncode == 1:
        click.echo("Error while planning deployment", err=True)
        return
    elif proc.returncode == 0:
        click.echo("No infrastructure changes needed.")
    elif proc.returncode == 2:
        if click.confirm("Continue with above modifications?"):
            proc = subprocess_run(["terraform", "apply", "outfile"], cwd=deployment_dir, universal_newlines=True)
            if proc.returncode == 1:
                click.echo("Error while running deployment", err=True)
                return
            else:
                click.echo("Deployment finished.")
        else:
            return
    else:
        return

    proc = subprocess_run(["terraform", "output", "-json"], cwd=deployment_dir, capture_output=True)
    json_output = proc.stdout
    provisioning_output = json.loads(json_output)
    return provisioning_output


def cloudcli_provisioning(deployment_dir, cwdf_user_config, job_id, public_key_path):
    script_path = cwdf_util.compose_cloudcli(deployment_dir, cwdf_user_config, job_id, public_key_path)

    click.echo("Running CloudCLI provisioning script...")
    proc = subprocess_run([script_path], universal_newlines=True)
    if proc.returncode != 0:
        click.secho("Error while initializing deploy script", err=True, bold=True, fg="red")
        return

    output_file = os.path.join(deployment_dir, "provision_output.json")
    with open(file=output_file, mode='r', encoding='utf-8') as json_file:
        cloudcli_output = json.load(json_file)

    return cloudcli_output


def remove_all_k8s_services(ansible_host_ip, private_key_path):
    ssh = SSHConnector(ip_address=ansible_host_ip,
                       username='ubuntu',
                       priv_key=private_key_path,
                       try_loop=True)
    click.echo("Removing all k8s services...")
    cmd = 'for each in $(kubectl get ns -o jsonpath="{.items[*].metadata.name}" | sed s/"kube-system"//); do kubectl delete service --all -n $each; done'
    stdout = ssh.exec_command(cmd)[1]
    stdout.channel.recv_exit_status()
    ssh.close_connection()


def temp_files_remove(deployment_dir, provisioner_tool, cloud_provider):
    click.echo("Removing temporary files...")

    discovery_results_path = os.path.join(deployment_dir, "discovery_results")
    ssh_dir = os.path.join(deployment_dir, "ssh")
    directories = [discovery_results_path, ssh_dir]

    cwdf_output_filename = os.path.join(deployment_dir, "cwdf_output.yaml")
    lock_path = os.path.join(deployment_dir, "tbd.lock")
    files = []
    if provisioner_tool == "terraform":
        manifest_path = os.path.join(deployment_dir, 'deploy.tf')
        outfile_path = os.path.join(deployment_dir, 'outfile')
        destroyplan = os.path.join(deployment_dir, 'destroyplan')
        terraform_tfstate = os.path.join(deployment_dir, 'terraform.tfstate')
        terraform_tf_backup = os.path.join(deployment_dir, 'terraform.tfstate.backup')
        files = [cwdf_output_filename, lock_path, manifest_path, outfile_path, destroyplan, terraform_tfstate, terraform_tf_backup]
    if provisioner_tool == "cloudcli":
        cleaning_script = os.path.join(deployment_dir, f"{cloud_provider}_cloudcli_cleanup.sh")
        provisioning_script = os.path.join(deployment_dir, f"{cloud_provider}_cloudcli_provisioning.sh")
        provision_output = os.path.join(deployment_dir, "provision_output.json")
        files = [cwdf_output_filename, lock_path, cleaning_script, provisioning_script, provision_output]

    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    if len(files) != 0:
        for file in files:
            if os.path.exists(file):
                os.remove(file)


def terraform_cleanup(deployment_dir, skip_service_cleanup):
    if not skip_service_cleanup:
        proc = subprocess_run(["terraform", "output", "-json"], cwd=deployment_dir, capture_output=True)
        json_output = proc.stdout
        terraform_output = json.loads(json_output)
        if "ansible_host_public_ip" in terraform_output:
            ansible_host_public_ip = terraform_output["ansible_host_public_ip"]["value"]
            private_key_path = os.path.join(deployment_dir, "ssh", "id_rsa")
            remove_all_k8s_services(ansible_host_public_ip, private_key_path)

    # Setup ~/.kube/config if in AKS environment to prevent helm provider errors
    authenticate_aks(deployment_dir)

    proc = subprocess_run(
        ["terraform", "plan", "-destroy", "-out=destroyplan", "-detailed-exitcode"],
        cwd=deployment_dir,
        universal_newlines=True
    )
    if proc.returncode == 1:
        click.echo("Error while planning deployment cleanup", err=True)
        return
    elif proc.returncode == 0:
        click.echo("No infrastructure changes needed.")
    elif proc.returncode != 2:
        return
    elif not click.confirm("Continue with above modifications?"):
        return
    else:
        proc = subprocess_run(["terraform", "apply", "destroyplan"], cwd=deployment_dir, universal_newlines=True)
        if proc.returncode == 1:
            click.echo("Error while running cleanup", err=True)
            return

        click.echo("Cleanup finished.")

    temp_files_remove(deployment_dir, "terraform", None)


def cloudcli_cleanup(deployment_dir):
    config_path = os.path.join(deployment_dir, "cwdf_util.yaml")

    # Verify config file exists
    if not os.path.exists(config_path):
        click.echo("Config file does not exist.", err=True)
        return None

    with open(config_path, 'r') as f:
        cwdf_user_config = f.read()
        configuration = yaml.safe_load(cwdf_user_config)
    cleaning_script = f"{configuration['cloudProvider']}_cloudcli_cleanup.sh"
    script_path = os.path.join(deployment_dir, cleaning_script)

    click.echo("Running CloudCLI cleaning script...")
    proc = subprocess_run([script_path], universal_newlines=True)
    if proc.returncode != 0:
        click.secho("Error while initializing cleaning script", err=True, bold=True, fg="red")
        return
    temp_files_remove(deployment_dir, "cloudcli", configuration['cloudProvider'])


@click.command()
@click.option('--deployment_dir', help='Path to deployment directory', required=True)
@click.option('--skip_service_cleanup', help='Skip deleting k8s service resources', default=False)
@click.option('--provisioner_tool', help='Select the tool that will be used for provisioning.', default='terraform')
def cleanup(deployment_dir, skip_service_cleanup, provisioner_tool):
    click.echo(f"Clean provisioner tool: {provisioner_tool}")
    if provisioner_tool == "terraform":
        terraform_cleanup(deployment_dir, skip_service_cleanup)
    if provisioner_tool == "cloudcli":
        if skip_service_cleanup:
            click.secho("Skip deleting K8s resources is not supported in CloudCLI yet.", err=True, bold=True, fg="red")
        cloudcli_cleanup(deployment_dir)


cli.add_command(deploy)
cli.add_command(cleanup)

if __name__ == "__main__":
    cli()
