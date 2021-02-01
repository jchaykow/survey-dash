FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y software-properties-common build-essential python3-pip  nano && \
    apt-get clean

COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 8050

CMD gunicorn -w 10 -b 0.0.0.0:8050 -t 100000 --max-requests 20 app:server

CMD ["python3", "application.py"]
