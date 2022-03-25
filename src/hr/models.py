from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class QuerySet(models.QuerySet):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except models.ObjectDoesNotExist:
            return None


class User(AbstractBaseUser):
    objects = QuerySet.as_manager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    email = models.EmailField(unique=True, null=False)

    first_name = models.CharField(max_length=255, null=False)
    second_name = models.CharField(max_length=255, null=False)
    patronymic = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f'{self.second_name} {self.first_name} {self.patronymic}'.strip()
