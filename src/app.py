# -*- coding: utf-8 -*-
"""
Módulo de compatibilidade para permitir que o Gunicorn carregue a aplicação via src.app
Este módulo importa e reexporta a aplicação Flask de api.py
"""

from src.api import api

# Exportar a aplicação Flask para ser usada pelo Gunicorn
app = api

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0") 