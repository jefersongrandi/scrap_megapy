#FROM python:3.8

#WORKDIR /var/api

#RUN pip install --no-cache-dir -r requirements.txt
#COPY requirements.txt /requirements.txt 
#RUN pip3 install --upgrade pip
#RUN pip3 install -r requirements.txt

#EXPOSE 5000

FROM ubuntu:22.04

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Atualizar e instalar dependências básicas
RUN apt-get update && apt-get install -y \
    curl \
    python3.10 \
    python3-pip \
    python3.10-distutils \
    firefox \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir Python 3.10 como padrão
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# Criar diretório para a aplicação
WORKDIR /home/user

# Copiar arquivos necessários
COPY requirements.txt /home/user/requirements.txt
COPY geckodriver /home/user/geckodriver
COPY docker-config/start.sh /start.sh

# Configurar permissões
RUN chmod +x /start.sh \
    && chmod +x /home/user/geckodriver

# Instalar dependências Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Configurar variáveis de ambiente para o Flask
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH=/home/user
# Por padrão, o Firebase é ativado. Para desativar, defina DISABLE_FIREBASE=true ao executar o container
ENV DISABLE_FIREBASE=false

# Copiar todos os arquivos do projeto
COPY . /home/user/

EXPOSE 5000

CMD ["/start.sh"]
