from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'challenge_roadmap_secret_key_2025'
app.config['DATABASE'] = 'database/challenges.db'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de progresso dos desafios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id INTEGER,
            status TEXT DEFAULT 'pending',
            completed_at TIMESTAMP,
            code_solution TEXT,
            language_used TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de desafios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            level INTEGER NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            hints TEXT,
            test_cases TEXT,
            points INTEGER DEFAULT 10
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_difficulty_color(difficulty):
    colors = {
        'Iniciante': 'success',
        'Intermediário': 'warning',
        'Avançado': 'danger',
        'Expert': 'dark',
        'Master': 'secondary'
    }
    return colors.get(difficulty, 'secondary')

# Registrar a função globalmente para todos os templates
@app.context_processor
def utility_processor():
    return dict(get_difficulty_color=get_difficulty_color)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/challenges')
def challenges():
    level = request.args.get('level', '1')
    return render_template('challenges.html', level=level)

@app.route('/challenge/<int:challenge_id>')
def challenge_detail(challenge_id):
    # Verificar se o usuário está logado, mas não redirecionar automaticamente
    # Permitir que usuários não logados vejam os desafios
    conn = get_db_connection()
    challenge = conn.execute(
        'SELECT * FROM challenges WHERE id = ?', (challenge_id,)
    ).fetchone()
    conn.close()
    
    if challenge is None:
        return "Desafio não encontrado", 404
    
    return render_template('challenge_detail.html', challenge=challenge)

@app.route('/api/challenges')
def api_challenges():
    level = request.args.get('level', '1')
    conn = get_db_connection()
    
    if level == 'all':
        challenges = conn.execute(
            'SELECT * FROM challenges ORDER BY level, id'
        ).fetchall()
    else:
        challenges = conn.execute(
            'SELECT * FROM challenges WHERE level = ? ORDER BY id', (level,)
        ).fetchall()
    
    conn.close()
    
    challenges_list = []
    for challenge in challenges:
        challenges_list.append({
            'id': challenge['id'],
            'title': challenge['title'],
            'description': challenge['description'],
            'level': challenge['level'],
            'category': challenge['category'],
            'difficulty': challenge['difficulty'],
            'points': challenge['points']
        })
    
    return jsonify(challenges_list)

@app.route('/api/submit_solution', methods=['POST'])
def submit_solution():
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    challenge_id = data.get('challenge_id')
    code = data.get('code')
    language = data.get('language')
    
    conn = get_db_connection()
    
    existing = conn.execute(
        'SELECT * FROM user_progress WHERE user_id = ? AND challenge_id = ?',
        (session['user_id'], challenge_id)
    ).fetchone()
    
    if existing:
        conn.execute(
            '''UPDATE user_progress SET status = 'completed', 
               completed_at = CURRENT_TIMESTAMP, code_solution = ?, language_used = ?
               WHERE user_id = ? AND challenge_id = ?''',
            (code, language, session['user_id'], challenge_id)
        )
    else:
        conn.execute(
            '''INSERT INTO user_progress (user_id, challenge_id, status, 
               completed_at, code_solution, language_used)
               VALUES (?, ?, 'completed', CURRENT_TIMESTAMP, ?, ?)''',
            (session['user_id'], challenge_id, code, language)
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Solução submetida com sucesso!'})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    progress = conn.execute('''
        SELECT COUNT(*) as completed_count 
        FROM user_progress 
        WHERE user_id = ? AND status = 'completed'
    ''', (session['user_id'],)).fetchone()
    
    conn.close()
    
    return render_template('profile.html', user=user, progress=progress)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and user['password_hash'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            # Redirecionar para desafios em vez de perfil
            return redirect(url_for('challenges'))
        else:
            return render_template('login.html', error='Credenciais inválidas')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password)
            )
            conn.commit()
            
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            conn.close()
            
            # Redirecionar para desafios em vez de perfil
            return redirect(url_for('challenges'))
            
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Usuário ou email já existe')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def populate_all_challenges():
    """Popula o banco com TODOS os 200 desafios"""
    conn = get_db_connection()
    
    # Limpar tabela existente e recriar com todos os desafios
    conn.execute('DELETE FROM challenges')
    
    challenges_data = []
    
    # ===== NÍVEL 1 - INICIANTE (1-30) =====
    nivel1_desafios = [
        (1, "Conversor de Temperatura", "Crie um programa que converta temperaturas entre Celsius, Fahrenheit e Kelvin. O usuário deve escolher a escala de origem e a de destino.", 1, "Fundamentos", "Iniciante", "Use condicionais para identificar a conversão. Lembre-se das fórmulas clássicas de conversão.", 10),
        (2, "Calculadora de IMC", "Peça o peso e a altura do usuário, calcule o IMC e exiba a classificação (normal, sobrepeso, obesidade…).", 1, "Fundamentos", "Iniciante", "IMC = peso / altura². Use intervalos para determinar a categoria.", 10),
        # ... (todos os outros desafios do nível 1)
    ]
    
    # Adicionar desafios restantes do nível 1 (3-30)
    for i in range(3, 31):
        nivel1_desafios.append((
            i, f"Desafio {i}", f"Descrição detalhada do desafio {i}. Este desafio foca em conceitos fundamentais de programação.", 
            1, "Fundamentos", "Iniciante",
            f"Dicas e orientações para resolver o desafio {i}",
            10
        ))
    
    # ===== NÍVEL 2 - INTERMEDIÁRIO (31-70) =====
    nivel2_desafios = []
    for i in range(31, 71):
        nivel2_desafios.append((
            i, f"Desafio {i} - Intermediário", f"Descrição detalhada do desafio intermediário {i}. Este desafio envolve conceitos mais complexos de programação.", 
            2, "Algoritmos", "Intermediário",
            f"Dicas e orientações avançadas para resolver o desafio {i}",
            15
        ))
    
    # ===== NÍVEL 3 - AVANÇADO (71-100) =====
    nivel3_desafios = []
    for i in range(71, 101):
        nivel3_desafios.append((
            i, f"Desafio {i} - Avançado", f"Descrição detalhada do desafio avançado {i}. Este desafio requer conhecimentos profundos de algoritmos e estruturas de dados.", 
            3, "Algoritmos", "Avançado",
            f"Dicas especializadas para o desafio avançado {i}",
            20
        ))
    
    # ===== NÍVEL 4 - EXPERT (101-150) =====
    nivel4_desafios = []
    for i in range(101, 151):
        nivel4_desafios.append((
            i, f"Desafio {i} - Expert", f"Descrição detalhada do desafio expert {i}. Desafio extremamente complexo para programadores experientes.", 
            4, "Expert", "Expert",
            f"Dicas avançadas para o desafio expert {i}",
            25
        ))
    
    # ===== NÍVEL 5 - MASTER (151-200) =====
    nivel5_desafios = []
    for i in range(151, 201):
        nivel5_desafios.append((
            i, f"Desafio {i} - Master", f"Descrição detalhada do desafio master {i}. Desafio de nível profissional e pesquisa.", 
            5, "Master", "Master",
            f"Dicas especializadas para o desafio master {i}",
            30
        ))
    
    # Combinar todos os desafios
    all_challenges = nivel1_desafios + nivel2_desafios + nivel3_desafios + nivel4_desafios + nivel5_desafios
    
    for challenge in all_challenges:
        conn.execute(
            'INSERT INTO challenges (id, title, description, level, category, difficulty, hints, points) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            challenge
        )
    
    conn.commit()
    conn.close()
    print(f"Populados {len(all_challenges)} desafios no banco de dados!")

if __name__ == '__main__':
    if not os.path.exists('database'):
        os.makedirs('database')
    
    init_db()
    populate_all_challenges()
    print("Servidor iniciando... Acesse: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)