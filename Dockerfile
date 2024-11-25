FROM python:3.10-slim
RUN apt-get update && apt-get install -y build-essential libpq-dev
WORKDIR /lik
COPY requirements.txt /lik/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /lik/
EXPOSE 8000
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000"]