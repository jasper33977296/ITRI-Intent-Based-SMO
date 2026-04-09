FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements/base.txt

CMD ["sh", "-c", "python manage.py makemigrations && \
                  python manage.py migrate && \
                  exec python manage.py runserver 0.0.0.0:30000"]
