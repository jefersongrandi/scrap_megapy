# Deploy e Execução Local do Firebase Functions

Este documento descreve como executar localmente e fazer o deploy das Firebase Functions do projeto usando Docker.

## Pré-requisitos

- Docker e Docker Compose instalados
- Conta no Firebase com acesso ao projeto `mega-sena-40cff`
- Arquivo de credenciais `serviceAccountKey.json` (para funcionalidades que dependem do Firebase)

## Estrutura

- `functions/` - Contém o código das funções Firebase
- `src/` - Código fonte compartilhado
- `docker-config/` - Arquivos de configuração para Docker
  - `Dockerfile.firebase` - Define a imagem Docker para execução e deploy
  - `docker-compose.firebase.yml` - Define os serviços para execução local e deploy

## Scripts Disponíveis

### Deploy para o Firebase

O script `deploy_firebase.sh` prepara o ambiente e faz o deploy das funções para o Firebase:

```bash
./deploy_firebase.sh
```

Este script:
1. Verifica se o arquivo de credenciais existe
2. Solicita login no Firebase, se necessário
3. Constrói a imagem Docker, se necessário
4. Executa o container de deploy, que:
   - Remove `functions/src` se existir
   - Copia `src/` para `functions/src/`
   - Cria ambiente virtual Python dentro de `functions/`
   - Instala as dependências necessárias
   - Faz deploy das funções para o Firebase

### Execução Local

O script `run_local.sh` inicia um servidor local para testar as funções:

```bash
./run_local.sh
```

Este script:
1. Constrói a imagem Docker, se necessário
2. Para qualquer container em execução com o mesmo nome
3. Inicia o servidor local em um container que:
   - Remove `functions/src` se existir
   - Copia `src/` para `functions/src/`
   - Cria ambiente virtual Python dentro de `functions/`
   - Instala as dependências necessárias
   - Inicia o servidor local na porta 8080

A API estará disponível em `http://localhost:8080`

## Endpoints da API

- **GET /** - Informações básicas da API
- **GET /megasena** - Obtém o resultado mais recente da Mega-Sena via scraping
- **GET /megasena/api** - Obtém dados da Megasena da API oficial da Caixa
- **GET /megasena/estatisticas** - Obtém estatísticas da Megasena
- **GET /megasena/historico** - Obtém o histórico de resultados da Megasena salvos no Firebase
- **GET /megasena/ultimos_sorteios** - Obtém os números sorteados dos últimos concursos

## Solução de Problemas

### Problemas com Permissões do Firebase

Se você encontrar erros de permissão ao acessar recursos do Firebase, verifique:
1. Se o arquivo `serviceAccountKey.json` é válido e tem as permissões necessárias
2. Se você está logado no Firebase CLI

### Problemas com o Selenium

Se você encontrar erros relacionados ao Firefox ou geckodriver:
1. Verifique se o Firefox está instalado no container
2. Verifique se o geckodriver está no caminho correto e tem permissões de execução

### Problemas de Serialização JSON

Se você encontrar erros como "Object of type X is not JSON serializable", verifique:
1. O tratamento de tipos de dados do Firestore no código
2. A classe `FirestoreEncoder` em `src/services/megasena_service.py` 