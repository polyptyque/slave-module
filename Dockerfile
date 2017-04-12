FROM resin/rpi-raspbian:latest

RUN apt-get update \
    && apt-get install python3

RUN apt-get install python3-pip

WORKDIR /home/pi/app/

RUN pip3 install configparser \
    && pip3 install requests

COPY . /home/pi/app/

CMD ["python3","app.py"]

