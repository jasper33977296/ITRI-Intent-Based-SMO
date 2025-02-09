FROM python:3.9

WORKDIR /app

COPY requirements /app/requirements

RUN pip install --no-cache-dir -r requirements/base.txt

COPY . /app

CMD ["python", "manage.py", "runserver", "0.0.0.0:30000"]
