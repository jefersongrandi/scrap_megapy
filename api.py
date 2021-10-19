import os
from flask import Flask
from json import dumps
from src.scrap import getResultMegasenaScrapping

app = Flask(__name__)

@app.route("/", methods=['GET'])
def working():
    res = getResultMegasenaScrapping()
    return dumps(res, indent=2)

#app.run()

if (__name__ == '__main__'):
    port = os.environ.get("PORT", 5000) #Heroku will set the PORT environment variable for web traffic
    app.run(debug=False, host="0.0.0.0", port=port) #set debug=False before deployment