import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json
from src.services.firebase_service import FirebaseService

class MegasenaAPI:
    """
    Classe para interagir com a API oficial da Megasena da Caixa.
    Implementada usando o padrão Singleton para garantir uma única instância.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MegasenaAPI, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa a configuração da API."""
        self.base_url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def _buscar_concurso_no_firestore(self, numero_concurso: Optional[int]) -> Optional[Dict[str, Any]]:
        """
        Tenta buscar os dados do concurso no Firestore.
        
        Args:
            numero_concurso: Número do concurso a ser buscado.
            
        Returns:
            Dicionário com os dados do concurso ou None se não encontrar.
        """
        if not FirebaseService.is_available():
            return None
            
        try:
            # Se não foi especificado um concurso, vamos buscar o último
            if numero_concurso is None:
                # Buscar o histórico de concursos ordenados por data de sorteio decrescente
                resultados = FirebaseService.buscar_historico_concursos_ordenado(limite=1)
                if resultados and len(resultados) > 0:
                    # O primeiro resultado deve ser o concurso mais recente
                    resultado = resultados[0]
                    if 'conteudo' in resultado and isinstance(resultado['conteudo'], dict):
                        numero_concurso_encontrado = resultado['conteudo'].get('concurso')
                        print(f"Concurso mais recente (número {numero_concurso_encontrado}) obtido do Firestore ordenado por data")
                        return resultado['conteudo']
            else:
                # Buscar um concurso específico com filtro direto na consulta
                # Usar o método buscar_concurso_por_numero do FirebaseService
                resultado = self._buscar_concurso_por_numero(numero_concurso)
                if resultado and 'conteudo' in resultado:
                    print(f"Concurso {numero_concurso} obtido do Firestore com filtro direto")
                    return resultado['conteudo']
        except Exception as e:
            print(f"Erro ao buscar concurso no Firestore: {str(e)}")
            
        return None
        
    def _buscar_concurso_por_numero(self, numero_concurso: int) -> Optional[Dict[str, Any]]:
        """
        Busca um concurso específico no Firestore usando filtro na consulta.
        
        Args:
            numero_concurso: Número do concurso a ser buscado.
            
        Returns:
            Dicionário com os dados do concurso ou None se não encontrar.
        """
        if not FirebaseService.is_available():
            return None
            
        try:
            # Verificar se o firebase_scraper está disponível
            firebase_scraper = FirebaseService.get_instance()
            if not firebase_scraper or not hasattr(firebase_scraper, 'db'):
                return None
                
            # Usar a nova sintaxe recomendada para evitar o warning
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            # Tentar buscar com filtro no conteudo.concurso
            query1 = (firebase_scraper.db.collection('scraping_results')
                     .where(filter=FieldFilter('conteudo.concurso', '==', numero_concurso))
                     .limit(1))
            
            docs1 = query1.get()
            for doc in docs1:
                data = doc.to_dict()
                return {
                    'id': doc.id,
                    'conteudo': data.get('conteudo', {}),
                    'metadados': data.get('metadados', {})
                }
            
            # Se não encontrou, tentar buscar com filtro nos metadados
            query2 = (firebase_scraper.db.collection('scraping_results')
                     .where(filter=FieldFilter('metadados.concurso', '==', numero_concurso))
                     .limit(1))
            
            docs2 = query2.get()
            for doc in docs2:
                data = doc.to_dict()
                return {
                    'id': doc.id,
                    'conteudo': data.get('conteudo', {}),
                    'metadados': data.get('metadados', {})
                }
                
            # Se não encontrou em nenhum dos dois, retornar None
            return None
        except Exception as e:
            print(f"Erro ao buscar concurso {numero_concurso} com filtro: {str(e)}")
            return None
    
    def _obter_concurso_da_api(self, numero_concurso: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém os dados de um concurso específico ou do último concurso diretamente da API da Caixa.
        
        Args:
            numero_concurso: Número do concurso a ser consultado. Se None, retorna o último concurso.
            
        Returns:
            Dicionário com os dados do concurso.
            
        Raises:
            Exception: Se houver erro na requisição ou processamento.
        """
        try:
            # Se não foi especificado um concurso, usamos uma string vazia para obter o último
            concurso_param = str(numero_concurso) if numero_concurso is not None else ""
            url = f"{self.base_url}/{concurso_param}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Levanta exceção para status de erro
            
            dados = response.json()
            
            # Salvar no Firestore se disponível
            if FirebaseService.is_available():
                try:
                    conteudo_formatado = self.formatar_resultado(dados)
                    FirebaseService.salvar_resultado(
                        url=f"megasena/concursos/{numero_concurso if numero_concurso else 'ultimo'}",
                        conteudo=conteudo_formatado,
                        metadados={
                            'fonte': 'api_caixa',
                            'concurso': dados.get('numero'),
                            'data_obtencao': datetime.now().isoformat()
                        }
                    )
                    print(f"Concurso {dados.get('numero')} salvo no Firestore")
                except Exception as e:
                    print(f"Erro ao salvar concurso no Firestore: {str(e)}")
            
            return dados
        except requests.RequestException as e:
            raise Exception(f"Erro ao obter dados do concurso: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Erro ao processar resposta da API (formato JSON inválido)")
    
    def obter_concurso(self, numero_concurso: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém os dados de um concurso específico ou do último concurso.
        Primeiro tenta buscar no Firestore, e se não encontrar, busca na API da Caixa.
        
        Args:
            numero_concurso: Número do concurso a ser consultado. Se None, retorna o último concurso.
            
        Returns:
            Dicionário com os dados do concurso.
            
        Raises:
            Exception: Se houver erro na requisição ou processamento.
        """
        # Primeiro, tenta buscar no Firestore
        resultado_firestore = self._buscar_concurso_no_firestore(numero_concurso)
        if resultado_firestore:
            # Verificar se os dados estão no formato esperado pela API
            # Se não estiverem, pode ser necessário converter para o formato bruto da API
            return self._converter_para_formato_api(resultado_firestore)
        
        # Se não encontrou no Firestore, busca na API
        print(f"Buscando concurso {numero_concurso if numero_concurso else 'mais recente'} na API da Caixa")
        return self._obter_concurso_da_api(numero_concurso)
    
    def _converter_para_formato_api(self, dados_formatados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados formatados de volta para o formato bruto da API, se necessário.
        Isso é útil quando os dados vêm do Firestore no formato já processado.
        
        Args:
            dados_formatados: Dados no formato processado/formatado
            
        Returns:
            Dados no formato bruto da API
        """
        # Verificar se os dados já estão no formato bruto da API
        if 'listaDezenas' in dados_formatados:
            return dados_formatados
            
        # Se estiver no formato formatado, converter para o formato bruto
        # Esta é uma conversão aproximada, pois nem todos os campos podem estar presentes
        try:
            # Converter data de string para formato dd/mm/yyyy
            data_sorteio = None
            data_proximo = None
            
            if dados_formatados.get('data_sorteio'):
                try:
                    dt = datetime.strptime(dados_formatados['data_sorteio'], "%Y-%m-%d")
                    data_sorteio = dt.strftime("%d/%m/%Y")
                except:
                    pass
                    
            if dados_formatados.get('data_proximo_concurso'):
                try:
                    dt = datetime.strptime(dados_formatados['data_proximo_concurso'], "%Y-%m-%d")
                    data_proximo = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Criar estrutura para premiações
            lista_rateio = []
            premiacao = dados_formatados.get('premiacao', {})
            
            for descricao, dados in premiacao.items():
                lista_rateio.append({
                    'descricaoFaixa': descricao,
                    'numeroDeGanhadores': dados.get('ganhadores', 0),
                    'valorPremio': dados.get('premio_individual', 0.0)
                })
            
            # Criar estrutura para cidades ganhadoras
            lista_municipios = []
            cidades = dados_formatados.get('cidades_ganhadoras', [])
            
            for cidade in cidades:
                lista_municipios.append({
                    'municipio': cidade.get('cidade', ''),
                    'uf': cidade.get('uf', ''),
                    'ganhadores': cidade.get('ganhadores', 0)
                })
            
            # Montar estrutura no formato da API
            return {
                'numero': dados_formatados.get('concurso'),
                'dataApuracao': data_sorteio,
                'dataProximoConcurso': data_proximo,
                'listaDezenas': dados_formatados.get('dezenas', []),
                'dezenasSorteadasOrdemSorteio': dados_formatados.get('dezenas_ordem_sorteio', []),
                'listaRateioPremio': lista_rateio,
                'listaMunicipioUFGanhadores': lista_municipios,
                'acumulado': dados_formatados.get('acumulado', False),
                'valorArrecadado': dados_formatados.get('valor_arrecadado', 0.0),
                'valorEstimadoProximoConcurso': dados_formatados.get('valor_estimado_proximo_concurso', 0.0),
                'valorAcumuladoProximoConcurso': dados_formatados.get('valor_acumulado_proximo_concurso', 0.0),
                'localSorteio': dados_formatados.get('local_sorteio', '')
            }
        except Exception as e:
            print(f"Erro ao converter formato: {str(e)}")
            # Se houver erro na conversão, retornar os dados originais
            return dados_formatados
    
    def formatar_resultado(self, dados_concurso: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata os dados do concurso em um formato mais amigável.
        
        Args:
            dados_concurso: Dados brutos do concurso da API
            
        Returns:
            Dicionário formatado com os dados mais relevantes
        """
        try:
            # Processar premiações
            premiacao = {}
            for faixa in dados_concurso.get("listaRateioPremio", []):
                descricao = faixa.get("descricaoFaixa", "")
                premiacao[descricao] = {
                    "ganhadores": faixa.get("numeroDeGanhadores", 0),
                    "premio_individual": faixa.get("valorPremio", 0.0)
                }
            
            # Processar cidades ganhadoras
            cidades_ganhadoras = []
            for cidade in dados_concurso.get("listaMunicipioUFGanhadores", []):
                cidades_ganhadoras.append({
                    "cidade": cidade.get("municipio", ""),
                    "uf": cidade.get("uf", ""),
                    "ganhadores": cidade.get("ganhadores", 0)
                })
            
            # Formatação das datas (convertendo de string para datetime)
            data_sorteio = None
            data_proximo = None
            
            try:
                if dados_concurso.get("dataApuracao"):
                    data_sorteio = datetime.strptime(dados_concurso["dataApuracao"], "%d/%m/%Y")
                
                if dados_concurso.get("dataProximoConcurso"):
                    data_proximo = datetime.strptime(dados_concurso["dataProximoConcurso"], "%d/%m/%Y")
            except ValueError:
                # Em caso de erro no formato da data, mantemos como None
                pass
            
            # Montagem do resultado formatado
            resultado = {
                "concurso": dados_concurso.get("numero"),
                "data_sorteio": data_sorteio.strftime("%Y-%m-%d") if data_sorteio else None,
                "data_proximo_concurso": data_proximo.strftime("%Y-%m-%d") if data_proximo else None,
                "dezenas": dados_concurso.get("listaDezenas", []),
                "dezenas_ordem_sorteio": dados_concurso.get("dezenasSorteadasOrdemSorteio", []),
                "premiacao": premiacao,
                "cidades_ganhadoras": cidades_ganhadoras,
                "acumulado": dados_concurso.get("acumulado", False),
                "valor_arrecadado": dados_concurso.get("valorArrecadado", 0.0),
                "valor_estimado_proximo_concurso": dados_concurso.get("valorEstimadoProximoConcurso", 0.0),
                "valor_acumulado_proximo_concurso": dados_concurso.get("valorAcumuladoProximoConcurso", 0.0),
                "local_sorteio": dados_concurso.get("localSorteio", ""),
                "local_gps": f"{dados_concurso.get('nomeMunicipioUFSorteio', '')}"
            }
            
            return resultado
        except Exception as e:
            raise Exception(f"Erro ao formatar dados: {str(e)}")
    
    def obter_resultado_formatado(self, numero_concurso: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém e formata os dados de um concurso.
        
        Args:
            numero_concurso: Número do concurso a ser consultado. Se None, retorna o último concurso.
            
        Returns:
            Dicionário formatado com os dados do concurso.
        """
        dados_brutos = self.obter_concurso(numero_concurso)
        return self.formatar_resultado(dados_brutos)
    
    def obter_ultimo_resultado(self) -> Dict[str, Any]:
        """
        Obtém e formata os dados do último concurso.
        
        Returns:
            Dicionário formatado com os dados do último concurso.
        """
        return self.obter_resultado_formatado()
    
    def obter_estatisticas(self, ultimos_n_concursos: int = 10) -> Dict[str, Any]:
        """
        Obtém estatísticas dos últimos N concursos.
        
        Args:
            ultimos_n_concursos: Número de concursos para analisar
            
        Returns:
            Dicionário com estatísticas sobre os sorteios
        """
        try:
            # Validar o parâmetro
            try:
                ultimos_n_concursos = int(ultimos_n_concursos)
                if ultimos_n_concursos <= 0:
                    ultimos_n_concursos = 10
            except (ValueError, TypeError):
                ultimos_n_concursos = 10
                
            # Primeiro obtemos o número do último concurso
            ultimo_concurso = self.obter_concurso()
            numero_ultimo = ultimo_concurso.get("numero", 0)
            
            # Tentar buscar estatísticas já calculadas no Firestore
            if FirebaseService.is_available():
                try:
                    # Usar o método específico para buscar estatísticas com filtros precisos
                    resultado = FirebaseService.buscar_estatisticas_megasena(
                        url="megasena_estatisticas",
                        ultimo_concurso=numero_ultimo,
                        ultimos_n_concursos=ultimos_n_concursos
                    )
                    
                    # Se encontrou resultado
                    if resultado and 'conteudo' in resultado:
                        print(f"Estatísticas encontradas no Firestore para os últimos {ultimos_n_concursos} concursos e concurso {numero_ultimo}")
                        
                        # Converter para o formato esperado pela aplicação
                        estatisticas_salvas = resultado['conteudo']
                        
                        # Verificar se tem o formato esperado
                        if (isinstance(estatisticas_salvas, dict) and 
                            'periodo' in estatisticas_salvas and 
                            'dezenas_mais_sorteadas' in estatisticas_salvas and
                            'dezenas_menos_sorteadas' in estatisticas_salvas):
                            
                            # Converter dezenas para o formato [(dezena, frequencia), ...]
                            dezenas_mais = []
                            for item in estatisticas_salvas.get('dezenas_mais_sorteadas', []):
                                if isinstance(item, dict) and 'dezena' in item and 'frequencia' in item:
                                    dezenas_mais.append((item['dezena'], item['frequencia']))
                                
                            dezenas_menos = []
                            for item in estatisticas_salvas.get('dezenas_menos_sorteadas', []):
                                if isinstance(item, dict) and 'dezena' in item and 'frequencia' in item:
                                    dezenas_menos.append((item['dezena'], item['frequencia']))
                            
                            # Montar estatísticas no formato esperado
                            return {
                                "concursos_analisados": estatisticas_salvas.get('total_concursos', 0),
                                "periodo": estatisticas_salvas.get('periodo', {}),
                                "dezenas_mais_sorteadas": dezenas_mais,
                                "dezenas_menos_sorteadas": dezenas_menos,
                                "total_ganhadores": estatisticas_salvas.get('total_ganhadores', {})
                            }
                except Exception as e:
                    print(f"Erro ao buscar estatísticas no Firestore: {str(e)}")
            
            # Se não encontrou no Firestore ou ocorreu erro, calcular novamente
            print(f"Calculando estatísticas para os últimos {ultimos_n_concursos} concursos")
            
            # Calculamos o número do primeiro concurso a analisar
            primeiro_concurso = max(1, numero_ultimo - ultimos_n_concursos + 1)
            
            # Inicializamos contadores
            frequencia_dezenas = {str(i).zfill(2): 0 for i in range(1, 61)}
            total_ganhadores = {
                "6 acertos": 0,
                "5 acertos": 0,
                "4 acertos": 0
            }
            
            # Coletamos dados dos concursos
            concursos_analisados = []
            for num_concurso in range(primeiro_concurso, numero_ultimo + 1):
                try:
                    # Usar a função obter_concurso, que agora tenta primeiro no Firestore
                    dados = self.obter_concurso(num_concurso)
                    concursos_analisados.append(num_concurso)
                    
                    # Contabiliza frequência das dezenas
                    for dezena in dados.get("listaDezenas", []):
                        if dezena in frequencia_dezenas:
                            frequencia_dezenas[dezena] += 1
                    
                    # Contabiliza ganhadores
                    for faixa in dados.get("listaRateioPremio", []):
                        descricao = faixa.get("descricaoFaixa", "")
                        if descricao in total_ganhadores:
                            total_ganhadores[descricao] += faixa.get("numeroDeGanhadores", 0)
                except Exception as e:
                    print(f"Erro ao obter concurso {num_concurso}: {str(e)}")
                    # Se houver erro em um concurso específico, continuamos para o próximo
                    continue
            
            # Ordenamos as dezenas por frequência (decrescente)
            dezenas_mais_sorteadas = sorted(
                [(dezena, freq) for dezena, freq in frequencia_dezenas.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Montamos as estatísticas
            estatisticas = {
                "concursos_analisados": len(concursos_analisados),
                "periodo": {
                    "primeiro_concurso": min(concursos_analisados) if concursos_analisados else None,
                    "ultimo_concurso": max(concursos_analisados) if concursos_analisados else None
                },
                "dezenas_mais_sorteadas": dezenas_mais_sorteadas[:10],
                "dezenas_menos_sorteadas": dezenas_mais_sorteadas[-10:],
                "total_ganhadores": total_ganhadores
            }
            
            # Salvar estatísticas no Firestore, se disponível
            if FirebaseService.is_available():
                try:
                    FirebaseService.salvar_resultado(
                        url="megasena_estatisticas",
                        conteudo={
                            "periodo": estatisticas["periodo"],
                            "total_concursos": estatisticas["concursos_analisados"],
                            "dezenas_mais_sorteadas": [{"dezena": d[0], "frequencia": d[1]} for d in estatisticas["dezenas_mais_sorteadas"]],
                            "dezenas_menos_sorteadas": [{"dezena": d[0], "frequencia": d[1]} for d in estatisticas["dezenas_menos_sorteadas"]],
                            "total_ganhadores": estatisticas["total_ganhadores"]
                        },
                        metadados={
                            'fonte': 'analise_interna', 
                            'ultimos_concursos': ultimos_n_concursos,
                            'ultimo_concurso': numero_ultimo,
                            'data_analise': datetime.now().isoformat()
                        }
                    )
                    print(f"Estatísticas salvas no Firestore")
                except Exception as e:
                    print(f"Erro ao salvar estatísticas no Firestore: {str(e)}")
            
            return estatisticas
        except Exception as e:
            raise Exception(f"Erro ao calcular estatísticas: {str(e)}")


# Exemplo de uso:
if __name__ == "__main__":
    megasena = MegasenaAPI()
    
    # Obtém dados do último concurso
    ultimo = megasena.obter_ultimo_resultado()
    print(f"Último concurso: {ultimo['concurso']}")
    print(f"Data: {ultimo['data_sorteio']}")
    print(f"Dezenas: {', '.join(ultimo['dezenas'])}")
    
    # Verifica se há ganhadores
    if ultimo['premiacao'].get('6 acertos', {}).get('ganhadores', 0) > 0:
        print(f"Houve {ultimo['premiacao']['6 acertos']['ganhadores']} ganhador(es) da sena!")
        print(f"Prêmio individual: R$ {ultimo['premiacao']['6 acertos']['premio_individual']:,.2f}")
    else:
        print("Não houve ganhadores da sena.")
        print(f"Valor acumulado: R$ {ultimo['valor_acumulado_proximo_concurso']:,.2f}")
    
    # Obtém estatísticas dos últimos 10 concursos
    estatisticas = megasena.obter_estatisticas(10)
    print("\nEstatísticas dos últimos concursos:")
    print(f"Dezenas mais sorteadas: {estatisticas['dezenas_mais_sorteadas'][:5]}")
    print(f"Dezenas menos sorteadas: {estatisticas['dezenas_menos_sorteadas'][:5]}") 