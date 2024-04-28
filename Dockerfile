FROM python:3.10-slim-buster

WORKDIR /app

RUN python3 -m venv venv

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8080

ENTRYPOINT ["uvicorn"]

CMD ["server:app", "--host=0.0.0.0", "--reload", "--port=8080"]