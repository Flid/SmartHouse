from django.db import models


class Node(models.Model):
    id = models.IntegerField(db_index=True, primary_key=True)
    name = models.CharField(db_index=True, max_length=255)

    login = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()

    def __str__(self):
        return f'<{self.__class__.__name__}: id={self.id} name={self.name}>'
