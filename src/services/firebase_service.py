# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from google.cloud import firestore
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

class FirestoreEncoder(json.JSONEncoder):
    """
    Classe para serializar objetos do Firestore para JSON.
    """
    def default(self, obj):
        # Lidar com objetos datetime e DatetimeWithNanoseconds
        if isinstance(obj, (datetime, DatetimeWithNanoseconds)):
            return obj.isoformat()
            
        # Lidar com referências do Firestore
        if hasattr(obj, 'id') and hasattr(obj, 'path') and callable(getattr(obj, 'get', None)):
            return {
                'id': obj.id,
                'path': obj.path,
                'reference_type': str(type(obj).__name__)
            }
            
        # Lidar com GeoPoint
        if hasattr(obj, 'latitude') and hasattr(obj, 'longitude'):
            return {'latitude': obj.latitude, 'longitude': obj.longitude}
        
        # Lidar com collections e outros iteráveis específicos do Firestore
        if hasattr(obj, '_data') and isinstance(obj._data, dict):
            return dict(obj._data)
            
        # Lidar com outros tipos de dados
        try:
            return dict(obj)
        except (TypeError, ValueError):
            try:
                return list(obj)
            except (TypeError, ValueError):
                try:
                    return str(obj)
                except Exception:
                    return None
                    
        return super().default(obj)

class FirebaseService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação do padrão Singleton para garantir uma única instância do serviço."""
        if cls._instance is None:
            cls._instance = cls._initialize_service()
        return cls._instance
    
    @classmethod
    def _initialize_service(cls):
        """Inicializa o serviço Firebase se disponível."""
        # Verificar se o Firebase deve ser desativado via variável de ambiente
        disable_firebase = os.environ.get('FLASK_DISABLE_FIREBASE', '').lower() == 'true'
        
        if disable_firebase:
            print("Firebase desativado por configuração (FLASK_DISABLE_FIREBASE=true)")
            return None
            
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Primeiro verificar se já temos uma instância do Firebase inicializada
            try:
                app = firebase_admin.get_app()
                db = firestore.client()
                print("Usando app Firebase existente")
            except ValueError:
                # Se não temos, verificar se estamos no ambiente de Cloud Functions ou local
                is_cloud_functions = os.environ.get('FUNCTION_TARGET') is not None
                
                if is_cloud_functions:
                    # No ambiente de Cloud Functions, usar credenciais implícitas
                    print("Inicializando Firebase no ambiente Cloud Functions")
                    firebase_admin.initialize_app(options={
                        'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'mega-sena-40cff'),
                    })
                    db = firestore.client()
                else:
                    # No ambiente local, usar arquivo de credenciais
                    # Verificar se o arquivo de credenciais existe
                    cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
                    if os.path.exists(cred_path):
                        # Inicializar o Firebase com as credenciais
                        print(f"Inicializando Firebase com credenciais em {cred_path}")
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                        db = firestore.client()
                    else:
                        print("Arquivo de credenciais do Firebase não encontrado")
                        return None
            
            # Criar uma classe simples para representar o serviço Firebase
            class FirebaseScraper:
                def __init__(self):
                    self.db = db
                
                def salvar_resultado(self, url, conteudo, metadados=None):
                    """Salva um resultado no Firestore."""
                    try:
                        # Adicionar timestamp à metadados
                        if metadados is None:
                            metadados = {}
                        
                        metadados['timestamp'] = datetime.now().isoformat()
                        
                        # Criar o documento
                        doc_data = {
                            'url': url,
                            'conteudo': conteudo,
                            'metadados': metadados
                        }
                        
                        # Salvar no Firestore
                        doc_ref = self.db.collection('scraping_results').document()
                        doc_ref.set(doc_data)
                        
                        return {
                            'status': 'success',
                            'id': doc_ref.id,
                            'message': 'Resultado salvo com sucesso'
                        }
                    except Exception as e:
                        print(f"Erro ao salvar no Firestore: {str(e)}")
                        raise
                
                def atualizar_status(self, status, metadados=None):
                    """Atualiza o status de uma operação no Firestore."""
                    try:
                        # Adicionar timestamp à metadados
                        if metadados is None:
                            metadados = {}
                        
                        metadados['timestamp'] = datetime.now().isoformat()
                        
                        # Criar o documento
                        doc_data = {
                            'status': status,
                            'metadados': metadados
                        }
                        
                        # Salvar no Firestore
                        doc_ref = self.db.collection('status').document()
                        doc_ref.set(doc_data)
                        
                        return {
                            'status': 'success',
                            'id': doc_ref.id,
                            'message': 'Status atualizado com sucesso'
                        }
                    except Exception as e:
                        print(f"Erro ao atualizar status no Firestore: {str(e)}")
                        raise
                
                def executar_scraping(self, url, opcoes=None):
                    """Simula a execução de um scraping."""
                    # Este método deveria implementar o scraping real
                    # Aqui estamos apenas simulando
                    return {
                        'status': 'success',
                        'message': 'Scraping executado com sucesso (simulação)',
                        'url': url,
                        'opcoes': opcoes
                    }
                
                def _concurso_ja_existe(self, num_concurso):
                    """
                    Verifica se um concurso já existe no Firestore baseado no número do concurso.
                    
                    Args:
                        num_concurso: Número do concurso a verificar
                        
                    Returns:
                        bool: True se o concurso já existe, False caso contrário
                    """
                    try:
                        from google.cloud.firestore_v1.base_query import FieldFilter
                        
                        collection_ref = self.db.collection('scraping_results')
                        query = collection_ref.where(filter=FieldFilter('metadados.concurso', '==', num_concurso))
                        
                        # Verificar se existe pelo menos um documento
                        docs = query.limit(1).get()
                        return len(docs) > 0
                        
                    except Exception as e:
                        print(f"Erro ao verificar se concurso {num_concurso} já existe: {str(e)}")
                        # Em caso de erro, assumir que não existe para não bloquear a importação
                        return False
                
                def _pular_concurso_existente(self, num_concurso):
                    """
                    Verifica se deve pular o concurso por já existir no banco.
                    
                    Args:
                        num_concurso: Número do concurso
                        
                    Returns:
                        bool: True se deve pular, False se deve processar
                    """
                    if self._concurso_ja_existe(num_concurso):
                        print(f"Concurso {num_concurso} já existe no banco, pulando...")
                        return True
                    return False
                
                def importar_concursos_megasena(self, inicio, fim=None):
                    """
                    Importa concursos da Megasena a partir da API oficial e salva no Firestore.
                    
                    Args:
                        inicio: Número do primeiro concurso a importar
                        fim: Número do último concurso a importar (opcional)
                        
                    Returns:
                        Dicionário com resultados da importação
                    """
                    try:
                        from src.megasena_api import MegasenaAPI
                        
                        # Inicializar API da Megasena
                        megasena_api = MegasenaAPI()
                        
                        # Se fim não for especificado, usar o último concurso disponível
                        if fim is None:
                            ultimo_concurso = megasena_api.obter_concurso()
                            fim = ultimo_concurso.get("numero", inicio + 10)
                        
                        # Validar o intervalo
                        if inicio > fim:
                            return {
                                'status': 'error',
                                'message': 'Número inicial deve ser menor ou igual ao número final'
                            }
                            
                        if fim - inicio > 100:
                            return {
                                'status': 'error',
                                'message': 'Limite máximo de 100 concursos por importação'
                            }
                        
                        # Importar concursos
                        concursos_importados = []
                        concursos_com_erro = []
                        
                        for num_concurso in range(inicio, fim + 1):
                            try:
                                print(f"Importando concurso {num_concurso}...")
                                
                                # Verificar se o concurso já existe antes de processar
                                if self._pular_concurso_existente(num_concurso):
                                    concursos_importados.append({
                                        'concurso': num_concurso,
                                        'status': 'ja_existe',
                                        'id': None
                                    })
                                    continue
                                
                                # Obter dados do concurso
                                dados = megasena_api.obter_resultado_formatado(num_concurso)
                                
                                # Salvar no Firestore
                                resultado = self.salvar_resultado(
                                    url=f"megasena/concursos/{num_concurso}",
                                    conteudo=dados,
                                    metadados={
                                        'fonte': 'api_caixa',
                                        'importacao_automatica': True,
                                        'concurso': num_concurso,
                                        'data_importacao': datetime.now().isoformat()
                                    }
                                )
                                
                                concursos_importados.append({
                                    'concurso': num_concurso,
                                    'id': resultado.get('id')
                                })
                                
                                # Aguardar um pouco para não sobrecarregar a API
                                import time
                                time.sleep(0.5)
                                
                            except Exception as e:
                                print(f"Erro ao importar concurso {num_concurso}: {str(e)}")
                                concursos_com_erro.append({
                                    'concurso': num_concurso,
                                    'erro': str(e)
                                })
                        
                        return {
                            'status': 'success',
                            'importados': len(concursos_importados),
                            'com_erro': len(concursos_com_erro),
                            'concursos': concursos_importados,
                            'erros': concursos_com_erro
                        }
                        
                    except Exception as e:
                        return {
                            'status': 'error',
                            'message': f'Erro ao importar concursos: {str(e)}'
                        }
                
                def obter_historico_megasena(self, limite=10):
                    """
                    Obtém o histórico de concursos da Megasena ordenados por data de sorteio decrescente.
                    """
                    # Reutilizar o método buscar_historico_concursos_ordenado do FirebaseService
                    try:
                        from src.services.firebase_service import FirebaseService
                        resultados = FirebaseService.buscar_historico_concursos_ordenado(limite)
                        
                        if resultados:
                            print(f"Encontrados {len(resultados)} concursos pela função obter_historico_megasena")
                            return resultados
                        
                        # Se não encontrou nada, usar a busca direta
                        print("Tentando busca direta por concursos no Firestore")
                        from google.cloud.firestore_v1.base_query import FieldFilter
                        
                        # Criar a query para buscar documentos onde conteudo.concurso existe
                        collection_ref = self.db.collection('scraping_results')
                        
                        # Primeiro, verificamos se o campo conteudo.concurso existe
                        query = collection_ref.where(filter=FieldFilter('metadados.fonte', '==', 'api_caixa'))
                        
                        # Limitar o número de resultados
                        query = query.limit(limite)
                        
                        # Executar a query
                        docs = query.get()
                        
                        # Processar os resultados
                        resultados = []
                        for doc in docs:
                            data = doc.to_dict()
                            resultados.append({
                                'id': doc.id,
                                'conteudo': data.get('conteudo', {}),
                                'metadados': data.get('metadados', {})
                            })
                        
                        print(f"Encontrados {len(resultados)} concursos com busca alternativa")
                        return resultados
                    except Exception as e:
                        print(f"Erro ao buscar histórico de concursos: {str(e)}")
                        return []
            
            # Criar e retornar a instância
            firebase_scraper = FirebaseScraper()
            print("Firebase inicializado com sucesso!")
            return firebase_scraper
        except Exception as e:
            # Firebase não está disponível ou ocorreu erro na inicialização
            print(f"Erro ao inicializar Firebase: {str(e)}")
            return None
    
    @staticmethod
    def is_available():
        """Verifica se o serviço Firebase está disponível."""
        return FirebaseService.get_instance() is not None
    
    @staticmethod
    def concurso_ja_existe(numero_concurso):
        """
        Verifica se um concurso já existe no Firestore.
        
        Args:
            numero_concurso: Número do concurso a verificar
            
        Returns:
            bool: True se o concurso já existe, False caso contrário
        """
        firebase_instance = FirebaseService.get_instance()
        if firebase_instance is None:
            return False
            
        return firebase_instance._concurso_ja_existe(numero_concurso)
    
    @staticmethod
    def _sanitize_data_for_firestore(data):
        """
        Sanitiza os dados para que possam ser armazenados no Firestore,
        convertendo estruturas complexas e tipos não suportados.
        
        Args:
            data: Dados a serem sanitizados
            
        Returns:
            Dados sanitizados prontos para serem armazenados no Firestore
        """
        # Se for None, retornar None
        if data is None:
            return None
            
        # Se for um tipo básico (string, int, float, bool), retornar como está
        if isinstance(data, (str, int, float, bool)):
            return data
            
        # Se for datetime, converter para string ISO
        if isinstance(data, (datetime, DatetimeWithNanoseconds)):
            return data.isoformat()
            
        # Se for uma lista, sanitizar cada elemento
        if isinstance(data, list):
            return [FirebaseService._sanitize_data_for_firestore(item) for item in data]
            
        # Se for um dicionário, sanitizar cada valor
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # No Firestore, as chaves não podem conter '.', '/', '[', ']', '*', '`'
                sanitized_key = key
                for char in ['.', '/', '[', ']', '*', '`']:
                    sanitized_key = sanitized_key.replace(char, '_')
                    
                sanitized[sanitized_key] = FirebaseService._sanitize_data_for_firestore(value)
            return sanitized
            
        # Para outros tipos, converter para string
        return str(data)
    
    @staticmethod
    def salvar_resultado(url, conteudo, metadados=None):
        """Salva um resultado no Firestore."""
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            raise ValueError("Firebase não está disponível")
        
        # Sanitizar os dados antes de salvar
        conteudo_sanitizado = FirebaseService._sanitize_data_for_firestore(conteudo)
        metadados_sanitizados = FirebaseService._sanitize_data_for_firestore(metadados) if metadados else None
        
        try:
            return firebase_scraper.salvar_resultado(url, conteudo_sanitizado, metadados_sanitizados)
        except Exception as e:
            print(f"Erro ao salvar resultado: {str(e)}")
            # Tentar serializar para JSON e depois deserializar como último recurso
            try:
                json_str = json.dumps(conteudo, cls=FirestoreEncoder)
                conteudo_json = json.loads(json_str)
                return firebase_scraper.salvar_resultado(url, conteudo_json, metadados_sanitizados)
            except Exception as e2:
                raise ValueError(f"Erro ao salvar dados no Firestore após sanitização: {str(e2)}")
    
    @staticmethod
    def atualizar_status(status, metadados=None):
        """Atualiza o status de uma operação no Firestore."""
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            raise ValueError("Firebase não está disponível")
        
        # Sanitizar os metadados antes de atualizar
        metadados_sanitizados = FirebaseService._sanitize_data_for_firestore(metadados) if metadados else None
        
        return firebase_scraper.atualizar_status(status, metadados_sanitizados)
    
    @staticmethod
    def executar_scraping(url, opcoes=None):
        """Executa um scraping e salva no Firebase."""
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            raise ValueError("Firebase não está disponível")
        
        # Sanitizar as opções antes de executar
        opcoes_sanitizadas = FirebaseService._sanitize_data_for_firestore(opcoes) if opcoes else None
        
        return firebase_scraper.executar_scraping(url, opcoes_sanitizadas)
    
    @staticmethod
    def importar_concursos_megasena(inicio, fim=None):
        """Importa vários concursos da Megasena e armazena no Firebase."""
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            raise ValueError("Firebase não está disponível")
        
        return firebase_scraper.importar_concursos_megasena(inicio, fim)
    
    @staticmethod
    def obter_historico_megasena(limite=10):
        """Obtém o histórico de resultados da Megasena armazenados no Firebase."""
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            raise ValueError("Firebase não está disponível")
        
        return firebase_scraper.obter_historico_megasena(limite)
    
    @staticmethod
    def obter_concurso_por_id(documento_id):
        """
        Obtém um concurso específico pelo ID do documento no Firestore.
        
        Args:
            documento_id: ID do documento no Firestore
            
        Returns:
            Dicionário com os dados do concurso ou None se não encontrado
        """
        try:
            # Obter a instância do Firebase
            instance = FirebaseService.get_instance()
            if not instance:
                print("Firebase não está disponível")
                return None
                
            # Obter o documento pelo ID
            doc_ref = instance.db.collection('scraping_results').document(documento_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"Documento com ID {documento_id} não encontrado")
                return None
                
            # Converter para dicionário
            resultado = doc.to_dict()
            resultado['id'] = doc.id
            
            return resultado
        except Exception as e:
            print(f"Erro ao obter concurso por ID {documento_id}: {str(e)}")
            return None
    
    @staticmethod
    def buscar_historico_concursos_ordenado(limite=10):
        """
        Busca o histórico de concursos da Megasena no Firestore,
        filtrando por documentos onde conteudo.concurso existe
        e ordenando por conteudo.data_sorteio de forma decrescente.
        
        Args:
            limite: Número máximo de resultados a retornar
            
        Returns:
            Lista de dicionários com os dados dos concursos
        """
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            return []
            
        try:
            # Verificar se o firebase_scraper tem um cliente Firestore
            if not hasattr(firebase_scraper, 'db') or firebase_scraper.db is None:
                print("FirebaseScraper não possui um cliente Firestore válido")
                return []
            
            # Usar a nova sintaxe recomendada para evitar o warning
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            # Criar a query para filtrar por conteudo.concurso existir e ordenar por data_sorteio
            # Não é possível verificar diretamente se um campo existe no Firestore,
            # então vamos filtrar por documentos onde conteudo.concurso não é nulo
            collection_ref = firebase_scraper.db.collection('scraping_results')
            
            # Primeiro, verificamos se o campo conteudo.concurso existe e não é nulo
            query = collection_ref.where(filter=FieldFilter('conteudo.concurso', '>', 0))
            
            # Ordenar por data_sorteio de forma decrescente
            # Nota: o Firestore só permite ordenar por campos que estão nos filtros ou são simples
            query = query.order_by('conteudo.data_sorteio', direction=firestore.Query.DESCENDING)
            
            # Limitar o número de resultados
            query = query.limit(limite)
            
            # Executar a query
            docs = query.get()
            
            # Processar os resultados
            resultados = []
            for doc in docs:
                data = doc.to_dict()
                resultados.append({
                    'id': doc.id,
                    'conteudo': data.get('conteudo', {}),
                    'metadados': data.get('metadados', {})
                })
            
            print(f"Encontrados {len(resultados)} concursos ordenados por data de sorteio")
            return resultados
        except Exception as e:
            print(f"Erro ao buscar histórico de concursos ordenado: {str(e)}")
            return []
        
    @staticmethod
    def buscar_estatisticas_megasena(url, ultimo_concurso, ultimos_n_concursos):
        """
        Busca estatísticas específicas da Megasena no Firestore baseado em critérios.
        
        Args:
            url: URL do documento a ser buscado (normalmente 'megasena_estatisticas')
            ultimo_concurso: Número do último concurso
            ultimos_n_concursos: Número de concursos analisados
            
        Returns:
            Dicionário com as estatísticas encontradas ou None se não encontrar
        """
        firebase_scraper = FirebaseService.get_instance()
        if not firebase_scraper:
            return None
            
        try:
            # Converter valores para tipos adequados para a comparação
            try:
                ultimo_concurso = int(ultimo_concurso)
            except (ValueError, TypeError):
                pass
                
            try:
                ultimos_n_concursos = int(ultimos_n_concursos)
            except (ValueError, TypeError):
                pass
            
            # Verificar se o FirebaseScraper tem um cliente Firestore
            if not hasattr(firebase_scraper, 'db') or firebase_scraper.db is None:
                print("FirebaseScraper não possui um cliente Firestore válido")
                return None
                
            # Usar o cliente Firestore do firebase_scraper
            # Usando a nova sintaxe recomendada para evitar o warning
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            collection_ref = firebase_scraper.db.collection('scraping_results')
            query = collection_ref.where(filter=FieldFilter('url', '==', url))
            query = query.where(filter=FieldFilter('metadados.ultimo_concurso', '==', ultimo_concurso))
            query = query.where(filter=FieldFilter('metadados.ultimos_concursos', '==', ultimos_n_concursos))
            
            # Executar a query
            docs = query.limit(1).get()
            
            # Processar o resultado
            for doc in docs:
                data = doc.to_dict()
                return {
                    'id': doc.id,
                    'conteudo': data.get('conteudo', {}),
                    'metadados': data.get('metadados', {}),
                    'url': data.get('url', '')
                }
                
            # Se não encontrou nenhum documento
            return None
        except Exception as e:
            print(f"Erro ao buscar estatísticas no Firestore: {str(e)}")
            return None 