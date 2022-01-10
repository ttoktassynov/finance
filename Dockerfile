# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
ENV API_KEY=pk_2bd1949aba62442aa8f0029455fec56c
CMD [ "waitress-serve", "--call" , "application:create_app"]