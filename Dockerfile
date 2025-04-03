FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements/base.txt

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:30000"]
