from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,make_response
import json
import os
from datetime import datetime
from flask_mysqldb import MySQL
import pymysql.cursors
import MySQLdb.cursors
from MySQLdb.cursors import DictCursor
from weasyprint import HTML
from io import BytesIO
import pandas as pd
import xlsxwriter
import openpyxl
from flask import send_file
from xhtml2pdf import pisa 
import io
from weasyprint.text.fonts import FontConfiguration
from werkzeug.security import generate_password_hash
import traceback
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from functools import wraps
import mysql.connector


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_chave_de_dev_aleatoria')

class ServidorForm(FlaskForm):
    nome = StringField('Nome da Conexão', validators=[DataRequired()])
    hostname = StringField('Hostname', validators=[DataRequired()])
    db_base = StringField('Banco de Dados', validators=[DataRequired()])
    port = StringField('Porta', validators=[DataRequired()])
    user = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Salvar Servidor')

@app.route('/service_control', methods=['GET', 'POST'])
def service_control():
    form = ServidorForm()
    mensagem = None

    if form.validate_on_submit():
        # use dados do WTForms
        nome = form.nome.data
        hostname = form.hostname.data
        db_base = form.db_base.data
        port = form.port.data
        user = form.user.data
        password = form.password.data

        # 1) criar tabela (sem hardcode de schema) e 2) inserir
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_controle_servico (
                    id_servico INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    hostname VARCHAR(150) NOT NULL,
                    db_base VARCHAR(100) NOT NULL,
                    port VARCHAR(10) NOT NULL,
                    user VARCHAR(50) NOT NULL,
                    `password` VARCHAR(255) NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO tbl_controle_servico
                (nome, hostname, db_base, port, user, `password`)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nome, hostname, db_base, port, user, password))
            mysql.connection.commit()
            mensagem = "✅ Servidor cadastrado com sucesso!"
        except Exception as e:
            mysql.connection.rollback()
            mensagem = f"❌ Erro: {str(e)}"
        finally:
            try:
                cursor.close()
            except: 
                pass    

    return render_template('service_control.html', form=form, mensagem=mensagem)

#Configuração MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'auth-db1937.hstgr.io')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'u799109175_db_funcae')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Q1k2v1y5@2025')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'u799109175_db_funcae')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


mysql = MySQL(app)
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Processa POST de login
    email = request.form['email']
    senha = request.form['senha']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, senha, tipo_acesso FROM tbl_cad_usuarioslogin WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        # Verifica a senha (texto puro) - substituir por hash em produção
        if user['senha'] == senha:
            session['email'] = email
            session['tipo_acesso'] = user['tipo_acesso']
            flash('Login bem-sucedido!', 'success')
        
            return redirect(url_for('home'))
        else:
            flash('Senha incorreta.', 'danger')
    else:
        flash('Usuário não encontrado.', 'danger')
        
    return redirect(url_for('login'))


def acesso_requerido(*tipo_acesso):
    """Decorador para restringir acesso por tipo (ex.: 'Master', 'Pleno')."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'tipo_acesso' not in session:
                flash('Login requerido.', 'danger')
                return redirect(url_for('login'))
            if session.get('tipo_acesso') not in tipo_acesso:
                flash('Acesso não autorizado para o seu tipo de usuário.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/home')
@acesso_requerido('Master', 'Pleno', 'Junior')
def home():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor específico
        
        # Primeiro, vamos ver todos os status únicos na tabela
        cur.execute("SELECT DISTINCT status_aluno FROM tbl_cad_alunos WHERE status_aluno IS NOT NULL")
        status_list = cur.fetchall()
        print(f"Status encontrados na tabela: {status_list}")
        
        # Consulta principal com mais debug
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN TRIM(UPPER(status_aluno)) = 'ATIVO' THEN 1 END) AS alunos_ativos,
                COUNT(CASE WHEN TRIM(UPPER(status_aluno)) = 'INATIVO' THEN 1 END) AS alunos_inativos,
                COUNT(*) AS total_alunos,
                GROUP_CONCAT(DISTINCT CONCAT("'", TRIM(UPPER(status_aluno)), "'")) AS todos_status
            FROM tbl_cad_alunos
        """)
        
        result = cur.fetchone()
        cur.close()
        
        print(f"Resultado da consulta: {result}")
        print(f"Status processados: {result.get('todos_status', 'Nenhum')}")

        # Garantir que os valores não sejam None
        total_alunos = int(result.get('total_alunos') or 0)
        alunos_ativos = int(result.get('alunos_ativos') or 0)
        alunos_inativos = int(result.get('alunos_inativos') or 0)
        
        print(f"Valores finais - Total: {total_alunos}, Ativos: {alunos_ativos}, Inativos: {alunos_inativos}")

    except Exception as e:
        print(f"Erro na consulta: {e}")
        import traceback
        traceback.print_exc()
        total_alunos = alunos_ativos = alunos_inativos = 0

    return render_template(
        'home.html',
        total_alunos=total_alunos,
        alunos_ativos=alunos_ativos,
        alunos_inativos=alunos_inativos
    )


@app.route('/cad_acesso', methods=['GET', 'POST'])
@acesso_requerido('Master')
def cad_acesso():
    if request.method == 'POST':
        # Captura dos dados do formulário
        nome_usuario = request.form.get('nome_usuario')
        email = request.form.get('email')
        dt_nascimento = request.form.get('dt_nascimento')
        senha = request.form.get('senha')
        tipo_acesso = request.form.get('tipo_acesso')
        data_registro = datetime.now().date()

        # Validações básicas
        if not all([nome_usuario, email, dt_nascimento, senha, tipo_acesso]):
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('cad_acesso.html')

        senha_hash = senha

        cursor = None
        try:
            cursor = mysql.connection.cursor()
            
            # Verificar se o email já existe
            cursor.execute("SELECT id FROM tbl_cad_usuarioslogin WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Este email já está cadastrado!', 'error')
                return render_template('cad_acesso.html')
            
            # Inserção corrigida (6 campos, 6 valores)
            cursor.execute("""
                INSERT INTO tbl_cad_usuarioslogin (
                    nome_usuario, email, dt_nascimento, senha, tipo_acesso, data_registro
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (nome_usuario, email, dt_nascimento, senha_hash, tipo_acesso, data_registro))
            
            mysql.connection.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            
            # Redirecionamento baseado no tipo de acesso
            if tipo_acesso == 'Master':
                return redirect(url_for('home'))
            else:
                return redirect(url_for('login'))
                
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'error')
            return render_template('cad_acesso.html')
        finally:
            if cursor:
                cursor.close()

    # Retorna o template para requisições GET
    return render_template('cad_acesso.html')


@app.route('/cad_aluno', methods=['GET', 'POST'])   
@acesso_requerido('Master', 'Pleno', 'Junior')
def cad_aluno():
    if request.method == 'POST':
        nome_aluno = request.form.get('nome_aluno')
        dt_nascimento = request.form.get('dt_nascimento')
        cpf_aluno = request.form.get('cpf_aluno')
        tipo_rede_social = request.form.get('tipo_rede_social')
        rede_social = request.form.get('rede_social')
        genero = request.form.get('genero')
        whatsapp = request.form.get('whatsapp')
        endereco_aluno = request.form.get('endereco_aluno')
        tipo_responsavel = request.form.get('tipo_responsavel')
        nome_pai = request.form.get('nome_pai')
        nome_mae = request.form.get('nome_mae')
        patologia = request.form.get('patologia')
        tipo_educacao = request.form.get('tipo_educacao')
        contato = request.form.get('contato')
        nome_escola = request.form.get('nome_escola')
        turma = request.form.get('turma')
        coordenador_pedagogico = request.form.get('coordenador_pedagogico')
        profissional_AEE = request.form.get('profissional_AEE')
        cod_cid = request.form.get('cod_cid')
        equipe_multidisciplinar = request.form.get('equipe_multidisciplinar')
        status_aluno = request.form.get('status_aluno')
        observacoes = request.form.get('observacoes')
        data_registro = datetime.now().date()

        try:
            cursor = mysql.connection.cursor()
            
            # Debug: verificar dados recebidos
            print(f"Dados recebidos: coordenador_pedagogico = {coordenador_pedagogico}")
            
            # Debug: contar campos e valores
            campos = [nome_aluno, data_registro, dt_nascimento, cpf_aluno, tipo_rede_social, rede_social, genero, whatsapp,endereco_aluno, tipo_responsavel,
                nome_pai, nome_mae, patologia, tipo_educacao, contato, nome_escola, turma,
                coordenador_pedagogico, profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes]
            print(f"Total de valores: {len(campos)}")
            
            cursor.execute("""
                        INSERT INTO tbl_cad_alunos (
                        nome_aluno, dt_nascimento, cpf_aluno,tipo_rede_social, rede_social, genero, whatsapp, endereco_aluno, tipo_responsavel,
                        nome_pai, nome_mae, patologia, tipo_educacao, contato, nome_escola, turma,
                        coordenador_pedagogico, profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,(
                nome_aluno, dt_nascimento, cpf_aluno,tipo_rede_social, rede_social, genero, whatsapp, endereco_aluno, tipo_responsavel,
                nome_pai, nome_mae, patologia, tipo_educacao, contato, nome_escola, turma,
                coordenador_pedagogico, profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes
            ))
            mysql.connection.commit()
            flash('Aluno cadastrado com sucesso!', 'success')
            print("Cadastro realizado com sucesso!")
            
        except Exception as e:
            flash(f'Erro ao cadastrar aluno: {str(e)}', 'error')
            print(f"Erro detalhado: {e}")   
            print(f"Tipo do erro: {type(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if cursor:
                cursor.close()
        return redirect(url_for('cad_aluno'))

    return render_template('cad_aluno.html')

@app.route('/atualizar_aluno', methods=['POST'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def atualizar_aluno():
    if request.method == 'POST':
        matricula_aluno = request.form.get('matricula_aluno')
        
        # Validar se matrícula foi informada
        if not matricula_aluno:
            flash('Matrícula do aluno não informada!', 'error')
            return redirect(url_for('cad_aluno'))
        
        # Capturar todos os dados do formulário
        nome_aluno = request.form.get('nome_aluno')
        dt_nascimento = request.form.get('dt_nascimento')
        cpf_aluno = request.form.get('cpf_aluno')
        tipo_rede_social = request.form.get('tipo_rede_social')
        rede_social = request.form.get('rede_social')
        genero = request.form.get('genero')
        whatsapp = request.form.get('whatsapp')
        endereco_aluno = request.form.get('endereco_aluno')
        tipo_responsavel = request.form.get('tipo_responsavel')
        nome_pai = request.form.get('nome_pai')
        nome_mae = request.form.get('nome_mae')
        patologia = request.form.get('patologia')
        tipo_educacao = request.form.get('tipo_educacao')
        contato = request.form.get('contato')
        nome_escola = request.form.get('nome_escola')
        turma = request.form.get('turma')
        coordenador_pedagogico = request.form.get('coordenador_pedagogico')
        profissional_AEE = request.form.get('profissional_AEE')
        cod_cid = request.form.get('cod_cid')
        equipe_multidisciplinar = request.form.get('equipe_multidisciplinar')
        status_aluno = request.form.get('status_aluno')
        observacoes = request.form.get('observacoes')

        try:
            cursor = mysql.connection.cursor()
            
            cursor.execute("""
                UPDATE tbl_cad_alunos SET
                    nome_aluno = %s,
                    dt_nascimento = %s,
                    cpf_aluno = %s,
                    tipo_rede_social = %s,
                    rede_social = %s,
                    genero = %s,
                    whatsapp = %s,
                    endereco_aluno = %s,
                    tipo_responsavel = %s,
                    nome_pai = %s,
                    nome_mae = %s,
                    patologia = %s,
                    tipo_educacao = %s,
                    contato = %s,
                    nome_escola = %s,
                    turma = %s,
                    coordenador_pedagogico = %s,
                    profissional_AEE = %s,
                    cod_cid = %s,
                    equipe_multidisciplinar = %s,
                    status_aluno = %s,
                    observacoes = %s
                WHERE matricula_aluno = %s
            """, (
                nome_aluno, dt_nascimento, cpf_aluno, tipo_rede_social, rede_social, 
                genero, whatsapp, endereco_aluno, tipo_responsavel, nome_pai, nome_mae, 
                patologia, tipo_educacao, contato, nome_escola, turma, coordenador_pedagogico, 
                profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes,
                matricula_aluno
            ))
            
            mysql.connection.commit()
            
            if cursor.rowcount > 0:
                flash('Dados do aluno atualizados com sucesso!', 'success')
                print(f"Aluno {matricula_aluno} atualizado com sucesso!")
            else:
                flash('Nenhum registro foi atualizado. Verifique a matrícula.', 'warning')
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Erro ao atualizar aluno: {str(e)}', 'error')
            print(f"Erro detalhado: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if cursor:
                cursor.close()
        
        return redirect(url_for('cad_aluno'))
@app.route('/teste_mysql')
def teste_mysql():
    try:
        print("\n=== TESTE CONEXÃO MYSQL ===")
        
        # 1. Verificar se mysql.connection existe
        if not hasattr(mysql, 'connection'):
            return jsonify({
                'erro': True,
                'mensagem': 'Objeto mysql.connection não existe'
            })
        
        print("1. Objeto mysql.connection existe: OK")
        
        # 2. Verificar se a conexão está ativa
        if not mysql.connection:
            return jsonify({
                'erro': True,
                'mensagem': 'mysql.connection é None - sem conexão com banco'
            })
            
        print("2. Conexão não é None: OK")
        
        # 3. Teste mais básico - verificar se consegue conectar
        cursor = mysql.connection.cursor()
        print("3. Cursor criado: OK")
        
        # 4. Teste simples - SELECT 1
        cursor.execute("SELECT 1 as teste")
        resultado = cursor.fetchone()
        print(f"4. SELECT 1 funcionou: {resultado}")
        
        # 5. Mostrar banco de dados atual
        cursor.execute("SELECT DATABASE() as banco_atual")
        banco = cursor.fetchone()
        print(f"5. Banco atual: {banco}")
        
        # 6. Listar tabelas
        cursor.execute("SHOW TABLES")
        tabelas = cursor.fetchall()
        print(f"6. Tabelas encontradas: {tabelas}")
        
        cursor.close()
        
        return jsonify({
            'erro': False,
            'mensagem': 'Conexão MySQL OK',
            'teste_basico': resultado[0] if resultado else None,
            'banco_atual': banco[0] if banco else 'N/A',
            'tabelas': [t[0] for t in tabelas] if tabelas else []
        })
        
    except AttributeError as e:
        print(f"Erro AttributeError: {e}")
        return jsonify({
            'erro': True,
            'tipo': 'AttributeError',
            'mensagem': f'Problema de configuração: {str(e)}',
            'dica': 'Verifique se o MySQL foi inicializado corretamente'
        })
        
    except Exception as e:
        print(f"Erro geral: {e}")
        print(f"Tipo do erro: {type(e).__name__}")
        return jsonify({
            'erro': True,
            'tipo': type(e).__name__,
            'mensagem': str(e),
            'dica': 'Verifique configurações de conexão MySQL'
        })

@app.route('/buscar_aluno')
@acesso_requerido('Master', 'Pleno', 'Junior')
def buscar_aluno():
    try:
        cpf_aluno = request.args.get('cpf_aluno')
        print(f"\n=== BUSCA POR CPF ===")
        print(f"CPF recebido: {cpf_aluno}")
        
        if not cpf_aluno:
            return jsonify({
                'encontrado': False,
                'erro': True,
                'mensagem': 'CPF não informado'
            }), 400

        cpf_limpo = ''.join(filter(str.isdigit, cpf_aluno))
        print(f"CPF limpo: {cpf_limpo}")

        if not mysql.connection:
            return jsonify({
                'encontrado': False,
                'erro': True,
                'mensagem': 'Sem conexão com banco de dados'
            }), 500

        cursor = mysql.connection.cursor()
        print("Cursor criado com sucesso")
        
        # CORREÇÃO: Tratamento robusto do fetchone() para DictCursor
        try:
            cursor.execute("SELECT COUNT(*) FROM tbl_cad_alunos")
            count_result = cursor.fetchone()
            print(f"count_result raw: {count_result} (tipo: {type(count_result)})")
            
            # Verificar se count_result é válido
            if count_result is None:
                print("ERRO: count_result é None")
                cursor.close()
                return jsonify({
                    'encontrado': False,
                    'erro': True,
                    'mensagem': 'Erro ao acessar tabela - resultado None'
                })
            
            # CORREÇÃO: Verificar se é tupla/lista OU dicionário (DictCursor)
            if isinstance(count_result, (tuple, list)) and len(count_result) > 0:
                total = count_result[0]
            elif isinstance(count_result, dict) and 'COUNT(*)' in count_result:
                total = count_result['COUNT(*)']
            else:
                print(f"ERRO: count_result formato inesperado: {count_result}")
                cursor.close()
                return jsonify({
                    'encontrado': False,
                    'erro': True,
                    'mensagem': f'Formato inesperado do resultado: {type(count_result)}'
                })
                
        except Exception as count_error:
            print(f"ERRO na query COUNT: {count_error}")
            cursor.close()
            return jsonify({
                'encontrado': False,
                'erro': True,
                'mensagem': f'Erro ao contar registros: {str(count_error)}'
            })
        
        print(f"Total de registros na tabela: {total}")
        
        if total == 0:
            cursor.close()
            return jsonify({
                'encontrado': False,
                'erro': False,
                'mensagem': 'Nenhum aluno cadastrado no sistema. Cadastre um aluno primeiro.',
                'debug': 'Tabela vazia'
            })
        
        # CORREÇÃO: Tratamento para DictCursor nos CPFs existentes
        try:
            cursor.execute("SELECT cpf_aluno, nome_aluno FROM tbl_cad_alunos LIMIT 3")
            cpfs_existentes = cursor.fetchall()
            print("CPFs existentes na base (primeiros 3):")
            for cpf_ex in cpfs_existentes:
                if isinstance(cpf_ex, dict):
                    print(f"  - CPF: '{cpf_ex['cpf_aluno']}', Nome: {cpf_ex['nome_aluno']}")
                else:
                    print(f"  - CPF: '{cpf_ex[0]}', Nome: {cpf_ex[1]}")
        except Exception as cpf_error:
            print(f"Erro ao buscar CPFs existentes: {cpf_error}")
            cpfs_existentes = []
        
        # Busca exata primeiro
        print(f"\n1. Testando busca exata por: '{cpf_aluno}'")
        try:
            cursor.execute("SELECT nome_aluno, cpf_aluno FROM tbl_cad_alunos WHERE cpf_aluno = %s", (cpf_aluno,))
            resultado_exato = cursor.fetchone()
            print(f"   Resultado busca exata: {resultado_exato}")
        except Exception as e:
            print(f"Erro na busca exata: {e}")
            resultado_exato = None
        
        # Busca por CPF limpo
        print(f"\n2. Testando busca por CPF limpo: '{cpf_limpo}'")
        try:
            cursor.execute("SELECT nome_aluno, cpf_aluno FROM tbl_cad_alunos WHERE REPLACE(REPLACE(REPLACE(cpf_aluno, '.', ''), '-', ''), ' ', '') = %s", (cpf_limpo,))
            resultado_limpo = cursor.fetchone()
            print(f"   Resultado busca limpa: {resultado_limpo}")
        except Exception as e:
            print(f"Erro na busca limpa: {e}")
            resultado_limpo = None
        
        # Se encontrou algum resultado, fazer a busca completa
        if resultado_exato or resultado_limpo:
            print("\n3. Aluno encontrado! Fazendo busca completa...")
            
            try:
                query = """
                    SELECT 
                        id_aluno, matricula_aluno, nome_aluno,
                        dt_nascimento, cpf_aluno, genero, whatsapp, 
                        endereco_aluno, tipo_responsavel, nome_pai, nome_mae, 
                        patologia, tipo_educacao, contato, nome_escola, turma,
                        coordenador_pedagogico, profissional_AEE, cod_cid, 
                        equipe_multidisciplinar, status_aluno, observacoes
                    FROM tbl_cad_alunos 
                    WHERE cpf_aluno = %s OR REPLACE(REPLACE(REPLACE(cpf_aluno, '.', ''), '-', ''), ' ', '') = %s
                """
                
                cursor.execute(query, (cpf_aluno, cpf_limpo))
                aluno = cursor.fetchone()
                
                if aluno:
                    # CORREÇÃO: Tratamento para DictCursor na busca completa
                    if isinstance(aluno, dict):
                        aluno_dict = aluno
                    else:
                        columns = [col[0] for col in cursor.description]
                        aluno_dict = dict(zip(columns, aluno))
                    
                    # Formatar data
                    if aluno_dict.get('dt_nascimento'):
                        if hasattr(aluno_dict['dt_nascimento'], 'strftime'):
                            aluno_dict['dt_nascimento'] = aluno_dict['dt_nascimento'].strftime('%Y-%m-%d')
                        else:
                            aluno_dict['dt_nascimento'] = str(aluno_dict['dt_nascimento'])
                    
                    print(f"   Dados completos encontrados: {list(aluno_dict.keys())}")
                    cursor.close()
                    
                    return jsonify({
                        'encontrado': True,
                        'erro': False,
                        'aluno': aluno_dict,
                        'mensagem': 'Aluno encontrado com sucesso'
                    })
            except Exception as e:
                print(f"Erro na busca completa: {e}")
        
        print("\n4. Nenhum resultado encontrado")
        cursor.close()
        
        # CORREÇÃO: Tratamento para DictCursor no debug final
        return jsonify({
            'encontrado': False,
            'erro': False,
            'mensagem': f'Aluno com CPF {cpf_aluno} não encontrado',
            'debug': {
                'cpfs_existentes': [
                    {'cpf': cpf['cpf_aluno'], 'nome': cpf['nome_aluno']} if isinstance(cpf, dict) 
                    else {'cpf': cpf[0], 'nome': cpf[1]} 
                    for cpf in cpfs_existentes
                ] if cpfs_existentes else [],
                'total_registros': total
            }
        })

    except Exception as e:
        print(f"Erro geral na busca: {str(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        
        try:
            if 'cursor' in locals():
                cursor.close()
        except:
            pass
            
        return jsonify({
            'encontrado': False,
            'erro': True,
            'mensagem': 'Erro interno do servidor',
            'detalhes': str(e)
        }), 500
@app.route('/test_db')
def test_db():
    """Rota para testar a conexão com o banco de dados"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Conexão com banco OK',
            'test_result': result[0]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro na conexão: {str(e)}'
        }), 500


# Rota para listar todas as tabelas (debug)
@app.route('/list_tables')
def list_tables():
    """Rota para listar tabelas do banco (apenas para debug)"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'tables': [table[0] for table in tables]
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# Rota para verificar estrutura da tabela
@app.route('/describe_table')
def describe_table():
    """Rota para verificar estrutura da tabela tbl_cad_alunos"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DESCRIBE tbl_cad_alunos")
        columns = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'columns': [{'field': col[0], 'type': col[1], 'null': col[2], 'key': col[3]} for col in columns]
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/saiba_mais', methods=['GET'])
def saiba_mais():
    return render_template('saiba_mais.html')

@app.route('/quest_pei', methods=['GET', 'POST'])
@acesso_requerido('Master','Pleno')
def quest_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos WHERE status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        cur = None  # Inicializa cursor como None
        try:
            aluno_id = request.form.get('aluno_id')
            
            # Validação básica
            if not aluno_id:
                flash('Por favor, selecione um aluno.', 'danger')
                return render_template('quest_pei.html', alunos=alunos)

            cur = mysql.connection.cursor()

            # 1 - Acompanhamento e avaliação
            cur.execute("""
                INSERT INTO tbl_acompanhamento_avaliacao (
                    aluno_id, frequencia_reavaliacao, responsavel_acompanhamento, reunioes
                ) VALUES (%s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('frequencia_reavaliacao'),
                request.form.get('responsavel_acompanhamento'),
                request.form.get('reunioes')
            ))

            # 2 - Comportamento e Interação
            cur.execute("""
                INSERT INTO tbl_comportamento_interacao_pei (
                    aluno_id, comunicacao, tipo_linguagem, atividades_grupo, comp_desaf, socializacao
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('comunicacao'),
                request.form.get('tipo_linguagem'),
                request.form.get('atividades_grupo'),
                request.form.get('comp_desaf'),
                request.form.get('socializacao')
            ))

            # 3 - Desenvolvimento Geral
            cur.execute("""
                INSERT INTO tbl_desenvolvimento_geral_pei (
                    aluno_id, autonomia, atraso_desenvolvimento, questoes_saude, talentos
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('autonomia'),
                request.form.get('atraso_desenvolvimento'),
                request.form.get('questoes_saude'),
                request.form.get('talentos')
            ))

            # 4 - Estratégia e Adaptações
            cur.execute("""
                INSERT INTO tbl_estrategias_adaptacoes_pei (
                    aluno_id, estrategias, adaptacoes_curriculares, materiais_concretos, avaliacoes
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('estrategias'),
                request.form.get('adaptacoes_curriculares'),
                request.form.get('materiais_concretos'),
                request.form.get('avaliacoes')
            ))

            # 5 - Habilidades Escolares
            cur.execute("""
                INSERT INTO tbl_habilidades_escolares_pei (
                    aluno_id, leitura_escrita, numeros_matematica, interesse_aulas, recursos_aprendizagem, barreiras
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('leitura_escrita'),
                request.form.get('numeros_matematica'),
                request.form.get('interesse_aulas'),
                request.form.get('recursos_aprendizagem'),
                request.form.get('barreiras')
            ))

            # 6 - Necessidade de Apoio
            # Tratamento especial para campo múltiplo
            apoios = request.form.getlist('apoios')  # Use getlist para select múltiplo
            apoios_str = ','.join(apoios) if apoios else None
            
            cur.execute("""
                INSERT INTO tbl_necessidades_apoio_pei (
                    aluno_id, apoios, equipamentos
                ) VALUES (%s, %s, %s)
            """, (
                aluno_id,
                apoios_str,
                request.form.get('equipamentos')
            ))

            # 7 - Objetivos PEI
            cur.execute("""
                INSERT INTO tbl_objetivos_pei (
                    aluno_id, objetivo_cognitivo, objetivo_linguagem, objetivo_autonomia, 
                    objetivo_interacao, objetivo_motor, objetivo_comportamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('objetivo_cognitivo'),
                request.form.get('objetivo_linguagem'),
                request.form.get('objetivo_autonomia'),
                request.form.get('objetivo_interacao'),
                request.form.get('objetivo_motor'),
                request.form.get('objetivo_comportamento')
            ))

            # 8 - Outras Informações
            cur.execute("""
                INSERT INTO tbl_outras_informacoes_pei (
                    aluno_id, historico_escolar, consideracoes_familia, 
                    observacoes_professores, comentarios_equipe
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('historico_escolar'),
                request.form.get('consideracoes_familia'),
                request.form.get('observacoes_professores'),
                request.form.get('comentarios_equipe')
            ))

            # Commit das transações
            mysql.connection.commit()
            cur.close()
            flash('Questionário PEI salvo com sucesso!', 'success')
            return redirect(url_for('quest_pei'))
            
        except Exception as e:
            # Rollback em caso de erros
            mysql.connection.rollback()
            if cur:
                cur.close()
            print(f"Erro detalhado: {str(e)}")  # Para debug
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return render_template('quest_pei.html', alunos=alunos)

    return render_template('quest_pei.html', alunos=alunos)



@app.route('/gerar_pdf_pei', methods=['GET', 'POST'])
@acesso_requerido('Master','Pleno')
def gerar_pdf_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos where status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    aluno_selecionado = None

    if request.method == 'POST':
        id_aluno = request.form.get('id_aluno')
        if id_aluno:
            return redirect(url_for('gerar_pdf_pei', id_aluno=id_aluno))
        else:
            flash('Por favor, selecione um aluno.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))

    id_aluno = request.args.get('id_aluno')
    if id_aluno:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vw_quest_pei WHERE id_aluno = %s", (id_aluno,))
        respostas = cur.fetchone()
        cur.close()

        if not respostas:
            flash('Aluno não encontrado ou sem respostas PEI.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))
        aluno = {
        "id_aluno": respostas.get("id_aluno"),
        "nome_aluno": respostas.get("nome_aluno"),
        "matricula_aluno": respostas.get("matricula_aluno"),
        "dt_nascimento": respostas.get("dt_nascimento")
        }

        html = render_template('relatorio_pdf_pei.html', aluno=aluno, respostas=respostas)
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf)
        if pisa_status.err:
            flash('Erro ao gerar o PDF.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))

        pdf.seek(0)
        nome_aluno = respostas.get("nome_aluno", "Aluno")
        return send_file(
            pdf,
            mimetype='application/pdf',
            download_name=f'Relatorio_PEI_Aluno_{nome_aluno}.pdf',
            as_attachment=False
        )

    return render_template('gerar_pdf_pei.html', alunos=alunos, aluno_selecionado=aluno_selecionado)


@app.route('/pdf_pei', methods=['GET'])
@acesso_requerido('Master','Pleno')
def pdf_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM u799109175_db_funcae.vw_quest_pei")
    dados = cur.fetchall()
    cur.close()

@app.route('/pei_excel', methods=['GET'])
def pei_excel():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT  
	id_aluno,
    matricula_aluno,
    nome_aluno,
    idade,
    id_desenvolvimento,
    autonomia,
    atraso_desenvolvimento,
    questoes_saude,
    talentos,
    id_habilidade,
    leitura_escrita,
    numeros_matematica,
    interesse_aulas,
    recursos_aprendizagem,
    barreiras,
    id_comportamento,
    comunicacao,
    tipo_linguagem,
    atividades_grupo,
    comp_desaf,
    socializacao,
    id_necessidade,
    apoios,
    equipamentos,
    id_estrategia,
    estrategias,
    adaptacoes_curriculares,
    materiais_concretos,
    avaliacoes,
    id_objetivo,
    objetivo_cognitivo,
    objetivo_linguagem,
    objetivo_autonomia,
    objetivo_interacao,
    objetivo_motor,
    objetivo_comportamento,
    id_informe,
    historico_escolar,
    consideracoes_familia,
    observacoes_professores,
    comentarios_equipe,
    id_acomp_av,
    frequencia_reavaliacao,
    responsavel_acompanhamento,
    reunioes
FROM u799109175_db_funcae.vw_quest_pei""")
    dados = cur.fetchall()
    cur.close()

    # Se não vier nenhum dado, retorna mensagem simples
    if not dados:
        return "Nenhum dado para exportar.", 404

    # Cria um DataFrame pandas com os dados retornados
    df = pd.DataFrame(dados)

    # Usa BytesIO para criar arquivo Excel na memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PEI')

    output.seek(0)

    # Retorna o arquivo Excel para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_pei.xlsx'
    )
    

@app.route('/alunos_ativos_excel', methods=['GET'])
@acesso_requerido('Master', 'Pleno')
def alunos_ativos_excel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_cad_alunos WHERE status_aluno = 'Ativo'")
    alunos = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]
    cur.close()

    if not alunos:
        return "Nenhum aluno ativo encontrado.", 404

    df = pd.DataFrame(alunos, columns=colunas)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Alunos Ativos')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='alunos_ativos.xlsx'
    )

@app.route('/baixa_alunos', methods=['GET'])
@acesso_requerido('Master', 'Pleno')
def baixa_alunos():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT id_aluno, matricula_aluno, nome_aluno, dt_nascimento, 
            idade, patologia, status_aluno 
        FROM tbl_cad_alunos
        ORDER BY nome_aluno
    """)
    alunos = cur.fetchall()
    cur.close()

    # Chama as funções de contagem
    total_ativos = get_total_ativos()
    total_inativos = get_total_inativos()

    return render_template(
        'baixa_alunos.html',
        alunos=alunos,
        total_ativos=total_ativos,
        total_inativos=total_inativos
    )

def get_total_ativos():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(*) AS total_ativos FROM tbl_cad_alunos WHERE LOWER(status_aluno) = 'ativo'")
    total_ativos = cur.fetchone()['total_ativos']
    cur.close()
    return total_ativos

def get_total_inativos():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(*) AS total_inativos FROM tbl_cad_alunos WHERE LOWER(status_aluno) = 'inativo'")
    total_inativos = cur.fetchone()['total_inativos']
    cur.close()
    return total_inativos


@app.route('/baixar_aluno/<int:id_aluno>', methods=['POST'])
@acesso_requerido('Master', 'Pleno')
def baixar_aluno(id_aluno):
    try:
        motivo = request.form.get('motivo', '')
        observacoes = request.form.get('observacoes', '')
        data_baixa = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cur = mysql.connection.cursor()
        
        # 1. Atualizar status do aluno para "Inativo"
        cur.execute("""
            UPDATE tbl_cad_alunos 
            SET status_aluno = 'Inativo' 
            WHERE id_aluno = %s
        """, (id_aluno,))
        
        # 2. Inserir registro na tabela de baixas (se existir)
        # Se você não tem essa tabela, pode criar ou comentar esta parte
        try:
            cur.execute("""
                INSERT INTO tbl_baixas_alunos 
                (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_aluno, motivo, observacoes, data_baixa, session.get('user_id', 'Sistema')))
        except Exception as e:
            # Se a tabela não existir, apenas registra no log
            print(f"Aviso: Tabela de baixas não encontrada: {e}")
        
        mysql.connection.commit()
        cur.close()
        
        flash('Aluno dado como baixa com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro ao dar baixa no aluno: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

@app.route('/reativar_aluno/<int:id_aluno>', methods=['POST'])
@acesso_requerido('Master', 'Pleno')
@acesso_requerido('Master','Pleno')
def reativar_aluno(id_aluno):
    try:
        cur = mysql.connection.cursor()
        
        # Reativar aluno
        cur.execute("""
            UPDATE tbl_cad_alunos 
            SET status_aluno = 'Ativo' 
            WHERE id_aluno = %s
        """, (id_aluno,))
        
        # Registrar reativação (opcional)
        try:
            cur.execute("""
                INSERT INTO tbl_baixas_alunos 
                (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_aluno, 'REATIVAÇÃO', 'Aluno reativado no sistema', 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                session.get('user_id', 'Sistema')))
        except:
            pass  # Se não tiver tabela de log, ignora
        
        mysql.connection.commit()
        cur.close()
        
        flash('Aluno reativado com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro ao reativar aluno: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

@app.route('/baixa_lote', methods=['POST'])
@acesso_requerido('Master', 'Pleno')
@acesso_requerido('Master','Pleno','Junior')
def baixa_lote():
    try:
        alunos_ids = request.form.getlist('alunos_ids')
        
        if not alunos_ids:
            flash('Nenhum aluno selecionado!', 'warning')
            return redirect(url_for('baixa_alunos'))
        
        cur = mysql.connection.cursor()
        
        # Baixa em lote
        for aluno_id in alunos_ids:
            cur.execute("""
                UPDATE tbl_cad_alunos 
                SET status_aluno = 'Inativo' 
                WHERE id_aluno = %s AND status_aluno = 'Ativo'
            """, (aluno_id,))
            
            # Log da baixa em lote
            try:
                cur.execute("""
                    INSERT INTO tbl_baixas_alunos 
                    (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (aluno_id, 'BAIXA EM LOTE', 'Baixa realizada em lote', 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    session.get('user_id', 'Sistema')))
            except:
                pass
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'{len(alunos_ids)} aluno(s) dado(s) como baixa com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro na baixa em lote: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

# Rota adicional para criar tabela de log de baixas (opcional)
@app.route('/criar_tabela_baixas')
def criar_tabela_baixas():
    """Rota para criar tabela de log de baixas - use apenas uma vez"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tbl_baixas_alunos (
                id_baixa INT AUTO_INCREMENT PRIMARY KEY,
                aluno_id INT NOT NULL,
                motivo_baixa VARCHAR(100),
                observacoes TEXT,
                data_baixa DATETIME,
                usuario_baixa VARCHAR(50),
                FOREIGN KEY (aluno_id) REFERENCES tbl_cad_alunos(id_aluno)
            )
        """)
        mysql.connection.commit()
        cur.close()
        return "Tabela de baixas criada com sucesso!"
    except Exception as e:
        return f"Erro ao criar tabela: {str(e)}"


@app.route('/quest_pedi', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno')
def quest_pedi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos WHERE status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        try:
            aluno_id = request.form.get('aluno_id')

            # CUIDADO PESSOAL
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO tbl_quest_pedi_cuidadopessoal (
                    alimentacao_talher, mastigacao, ingestao_liquidos, cortar_alimentos, recurso_comer,
                    escovacao_dentes, higiene_maos, papel_higienico, enxugase_banho, lembrete_higiene,
                    vestimenta_camisa, vestimenta_calca, autonomia_ziper_amarras, calcados, diferencia_frente_verso,
                    comunicacao_banheiro, autonomia_vaso_sanitario, acidentes_urina_outros, lavar_maos, supervisao_banheiro,
                    observacoes, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('alimentacao_talher'),
                request.form.get('mastigacao'),
                request.form.get('ingestao_liquidos'),
                request.form.get('cortar_alimentos'),
                request.form.get('recurso_comer'),
                request.form.get('escovacao_dentes'),
                request.form.get('higiene_maos'),
                request.form.get('papel_higienico'),
                request.form.get('enxugase_banho'),
                request.form.get('lembrete_higiene'),
                request.form.get('vestimenta_camisa'),
                request.form.get('vestimenta_calca'),
                request.form.get('autonomia_ziper_amarras'),
                request.form.get('calcados'),
                request.form.get('diferencia_frente_verso'),
                request.form.get('comunicacao_banheiro'),
                request.form.get('autonomia_vaso_sanitario'),
                request.form.get('acidentes_urina_outros'),
                request.form.get('lavar_maos'),
                request.form.get('supervisao_banheiro'),
                request.form.get('observacoes'),
                aluno_id
            ))

            # MOBILIDADE
            cur.execute("""
                INSERT INTO tbl_quest_pedi_mobilidade (
                    senta_sozinho, levanta_cadeira, anda_sozinho, abre_portas, locomocao_escadas, locomocao_terrenos,
                    usa_transporte, empurra_brinquedos, corre_pula, cadeira_rodas, observacoes_mobilidade, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('senta_sozinho'),
                request.form.get('levanta_cadeira'),
                request.form.get('anda_sozinho'),
                request.form.get('abre_portas'),
                request.form.get('locomocao_escadas'),
                request.form.get('locomocao_terrenos'),
                request.form.get('usa_transporte'),
                request.form.get('empurra_brinquedos'),
                request.form.get('corre_pula'),
                request.form.get('cadeira_rodas'),
                request.form.get('observacoes_mobilidade'),
                aluno_id
            ))

            # FUNÇÃO SOCIAL
            cur.execute("""
                INSERT INTO tbl_quest_pedi_funcaosocial (
                    responde_chamado, contato_visual, imita_acoes, participa_brincadeiras, respeita_turnos,
                    fala_palavras, gestos_sinais, pede_ajuda, compreende_instrucoes, expressa_sentimento,
                    guarda_brinquedo, lembra_atividades, cumpre_combinado, escolhe_roupas, demonstra_interesse,
                    observacoes_fun_social, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('responde_chamado'),
                request.form.get('contato_visual'),
                request.form.get('imita_acoes'),
                request.form.get('participa_brincadeiras'),
                request.form.get('respeita_turnos'),
                request.form.get('fala_palavras'),
                request.form.get('gestos_sinais'),
                request.form.get('pede_ajuda'),
                request.form.get('compreende_instrucoes'),
                request.form.get('expressa_sentimento'),
                request.form.get('guarda_brinquedo'),
                request.form.get('lembra_atividades'),
                request.form.get('cumpre_combinado'),
                request.form.get('escolhe_roupas'),
                request.form.get('demonstra_interesse'),
                request.form.get('observacoes_fun_social'),
                aluno_id
            ))

            mysql.connection.commit()
            cur.close()
            flash('Questionário PEDI salvo com sucesso!', 'success')
            return redirect(url_for('quest_pedi'))

        except Exception as e:
            mysql.connection.rollback()
            if cur:
                cur.close()
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return render_template('quest_pedi.html', alunos=alunos)

    return render_template('quest_pedi.html', alunos=alunos)

@app.route('/gerar_pdf_pdi', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def gerar_pdf_pdi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos where status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        id_aluno = request.form.get('id_aluno')
        if id_aluno:
            return redirect(url_for('gerar_pdf_pdi', id_aluno=id_aluno))
        else:
            flash('Por favor, selecione um aluno.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

    id_aluno = request.args.get('id_aluno')
    if id_aluno:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vw_quest_pedi WHERE id_aluno = %s", (id_aluno,))
        respostas = cur.fetchone()
        cur.close()

        if not respostas:
            flash('Aluno não encontrado ou sem respostas PEDI.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

        # Passa todas as respostas diretamente para o template
        html = render_template('relatorio_pdf_pedi.html', respostas=respostas)
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf)
        if pisa_status.err:
            flash('Erro ao gerar o PDF.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

        pdf.seek(0)
        nome_aluno = respostas.get("nome_aluno", "Aluno")
        return send_file(
            pdf,
            mimetype='application/pdf',
            download_name=f'Relatorio_PEDI_Aluno_{nome_aluno}.pdf',
            as_attachment=False
        )

    return render_template('gerar_pdf_pdi.html', alunos=alunos)

#gerando pdf pedi
@app.route('/pdf_pdi', methods=['GET'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def pdf_pdi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM u799109175_db_funcae.vw_quest_pedi")
    dados = cur.fetchall()
    cur.close()

@app.route('/gerar_excel_pdi', methods=['GET'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def gerar_excel_pdi():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT  
        id_aluno,
        matricula_aluno,
        nome_aluno,
        idade,
        id_cuid_pessoal,
        alimentacao_talher,
        mastigacao,
        ingestao_liquidos,
        cortar_alimentos,
        recurso_comer,
        escovacao_dentes,
        higiene_maos,
        papel_higienico,
        enxugase_banho,
        lembrete_higiene,
        vestimenta_camisa,
        vestimenta_calca,
        autonomia_ziper_amarras,
        calcados,
        diferencia_frente_verso,
        comunicacao_banheiro,
        autonomia_vaso_sanitario,
        acidentes_urina_outros,
        lavar_maos,
        supervisao_banheiro,
        observacoes,
        id_mobilidade,
        senta_sozinho,
        levanta_cadeira,
        anda_sozinho,
        abre_portas,
        locomocao_escadas,
        locomocao_terrenos,
        usa_transporte,
        empurra_brinquedos,
        corre_pula,
        cadeira_rodas,
        observacoes_mobilidade,
        id_func_social,
        responde_chamado,
        contato_visual,
        imita_acoes,
        participa_brincadeiras,
        respeita_turnos,
        fala_palavras,
        gestos_sinais,
        pede_ajuda,
        compreende_instrucoes,
        expressa_sentimento,
        guarda_brinquedo,
        lembra_atividades,
        cumpre_combinado,
        escolhe_roupas,
        demonstra_interesse,
        observacoes_fun_social
    FROM u799109175_db_funcae.vw_quest_pedi""")

    dados = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]  # pega nomes das colunas
    cur.close()

    if not dados:
        return "Nenhum dado para exportar.", 404

    # Cria DataFrame com nomes das colunas
    df = pd.DataFrame(dados, columns=colunas)

    # Cria Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PDI')

    output.seek(0)

    # Retorna Excel para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_pdi.xlsx'
    )

@app.route('/manutencao')
def manutencao():
    dados = {
        'titulo': 'Página de Manutenção',
        'data_atual': datetime.now().strftime('%d/%m/%Y')
    }
    return render_template('manutencao.html', **dados)


@app.route('/ficha_matricula', methods=['GET'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def ficha_matricula():
    return render_template('ficha_matricula.html')


@app.route('/relatorio_avaliacao', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno')
def relatorio_avaliacao():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos where status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()
    
    if request.method == 'POST':
        try:
            # Verificar qual ação foi solicitada
            action = request.form.get('action')
            
            # Receber dados do formulário com os nomes corretos do HTML
            aluno_id = request.form.get('id_aluno')
            data_inicio = request.form.get('data_inicio')
            data_fim = request.form.get('data_fim')
            responsavel_av = request.form.get('responsavel_av')
            questionario = request.form.get('questionario')  
            relatorio = request.form.get('relatorio')
            anexo_doc = request.form.get('anexo_doc')
            

            #validar questionario
            validar_questionario = ['PEI', 'PDI', 'GUIDE','OUTROS']
            if questionario not in validar_questionario:
                flash('Selecione um questionário válido.', 'danger')
                return render_template('relatorio_avaliacao.html', alunos=alunos)

            # Validação básica
            if not all([aluno_id, data_inicio, data_fim, responsavel_av, questionario, relatorio]):
                flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
                return render_template('relatorio_avaliacao.html', alunos=alunos)
            
            # VALIDAÇÃO DE TAMANHO DOS CAMPOS DE TEXTO
            # Verificar tamanho do questionário (ajuste conforme sua estrutura de BD)
            if len(questionario) > 5000:  # Ajuste este valor conforme o tamanho da coluna
                flash('Texto do questionário muito longo. Limite: 5000 caracteres.', 'danger')
                return render_template('relatorio_avaliacao.html', alunos=alunos)
            
            # Verificar tamanho do relatório
            if len(relatorio) > 10000:  # Ajuste este valor conforme o tamanho da coluna
                flash('Texto do relatório muito longo. Limite: 10000 caracteres.', 'danger')
                return render_template('relatorio_avaliacao.html', alunos=alunos)
            
            # Verificar tamanho do responsável
            if len(responsavel_av) > 255:  # Comum para campos VARCHAR
                flash('Nome do responsável muito longo. Limite: 255 caracteres.', 'danger')
                return render_template('relatorio_avaliacao.html', alunos=alunos)
            
            # Processamento de arquivo (se houver)
            anexo_doc = None
            if 'anexo_doc' in request.files:
                file = request.files['anexo_doc']
                if file and file.filename:
                    allowed_extensions = {'pdf'}
                    if '.' in file.filename:
                        file_ext = file.filename.rsplit('.', 1)[1].lower()
                        if file_ext in allowed_extensions:
                            file.seek(0, os.SEEK_END)
                            file_size = file.tell()
                            file.seek(0)
                            if file_size > 10 * 1024 * 1024:
                                flash('Arquivo muito grande. Tamanho máximo: 10MB', 'danger')
                                return render_template('relatorio_avaliacao.html', alunos=alunos)
                            anexo_doc = file.read()
                        else:
                            flash('Tipo de arquivo não permitido. Use: PDF', 'danger')
                            return render_template('relatorio_avaliacao.html', alunos=alunos)
            
            # Buscar nome do aluno para salvar junto
            cur = mysql.connection.cursor()
            cur.execute("SELECT nome_aluno FROM tbl_cad_alunos WHERE id_aluno = %s", (aluno_id,))
            aluno = cur.fetchone()
            nome_aluno = aluno['nome_aluno'] if aluno else ''
            
            # TRUNCAR DADOS SE NECESSÁRIO CONFORME ESTRUTURA DO BD
            # nome_aluno: VARCHAR(50) - já tratado acima
            # responsavel_av: VARCHAR(50) - validado acima  
            # questionario: ENUM - validado acima
            # relatorio: LONGTEXT - sem limite prático
            
            if action == 'save':
                # Inserir no banco de dados
                cur.execute("""
                    INSERT INTO tbl_rel_ava_anterior (
                        nome_aluno, data_inicio, data_fim, responsavel_av,
                        questionario, relatorio, anexo_doc, aluno_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nome_aluno,
                    data_inicio,
                    data_fim,
                    responsavel_av,  
                    questionario,      
                    relatorio,
                    anexo_doc,
                    aluno_id
                ))
                
                mysql.connection.commit()
                cur.close()
                
                flash('Relatório de avaliação salvo com sucesso!', 'success')
                return redirect(url_for('relatorio_avaliacao'))
                
            elif action == 'generate_pdf':
                
                cur.execute("""
                    INSERT INTO tbl_rel_ava_anterior (
                        nome_aluno, data_inicio, data_fim, responsavel_av,
                        questionario, relatorio, anexo_doc, aluno_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nome_aluno,
                    data_inicio,
                    data_fim,
                    responsavel_av,
                    questionario,
                    relatorio,
                    anexo_doc,
                    aluno_id
                ))
                
                mysql.connection.commit()
                cur.close()
                
                
                flash('PDF gerado e dados salvos com sucesso!', 'success')
                return redirect(url_for('relatorio_avaliacao'))
            
        except Exception as e:
            mysql.connection.rollback()
            if 'cur' in locals():
                cur.close()
            print(f"Erro ao salvar relatório: {str(e)}")
            flash('Erro ao salvar relatório. Tente novamente.', 'danger')
            return render_template('relatorio_avaliacao.html', alunos=alunos)
    
    return render_template('relatorio_avaliacao.html', alunos=alunos)

# Rota adicional para visualizar relatórios salvos
@app.route('/listar_relatorios')
def listar_relatorios():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                id_relatorio, nome_aluno, data_inicio, data_fim, 
                responsavel_av, questionario, 
                CASE WHEN anexo_doc IS NOT NULL THEN 'Sim' ELSE 'Não' END as tem_anexo,
                aluno_id
            FROM tbl_rel_ava_anterior 
            ORDER BY data_inicio DESC
        """)
        relatorios = cur.fetchall()
        cur.close()
        
        return render_template('listar_relatorios.html', relatorios=relatorios)
    
    except Exception as e:
        flash(f'Erro ao carregar relatórios: {str(e)}', 'danger')
        return redirect(url_for('home'))

# Rota para visualizar um relatório específico
@app.route('/ver_relatorio/<int:id_relatorio>')
def ver_relatorio(id_relatorio):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT * FROM tbl_rel_ava_anterior 
            WHERE id_relatorio = %s
        """, (id_relatorio,))
        relatorio = cur.fetchone()
        cur.close()
        
        if not relatorio:
            flash('Relatório não encontrado.', 'danger')
            return redirect(url_for('listar_relatorios'))
        
        return render_template('ver_relatorio.html', relatorio=relatorio)
    
    except Exception as e:
        flash(f'Erro ao carregar relatório: {str(e)}', 'danger')
        return redirect(url_for('listar_relatorios'))

# Rota para download de anexo
@app.route('/download_anexo/<int:id_relatorio>')
def download_anexo(id_relatorio):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT anexo_doc, nome_aluno FROM tbl_rel_ava_anterior 
            WHERE id_relatorio = %s AND anexo_doc IS NOT NULL
        """, (id_relatorio,))
        resultado = cur.fetchone()
        cur.close()
        
        if not resultado:
            flash('Anexo não encontrado.', 'danger')
            return redirect(url_for('listar_relatorios'))
        
        anexo_doc = resultado['anexo_doc']
        nome_aluno = resultado['nome_aluno']
        
        # Criar resposta com arquivo
        response = make_response(anexo_doc)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename=anexo_relatorio_{nome_aluno}_{id_relatorio}'
        
        return response
    
    except Exception as e:
        flash(f'Erro ao baixar anexo: {str(e)}', 'danger')
        return redirect(url_for('listar_relatorios'))

# Rota para deletar relatório
@app.route('/deletar_relatorio/<int:id_relatorio>', methods=['POST'])
def deletar_relatorio(id_relatorio):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM tbl_rel_ava_anterior WHERE id_relatorio = %s", (id_relatorio,))
        mysql.connection.commit()
        cur.close()
        
        flash('Relatório deletado com sucesso!', 'success')
    
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Erro ao deletar relatório: {str(e)}', 'danger')
    
    return redirect(url_for('listar_relatorios'))


@app.route('/quest_guide', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno')
def quest_guide():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos WHERE status_aluno = 'Ativo' ORDER BY nome_aluno ")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        try:    
            aluno_id = request.form.get('aluno_id')

            # 1. Socialização
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO tbl_socializacao_guide (
                    aluno_id, sorri_amigavel, contato_visual, imita_acoes, brinca_com_criancas, responde_gestos, observacoes_socializacao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('sorri_amigavel'),
                request.form.get('contato_visual'),
                request.form.get('imita_acoes'),
                request.form.get('brinca_com_criancas'),
                request.form.get('responde_gestos'),
                request.form.get('observacoes_socializacao')
            ))

            # 2. Linguagem
            cur.execute("""
                INSERT INTO tbl_linguagem_guide (
                    aluno_id, responde_chamado, emite_sons, usa_gestos, nomeia_objetos, constroi_frases, observacoes_linguagem
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('responde_chamado'),
                request.form.get('emite_sons'),
                request.form.get('usa_gestos'),
                request.form.get('nomeia_objetos'),
                request.form.get('constroi_frases'),
                request.form.get('observacoes_linguagem')
            ))

            # 3. Autocuidado
            cur.execute("""
                INSERT INTO tbl_autocuidado_guide (
                    aluno_id, colher_aboca, bebe_copos, uso_sapatos, avisa_banheiro, escova_dentes, observacoes_autocuidados
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('colher_aboca'),
                request.form.get('bebe_copos'),
                request.form.get('uso_sapatos'),
                request.form.get('avisa_banheiro'),
                request.form.get('escova_dentes'),
                request.form.get('observacoes_autocuidados')
            ))

            # 4. Motricidade Fina
            cur.execute("""
                INSERT INTO tbl_motricidade_guide (
                    aluno_id, pega_objetos, empilha_blocos, encaixa_pecas, recorta_papel, faz_rabiscos, observacoes_motrocidade
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('pega_objetos'),
                request.form.get('empilha_blocos'),
                request.form.get('encaixa_pecas'),
                request.form.get('recorta_papel'),
                request.form.get('faz_rabiscos'),
                request.form.get('observacoes_motrocidade')
            ))

            # 5. Motricidade Global
            cur.execute("""
                INSERT INTO tbl_motroc_global_guide (
                    aluno_id, engatinha, anda_semapoio, corre_controle, sobe_escadas_correto, pula_doispes, observacao_motroc_glob
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('engatinha'),
                request.form.get('anda_semapoio'),
                request.form.get('corre_controle'),
                request.form.get('sobe_escadas_correto'),
                request.form.get('pula_doispes'),
                request.form.get('observacao_motroc_glob')  
            ))

            mysql.connection.commit()
            cur.close()
            flash('Questionário GUIDE salvo com sucesso!', 'success')
            return redirect(url_for('quest_guide'))
        except Exception as e:
            mysql.connection.rollback()
            if 'cur' in locals():
                cur.close()
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return render_template('quest_guide.html', alunos=alunos)

    return render_template('quest_guide.html', alunos=alunos)

@app.route('/gerar_pdf_guide', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno')
def gerar_pdf_guide():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos WHERE status_aluno = 'Ativo' ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        id_aluno = request.form.get('id_aluno')
        if not id_aluno:
            flash('Selecione um aluno.', 'danger')
            return render_template('gerar_pdf_guide.html', alunos=alunos)

        # Busca as respostas do aluno na view
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT * FROM vw_quest_guide WHERE id_aluno = %s
        """, (id_aluno,))
        respostas = cur.fetchone()
        cur.close()

        if not respostas:
            flash('Nenhum registro GUIDE encontrado para este aluno.', 'warning')
            return render_template('gerar_pdf_guide.html', alunos=alunos)

        try:
            # Renderiza o HTML do relatório
            rendered = render_template('relatorio_pdf_guide.html', respostas=respostas)

            # Configurações do WeasyPrint para melhor qualidade
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            
            # CSS adicional para PDF
            css_string = """
            @page {
                size: A4;
                margin: 2cm;
                @bottom-center {
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 10px;
                    color: #666;
                }
            }
            body { 
                font-size: 12px; 
                line-height: 1.4; 
            }
            """
            
            # Gera o PDF com configurações otimizadas
            pdf = BytesIO()
            HTML(string=rendered).write_pdf(
                pdf,
                stylesheets=[CSS(string=css_string)],
                font_config=font_config,
                presentational_hints=True
            )
            pdf.seek(0)
            
            # Nome do arquivo limpo
            nome_aluno_limpo = respostas['nome_aluno'].replace(' ', '_').replace('/', '_')
            nome_arquivo = f"relatorio_guide_{nome_aluno_limpo}.pdf"
            
            return send_file(
                pdf, 
                download_name=nome_arquivo, 
                as_attachment=False,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            flash(f'Erro ao gerar o PDF: {str(e)}', 'danger')
            return render_template('gerar_pdf_guide.html', alunos=alunos)

    return render_template('gerar_pdf_guide.html', alunos=alunos)


@app.route('/gerar_excel_guide', methods=['GET'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def gerar_excel_guide():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT  
        id_aluno,
        matricula_aluno,
        nome_aluno,
        idade,
        id_social,
        sorri_amigavel,
        contato_visual,
        imita_acoes,
        brinca_com_criancas,
        responde_gestos,
        observacoes_socializacao,
        id,
        responde_chamado,
        emite_sons,
        usa_gestos,
        nomeia_objetos,
        constroi_frases,
        observacoes_linguagem,
        id_auto,
        colher_aboca,
        bebe_copos,
        uso_sapatos,
        avisa_banheiro,
        escova_dentes,
        observacoes_autocuidados,
        pega_objetos,
        empilha_blocos,
        encaixa_pecas,
        recorta_papel,
        faz_rabiscos,
        observacoes_motrocidade,
        engatinha,
        anda_semapoio,
        corre_controle,
        sobe_escadas_correto,
        pula_doispes,
        observacao_motroc_glob
    FROM u799109175_db_funcae.vw_quest_guide""")

    dados = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]  # pega nomes das colunas
    cur.close()

    if not dados:
        return "Nenhum dado para exportar.", 404

    # Cria DataFrame com nomes das colunas
    df = pd.DataFrame(dados, columns=colunas)

    # Cria Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='GUIDE')

    output.seek(0)

    # Retorna Excel para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_guide.xlsx'
    )

@app.route('/gerar_avaliacao_pdf/<int:id_relatorio>', methods=['GET'])
@acesso_requerido('Master', 'Pleno')
def gerar_avaliacao_pdf(id_relatorio):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_rel_ava_anterior WHERE id_relatorio = %s", (id_relatorio,))
    respostas = cur.fetchone()
    cur.close()
    
    if not respostas:
        flash('Relatório não encontrado.', 'danger')
        return redirect(url_for('listar_relatorios'))

    try:
        rendered = render_template('relatorio_pdf_avaliacao.html', respostas=respostas)

        font_config = FontConfiguration()
        
        pdf = BytesIO()
        HTML(string=rendered).write_pdf(pdf, font_config=font_config)
        pdf.seek(0)
        
        nome_arquivo = f"avaliacao_{id_relatorio}.pdf"
        return send_file(
            pdf,
            download_name=nome_arquivo,
            as_attachment=False,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('listar_relatorios'))

# Rota para baixar no excel alunos inativos
@app.route('/excel_alunos_inativos', methods=['GET'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def excel_alunos_inativos():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_cad_alunos WHERE status_aluno = 'Inativo'")
    alunos = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]
    cur.close()

    if not alunos:
        return "Nenhum aluno inativo encontrado.", 404

    df = pd.DataFrame(alunos, columns=colunas)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Alunos Inativos')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='alunos_inativos.xlsx'
    )


@app.template_filter('grade_class')
def grade_class_filter(nota):
    """Filtro Jinja para aplicar classes de estilo conforme a nota"""
    try:
        nota = float(nota or 0.0)
    except Exception:
        nota = 0.0
    if nota >= 9.0:
        return 'grade-excellent'
    elif nota >= 7.0:
        return 'grade-good'
    elif nota >= 5.0:
        return 'grade-average'
    else:
        return 'grade-needs-improvement'

@app.route('/dashboard')
@acesso_requerido('Master', 'Pleno')
def dashboard():
    """Rota para exibir o dashboard com dados dos alunos"""
    cursor = None
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        
        # === BUSCAR DADOS DAS VIEWS ===
        cursor.execute("SELECT id_aluno, nome_aluno, ROUND(COALESCE(media_autocuidado,0),1) as media_autocuidado FROM u799109175_db_funcae.vw_boletim_autocuidado;")
        dados_autocuidado = {r['id_aluno']: (r['nome_aluno'], float(r['media_autocuidado'] or 0.0)) for r in cursor.fetchall()}
        
        cursor.execute("SELECT id_aluno, nome_aluno, ROUND(COALESCE(media_linguagem,0),1) as media_linguagem FROM u799109175_db_funcae.vw_boletim_linguagem;")
        dados_linguagem = {r['id_aluno']: (r['nome_aluno'], float(r['media_linguagem'] or 0.0)) for r in cursor.fetchall()}
        
        cursor.execute("SELECT id_aluno, nome_aluno, ROUND(COALESCE(media_socializacao,0),1) as media_socializacao FROM u799109175_db_funcae.vw_boletim_socializacao;")
        dados_socializacao = {r['id_aluno']: (r['nome_aluno'], float(r['media_socializacao'] or 0.0)) for r in cursor.fetchall()}
        
        cursor.execute("SELECT id_aluno, nome_aluno, ROUND(COALESCE(media_motrocidade,0),1) as media_motrocidade FROM u799109175_db_funcae.vw_boletim_motrocidade;")
        dados_motrocidade = {r['id_aluno']: (r['nome_aluno'], float(r['media_motrocidade'] or 0.0)) for r in cursor.fetchall()}
        
        cursor.execute("SELECT id_aluno, nome_aluno, ROUND(COALESCE(media_motrocidade_global,0),1) as media_motrocidade_global FROM u799109175_db_funcae.vw_boletim_motrocidade_global;")
        dados_motrocidade_global = {r['id_aluno']: (r['nome_aluno'], float(r['media_motrocidade_global'] or 0.0)) for r in cursor.fetchall()}
    
        # === Montagem dos alunos ===
        alunos = []
        todas_notas = {
            'autocuidado': [],
            'linguagem': [],
            'socializacao': [],
            'motrocidade': [],
            'motrocidade_global': []
        }
        
        all_ids = set(dados_autocuidado.keys()) \
                | set(dados_linguagem.keys()) \
                | set(dados_socializacao.keys()) \
                | set(dados_motrocidade.keys()) \
                | set(dados_motrocidade_global.keys())
        
        for aluno_id in all_ids:
            nome_aluno = next(
                (d[aluno_id][0] for d in [
                    dados_autocuidado, dados_linguagem, dados_socializacao,
                    dados_motrocidade, dados_motrocidade_global
                ] if aluno_id in d),
                "Aluno não identificado"
            )
            
            # CORREÇÃO: Usar os nomes corretos das variáveis
            auto = dados_autocuidado.get(aluno_id, (None, 0.0))[1]
            ling = dados_linguagem.get(aluno_id, (None, 0.0))[1]
            soc = dados_socializacao.get(aluno_id, (None, 0.0))[1]
            motr = dados_motrocidade.get(aluno_id, (None, 0.0))[1]
            motr_g = dados_motrocidade_global.get(aluno_id, (None, 0.0))[1]
            
            notas_validas = [n for n in [auto, ling, soc, motr, motr_g] if n > 0]
            media_geral = round(sum(notas_validas) / len(notas_validas), 1) if notas_validas else 0.0
            
            alunos.append({
                "id": aluno_id,
                "nome": nome_aluno,
                "autocuidado": auto,          # CORRIGIDO
                "linguagem": ling,            # CORRIGIDO
                "socializacao": soc,          # CORRIGIDO
                "motrocidade": motr,          # CORRIGIDO
                "motrocidade_global": motr_g, # CORRIGIDO
                "media_geral": media_geral
            })
            
            todas_notas['autocuidado'].append(auto)
            todas_notas['linguagem'].append(ling)
            todas_notas['socializacao'].append(soc)
            todas_notas['motrocidade'].append(motr)
            todas_notas['motrocidade_global'].append(motr_g)
        
        # === Cálculo das médias gerais ===
        medias = {k: round(sum(v) / len(v), 1) if v else 0.0 for k, v in todas_notas.items()}
        
        data = {
            "medias": medias,
            "total_alunos": len(alunos),
            "alunos": sorted(alunos, key=lambda x: x['nome'])
        }
        
        print("Resumo enviado ao template -> total_alunos:", data['total_alunos'], "medias:", data['medias'])
        
        return render_template("dashboard.html", data=data)
        
    except Exception as e:
        print("ERRO no dashboard:", e)
        traceback.print_exc()
        
        medias_vazias = {
            "autocuidado": 0.0,
            "linguagem": 0.0,
            "socializacao": 0.0,
            "motrocidade": 0.0,
            "motrocidade_global": 0.0
        }
        
        return render_template("dashboard.html", data={"medias": medias_vazias, "alunos": [], "total_alunos": 0})
        
    finally:
        if cursor:
            cursor.close()


# ADICIONE esta função de filtro personalizado ANTES das rotas
@app.template_filter('grade_class')
def grade_class(grade):
    """Filtro para definir a classe CSS baseada na nota"""
    try:
        grade = float(grade)
        if grade >= 9.0:
            return 'grade-excellent'
        elif grade >= 7.0:
            return 'grade-good'
        elif grade >= 5.0:
            return 'grade-average'
        else:
            return 'grade-needs-improvement'
    except (ValueError, TypeError):
        return 'grade-needs-improvement'

@app.route('/suport', methods=['GET', 'POST'])
@acesso_requerido('Master', 'Pleno', 'Junior')
def suport():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if request.method == 'POST':
            tipo = request.form.get('tipo')
            data_registro = request.form.get('data_registro')
            nome_usuario = request.form.get('nome_usuario')
            descricao = request.form.get('descricao')

            # Captura do arquivo
            evidencia_file = request.files.get('evidencia')
            evidencia_nome = None

            if evidencia_file and evidencia_file.filename != '':
                # Salvar o arquivo em uma pasta local
                from werkzeug.utils import secure_filename
                import os

                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)

                evidencia_nome = secure_filename(evidencia_file.filename)
                evidencia_file.save(os.path.join(upload_folder, evidencia_nome))

            # Validação mínima
            if not all([tipo, data_registro, nome_usuario, descricao]):
                flash('⚠️ Por favor, preencha todos os campos obrigatórios.', 'danger')
            else:
                try:
                    cursor.execute("""
                        INSERT INTO u799109175_db_funcae.tbl_chamados_suport
                        (tipo, data_registro, nome_usuario, evidencia, descricao)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (tipo, data_registro, nome_usuario, evidencia_nome, descricao))
                    mysql.connection.commit()
                    flash('✅ Ocorrência registrada com sucesso.', 'success')
                except Exception as e:
                    mysql.connection.rollback()
                    print(f'❌ Erro ao inserir chamado: {e}')
                    flash('Erro ao salvar ocorrência. Tente novamente mais tarde.', 'danger')

        # sempre carregar ocorrências para exibir na tela
        try:
            cursor.execute("""
                SELECT * 
                FROM u799109175_db_funcae.tbl_chamados_suport
                ORDER BY data_criacao DESC
            """)
            chamados = cursor.fetchall()
        except Exception as e:
            print(f'Erro ao carregar chamados: {e}')
            chamados = []

        return render_template('suport.html', chamados=chamados)

    finally:
        cursor.close()
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)