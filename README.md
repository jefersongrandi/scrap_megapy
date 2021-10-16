# scrap_megapy

Utilizar Python 3.7 ou acima.

1) Rodar localmente sem container

    #instalar virutalenv
    python3 -m venv venv

    #instalar lib dentro do venv
    pip install -r requirements.txt

    #executar app dentro do venv
    python3 -m flask run --host=127.0.0.1


2) Rodar por container

    docker-compose up -d

