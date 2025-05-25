# -*- coding: utf-8 -*-
"""
Firebase Scraper
Classe para gerenciar operações de scraping e armazenamento no Firebase
"""

import os
import time
import uuid
from datetime import datetime
import firebase_admin
from firebase_admin import firestore
from src.megasena_api import MegasenaAPI

class FirebaseScraper:
    """Classe para gerenciar operações de scraping e armazenamento no Firestore."""
    
    def __init__(self):
        """Inicializa a conexão com o Firestore."""
        self.db = firestore.client()
        self.collection_scraping = self.db.collection('scraping_results')
        self.collection_status = self.db.collection('scraping_status')
        self.collection_megasena = self.db.collection('megasena_resultados')
    
    def atualizar_status(self, status, metadados=None):
        """Atualiza o status de um processo de scraping no Firestore."""
        try:
            doc_ref = self.collection_status.document('ultimo_status')
            
            dados = {
                'status': status,
                'timestamp': datetime.now(),
                'metadados': metadados or {}
            }
            
            doc_ref.set(dados)
            return True
        except Exception as e:
            print(f"Erro ao atualizar status: {str(e)}")
            return False
    
    def salvar_resultado(self, url, conteudo, metadados=None):
        """Salva o resultado de um scraping no Firestore."""
        try:
            # Gerar um ID único para o documento
            doc_id = str(uuid.uuid4())
            
            # Preparar dados para armazenar
            dados = {
                'url': url,
                'conteudo': conteudo,
                'timestamp': datetime.now(),
                'metadados': metadados or {}
            }
            
            # Salvar no Firestore
            doc_ref = self.collection_scraping.document(doc_id)
            doc_ref.set(dados)
            
            return doc_id
        except Exception as e:
            print(f"Erro ao salvar resultado: {str(e)}")
            raise
    
    def executar_scraping(self, url=None, opcoes=None):
        """Executa um scraping e salva o resultado no Firestore."""
        try:
            # Atualizar status para 'running'
            self.atualizar_status('running', {
                'url': url,
                'opcoes': opcoes
            })
            
            # Simular um processo de scraping (implementação completa necessitaria de um scraper real)
            # Em um caso real, aqui seria chamado o código de scraping
            resultado = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'dados': {'mensagem': 'Simulação de scraping realizada com sucesso'}
            }
            
            # Salvar resultado no Firestore
            doc_id = self.salvar_resultado(
                url=url or 'scraping_generico',
                conteudo=resultado,
                metadados={
                    'opcoes': opcoes,
                    'fonte': 'firebase_function'
                }
            )
            
            # Atualizar status para 'complete'
            self.atualizar_status('complete', {
                'url': url,
                'doc_id': doc_id,
                'sucesso': True
            })
            
            return {
                'status': 'success',
                'doc_id': doc_id,
                'resultado': resultado
            }
        except Exception as e:
            # Atualizar status para 'error'
            self.atualizar_status('error', {
                'url': url,
                'erro': str(e)
            })
            
            raise Exception(f"Erro ao executar scraping: {str(e)}")
    
    def importar_concursos_megasena(self, inicio=2800, fim=None):
        """Importa vários concursos da Megasena e armazena no Firestore."""
        try:
            # Inicializar API da Megasena
            megasena_api = MegasenaAPI()
            
            # Se não foi especificado o fim, pegar o último concurso
            if fim is None:
                ultimo_concurso = megasena_api.obter_concurso()
                fim = ultimo_concurso.get('numero', inicio + 10)
            
            # Garantir que inicio <= fim
            if inicio > fim:
                inicio, fim = fim, inicio
            
            # Atualizar status para 'running'
            self.atualizar_status('running', {
                'tipo': 'importacao_megasena',
                'inicio': inicio,
                'fim': fim
            })
            
            # Importar cada concurso
            resultados = []
            for num_concurso in range(inicio, fim + 1):
                try:
                    dados = megasena_api.obter_resultado_formatado(num_concurso)
                    
                    # Salvar no Firestore
                    doc_id = self.salvar_resultado(
                        url=f"megasena/concurso/{num_concurso}",
                        conteudo=dados,
                        metadados={
                            'fonte': 'api_caixa',
                            'concurso': num_concurso
                        }
                    )
                    
                    resultados.append({
                        'concurso': num_concurso,
                        'doc_id': doc_id,
                        'sucesso': True
                    })
                    
                    # Aguardar um pouco para não sobrecarregar a API
                    time.sleep(0.5)
                except Exception as e:
                    resultados.append({
                        'concurso': num_concurso,
                        'sucesso': False,
                        'erro': str(e)
                    })
            
            # Atualizar status para 'complete'
            self.atualizar_status('complete', {
                'tipo': 'importacao_megasena',
                'inicio': inicio,
                'fim': fim,
                'total_sucesso': sum(1 for r in resultados if r.get('sucesso')),
                'total_erro': sum(1 for r in resultados if not r.get('sucesso'))
            })
            
            return {
                'status': 'success',
                'total': len(resultados),
                'inicio': inicio,
                'fim': fim,
                'resultados': resultados
            }
        except Exception as e:
            # Atualizar status para 'error'
            self.atualizar_status('error', {
                'tipo': 'importacao_megasena',
                'inicio': inicio,
                'fim': fim,
                'erro': str(e)
            })
            
            raise Exception(f"Erro ao importar concursos da Megasena: {str(e)}")
    
    def obter_historico_megasena(self, limite=10):
        """Obtém o histórico de resultados da Megasena salvos no Firestore."""
        try:
            # Consultar o Firestore
            query = (self.collection_scraping
                    .where('metadados.fonte', '==', 'api_caixa')
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limite))
            
            resultados = []
            for doc in query.stream():
                dados = doc.to_dict()
                dados['id'] = doc.id
                resultados.append(dados)
            
            return resultados
        except Exception as e:
            print(f"Erro ao obter histórico da Megasena: {str(e)}")
            raise 