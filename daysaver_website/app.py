from flask import Flask, render_template, request, redirect, send_from_directory, session
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR)

app.secret_key = 'daysaver_secure_session_key_999'

@app.route('/<path:filename>')
def serve_static_files(filename):
    if filename.startswith('daysaver_images/'):
        return send_from_directory(BASE_DIR, filename)
    elif filename.endswith('.css'):
        return send_from_directory(BASE_DIR, filename)
    return "File Not Found", 404

@app.route('/')
def home():
    return render_template('daysaver_landing.html')

@app.route('/signup')
def signup_page():
    return render_template('daysaver_signuppage.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('first')
    password = request.form.get('password')

    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Username already exists! Go back and choose another."
    finally:
        conn.close()

    return redirect('/login')

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user' not in session:
        return redirect('/')

    tx_name = request.form.get('name')
    tx_type = request.form.get('type')
    amount = float(request.form.get('amount', 0.0))
    date = request.form.get('date')

    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO transactions (user_id, type, name, amount, date) VALUES (?, ?, ?, ?, ?)",
        (session['user_id'], tx_type, tx_name, amount, date)
    )
    
    conn.commit()
    conn.close()
    
    print(f"Successfully recorded transaction: {tx_name} (${amount})")
    
    return redirect('/transactions')

@app.route('/login')
def login_page():
    return render_template('daysaver_loginpage.html', error=None)

@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form.get('first')
    password = request.form.get('password')

    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = username
        session['user_id'] = user['id']
        
        if user['salary'] == 0.0 or user['salary'] is None:
            return redirect('/setup_wage')
        
        return redirect('/dashboard')
    else:
        return render_template('daysaver_loginpage.html', error="Invalid username or password")

@app.route('/setup_wage')
def setup_wage_page():
    if 'user' not in session: return redirect('/')
    return '''
    <div style="max-width: 400px; margin: 100px auto; font-family: sans-serif; text-align: center;">
        <h2>Welcome to Daysaver!</h2>
        <p>To calculate your spending percentages, please enter your <b>Annual Salary</b>:</p>
        <form action="/save_wage" method="POST">
            <input type="text" name="salary" placeholder="e.g. 50000" style="padding: 10px; width: 80%; margin-bottom: 15px;"><br>
            <button type="submit" style="padding: 10px 20px; background: #627444; color: #fffbed; border: none; cursor: pointer;">Get Started</button>
        </form>
    </div>
    '''

@app.route('/save_wage', methods=['POST'])
def save_wage():
    if 'user' not in session: return redirect('/')
    salary = float(request.form.get('salary', 0.0))
    
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET salary = ? WHERE id = ?", (salary, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard_page():
    if 'user' not in session:
        return redirect('/')
        
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    annual_salary = user_data['salary'] if user_data['salary'] else 0.0
    daily_wage = round(annual_salary / 365, 2) if annual_salary > 0 else 0.0
    
    recent_tx_raw = cursor.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5", 
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    recent_transactions = []
    for row in recent_tx_raw:
        tx = dict(row)
        tx['percentage'] = round((tx['amount'] / daily_wage) * 100, 1) if daily_wage > 0 else 0.0
        recent_transactions.append(tx)

    return render_template(
        'daysaver_dashboard.html', 
        username=session['user'], 
        salary=annual_salary, 
        daily_wage=daily_wage,
        recent_transactions=recent_transactions
    )

@app.route('/tracking')
def tracking_page():
    if 'user' not in session:
        return redirect('/')
    return render_template('daysaver_tracking.html')

@app.route('/transactions')
def transactions_page():
    if 'user' not in session:
        return redirect('/')
        
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    daily_wage = round(user_data['salary'] / 365, 2) if user_data['salary'] and user_data['salary'] > 0 else 0.0
    all_tx_raw = cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", (session['user_id'],)).fetchall()
    conn.close()
    
    all_transactions = []
    for row in all_tx_raw:
        tx = dict(row)
        tx['percentage'] = round((tx['amount'] / daily_wage) * 100, 1) if daily_wage > 0 else 0.0
        all_transactions.append(tx)

    return render_template('daysaver_transactions.html', all_transactions=all_transactions)

@app.route('/logout')
def logout():
    session.pop('user', None)
    print("User successfully logged out.")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
