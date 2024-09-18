from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/pagina-proposicao.html')
def pagVer():
    return render_template('pagina-proposicao.html')

@app.route('/proposicoes.html')
def listProp():
    return render_template('proposicoes.html')

if __name__ == "__main__":
    app.run(debug=True)