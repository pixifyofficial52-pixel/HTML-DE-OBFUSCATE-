from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import secrets
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  email TEXT, html_renders INTEGER DEFAULT 0, url_renders INTEGER DEFAULT 0,
                  created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, source TEXT,
                  content TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# HTML Cleaner
def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style", "iframe"]):
        script.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

# HTML Templates
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>HTML Render Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
        body{background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;color:white;}
        .navbar{background:rgba(255,255,255,0.1);padding:1rem 2rem;display:flex;justify-content:space-between;}
        .nav-links a{color:white;text-decoration:none;margin-left:20px;padding:8px 16px;border-radius:20px;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1200px;margin:0 auto;padding:2rem;}
        .hero{text-align:center;padding:4rem 0;}
        .hero h1{font-size:3rem;margin-bottom:1rem;}
        .btn{display:inline-block;padding:12px 30px;background:white;color:#667eea;text-decoration:none;
             border-radius:25px;font-weight:bold;margin:10px;border:none;cursor:pointer;}
        .btn:hover{transform:scale(1.05);box-shadow:0 5px 15px rgba(0,0,0,0.3);}
        .features{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-top:3rem;}
        .feature-card{background:white;color:#333;padding:2rem;border-radius:15px;text-align:center;}
        .feature-card i{font-size:3rem;color:#667eea;margin-bottom:1rem;}
        .form-container{background:white;color:#333;padding:2rem;border-radius:15px;max-width:400px;margin:2rem auto;}
        .form-container input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;}
        .form-container button{width:100%;padding:10px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;}
        .dashboard{background:#f4f7fc;min-height:100vh;color:#333;}
        .sidebar{background:linear-gradient(135deg,#667eea,#764ba2);color:white;width:250px;position:fixed;height:100vh;padding:2rem;}
        .sidebar a{color:white;text-decoration:none;display:block;padding:10px;margin:5px 0;border-radius:5px;}
        .sidebar a:hover{background:rgba(255,255,255,0.2);}
        .content{margin-left:250px;padding:2rem;}
        .stat-card{background:white;padding:1.5rem;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:1rem;}
        .upload-area{border:2px dashed #667eea;border-radius:10px;padding:2rem;text-align:center;background:#f8f9fa;cursor:pointer;}
        .upload-area:hover{background:#e9ecef;}
        .result-area{background:#2d2d2d;color:#fff;padding:1rem;border-radius:10px;max-height:400px;overflow:auto;font-family:monospace;}
        .loader{border:5px solid #f3f3f3;border-top:5px solid #667eea;border-radius:50%;width:50px;height:50px;animation:spin 1s linear infinite;margin:20px auto;}
        @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
    </style>
</head>
<body>
    <div class="navbar">
        <h2>📄 HTML Render Pro</h2>
        <div class="nav-links">
            {% if session.user_id %}
                <a href="/dashboard">Dashboard</a>
                <a href="/logout">Logout</a>
            {% else %}
                <a href="/login">Login</a>
                <a href="/register" style="background:white;color:#667eea;">Sign Up</a>
            {% endif %}
        </div>
    </div>
    
    <div class="container">
        <div class="hero">
            <h1>Advanced HTML Rendering Solution</h1>
            <p>Transform HTML files and URLs into clean, readable text instantly</p>
            {% if not session.user_id %}
                <a href="/register" class="btn">Get Started Free</a>
            {% else %}
                <a href="/dashboard" class="btn">Go to Dashboard</a>
            {% endif %}
        </div>
        
        <div class="features">
            <div class="feature-card">
                <i>📄</i>
                <h3>Smart Rendering</h3>
                <p>Extract clean text from any HTML</p>
            </div>
            <div class="feature-card">
                <i>🌐</i>
                <h3>URL Support</h3>
                <p>Render any webpage content</p>
            </div>
            <div class="feature-card">
                <i>🛡️</i>
                <h3>Safe & Secure</h3>
                <p>Malware protection included</p>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - HTML Render Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
        .sidebar{background:linear-gradient(135deg,#667eea,#764ba2);color:white;width:250px;position:fixed;height:100vh;padding:2rem;}
        .sidebar h3{margin-bottom:2rem;}
        .sidebar a{color:white;text-decoration:none;display:block;padding:10px;margin:5px 0;border-radius:5px;}
        .sidebar a:hover,.sidebar a.active{background:rgba(255,255,255,0.2);}
        .content{margin-left:250px;padding:2rem;background:#f4f7fc;min-height:100vh;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:2rem;}
        .stat-card{background:white;padding:1.5rem;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
        .stat-card h2{color:#667eea;margin-top:0.5rem;}
        .card{background:white;border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
        .upload-area{border:2px dashed #667eea;border-radius:10px;padding:2rem;text-align:center;background:#f8f9fa;cursor:pointer;margin:1rem 0;}
        .upload-area:hover{background:#e9ecef;}
        .url-input{display:flex;gap:10px;margin:1rem 0;}
        .url-input input{flex:1;padding:10px;border:1px solid #ddd;border-radius:5px;}
        .url-input button{padding:10px 20px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;}
        .result-area{background:#2d2d2d;color:#fff;padding:1rem;border-radius:10px;max-height:400px;overflow:auto;font-family:monospace;margin:1rem 0;}
        .btn{padding:8px 16px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;margin-right:10px;}
        .btn:hover{opacity:0.9;}
        .loader{display:none;border:5px solid #f3f3f3;border-top:5px solid #667eea;border-radius:50%;width:50px;height:50px;animation:spin 1s linear infinite;margin:20px auto;}
        @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
        .table{width:100%;background:white;border-radius:10px;overflow:hidden;}
        .table th{background:#667eea;color:white;padding:10px;text-align:left;}
        .table td{padding:10px;border-bottom:1px solid #ddd;}
        .tab{display:inline-block;padding:10px 20px;cursor:pointer;background:#ddd;border-radius:5px 5px 0 0;margin-right:5px;}
        .tab.active{background:#667eea;color:white;}
        .tab-content{display:none;background:white;padding:20px;border-radius:0 5px 5px 5px;}
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>📊 HTML Render Pro</h3>
        <a href="#" onclick="showTab('dashboard')" class="active" id="tab-dashboard">🏠 Dashboard</a>
        <a href="#" onclick="showTab('render')" id="tab-render">📄 Render HTML</a>
        <a href="#" onclick="showTab('url')" id="tab-url">🌐 Render URL</a>
        <a href="#" onclick="showTab('history')" id="tab-history">📜 History</a>
        <a href="/logout">🚪 Logout</a>
    </div>
    
    <div class="content">
        <!-- Dashboard Tab -->
        <div id="dashboard-tab" class="tab-content" style="display:block;">
            <h2>Welcome, {{ username }}!</h2>
            <div class="stats">
                <div class="stat-card">
                    <div>HTML Renders</div>
                    <h2>{{ html_renders }}</h2>
                </div>
                <div class="stat-card">
                    <div>URL Renders</div>
                    <h2>{{ url_renders }}</h2>
                </div>
                <div class="stat-card">
                    <div>Total</div>
                    <h2>{{ html_renders + url_renders }}</h2>
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Activity</h3>
                <table class="table">
                    <tr><th>Type</th><th>Source</th><th>Date</th></tr>
                    {% for h in history %}
                    <tr>
                        <td>📄 {{ h[2]|upper }}</td>
                        <td>{{ h[3][:50] }}{% if h[3]|length > 50 %}...{% endif %}</td>
                        <td>{{ h[5] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        
        <!-- Render HTML Tab -->
        <div id="render-tab" class="tab-content">
            <h2>Render HTML File</h2>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" accept=".html,.htm" style="display:none;" onchange="uploadFile()">
                <h3>📤 Click to upload HTML file</h3>
                <p>or drag and drop</p>
                <small>Max 50MB</small>
            </div>
            <div id="html-loader" class="loader"></div>
            <div id="html-result" style="display:none;">
                <h3>Rendered Output:</h3>
                <div id="html-output" class="result-area"></div>
                <button class="btn" onclick="copyOutput('html-output')">📋 Copy</button>
                <button class="btn" onclick="downloadOutput('html-output', 'rendered.txt')">📥 Download</button>
            </div>
        </div>
        
        <!-- Render URL Tab -->
        <div id="url-tab" class="tab-content">
            <h2>Render URL</h2>
            <div class="url-input">
                <input type="url" id="urlInput" placeholder="Enter URL (e.g., https://example.com)">
                <button onclick="renderURL()">Render</button>
            </div>
            <div id="url-loader" class="loader"></div>
            <div id="url-result" style="display:none;">
                <div id="url-title" class="card" style="padding:10px;"></div>
                <h3>Content:</h3>
                <div id="url-output" class="result-area"></div>
                <button class="btn" onclick="copyOutput('url-output')">📋 Copy</button>
                <button class="btn" onclick="downloadOutput('url-output', 'url-content.txt')">📥 Download</button>
            </div>
        </div>
        
        <!-- History Tab -->
        <div id="history-tab" class="tab-content">
            <h2>Render History</h2>
            <table class="table">
                <tr><th>ID</th><th>Type</th><th>Source</th><th>Date</th></tr>
                {% for h in all_history %}
                <tr>
                    <td>{{ h[0] }}</td>
                    <td>📄 {{ h[2]|upper }}</td>
                    <td>{{ h[3] }}</td>
                    <td>{{ h[5] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
            document.getElementById(tab + '-tab').style.display = 'block';
            document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
        }
        
        function uploadFile() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('html-loader').style.display = 'block';
            document.getElementById('html-result').style.display = 'none';
            
            fetch('/api/render/html', {method:'POST', body:formData})
            .then(r => r.json())
            .then(data => {
                document.getElementById('html-loader').style.display = 'none';
                if (data.error) return alert('Error: ' + data.error);
                document.getElementById('html-output').innerText = data.text;
                document.getElementById('html-result').style.display = 'block';
            });
        }
        
        function renderURL() {
            const url = document.getElementById('urlInput').value;
            if (!url) return alert('Enter URL');
            
            document.getElementById('url-loader').style.display = 'block';
            document.getElementById('url-result').style.display = 'none';
            
            fetch('/api/render/url', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({url:url})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('url-loader').style.display = 'none';
                if (data.error) return alert('Error: ' + data.error);
                document.getElementById('url-title').innerHTML = '<strong>Title:</strong> ' + data.title;
                document.getElementById('url-output').innerText = data.text;
                document.getElementById('url-result').style.display = 'block';
            });
        }
        
        function copyOutput(id) {
            navigator.clipboard.writeText(document.getElementById(id).innerText)
                .then(() => alert('Copied!'));
        }
        
        function downloadOutput(id, filename) {
            const text = document.getElementById(id).innerText;
            const blob = new Blob([text], {type:'text/plain'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            a.click();
        }
    </script>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - HTML Render Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
        body{background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;}
        .form-container{background:white;padding:2rem;border-radius:15px;width:90%;max-width:400px;box-shadow:0 10px 30px rgba(0,0,0,0.2);}
        h2{text-align:center;color:#333;margin-bottom:1.5rem;}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;}
        button{width:100%;padding:10px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
        button:hover{background:#764ba2;}
        .link{text-align:center;margin-top:1rem;}
        .link a{color:#667eea;text-decoration:none;}
        .error{color:red;text-align:center;margin:10px 0;}
    </style>
</head>
<body>
    <div class="form-container">
        <h2>🔐 Login</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="link">
            Don't have account? <a href="/register">Register</a>
        </div>
    </div>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - HTML Render Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
        body{background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;}
        .form-container{background:white;padding:2rem;border-radius:15px;width:90%;max-width:400px;box-shadow:0 10px 30px rgba(0,0,0,0.2);}
        h2{text-align:center;color:#333;margin-bottom:1.5rem;}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;}
        button{width:100%;padding:10px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;}
        button:hover{background:#764ba2;}
        .link{text-align:center;margin-top:1rem;}
        .link a{color:#667eea;text-decoration:none;}
        .error{color:red;text-align:center;margin:10px 0;}
    </style>
</head>
<body>
    <div class="form-container">
        <h2>📝 Register</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <div class="link">
            Already have account? <a href="/login">Login</a>
        </div>
    </div>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    return render_template_string(INDEX_HTML, session=session)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)",
                     (username, password, email, str(datetime.now())))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            conn.close()
            return render_template_string(REGISTER_HTML, error='Username already exists')
    
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
        
        return render_template_string(LOGIN_HTML, error='Invalid credentials')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Get user data
    c.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()
    
    # Get recent history
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY date DESC LIMIT 5", (session['user_id'],))
    history = c.fetchall()
    
    # Get all history
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY date DESC", (session['user_id'],))
    all_history = c.fetchall()
    
    conn.close()
    
    return render_template_string(DASHBOARD_HTML, 
                                 username=user[1],
                                 html_renders=user[4],
                                 url_renders=user[5],
                                 history=history,
                                 all_history=all_history)

@app.route('/api/render/html', methods=['POST'])
@login_required
def api_render_html():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    html_content = file.read().decode('utf-8')
    cleaned = clean_html(html_content)
    
    # Update stats
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET html_renders = html_renders + 1 WHERE id=?", (session['user_id'],))
    c.execute("INSERT INTO history (user_id, type, source, content, date) VALUES (?, ?, ?, ?, ?)",
             (session['user_id'], 'html', file.filename, cleaned[:100], str(datetime.now())))
    conn.commit()
    conn.close()
    
    return jsonify({'text': cleaned})

@app.route('/api/render/url', methods=['POST'])
@login_required
def api_render_url():
    data = request.json
    url = data.get('url', '')
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        response = requests.get(url, timeout=10)
        cleaned = clean_html(response.text)
        
        # Get title
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'No title'
        
        # Update stats
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET url_renders = url_renders + 1 WHERE id=?", (session['user_id'],))
        c.execute("INSERT INTO history (user_id, type, source, content, date) VALUES (?, ?, ?, ?, ?)",
                 (session['user_id'], 'url', url, cleaned[:100], str(datetime.now())))
        conn.commit()
        conn.close()
        
        return jsonify({'text': cleaned, 'title': title})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
