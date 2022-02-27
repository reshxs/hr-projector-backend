# hr-projector-backend
## Запуск
### Окружение
Для того чтобы запустить приложение, сперва необходимо поднять окружение:
```bash
> docker compose up -d
```
### Web приложение
Приложение запускается с помощью ```run.py```:
```bash
> python3 src/run.py web [--collectstatic | --no-collect-static] [--uvicorn-debug | --no-uvicorn-debug]
```
### Django
Перед запуском не забываем применять миграции:
```bash
> python3 src/manage.py migrate
```
