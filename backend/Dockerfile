FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . ./
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]
LABEL author='alekseikogan@yandex.ru' ip='158.160.30.17' date='04/05/2023'