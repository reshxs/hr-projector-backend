import enum

from concurrency.fields import IntegerVersionField
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


class UserRole(models.TextChoices):
    EMPLOYEE = 'EMPLOYEE', 'рядовой сотрудник'
    MANAGER = 'MANAGER', 'менеджер'


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
    role = models.CharField(
        max_length=25,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
    )

    USERNAME_FIELD = 'email'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()


class ResumeState(models.TextChoices):
    DRAFT = 'DRAFT', 'Черновое'
    PUBLISHED = 'PUBLISHED', 'Опубликовано'
    HIDDEN = 'HIDDEN', 'Скрыто'


class Resume(BaseModel):
    class Meta:
        verbose_name = 'Резюме'
        verbose_name_plural = 'Резюме'

    State = ResumeState

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(
        'Состояние',
        max_length=25,
        choices=State.choices,
        default=State.DRAFT,
    )
    content = models.TextField('Содержимое', null=True, blank=True)
    created_at = models.DateTimeField('Дата/Время создания', auto_now_add=True)
    published_at = models.DateTimeField('Дата/Время публикации', null=True, blank=True)
    _version = IntegerVersionField()
