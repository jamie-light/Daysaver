from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR)

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

@app.route('/login')
def login_page():
    return render_template('daysaver_loginpage.html', error=None)

@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form.get('first')
    password = request.form.get('password')

    conn = sqlite3.connect(os.path.join(BASE_DIR, 'daysaver.db'))
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        print(f"User {username} successfully logged in.")
        return redirect('/dashboard')
    else:
        return render_template('daysaver_loginpage.html', error="Invalid username or password")

@app.route('/dashboard')
def dashboard_page():
    return render_template('daysaver_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
