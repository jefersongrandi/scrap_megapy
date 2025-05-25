# Scraping Megasena

Aplicação para captura de dados da Megasena utilizando Python e Firebase como backend para armazenamento.

## Sumário

- [Requisitos](#requisitos)
- [Executando o Projeto](#executando-o-projeto)
  - [Localmente sem Container](#localmente-sem-container)
  - [Com Docker](#com-docker)
- [Endpoints da API](#endpoints-da-api)
  - [Principais Endpoints](#principais-endpoints)
  - [Endpoint de Últimos Sorteios](#endpoint-de-últimos-sorteios)
- [Firebase Functions](#firebase-functions)
  - [Estrutura das Functions](#estrutura-das-functions)
  - [Endpoints das Functions](#endpoints-das-functions)
- [Configuração do Firebase](#configuração-do-firebase)
  - [Arquivos de Configuração](#arquivos-de-configuração)
  - [Configuração do Ambiente](#configuração-do-ambiente)
  - [Autenticação](#autenticação)
  - [Estrutura de Dados](#estrutura-de-dados)
  - [Deploy para o Firebase](#deploy-para-o-firebase)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Executando com Script Unificado](#executando-com-script-unificado)

## Requisitos

- Python 3.8 ou superior
- Docker e Docker Compose (opcional, para execução em containers)
- Node.js e npm (opcional, para deploy no Firebase)

## Executando o Projeto

### Localmente sem Container

```bash
# Instalar virtualenv
python3 -m venv venv

# Ativar o ambiente virtual
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar a aplicação
python -m flask run --host=127.0.0.1 --port=5001
```

### Com Docker

```bash
# Construir e iniciar os containers
docker compose up -d

# Verificar logs
docker logs scrap_py
docker logs firebase_functions
```

Os serviços ficarão disponíveis em:
- API principal: http://localhost:5001
- Firebase Functions: http://localhost:8080

## Endpoints da API

### Principais Endpoints

- **`/megasena`**: Retorna o resultado atual da Megasena via scraping
- **`/megasena/api`**: Retorna dados do último concurso via API oficial da Caixa
- **`/megasena/api?concurso=XXXX`**: Retorna dados de um concurso específico
- **`/megasena/estatisticas?ultimos=N`**: Retorna estatísticas dos últimos N concursos
- **`/megasena/historico`**: Retorna histórico de resultados armazenados no Firestore
- **`/megasena/importar`**: Endpoint POST para importar diversos concursos

### Endpoint de Últimos Sorteios

```
GET /megasena/ultimos_sorteios?ultimos=N
```

Retorna os números sorteados dos últimos N concursos e salva no Firestore (sem duplicação).

Exemplo de resposta:
```json
{
  "status": "success",
  "total": 3,
  "ultimos_n": 3,
  "sorteios": [
    {
      "concurso": 2866,
      "data_sorteio": "2025-05-22",
      "dezenas": ["01", "12", "17", "19", "36", "60"],
      "premio_acumulado": 0.0
    },
    ...
  ]
}
```

## Firebase Functions

As Firebase Functions fornecem uma camada de serviços para processamento e armazenamento de dados da Megasena.

### Estrutura das Functions

- `main.py`: Contém as funções HTTP que podem ser chamadas de aplicações externas
- `firebase_scraper.py`: Classe adaptadora que integra as funções de scraping com o Firebase
- `firebase_init.py`: Inicialização do Firebase conforme ambiente
- `megasena_api.py`: Classe para comunicação com a API da Megasena

### Endpoints das Functions

- **`GET /scraping_status`**: Retorna o status atual das operações de scraping
- **`POST /iniciar_scraping`**: Inicia uma nova operação de scraping
- **`POST /salvar_resultado`**: Salva o resultado de uma operação de scraping no Firestore
- **`GET /megasena_dados`**: Retorna dados de um concurso específico
- **`GET /megasena_ultimos_sorteios`**: Retorna os últimos sorteios da Megasena

## Configuração do Firebase

Este projeto está configurado para usar o Firebase como backend para armazenamento de dados da Megasena. A configuração está definida para o projeto `mega-sena-40cff`.

### Arquivos de Configuração

Os seguintes arquivos de configuração foram criados:

- `.firebaserc`: Define o projeto padrão do Firebase
- `firebase.json`: Configuração principal do Firebase, incluindo Functions, Firestore e Hosting
- `firestore.rules`: Regras de segurança para o Firestore
- `firestore.indexes.json`: Índices do Firestore para consultas otimizadas

### Configuração do Ambiente

O ambiente está configurado para usar o Firebase de duas formas:

1. **Modo Simulado** (desenvolvimento local): Usa um simulador em memória do Firestore
2. **Modo Real** (produção): Conecta-se ao Firestore real no projeto `mega-sena-40cff`

As variáveis de ambiente que controlam esse comportamento são:

- `FIREBASE_USE_REAL`: Define se o Firebase real deve ser usado (`true` ou `false`)
- `FIREBASE_PROJECT_ID`: Define o ID do projeto do Firebase (padrão: `mega-sena-40cff`)

### Autenticação

Para usar o Firebase real em ambiente de desenvolvimento, é necessário ter um arquivo de credenciais:

1. Acesse o [Console do Firebase](https://console.firebase.google.com/project/mega-sena-40cff/settings/serviceaccounts/adminsdk)
2. Gere uma nova chave privada
3. Salve o arquivo como `functions/serviceAccountKey.json`

### Estrutura de Dados

O Firestore é usado para armazenar os seguintes dados:

- **resultados_scraping**: Resultados da Megasena obtidos via API
- **status**: Status das operações de scraping

## Deploy para o Firebase com Python 3.13

O projeto inclui scripts automatizados para fazer o deploy para o Firebase usando contêineres Docker, sem a necessidade de instalar o Firebase CLI localmente.

### Requisitos para Deploy

- Docker instalado e em execução
- Node.js (para desenvolvimento local)
- Python 3.13 (utilizado via Docker)

### Comandos Disponíveis

Execute os comandos através do script `run.sh`:

```bash
./run.sh [comando]
```

### Comandos

- `help` - Exibe a ajuda
- `deploy` - Deploy do Firebase (Firestore e Hosting)
- `deploy:functions` - Deploy das Functions do Firebase com Python 3.13
- `deploy:all` - Deploy completo do Firebase (Firestore, Hosting e Functions)
- `clean` - Limpa arquivos temporários

### Deploy das Functions (Python 3.13)

O deploy das Functions é realizado usando Docker com Python 3.13, conforme exigido pelo Firebase. O script `deploy-functions.sh` automatiza todo o processo:

1. Cria uma imagem Docker com Python 3.13
2. Configura o ambiente virtual Python
3. Instala as dependências necessárias
4. Realiza o deploy usando o Firebase CLI

### Estrutura dos Scripts

- `run.sh` - Interface unificada para todos os comandos
- `deploy-firebase.sh` - Script para deploy de Firestore e Hosting
- `deploy-functions.sh` - Script para deploy das Functions com Python 3.13

### Exemplo de Uso

Para realizar um deploy completo da aplicação:

```bash
./run.sh deploy:all
```

Para apenas as Functions:

```bash
./run.sh deploy:functions
```

### Problemas Comuns

#### Erro de Autenticação

Se encontrar erros de autenticação ao fazer deploy, execute:

```bash
firebase login
```

Ou no caso de estar usando Docker:

```bash
docker run --rm -it -v "$HOME/.config:/root/.config" firebase-tools:latest firebase login
```

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

- `functions/`: Contém as funções Firebase
- `src/`: Código fonte compartilhado
- `docker-config/`: Arquivos de configuração do Docker e scripts
- `run.sh`: Script principal para executar comandos do projeto
- `deploy-firebase.sh`: Script para deploy de Firestore e Hosting
- `deploy-functions.sh`: Script para deploy das Cloud Functions