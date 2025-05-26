#!/bin/sh

#corrigir locale que dava erro ao rodar o flask no container
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Configurar variável de ambiente para desativar o Firebase se necessário
# Se você quiser desativar o Firebase, defina DISABLE_FIREBASE=true
if [ "$DISABLE_FIREBASE" = "true" ]; then
  echo "Iniciando a aplicação com o Firebase desativado..."
  export FLASK_DISABLE_FIREBASE=true
else
  echo "Iniciando a aplicação com o Firebase ativado..."
fi

#executa o flask para gerar api no container
#exec python3 -m flask run --host=0.0.0.0
cd /home/user
echo "Valor da variável DEBUG: $DEBUG"
gunicorn api:api -w 2 --threads 2 -b "0.0.0.0:$PORT"