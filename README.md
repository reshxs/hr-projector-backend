# hr-projector-backend

## Разработка

### Поднять приложение с окружением
Для удобства frontend-разработки можно развернуть локально backend целиком. Для этого есть отдельный файл test.docker-compose.yml:
```bash
docker compose -f test.docker-compose.yml up -d
```

### Поднять окружение
Для того чтобы запустить приложение, сперва необходимо поднять окружение:
```bash
docker compose up -d
```

### Окружение разработчика
Для разработки создаем виртуальное окружение и ставим все необходимые зависимости:
```bash
python3 -m venv venv
pip install -r src/requirements.txt
```
! Если понадобится установить новый пакет в проект - не зыбываем обновлять requirements.txt !
```bash
pip freeze > src/requirements.txt
```

### Запуск web приложения
Приложение запускается с помощью ```run.py```:
```bash
python3 src/run.py web [--collectstatic | --no-collect-static] [--uvicorn-debug | --no-uvicorn-debug] [--migrate | --no-migrate]
```

### Запуск в Docker
```bash
docker build . -t <image-name>
docker run -it -p 8000:8000 <image-name>
```

### Django
Перед запуском не забываем применять миграции:
```bash
python3 src/manage.py migrate
```

### Конфигурация
Для удобной конфигурации приложения используем .env

## Deploy 
[TODO]
