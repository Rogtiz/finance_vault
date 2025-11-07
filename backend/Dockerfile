FROM python:3.10-slim
WORKDIR /app

# Копируем только зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всю директорию app
COPY ./app /app/app

# Запускаем uvicorn, указывая на app/main.py, и объект app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]