#!/bin/bash

# Script para construir o frontend e colocá-lo na pasta public

echo "Iniciando build do frontend..."

# Navegar para o diretório frontend
cd frontend

# Instalar dependências
echo "Instalando dependências..."
yarn install

# Construir o projeto
echo "Construindo o projeto..."
yarn build:public

# Voltar ao diretório raiz
cd ..

echo "Build concluído! Os arquivos estão disponíveis na pasta 'public'." 