from django.contrib import admin


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

register_models()
