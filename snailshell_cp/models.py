from django.db import models


class Node(models.Model):
    name = models.CharField(db_index=True, max_length=255)

    login = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()

    is_provisioned = models.BooleanField(default=False)

    def __str__(self):
        return f'<{self.__class__.__name__}: id={self.id} name={self.name}>'


class Service(models.Model):
    node = models.ForeignKey(Node, on_delete=models.PROTECT)
    image_name = models.CharField(max_length=255)
    default_image_tag = models.CharField(max_length=255, default='latest')
    container_name = models.CharField(max_length=255)

    is_system_service = models.BooleanField(default=False)

    env_variables = models.TextField(
        help_text=(
            'JSON, containing a key: value map. If value starts with $ - '
            'it is considered to be a name settings variable, '
            'the value will be sent over'
        ),
        null=True,
        blank=True,
    )
    host_config = models.TextField(
        help_text='JSON to be passed to container creation Docker API endpoint',
        null=True,
        blank=True,
    )
    volumes = models.TextField(
        help_text='JSON to be passed to container creation Docker API endpoint',
        null=True,
        blank=True,
    )
    command = models.TextField(
        help_text='JSON, passed to `Cmd` parameter on container creation',
        null=True,
        blank=True,
    )
    user_name = models.CharField(
        help_text='Linux user to run the container with',
        max_length=255,
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f'<{self.__class__.__name__}: id={self.id} node={self.node.name} '
            f'image={self.image_name}:{self.default_image_tag}>'
        )


class AsyncJob(models.Model):
    PENDING = 'pending'
    FAILED = 'failed'
    FINISHED = 'finished'

    created_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True)
    status = models.CharField(
        choices=[(key, key) for key in [PENDING, FAILED, FINISHED]],
        default=PENDING,
        max_length=255,
    )

    class Meta:
        abstract = True


class DeployJob(AsyncJob):
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    image_tag = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return (
            f'<{self.__class__.__name__}: id={self.id} '
            f'service={self.service} tag={self.image_tag}>'
        )


class NodeProvisionJob(AsyncJob):
    node = models.ForeignKey(Node, on_delete=models.PROTECT)

    def __str__(self):
        return f'<{self.__class__.__name__}: node_id={self.node_id}'


PERMISSION_DEPLOY = 'deploy'


class AccessKey(models.Model):
    # Comma-separated list of permissions
    permissions = models.TextField()
    value = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return (
            f'<{self.__class__.__name__}: permissions={self.permissions} '
            f'value={self.value}>'
        )
