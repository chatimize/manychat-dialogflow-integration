FROM ubuntu:20.04
RUN apt-get update -y && \
    apt-get install -y python3.8 python3-pip

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . /app
EXPOSE 80
ENTRYPOINT [ "python3" ]
CMD [ "manychat-dialogflow.py" ]
