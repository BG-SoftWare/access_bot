FROM python:3.11.7-bookworm

WORKDIR /usr/src/controlbot
COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DOCKERIZED=1

CMD ["python", "./bot.py"]