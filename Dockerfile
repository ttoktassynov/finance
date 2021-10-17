# syntax=docker/dockerfile:1

FROM python:3.9.0a3-alpine3.10
WORKDIR /app
COPY requirements.txt requirments.txt
RUN pip install -r requirments.txt
COPY . .
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]