from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
#from flask_restful import Resource, Api
from json import dumps

app = Flask(__name__)

@app.route("/", methods=['GET'])
def working():
    return "A aplicação está rodando!"