import typing as tp

from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms
from django.urls import reverse
from django.utils.html import format_html

from hr import models

_AdminActionT = tp.TypeVar('_AdminActionT', bound=tp.Callable[..., object])

admin.site.index_title = 'HR Projector'
admin.site.site_header = 'HR Projector'


class _AdminActionAttrs(tp.Protocol[_AdminActionT]):
    short_description: str | None
    __call__: _AdminActionT


def admin_attrs(
    short_description: str | None = None,
    boolean: bool | None = None,
):
    def inner(func: _AdminActionT) -> _AdminActionAttrs[_AdminActionT]:
        func_ = tp.cast(_AdminActionAttrs[_AdminActionT], func)
        if short_description is not None:
            func_.short_description = short_description

        if boolean is not None:
            func_.boolean = boolean

        return func_

    return inner


class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = (
            'email',
            'password',
            'first_name',
            'last_name',
            'patronymic',
            'department',
            'role',
        )
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_password(self):
        return make_password(self.cleaned_data['password'])


@admin.register(models.User)
class UserModelAdmin(admin.ModelAdmin):
    form = UserForm
    list_display = ('id', 'email', 'full_name')
    list_filter = ('role',)


@admin.register(models.Vacancy)
class VacancyModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'state',
        'position',
        'creator_link',
        'created_at',
        'published_at',
    )
    list_filter = (
        'state',
        'experience',
    )

    @admin_attrs(short_description='Создатель')
    def creator_link(self, obj):
        link = reverse('admin:hr_user_change', args=[obj.creator_id])
        return format_html(f'<a href="{link}">{obj.creator}</a>')


@admin.register(models.Resume)
class ResumeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'state',
        'user_link',
        'created_at',
        'published_at',
    )
    list_filter = (
        'state',
    )

    @admin_attrs(short_description='Создатель')
    def user_link(self, obj):
        link = reverse('admin:hr_user_change', args=[obj.user_id])
        return format_html(f'<a href="{link}">{obj.user}</a>')


def register_models():
    from django.apps import apps
    from django.contrib.admin.sites import AlreadyRegistered

    app_models = apps.get_app_config('hr').get_models()
    for model in app_models:
        try:
            list_display = [field.name for field in model._meta.fields]
            admin.site.register(model, list_display=list_display)
        except AlreadyRegistered:
            pass


register_models()
