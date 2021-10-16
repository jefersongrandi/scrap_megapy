#FROM python:3.8

#WORKDIR /var/api

#RUN pip install --no-cache-dir -r requirements.txt
#COPY requirements.txt /requirements.txt 
#RUN pip3 install --upgrade pip
#RUN pip3 install -r requirements.txt

#EXPOSE 5000

FROM ubuntu:16.04

#Instalar o Curl
RUN apt update -y && apt upgrade -y && apt install curl -y

#Dependências do sistema
RUN apt-get update -y
RUN apt-get install -y python3-dev python3-pip build-essential

#Ajustar o pip do Python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.5 1
RUN curl -O https://bootstrap.pypa.io/pip/3.5/get-pip.py
RUN python get-pip.py
RUN python -m pip install --upgrade "pip < 21.0"

#copiar arquivo para container e dar permissão
COPY start.sh /start.sh
RUN chmod +x /start.sh

#criar diretório para colocar arquivos api
RUN mkdir -p /home/user
WORKDIR /home/user
COPY requirements.txt /home/user/requirements.txt

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["/start.sh"]
