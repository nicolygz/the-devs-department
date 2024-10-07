from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'  # or your MySQL server IP
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pedro'
app.config['MYSQL_DATABASE'] = 'vereadoresDB'

# Create a MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DATABASE']
    )
    return connection

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/visao-geral')
def geral():
    return render_template('visao-geral.html')

@app.route('/lista-vereadores')
def lista_vereadores():
    
   # Get a database connection
    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute a query to fetch vereadores
    cursor.execute('SELECT * FROM vereadores')  # Replace 'vereadores' with your actual table name
    vereadores = cursor.fetchall()

    # Clean up
    cursor.close()
    connection.close()

    print(f"vereadores")

    # Pass the vereadores data to the template
    return render_template("lista-vereadores.html", vereadores = vereadores)

@app.route('/vereador')
def pagina_vereador():
    return render_template('vereador.html')

@app.route('/pagina-proposicao')
def pagVer():
    return render_template('pagina-proposicao.html')

@app.route('/proposicoes')
def listProp():
    return render_template('filtro.html')

if __name__ == "__main__":
    app.run(debug=True)