FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y git

RUN git clone https://github.com/jasper33977296/ITRI-Intent-Based-SMO.git

COPY .env ITRI-Intent-Based-SMO/.env

RUN pip install --no-cache-dir -r ITRI-Intent-Based-SMO/requirements/base.txt

WORKDIR /app/ITRI-Intent-Based-SMO

CMD ["python", "manage.py", "runserver", "0.0.0.0:30000"]
