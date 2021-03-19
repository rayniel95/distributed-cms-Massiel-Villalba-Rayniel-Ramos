FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
# disable proxy options if you arent using it
RUN pip3 install --proxy=http://192.168.49.1:8282 --no-cache-dir -r requirements.txt

COPY ./code ./

VOLUME ["/data"]

EXPOSE 5000

CMD ["python", "./launcher.py"]