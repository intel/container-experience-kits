"""Class for SSH connection"""
from http import client
from logging import exception
import os
import io
import subprocess
import click
from paramiko import SSHClient, SSHConfig, ProxyCommand, AutoAddPolicy, SSHException
from scp import SCPClient, SCPException


class SSHConnector:
    """
    SSHConnector class for managing SSH connections to remote instances.
    Class supports proxy jump connection for cloud instances without public access.
    """

    def __init__(self, ip_address, username, port=22, priv_key=None, gateway=None):
        """
        Initialize the class and connect to the client.
        The method supports gateway proxy hopping.
        The gateway uses an already open SSH connection using the same SSHConnector class.

        Parameters:
        ip_address (string): IP address of the remote instance
        username (string): User name for autentication in remote instance
        port (int): SSH port
        priv_key (string): Path to private RSA key for autentication in remote instance
        gateway (SSHConnector obj): [optional] SSHConnector object with active SSH connection
                                               to gateway for create proxy jump

        Rerurn:
        None

        """
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())

        sock = None
        if gateway:
            dest_addr = (ip_address, port)
            local_addr = ('127.0.0.1', 1234)
            sock = gateway.get_transport().open_channel(
                'direct-tcpip', dest_addr, local_addr
            )

        cfg = {
            'hostname': ip_address,
            'port': port,
            'timeout': 200,
            'banner_timeout': 15,
            'key_filename': priv_key,
            'username': username,
            'sock': sock
        }

        if os.path.exists(os.path.expanduser("~/.ssh/config")):
            ssh_config = SSHConfig()
            user_config_file = os.path.expanduser("~/.ssh/config")
            with io.open(user_config_file, 'rt', encoding='utf-8') as conf_file:
                ssh_config.parse(conf_file)

            host_conf = ssh_config.lookup(ip_address)
            if host_conf:
                if ('proxycommand' in host_conf) and (gateway is None):
                    cfg['sock'] = ProxyCommand(host_conf['proxycommand'])
                if 'user' in host_conf:
                    cfg['username'] = host_conf['user']
                if 'identityfile' in host_conf:
                    cfg['key_filename'] = host_conf['identityfile']
                if 'hostname' in host_conf:
                    cfg['hostname'] = host_conf['hostname']

        try:
            self.client.connect(**cfg)
        except SSHException as ssh_excep:
            click.echo("Cannot connect to instance via SSH", err=True)
            click.echo(f"Error message: {ssh_excep}", err=True)

    def exec_command(self, command, print_output=False):
        """
        Executes command on connected client.

        Parameters:
        command (string): Command to execute on remote instance
        print_output (bool): To print output to console

        Return:
        string:Command output

        """
        stdin = None
        stdout = None
        stderr = None
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
        except SSHException:
            click.echo(f"During command: {stdin}")
            click.echo(f"Error ocured: {stderr}")
        if print_output:
            for line in iter(lambda: stdout.readline(2048), ""):
                click.echo(line, nl=False)
        return stdout.read().decode('ascii').strip('\n')

    def progress(self, filename, size, sent):
        """
        Define progress callback that prints the current
        percentage completed for the file

        Parameters:
        filename (string): Name of the uploaded file
        size (int): Size of the file
        sent (int): Count of already sent bytes

        Return:
        None

        """
        with click.progressbar(length=100,
                       label=f"Uploading {filename} progress") as prog_bar:
            prog_bar.update(float(sent)/float(size)*100)

    def copy_file(self, file_path, destination_path):
        """
        For upload file to remote client via SCP protocol.

        Parameters:
        file_path (string): Path to file to upload
        destination_path (string): Path where to upload file

        Return:
        None

        """
        scp = SCPClient(self.client.get_transport(), progress=self.progress)
        try:
            scp.put(file_path, destination_path)
        except SCPException as error:
            click.print(f"Error during uploading host_var file: {error}", err=True)
        scp.close()

    def close_connection(self):
        """
        Close SSH connection.

        Return:
        None

        """
        self.client.close()
