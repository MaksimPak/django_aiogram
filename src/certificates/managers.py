from django.db import models

from certificates.utils.helpers import generate_cert


class CertManager(models.Manager):
    def bulk_create(self, items, *args, **kwargs):
        new_objs = super(CertManager, self).bulk_create(items, *args, **kwargs)
        for obj in new_objs:
            generate_cert(obj)

        return new_objs
