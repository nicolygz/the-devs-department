from flask import Flask, render_template

app = Flask(__name__)

@app.route('/home.html')
def home():
    return render_template('home.html')

@app.route('/visao-geral')
def geral():
    return render_template('visao-geral.html')

@app.route('/lista-vereadores')
def lista_vereadores():
    return render_template('lista-vereadores.html')

@app.route('/vereador')
def pagina_vereador():
    return render_template('vereador.html')

if __name__ == "__main__":
    app.run(debug=True)