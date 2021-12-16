#!/bin/sh

#corrigir locale que dava erro ao rodar o flask no container
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

#executa o flask para gerar api no container
#exec python3 -m flask run --host=0.0.0.0
gunicorn main:api -w 2 --threads 2 -b "0.0.0.0:$PORT"