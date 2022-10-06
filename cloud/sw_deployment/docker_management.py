"""Class for Docker images management"""
from dis import show_code
import os
from pathlib import Path
import configparser
import base64
import validators
import click
import docker
import boto3


class DockerManagement:
    """
    Class contains methods for copy docker images between registries.
    """
    docker_client = None
    CLOUD = None
    to_registry = None
    from_registry = None
    show_log = False
    images_to_replicate = None
    tagged_images = []

    AWS_ACCESS_KEY_ID = None
    AWS_ACCESS_SECRET_KEY = None
    AWS_REGION = None
    ECR_PASSWORD = None
    ECR_USERNAME = 'AWS'
    ECR_URL = None

    def __init__(self, from_registry, to_registry, images_to_replicate, region, cloud=None, show_log=False):
        """
        Init method for class.

        Parameters:
        from_registry (string): URL adress of source registry
        to_registry (string): URL address of target registry
        images_to_duplicate (list): List of images to copy between registries
        cloud (string): [Not required] Type of cloud with targer registry. Currently supported: ['aws']
        show_log (bool): [Not required] Show log of push image

        Return:
        None

        """
        self.docker_client = docker.from_env()
        self.CLOUD = cloud
        self.AWS_REGION = region
        self.show_log = show_log
        self.to_registry = to_registry
        self.images_to_replicate = images_to_replicate

        if not validators.url(from_registry):
            click.secho('The source registry does not have a valid URL!', fg='red')
            return
        else:
            self.from_registry = from_registry.replace('https://', '')

        self.images_to_replicate = images_to_replicate
        click.echo(f"Images to replicate: {self.images_to_replicate}")

        if self.CLOUD == "aws":
            self.initialize_ecr()

    def copy_images(self):
        """
        Copy images between registries.
        In case of set cloud, method using global variables with cloud credentials.

        Parameters:
        None

        Return:
        None

        """
        for image in self.images_to_replicate:
            self.pull_image(registry_url=self.from_registry,
                                image_name=image)
            new_image = self.tag_image(image_name=image,
                                       registry_old= self.from_registry,
                                       registry_new=self.to_registry)
            self.tagged_images.append(new_image)
            if self.CLOUD == 'aws':
                self.push_image(image=new_image['repository'],
                                tag=new_image['tag'],
                                registry=self.ECR_URL,
                                username=self.ECR_USERNAME,
                                password=self.ECR_PASSWORD)
            else:
                self.push_image(image=new_image['repository'],
                                tag=new_image['tag'],
                                registry=self.to_registry)

    def initialize_ecr(self):
        """
        Initializing ECR and getting AWS credentials for autentification in ECR.
        Method using local AWS credentials and config files for autentification.
        Method set the global variables used in previous method.

        Parameters:
        None

        Return:
        None

        """
        aws_credentials = os.path.join(Path.home(), '.aws', 'credentials')
        config = configparser.RawConfigParser()
        try:
            config.read(aws_credentials)
            credentials = config['default']
            self.AWS_ACCESS_KEY_ID = credentials['aws_access_key_id']
            self.AWS_ACCESS_SECRET_KEY = credentials['aws_secret_access_key']
        except configparser.ParsingError as parser_error:
            click.secho(parser_error, fg='red')

        aws_session = boto3.Session(region_name=self.AWS_REGION)
        ecr_client = aws_session.client('ecr', aws_access_key_id=self.AWS_ACCESS_KEY_ID, 
                                        aws_secret_access_key=self.AWS_ACCESS_SECRET_KEY, 
                                        region_name=self.AWS_REGION)

        ecr_credentials = (ecr_client.get_authorization_token()['authorizationData'][0])
        self.ECR_PASSWORD = (base64.b64decode(ecr_credentials['authorizationToken'])
                            .replace(b'AWS:', b'').decode('utf-8'))
        self.ECR_URL = self.to_registry

    def pull_image(self, registry_url, image_name, username=None, password=None):
        """
        Downloading image from remote to local registry.

        Parametes:
        registry_url (string): URL adress of source registry
        image_name (string): Name of downloaded image
        username (string): User name for source registry
        password (string): Password for source registry

        Return:
        None

        """
        if not (username is None and password is None):
            self.docker_client.login(username=username,
                                     password=password,
                                     registry=registry_url)
            output = self.docker_client.images.pull(f"{registry_url}/{image_name}")
            click.echo(output)
        else:
            output = self.docker_client.images.pull(f"{registry_url}/{image_name}")
            click.echo(output)

    def tag_image(self, image_name, registry_old, registry_new):
        """
        Tagging image with new registry.

        Parameters:
        image_name (string): Name of image
        registry_old (string): URL address of source registry
        registry_new (string): URL address of target registry

        Return:
        string:Name of tagged image

        """
        image = self.docker_client.images.get(f"{registry_old}/{image_name}")
        if self.CLOUD == 'aws':
            target_image = registry_new
            tag = image_name.replace('/', '-').replace(':', '-')
        else:
            target_image = f"{registry_new}/{image_name}"
            tag = 'latest'
        result = image.tag(target_image, tag)
        if result:
            return {'repository': target_image, 'tag': tag}

    def push_image(self, image, tag, registry=None, username=None, password=None):
        """
        Pushing image to target registry.

        Parameters:
        image (string): Name of the image
        registry (string): URL address of target registry
        username (string): User name for target registry
        password (string): Password for target registry

        Return:
        None

        """
        click.echo("Pushing image:")
        if registry is not None and username is not None and password is not None:
            self.docker_client.login(username=username,
                                     password=password,
                                     registry=registry)
            auth_config = {'username': username, 'password': password}
        push_log = self.docker_client.images.push(image, tag=tag, auth_config=auth_config)
        if not self.show_log:
            click.echo(push_log)
