from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):

    class UserTypes(models.TextChoices):
        ADMIN = 'admin', _('admin')
        USER = 'user', _('user')

    class UserRoles(models.TextChoices):
        LEVEL_0 = 'level-0', _('level-0')
        LEVEL_1 = 'level-1', _('level-1')
        LEVEL_2 = 'level-2', _('level-2')
        LEVEL_3 = 'level-3', _('level-3')

    access_type = models.CharField(max_length=20, choices=UserTypes.choices, default=UserTypes.USER)
    role = models.CharField(max_length=20, choices=UserRoles.choices, default=UserRoles.LEVEL_0)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    expiration_date = models.CharField(max_length=30, null=True, blank=True)
