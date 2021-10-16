#!/bin/sh

#corrigir locale que dava erro ao rodar o flask no container
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

#executa o flask para gerar api no container
exec python -m flask run --host=0.0.0.0