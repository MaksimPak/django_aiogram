from django.db import models


class LeadManager(models.Manager):
    def get_queryset(self):
        return super(LeadManager, self).get_queryset().filter(is_client=False)


class ClientManager(models.Manager):
    def get_queryset(self):
        return super(ClientManager, self).get_queryset().filter(is_client=True)
