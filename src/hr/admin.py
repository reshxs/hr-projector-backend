from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms

from hr import models


admin.site.index_title = 'HR Projector'
admin.site.site_header = 'HR Projector'


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


register_models()
