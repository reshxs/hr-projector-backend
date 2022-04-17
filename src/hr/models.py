from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class QuerySet(models.QuerySet):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except models.ObjectDoesNotExist:
            return None


class BaseModel(models.Model):
    objects = QuerySet.as_manager()


class Department(BaseModel):
    class Meta:
        verbose_name = 'Департамент'
        verbose_name_plural = 'Департаменты'

    name = models.CharField('Название департамента', max_length=150)


class User(AbstractBaseUser):
    objects = QuerySet.as_manager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    email = models.EmailField('Адрес электронной почты', unique=True)

    first_name = models.CharField('Имя', max_length=255)
    last_name = models.CharField('Фамилия', max_length=255)
    patronymic = models.CharField('Отчество', max_length=255, null=True, blank=True)

    department = models.ForeignKey(Department, verbose_name='Департамент', on_delete=models.PROTECT)
    is_manager = models.BooleanField('Является менеджером', default=False)

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()
