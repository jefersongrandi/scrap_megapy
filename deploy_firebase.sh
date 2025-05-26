#!/bin/bash

# Script para preparar e executar o deploy do Firebase Functions
# Autor: Seu Nome
# Data: 25/05/2025

# Cores para saída do terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Iniciando processo de deploy para Firebase Functions ===${NC}"

# Verificar se o arquivo serviceAccountKey.json existe
if [ ! -f "serviceAccountKey.json" ]; then
    echo -e "${RED}Erro: Arquivo serviceAccountKey.json não encontrado!${NC}"
    echo "Por favor, obtenha o arquivo de credenciais do Firebase e salve-o como serviceAccountKey.json na raiz do projeto."
    exit 1
fi

# Executar o build do frontend
echo -e "${YELLOW}=== Construindo o frontend antes do deploy ===${NC}"
if [ -f "./build.sh" ]; then
    echo "Executando o script build.sh..."
    chmod +x ./build.sh
    ./build.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Erro durante a construção do frontend. Abortando deploy.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Build do frontend concluído com sucesso!${NC}"
else
    echo -e "${RED}Arquivo build.sh não encontrado. Verifique se o script existe na raiz do projeto.${NC}"
    exit 1
fi

# Verificar se o token do Firebase está disponível
# if [ -z "$FIREBASE_TOKEN" ]; then
#     echo -e "${YELLOW}Token do Firebase não encontrado no ambiente.${NC}"
#     echo "Você deseja fazer login no Firebase CLI agora? (s/n)"
#     read -r resposta
    
#     if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
#         echo "Executando login no Firebase..."
#         firebase login
#         # Obter e exportar o token do Firebase para uso no container
#         FIREBASE_TOKEN=$(firebase login:ci)
#         export FIREBASE_TOKEN
#     else
#         echo -e "${RED}Sem token do Firebase, não é possível continuar.${NC}"
#         exit 1
#     fi
# fi

# Construir a imagem Docker, se necessário
echo -e "${YELLOW}Verificando se é necessário construir a imagem Docker...${NC}"
if [[ "$(docker images -q scrap_megapy_firebase_deploy 2> /dev/null)" == "" ]]; then
    echo "Construindo imagem Docker..."
    docker compose -f docker-config/docker-compose.firebase.yml build firebase-deploy
fi

# Executar o container de deploy
echo -e "${YELLOW}Iniciando container para deploy...${NC}"
docker compose -f docker-config/docker-compose.firebase.yml run --rm firebase-deploy

# Verificar se o deploy foi bem sucedido
if [ $? -eq 0 ]; then
    echo -e "${GREEN}=== Deploy concluído com sucesso! ===${NC}"
    echo -e "Função disponível em: ${YELLOW}https://api-mty2yurbea-uc.a.run.app${NC}"
else
    echo -e "${RED}=== Ocorreu um erro durante o deploy ===${NC}"
    echo "Verifique os logs acima para mais detalhes."
    exit 1
fi 