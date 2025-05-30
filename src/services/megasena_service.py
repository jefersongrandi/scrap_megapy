# -*- coding: utf-8 -*-
from src.scrap import getResultMegasenaScrapping
from src.megasena_api import MegasenaAPI
import json
from datetime import datetime
from google.cloud import firestore
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from src.services.firebase_service import FirebaseService, FirestoreEncoder

def obter_resultado_via_scraping():
    """Obtém o resultado da Megasena via scraping."""
    res = getResultMegasenaScrapping()
    
    # Se o Firebase estiver disponível, salvar o resultado no Firestore
    if FirebaseService.is_available():
        try:
            # Atualizar status para 'running'
            FirebaseService.atualizar_status('running', {'tipo': 'megasena'})
            
            # Salvar resultado no Firestore
            FirebaseService.salvar_resultado(
                url='https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx',
                conteudo=res,
                metadados={'fonte': 'api_endpoint'}
            )
            
            # Atualizar status para 'complete'
            FirebaseService.atualizar_status('complete', {
                'tipo': 'megasena',
                'sucesso': True
            })
        except Exception as e:
            # Registrar erro, mas não interromper o fluxo
            print(f"Erro ao integrar com Firebase: {str(e)}")
    
    return res

def obter_resultado_api(concurso=None):
    """Obtém dados da Megasena da API oficial da Caixa."""
    # Inicializar API da Megasena
    megasena_api = MegasenaAPI()
    
    # Verificar se foi informado um número de concurso
    if concurso:
        try:
            concurso = int(concurso)
            resultado = megasena_api.obter_resultado_formatado(concurso)
        except ValueError:
            raise ValueError("Número de concurso inválido")
    else:
        resultado = megasena_api.obter_ultimo_resultado()
    
    # Salvar resultado no Firebase, se disponível
    if FirebaseService.is_available():
        try:
            FirebaseService.salvar_resultado(
                url=f"https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/{concurso if concurso else ''}",
                conteudo=resultado,
                metadados={'fonte': 'api_caixa', 'endpoint': '/megasena/api'}
            )
        except Exception as e:
            print(f"Erro ao salvar resultado no Firebase: {str(e)}")
    
    return resultado

def obter_estatisticas(ultimos_n=10):
    """Obtém estatísticas da Megasena."""
    # Validar o parâmetro
    try:
        ultimos_n = int(ultimos_n)
        if ultimos_n <= 0:
            ultimos_n = 10
    except (ValueError, TypeError):
        ultimos_n = 10
    
    # Inicializar API da Megasena
    megasena_api = MegasenaAPI()
    
    # Obter estatísticas
    estatisticas = megasena_api.obter_estatisticas(ultimos_n)
    
    # # Salvar estatísticas no Firebase, se disponível
    # if FirebaseService.is_available():
    #     try:
    #         FirebaseService.salvar_resultado(
    #             url="estatisticas_megasena",
    #             conteudo=estatisticas,
    #             metadados={'fonte': 'analise_interna', 'ultimos_concursos': ultimos_n}
    #         )
    #     except Exception as e:
    #         print(f"Erro ao salvar estatísticas no Firebase: {str(e)}")
    
    return estatisticas

def executar_scraping(url=None, opcoes=None):
    """Executa um scraping e salva no Firebase."""
    if not FirebaseService.is_available():
        raise Exception('Firebase não está disponível neste ambiente')
    
    # Definir URL padrão se não fornecida
    if not url:
        url = 'https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx'
    
    # Executar scraping e salvar no Firebase
    resultado = FirebaseService.executar_scraping(url=url, opcoes=opcoes)
    
    return resultado

def importar_concursos_megasena(inicio=2800, fim=None):
    """Importa vários concursos da Megasena e armazena no Firebase."""
    if not FirebaseService.is_available():
        raise Exception('Firebase não está disponível neste ambiente')
    
    # Validar parâmetros
    try:
        inicio = int(inicio)
        if fim is not None:
            fim = int(fim)
    except ValueError:
        raise ValueError('Parâmetros inválidos (devem ser números)')
    
    # Executar importação
    resultado = FirebaseService.importar_concursos_megasena(inicio, fim)
    
    return resultado

def obter_historico_megasena(limite=10):
    """Obtém o histórico de resultados da Megasena armazenados no Firebase."""
    if not FirebaseService.is_available():
        raise ValueError("Firebase não está disponível")
    
    # Obter os resultados e validar o limite
    try:
        limite = int(limite)
    except ValueError:
        limite = 10
        
    resultados = FirebaseService.obter_historico_megasena(limite)
    
    # Processar os resultados para garantir que todos os dados são serializáveis
    resultados_processados = []
    for resultado in resultados:
        # Limpar tipos de dados que podem causar problemas
        resultado_limpo = {}
        for chave, valor in resultado.items():
            # Remover campos que podem conter objetos não serializáveis
            if chave in ['_firestore_client', '_reference', '_document_snapshot']:
                continue
                
            # Converter timestamps para strings ISO
            if isinstance(valor, (datetime, DatetimeWithNanoseconds)):
                resultado_limpo[chave] = valor.isoformat()
            # Processar metadados se for um dicionário
            elif chave == 'metadados' and isinstance(valor, dict):
                resultado_limpo[chave] = {}
                for k, v in valor.items():
                    if isinstance(v, (datetime, DatetimeWithNanoseconds)):
                        resultado_limpo[chave][k] = v.isoformat()
                    else:
                        resultado_limpo[chave][k] = v
            # Outros valores são mantidos como estão
            else:
                resultado_limpo[chave] = valor
                
        resultados_processados.append(resultado_limpo)
    
    # Usar o encoder personalizado para lidar com os tipos restantes
    try:
        resultados_json = json.dumps(resultados_processados, cls=FirestoreEncoder)
        resultados_serializaveis = json.loads(resultados_json)
    except TypeError as e:
        # Se ainda houver erro, fazer serialização mais agressiva
        resultados_str = str(resultados_processados)
        return {
            'status': 'warning',
            'mensagem': f'Serialização de emergência aplicada devido a: {str(e)}',
            'resultados': resultados_str
        }
    
    return {
        'status': 'success',
        'total': len(resultados_serializaveis),
        'resultados': resultados_serializaveis
    }

def obter_ultimos_sorteios(ultimos_n=10):
    """Obtém os números sorteados dos últimos concursos da Megasena."""
    # Inicializar API da Megasena
    megasena_api = MegasenaAPI()
    
    # Verificar se foi informado o número de concursos a analisar
    try:
        ultimos_n = int(ultimos_n)
        if ultimos_n <= 0:
            ultimos_n = 10
    except (ValueError, TypeError):
        ultimos_n = 10
    
    # Obter o último concurso para determinar o intervalo
    ultimo_concurso = megasena_api.obter_concurso()
    numero_ultimo = ultimo_concurso.get("numero", 0)
    
    # Calcular o número do primeiro concurso a analisar
    primeiro_concurso = max(1, numero_ultimo - ultimos_n + 1)
    
    # Obter concursos já salvos no Firestore (para evitar duplicação)
    concursos_existentes = {}
    if FirebaseService.is_available():
        try:
            # Buscar documentos que possuem o atributo metadados.concurso
            from google.cloud.firestore_v1.base_query import FieldFilter
            db = FirebaseService.get_instance().db
            
            # Para cada concurso no intervalo desejado, verificar se já existe
            for num_concurso in range(primeiro_concurso, numero_ultimo + 1):
                # Buscar por documentos onde metadados.concurso == num_concurso
                query = db.collection('scraping_results').where(
                    filter=FieldFilter('metadados.concurso', '==', num_concurso)
                ).limit(1)
                
                docs = list(query.get())
                if docs:
                    # Se encontrou o documento, armazena o ID
                    concursos_existentes[num_concurso] = docs[0].id
                    print(f"Concurso {num_concurso} já existe no Firestore com ID {docs[0].id}")
        except Exception as e:
            print(f"Erro ao verificar concursos existentes: {str(e)}")
    
    # Coletar dados dos concursos
    ultimos_sorteios = []
    for num_concurso in range(primeiro_concurso, numero_ultimo + 1):
        try:
            if num_concurso in concursos_existentes:
                # Se o concurso já existe, obter do Firestore
                try:
                    if FirebaseService.is_available():
                        doc_ref = db.collection('scraping_results').document(concursos_existentes[num_concurso])
                        doc = doc_ref.get()
                        
                        if doc.exists and 'conteudo' in doc.to_dict():
                            print(f"Obtendo concurso {num_concurso} do Firestore")
                            ultimos_sorteios.append(doc.to_dict()['conteudo'])
                        else:
                            print(f"Documento do concurso {num_concurso} existe, mas faltam dados. Obtendo da API...")
                            obter_e_adicionar_concurso(megasena_api, num_concurso, ultimos_sorteios, salvar=False)
                except Exception as e:
                    print(f"Erro ao obter concurso {num_concurso} do Firestore: {str(e)}")
                    # Fallback para API
                    obter_e_adicionar_concurso(megasena_api, num_concurso, ultimos_sorteios, salvar=False)
            else:
                # Se o concurso não existe, obter da API e salvar
                obter_e_adicionar_concurso(megasena_api, num_concurso, ultimos_sorteios, salvar=True)
        except Exception as e:
            print(f"Erro ao processar concurso {num_concurso}: {str(e)}")
    
    # Ordenar por número do concurso (decrescente)
    ultimos_sorteios.sort(key=lambda x: x.get('concurso', 0), reverse=True)
    
    return {
        'status': 'success',
        'total': len(ultimos_sorteios),
        'ultimos_n': ultimos_n,
        'sorteios': ultimos_sorteios
    }

def obter_e_adicionar_concurso(megasena_api, num_concurso, ultimos_sorteios, salvar=False):
    """
    Função auxiliar para obter um concurso da API e opcionalmente salvá-lo.
    
    Args:
        megasena_api: Instância da API da Megasena
        num_concurso: Número do concurso a obter
        ultimos_sorteios: Lista onde adicionar o sorteio
        salvar: Se True, salva o resultado no Firestore
    """
    print(f"Obtendo concurso {num_concurso} da API...")
    try:
        dados = megasena_api.obter_resultado_formatado(num_concurso)
        
        # Extrair apenas as informações relevantes
        sorteio = {
            'concurso': dados.get('concurso'),
            'data_sorteio': dados.get('data_sorteio'),
            'dezenas': dados.get('dezenas', []),
            'premio_acumulado': dados.get('valor_acumulado_proximo_concurso', 0.0)
        }
        
        # Adicionar o sorteio à lista
        ultimos_sorteios.append(sorteio)
        
        # Salvar no Firestore, se solicitado
        if salvar and FirebaseService.is_available():
            print(f"Verificando se o concurso {num_concurso} já existe antes de salvar...")
            try:
                from google.cloud.firestore_v1.base_query import FieldFilter
                db = FirebaseService.get_instance().db
                
                # Verificar se o concurso já existe
                query = db.collection('scraping_results').where(
                    filter=FieldFilter('metadados.concurso', '==', num_concurso)
                ).limit(1)
                
                docs = list(query.get())
                if not docs:
                    # Se não existe, salvar
                    print(f"Concurso {num_concurso} não existe no Firestore. Salvando...")
                    doc_id = FirebaseService.salvar_resultado(
                        url=f"ultimos_sorteios/megasena/{num_concurso}",
                        conteudo=sorteio,
                        metadados={
                            'fonte': 'api_caixa', 
                            'endpoint': '/megasena/ultimos_sorteios',
                            'concurso': num_concurso
                        }
                    )
                    print(f"Concurso {num_concurso} salvo com ID {doc_id}")
                else:
                    print(f"Concurso {num_concurso} já existe no Firestore com ID {docs[0].id}, não será salvo novamente")
            except Exception as e:
                print(f"Erro ao verificar/salvar concurso {num_concurso} no Firestore: {str(e)}")
    except Exception as e:
        print(f"Erro ao obter concurso {num_concurso} da API: {str(e)}")
        return None
    
    return sorteio 