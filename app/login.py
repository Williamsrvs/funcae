from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_chave_de_dev_aleatoria')

#Configuração MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'auth-db1937.hstgr.io')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'u799109175_db_funcae')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Q1k2v1y5@2025')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'u799109175_db_funcae')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Rota para exibir e processar o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Processa POST de login
    email = request.form['email']
    senha = request.form['senha']

    # Verifica se o usuário existe no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("SELECT senha, tipo_usuario FROM tbl_user WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        senha_hash, tipo_usuario = user
        # Verifica se a senha está correta
        if check_password_hash(senha_hash, senha):
            if tipo_usuario == 'Administrador':
                session['user_email'] = email  # Salva o e-mail na sessão
                flash('Login bem-sucedido!', 'success')
                return redirect(url_for('admin'))  # Redireciona para a tela de admin
            else:
                flash('Acesso permitido apenas para administradores.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Senha incorreta.', 'danger')
    else:
        flash('Usuário não encontrado.', 'danger')

    return redirect(url_for('login.html'))

# Rota principal (index)
@app.route('/')
def raiz():
    return render_template('index.html')

# Rota para a tela de admin
@app.route('/home')
def admin():
    if 'user_email' not in session:
        flash('Faça login para acessar esta página.', 'danger')
        return redirect(url_for('login'))
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Remove o e-mail da sessão
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))
