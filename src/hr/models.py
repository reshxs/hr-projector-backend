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

    class Meta:
        abstract = True


class Department(BaseModel):
    class Meta:
        verbose_name = 'Департамент'
        verbose_name_plural = 'Департаменты'

    name = models.CharField('Название департамента', max_length=150)

    def __str__(self):
        return f'{self.name}({self.id})'


class UserRole(models.TextChoices):
    APPLICANT = 'APPLICANT', 'соискатель'  #: тот, кто хочет поменять место работы
    MANAGER = 'MANAGER', 'менеджер'  #: тот, кто предлагает место работы


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
        default=UserRole.APPLICANT,
        verbose_name='Роль',
    )

    USERNAME_FIELD = 'email'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic or ""}'.strip()

    def __str__(self):
        return f'{self.full_name} ({self.email})'


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


class VacancyState(models.TextChoices):
    DRAFT = 'DRAFT', 'Черновая'
    PUBLISHED = 'PUBLISHED', 'Опубликована'
    HIDDEN = 'HIDDEN', 'Скрыта'


class Vacancy(BaseModel):
    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

    State = VacancyState

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='Менеджер, разместивший вакансию',
    )

    state = models.CharField(
        'Состояние',
        max_length=50,
        choices=State.choices,
        default=State.DRAFT,
    )

    position = models.CharField('Должность', max_length=50)
    experience = models.PositiveIntegerField(
        'Стаж работы',
        null=True,
        blank=True,
        help_text='В годах',
    )
    description = models.TextField('Описание')

    created_at = models.DateTimeField('Дата/Время создания', auto_now=True)
    published_at = models.DateTimeField('Дата/Время публикации', null=True, blank=True)
