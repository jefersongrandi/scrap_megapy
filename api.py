import os
from flask import Flask
from json import dumps
from src.scrap import getResultMegasenaScrapping

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000)) #Heroku will set the PORT environment variable for web traffic

@app.route("/", methods=['GET'])
def working():
    return 'Api working well'

@app.route("/megasena", methods=['GET'])
def getresult():
    res = getResultMegasenaScrapping()
    return dumps(res, indent=2)

if (__name__ == '__main__'):
    app.run(debug=False, host="0.0.0.0", port=port) #set debug=False before deployment