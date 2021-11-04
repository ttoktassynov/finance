# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
ENV FLASK_APP=application.py API_KEY=pk_2bd1949aba62442aa8f0029455fec56c
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]