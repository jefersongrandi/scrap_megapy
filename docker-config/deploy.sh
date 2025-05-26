#!/bin/bash
set -e

echo "=== Preparando ambiente para deploy ==="

# Remover a pasta functions/src se existir
if [ -d "functions/src" ]; then
  echo "Removendo pasta functions/src existente..."
  rm -rf functions/src
fi

# Copiar a pasta src para functions/src
echo "Copiando src para functions/src..."
mkdir -p functions/src
cp -r src/* functions/src/

# Criar ambiente virtual Python
echo "Criando ambiente virtual Python..."
cd functions
python3 -m venv venv

# Ativar ambiente virtual e instalar dependências
echo "Instalando dependências..."
source venv/bin/activate
pip install -r requirements.txt

# Executar deploy
echo "Iniciando deploy para Firebase..."
# Usar a chave de serviço para autenticação
firebase use mega-sena-40cff --non-interactive
firebase deploy --non-interactive

echo "=== Deploy concluído com sucesso! ===" 