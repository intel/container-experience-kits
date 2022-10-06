import os
import io
from Crypto.PublicKey import RSA
import click
import json
import paramiko
import subprocess
from paramiko import SSHClient, SSHException
from scp import SCPClient
import string
import random
import socket
from time import sleep
import cwdf
import yaml
import shutil
import sw_deployment.sw_deployment_tool as sw_deployment

def generate_ssh_keys(ssh_dir, public_key_path, private_key_path):
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        private_key = RSA.generate(2048)
        with open(private_key_path, 'wb') as f:
            f.write(private_key.exportKey('PEM'))
        public_key = private_key.publickey()
        with open(public_key_path, 'wb') as f:
            f.write(public_key.exportKey('OpenSSH'))
        os.chmod(private_key_path, 0o600)


@click.group()
def cli():
    pass


@click.command()
@click.option('--deployment_dir', help='Path to deployment directory', required=True)
def deploy(deployment_dir):
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
        cwdf_configuration = f.read()

    # Generate SSH keys for instances
    ssh_dir = os.path.join(os.path.abspath(deployment_dir), "ssh")
    public_key_path = os.path.join(ssh_dir, "id_rsa.pub")
    private_key_path = os.path.join(ssh_dir, "id_rsa")
    generate_ssh_keys(ssh_dir, public_key_path, private_key_path)
    with open(public_key_path, 'r') as f:
        ssh_public_key = f.read()
    with open(private_key_path, 'r') as f:
        ssh_private_key = f.read()

    # Create lock file if not exists
    # Lock file is intended to contain info not to break previous deployment in future
    # For now only job id is stored there to preserve previous deployment
    lock_path = os.path.join(deployment_dir, "tbd.lock")
    with open(lock_path, 'a+') as f:
        f.seek(0)
        lock_str = f.read()
        try:
            lock = json.loads(lock_str)
        except ValueError as e:
            lock = None

        if lock is not None and "job_id" in lock:
            job_id = lock["job_id"]
        else:
            # Random 8 digit identifier
            job_id = ''.join(random.choices(string.digits, k=8))
            lock = json.dumps({"job_id": job_id})
            f.write(lock)

    click.echo("Job ID: " + job_id)

    manifest = cwdf.compose_terraform(cwdf_configuration, job_id, ssh_public_key)
    manifest_path = os.path.join(deployment_dir, 'deploy.tf')
    with open(manifest_path, 'w') as f:
        f.write(manifest)

    click.echo("Initializing Terraform...")
    proc = subprocess.run(["terraform", "init"], cwd=deployment_dir, universal_newlines=True)
    if proc.returncode != 0:
        click.secho("Error while initializing Terraform", err=True, bold=True, fg="red")
        return

    click.echo("Building Terraform plan...")
    proc = subprocess.run([
        "terraform", "plan", "-out=outfile", "-detailed-exitcode"],
        cwd=deployment_dir, universal_newlines=True
    )
    if proc.returncode == 1:
        click.echo("Error while planning deployment", err=True)
        return
    elif proc.returncode == 0:
        click.echo("No changes needed.")
        #return

    if click.confirm("Continue with above modifications?"):
        proc = subprocess.run(["terraform", "apply", "outfile"], cwd=deployment_dir, universal_newlines=True)
        if proc.returncode == 1:
            click.echo("Error while running deployment", err=True)
            return
        else:
            click.echo("Deployment finished.")
    else:
        return

    proc = subprocess.run(["terraform", "output", "-json"], cwd=deployment_dir, capture_output=True)
    json_output = proc.stdout
    terraform_output = json.loads(json_output)
    ansible_host_ip = terraform_output["ansible_host_public_ip"]["value"]
    click.echo("Ansible Host is accessible on: " + ansible_host_ip)
    click.echo("-------------------")
    ecr_url = terraform_output["ecr_url"]["value"]
    click.echo("ECR Registry URL:")
    click.echo(ecr_url)
    click.echo("-------------------")
    click.echo("Worker nodes:")
    click.echo("-------------------")
    workers = terraform_output["eks_worker_instances"]["value"]
    workers_ip = []
    for worker in workers:
        workers_ip.append(worker["private_ip"])
        click.echo("Worker " + worker["id"])
        click.echo("Private ip: " + worker["private_ip"])
        click.echo("Public ip: " + worker["public_ip"])
        click.echo("-------------------")
    click.echo("Opening SSH connection to Ansible host...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cfg = {
            'hostname': ansible_host_ip,
            'timeout': 200,
            'username': 'ubuntu',
            'key_filename': private_key_path
        }
    if os.path.exists(os.path.expanduser("~/.ssh/config")):
        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        with io.open(user_config_file, 'rt', encoding='utf-8') as f:
            ssh_config.parse(f)
        host_conf = ssh_config.lookup(ansible_host_ip)
        if host_conf:
            if 'proxycommand' in host_conf:
                cfg['sock'] = paramiko.ProxyCommand(host_conf['proxycommand'])
            if 'user' in host_conf:
                cfg['username'] = host_conf['user']
            if 'identityfile' in host_conf:
                cfg['key_filename'] = host_conf['identityfile']
            if 'hostname' in host_conf:
                cfg['hostname'] = host_conf['hostname']
    ssh_connected = False
    while not ssh_connected:
        try:
            ssh.connect(**cfg)
            ssh_connected = True
        except (SSHException, socket.error) as e:
            click.echo("SSH not available yet. Retrying in 10 seconds.")
            sleep(10)
    click.echo("Opened SSH connection.")
    click.echo("Waiting for cloud init to complete on Ansible host...")
    scp = SCPClient(ssh.get_transport())
    stdin, stdout, stderr = ssh.exec_command("cloud-init status --wait")
    stdout.channel.recv_exit_status()
    click.echo("Cloud init done.")

    # Make deployment output yaml file
    cwdf_output = {
        "ecr_url": ecr_url,
        "eks_worker_instances": workers
    }
    cwdf_output_filename = os.path.join(deployment_dir, "cwdf_output.yaml")
    with open(cwdf_output_filename, 'w') as f:
        yaml.dump(cwdf_output, f)
    scp.put(cwdf_output_filename, remote_path="/home/ubuntu/cwdf_deployment/")

    click.echo("Transferring SSH keys to Ansible machine...")
    scp.put(private_key_path, remote_path='/tmp/id_rsa',)
    ssh.exec_command("sudo mv /tmp/id_rsa /home/ubuntu/cwdf_deployment/ssh/id_rsa")
    ssh.exec_command("sudo chmod 600 /home/ubuntu/cwdf_deployment/ssh/id_rsa")
    click.echo("Successfully transferred SSH key to ~/cwdf_deployment/ssh/id_rsa")
    click.echo("Transferring discovery to Ansible instance...")
    scp.put("discovery", remote_path="/home/ubuntu/cwdf_deployment/", recursive=True)
    click.echo("Successfully transferred discovery to ~/cwdf_deployment/discovery")
    click.echo("Running discovery on EKS workers...")
    discovery_results_path = os.path.join(deployment_dir, "discovery_results")
    if not os.path.exists(discovery_results_path):
        os.makedirs(discovery_results_path)
    for worker in workers:
        stdin, stdout, stderr = ssh.exec_command(
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
    scp.put(discovery_results_path, remote_path="/home/ubuntu/cwdf_deployment/", recursive=True)
    click.echo("Copied discovery results to Ansible host.")
    ssh.close()

    click.echo("-------------------")
    click.echo('Running SW deployment')

    with open(file=sw_config_path, mode='r', encoding='utf-8') as file:
        sw_configuration = yaml.load(file, Loader=yaml.FullLoader)
    sw_configuration['ansible_host_ip'] = ansible_host_ip
    sw_configuration['worker_ips'] = workers_ip
    sw_configuration['ssh_key'] = os.path.join('..', private_key_path)
    sw_configuration['replicate_to_container_registry'] = ecr_url
    with open(file=sw_config_path, mode="w", encoding='utf-8') as file:
        yaml.dump(sw_configuration, file)

    sw_deployment.start_deploy(config=sw_config_path)

@click.command()
@click.option('--deployment_dir', help='Path to deployment directory', required=True)
def cleanup(deployment_dir):
    sw_deployment.cleanup(config=os.path.join(deployment_dir, "sw.yaml"))
    subprocess.run(["terraform", "destroy"], cwd=deployment_dir, universal_newlines=True)
    click.echo("Removing temporary files...")

    discovery_results_path = os.path.join(deployment_dir, "discovery_results")
    ssh_dir = os.path.join(deployment_dir, "ssh")
    directories = [discovery_results_path, ssh_dir]

    cwdf_output_filename = os.path.join(deployment_dir, "cwdf_output.yaml")
    lock_path = os.path.join(deployment_dir, "tbd.lock")
    manifest_path = os.path.join(deployment_dir, 'deploy.tf')
    outfile_path = os.path.join(deployment_dir, 'outfile')
    files = [cwdf_output_filename, lock_path, manifest_path, outfile_path]

    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    for file in files:
        if os.path.exists(file):
            os.remove(file)


cli.add_command(deploy)
cli.add_command(cleanup)


if __name__ == "__main__":
    cli()
