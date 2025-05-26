import os
import sys
import json
import firebase_admin
from firebase_functions import https_fn
from firebase_functions import scheduler_fn
from flask import jsonify, Request

# Adicionar o diretório raiz ao path do Python para permitir importar módulos do src
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)

# Importar os serviços de src
from src.services.megasena_service import (
    obter_resultado_via_scraping,
    obter_resultado_api,
    obter_estatisticas,
    executar_scraping,
    importar_concursos_megasena,
    obter_historico_megasena,
    obter_ultimos_sorteios
)

# Importar o FirebaseService
from src.services.firebase_service import FirebaseService

# Inicializar o Firebase
firebase_available = False
try:
    # Verificar se o Firebase já foi inicializado
    try:
        app = firebase_admin.get_app()
    except ValueError:
        # Inicializar o Firebase com as credenciais padrão no ambiente do Cloud Functions
        # Não precisa de arquivo de credenciais no ambiente do GCP, pois usa as credenciais implícitas
        firebase_admin.initialize_app(options={
            'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'mega-sena-40cff'),
        })
    
    # Inicializar explicitamente o Firestore para o FirebaseService
    from firebase_admin import firestore
    db = firestore.client()
    
    # Verificar se o Firebase está disponível após a inicialização
    firebase_available = True
    print("Firebase inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar Firebase: {str(e)}")
    firebase_available = False

# Função programada para obter o último sorteio a cada 10 minutos nos horários específicos
@scheduler_fn.on_schedule(schedule="*/10 5-6,20-21 * * *")
def atualizar_ultimo_sorteio(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Função programada para executar todos os dias das 05:00 às 07:00 e das 20:00 às 22:00 a cada 10 minutos.
    Obtém apenas o último concurso da Mega-Sena e atualiza no Firebase.
    """
    try:
        # Obter apenas o último sorteio (ultimos_n=1)
        resultado = obter_ultimos_sorteios(1)
        
        # Registrar log de execução
        print(f"Atualização do último sorteio executada com sucesso: {resultado}")
        
        return None
    except Exception as e:
        print(f"Erro ao atualizar último sorteio: {str(e)}")
        return None

# Função Firebase Functions
@https_fn.on_request()
def api(request: https_fn.Request) -> https_fn.Response:
    """
    Função principal que funciona como um router para diferentes endpoints para o Firebase Functions.
    """
    # Habilitar CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response('', status=204, headers=headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    
    # Extrair o caminho da URL
    path = request.path
    
    # Rotas da API
    if path == '/' or path == '':
        return https_fn.Response(json.dumps({'status': 'Api working well'}), status=200, headers=headers)
    
    elif path == '/megasena':
        res = obter_resultado_via_scraping()
        return https_fn.Response(json.dumps(res), status=200, headers=headers)
    
    elif path == '/megasena/api':
        try:
            concurso = request.args.get('concurso')
            resultado = obter_resultado_api(concurso)
            return https_fn.Response(json.dumps(resultado), status=200, headers=headers)
        except ValueError as ve:
            return https_fn.Response(json.dumps({"erro": str(ve)}), status=400, headers=headers)
        except Exception as e:
            return https_fn.Response(json.dumps({"erro": str(e)}), status=500, headers=headers)
    
    elif path == '/megasena/estatisticas':
        try:
            ultimos_n = request.args.get('ultimos', 10)
            estatisticas = obter_estatisticas(ultimos_n)
            return https_fn.Response(json.dumps(estatisticas), status=200, headers=headers)
        except Exception as e:
            return https_fn.Response(json.dumps({"erro": str(e)}), status=500, headers=headers)
    
    elif path == '/firebase-scraping':
        if not firebase_available:
            return https_fn.Response(json.dumps({'error': 'Firebase não está disponível neste ambiente'}), status=503, headers=headers)
        
        try:
            data = request.get_json() if request.is_json else {}
            url = data.get('url')
            opcoes = data.get('opcoes')
            
            resultado = executar_scraping(url, opcoes)
            return https_fn.Response(json.dumps(resultado), status=200, headers=headers)
        except Exception as e:
            return https_fn.Response(json.dumps({'error': str(e)}), status=500, headers=headers)
    
    elif path == '/megasena/importar':
        if not firebase_available:
            return https_fn.Response(json.dumps({'erro': 'Firebase não está disponível neste ambiente'}), status=503, headers=headers)
        
        try:
            data = request.get_json() if request.is_json else {}
            inicio = data.get('inicio', 2800)
            fim = data.get('fim')
            
            resultado = importar_concursos_megasena(inicio, fim)
            
            return https_fn.Response(json.dumps(resultado), status=200, headers=headers)
        except ValueError as ve:
            return https_fn.Response(json.dumps({'erro': str(ve)}), status=400, headers=headers)
        except Exception as e:
            return https_fn.Response(json.dumps({'status': 'error', 'erro': str(e)}), status=500, headers=headers)
    
    elif path == '/megasena/historico':
        if not firebase_available:
            return https_fn.Response(json.dumps({'erro': 'Firebase não está disponível neste ambiente'}), status=503, headers=headers)
        
        try:
            limite = request.args.get('limite', 10)
            limite = int(limite) if limite else 10
            resultados = obter_historico_megasena(limite)
            
            # Usar diretamente o conteúdo já serializado em obter_historico_megasena
            return https_fn.Response(
                json.dumps(resultados), 
                status=200, 
                headers=headers
            )
        except TypeError as te:
            # Capturar erros específicos de serialização JSON
            if "not JSON serializable" in str(te):
                return https_fn.Response(
                    json.dumps({
                        'status': 'error', 
                        'erro': 'Erro na serialização dos dados do Firestore. Detalhes: ' + str(te)
                    }), 
                    status=500, 
                    headers=headers
                )
            return https_fn.Response(json.dumps({'status': 'error', 'erro': str(te)}), status=500, headers=headers)
        except Exception as e:
            return https_fn.Response(
                json.dumps({
                    'status': 'error', 
                    'erro': str(e),
                    'tipo': str(type(e).__name__)
                }), 
                status=500, 
                headers=headers
            )
    
    elif path == '/megasena/ultimos_sorteios':
        try:
            ultimos_n = request.args.get('ultimos', 10)
            ultimos_n = int(ultimos_n) if ultimos_n else 10
            resultado = obter_ultimos_sorteios(ultimos_n)
            return https_fn.Response(json.dumps(resultado), status=200, headers=headers)
        except Exception as e:
            return https_fn.Response(json.dumps({"erro": str(e)}), status=500, headers=headers)
    
    # Rota não encontrada
    return https_fn.Response(json.dumps({'error': 'Endpoint não encontrado'}), status=404, headers=headers)

    """
    Wrapper para executar a função com o functions-framework local.
    Esta função converte uma requisição Flask para o formato do Firebase Functions.
    """
    # Implementar adapter para a função Firebase
    class FirebaseFunctionsRequestAdapter(https_fn.Request):
        def __init__(self, flask_request):
            self.flask_request = flask_request
            
        @property
        def method(self):
            return self.flask_request.method
            
        @property
        def path(self):
            return self.flask_request.path
            
        @property
        def query_string(self):
            return self.flask_request.query_string
            
        @property
        def args(self):
            return self.flask_request.args
            
        def get_json(self, *args, **kwargs):
            return self.flask_request.get_json(*args, **kwargs)
            
        @property
        def is_json(self):
            return self.flask_request.is_json
    
    # Criar um adaptador de requisição
    firebase_request = FirebaseFunctionsRequestAdapter(request)
    
    # Chamar a função original
    response = firebase_api_handler(firebase_request)
    
    # Converter a resposta do Firebase Functions para Flask
    return response.body, response.status_code, response.headers 