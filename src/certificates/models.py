from django.contrib.postgres.fields import ArrayField
from django.db import models

from certificates.utils.uploaders import cert_tmplt_dir, cert_upload_dir
from certificates.utils.validators import validate_x_y


from general.models import BaseModel


# Create your models here.

class CertTemplate(BaseModel):
    date_coord = ArrayField(models.IntegerField(), size=2, validators=[validate_x_y])
    name_coord = ArrayField(models.IntegerField(), size=2, validators=[validate_x_y])
    template = models.ImageField(verbose_name='Шаблон', upload_to=cert_tmplt_dir)
    course = models.OneToOneField('courses.Course', on_delete=models.CASCADE,
                                  verbose_name='Курс')


class Certificate(BaseModel):
    student = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE,
                                verbose_name='Студент')
    template = models.ForeignKey(CertTemplate, on_delete=models.CASCADE,
                                 verbose_name='Шаблон')
    generated_cert = models.ImageField(verbose_name='Сертификат', blank=True, null=True,
                                       upload_to=cert_upload_dir)
