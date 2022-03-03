# hr-projector-backend

## Разработка

### Поднять окружение
Для того чтобы запустить приложение, сперва необходимо поднять окружение:
```bash
> docker compose up -d
```

### Запуск web приложения
Приложение запускается с помощью ```run.py```:
```bash
> python3 src/run.py web [--collectstatic | --no-collect-static] [--uvicorn-debug | --no-uvicorn-debug]
```

### Django
Перед запуском не забываем применять миграции:
```bash
> python3 src/manage.py migrate
```

### Конфигурация
Для удобной конфигурации приложения используем .env

## Deploy 
[TODO]
