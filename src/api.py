# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify
from json import dumps
import importlib.util
import sys
from src.services.megasena_service import (
    obter_resultado_via_scraping,
    obter_resultado_api,
    obter_estatisticas,
    executar_scraping,
    importar_concursos_megasena,
    obter_historico_megasena,
    obter_ultimos_sorteios
)
from src.services.firebase_service import FirebaseService

api = Flask(__name__)

# Inicializar o serviço Firebase
firebase_available = FirebaseService.is_available()
if firebase_available:
    print("Firebase inicializado com sucesso!")
else:
    print("Firebase não está disponível neste ambiente")

@api.route("/", methods=['GET'])
def working():
    return 'Api working well'

@api.route("/megasena", methods=['GET'])
def getresult():
    res = obter_resultado_via_scraping()
    return dumps(res, indent=2)

@api.route("/megasena/api", methods=['GET'])
def get_megasena_api():
    """Endpoint para obter dados da Megasena da API oficial da Caixa."""
    try:
        # Verificar se foi informado um número de concurso
        concurso = request.args.get('concurso')
        resultado = obter_resultado_api(concurso)
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({"erro": str(ve)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@api.route("/megasena/estatisticas", methods=['GET'])
def get_megasena_estatisticas():
    """Endpoint para obter estatísticas da Megasena."""
    try:
        # Verificar se foi informado o número de concursos a analisar
        ultimos_n = request.args.get('ultimos', 10)
        estatisticas = obter_estatisticas(ultimos_n)
        return jsonify(estatisticas)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@api.route("/firebase-scraping", methods=['POST'])
def firebase_scraping():
    """Endpoint para iniciar um scraping e salvar no Firebase."""
    if not firebase_available:
        return jsonify({
            'error': 'Firebase não está disponível neste ambiente'
        }), 503
    
    try:
        # Obter parâmetros da requisição
        data = request.get_json() if request.is_json else {}
        url = data.get('url')
        opcoes = data.get('opcoes')
        
        resultado = executar_scraping(url, opcoes)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@api.route("/megasena/importar", methods=['POST'])
def importar_megasena():
    """Endpoint para importar vários concursos da Megasena e armazenar no Firebase."""
    if not firebase_available:
        return jsonify({
            'erro': 'Firebase não está disponível neste ambiente'
        }), 503
    
    try:
        # Obter parâmetros da requisição
        data = request.get_json() if request.is_json else {}
        inicio = data.get('inicio', 2800)
        fim = data.get('fim')
        
        resultado = importar_concursos_megasena(inicio, fim)
        
        return jsonify(resultado)
    except ValueError as ve:
        return jsonify({'erro': str(ve)}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'erro': str(e)
        }), 500

@api.route("/megasena/historico", methods=['GET'])
def historico_megasena():
    """Endpoint para obter o histórico de resultados da Megasena salvos no Firebase."""
    if not firebase_available:
        return jsonify({
            'erro': 'Firebase não está disponível neste ambiente'
        }), 503
    
    try:
        # Obter parâmetros
        limite = request.args.get('limite', 10)
        resultados = obter_historico_megasena(limite)
        return jsonify(resultados)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'erro': str(e)
        }), 500

@api.route("/megasena/ultimos_sorteios", methods=['GET'])
def get_megasena_ultimos_sorteios():
    """Endpoint para obter os números sorteados dos últimos concursos da Megasena."""
    try:
        # Verificar se foi informado o número de concursos a analisar
        ultimos_n = request.args.get('ultimos', 10)
        resultado = obter_ultimos_sorteios(ultimos_n)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if (__name__ == '__main__'):
    port = os.environ.get("PORT", 5000) #Heroku will set the PORT environment variable for web traffic
    api.run(debug=False, host="0.0.0.0", port=port) #set debug=False before deployment