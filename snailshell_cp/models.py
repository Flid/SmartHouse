from django.db import models


class Node(models.Model):
    name = models.CharField(db_index=True, max_length=255)

    login = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()

    is_provisioned = models.BooleanField(default=False)

    def __str__(self):
        return f'<{self.__class__.__name__}: id={self.id} name={self.name}>'


class AsyncJob(models.Model):
    created_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class DeployJob(AsyncJob):
    node = models.ForeignKey(Node, on_delete=models.PROTECT)
    image_name = models.CharField(max_length=255)
    image_tag = models.CharField(max_length=255)

    def __str__(self):
        return (
            f'<{self.__class__.__name__}: node_id={self.node_id} '
            f'image={self.image_name}:{self.image_tag}>'
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
