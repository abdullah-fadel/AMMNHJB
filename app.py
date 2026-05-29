# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "academic_secret_key_123"

API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ذكاء في تحديد مسار قاعدة البيانات: إذا كان السيرفر على Render يختار المسار الدائم، وإذا حاسبتك يختار المسار العادي
DB_PATH = "/data/academic_platform.db" if os.path.exists("/data") else "academic_platform.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visitors_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tools_usage (
            tool_name TEXT PRIMARY KEY,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    conn.execute("INSERT OR IGNORE INTO tools_usage (tool_name, usage_count) VALUES ('search', 0)")
    conn.execute("INSERT OR IGNORE INTO tools_usage (tool_name, usage_count) VALUES ('paraphrase', 0)")
    conn.execute("INSERT OR IGNORE INTO tools_usage (tool_name, usage_count) VALUES ('proposal', 0)")
    conn.commit()
    conn.close()

init_db()

def call_deepseek(prompt, system_content):
    if not API_KEY: return "ERROR_NO_KEY"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": prompt}], "temperature": 0.3}
    try:
        response = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=60)
        if response.status_code == 200: return response.json()['choices'][0]['message']['content']
        return "ERROR_SERVER"
    except Exception: return "ERROR_CONNECTION"

@app.route('/api/ping')
def ping_server():
    return jsonify({"status": "online"})

@app.route('/')
def index():
    conn = get_db_connection()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if 'visited_today' not in session:
        conn.execute('INSERT INTO visitors_log (visit_date) VALUES (?)', (current_time,))
        conn.commit()
        session['visited_today'] = True

    current_year = datetime.now().strftime('%Y')
    current_month = datetime.now().strftime('%Y-%m')

    stats = {
        "total_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log').fetchone()[0],
        "year_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log WHERE visit_date LIKE ?', (f'{current_year}%',)).fetchone()[0],
        "month_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log WHERE visit_date LIKE ?', (f'{current_month}%',)).fetchone()[0],
        "tool_search_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='search'").fetchone()[0],
        "tool_paraphrase_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='paraphrase'").fetchone()[0],
        "tool_proposal_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='proposal'").fetchone()[0]
    }
    
    articles = conn.execute('SELECT * FROM articles ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', articles=articles, stats=stats)

# مسار عرض المقال الجديد والمستقل
@app.route('/article/<int:id>')
def view_article(id):
    conn = get_db_connection()
    article = conn.execute('SELECT * FROM articles WHERE id = ?', (id,)).fetchone()
    conn.close()
    if article is None:
        return "المقال غير موجود", 404
    return render_template('article.html', article=article)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
        ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "password123")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template('login.html', error=error)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'): return redirect(url_for('login'))
        
    conn = get_db_connection()
    if request.method == 'POST' and request.form.get('action') == 'publish':
        title = request.form.get('title')
        content = request.form.get('content')
        current_date = datetime.now().strftime('%Y-%m-%d')
        if title and content:
            conn.execute('INSERT INTO articles (title, content, date) VALUES (?, ?, ?)', (title, content, current_date))
            conn.commit()
            return redirect(url_for('admin_dashboard'))

    current_year = datetime.now().strftime('%Y')
    current_month = datetime.now().strftime('%Y-%m')

    stats = {
        "total_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log').fetchone()[0],
        "year_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log WHERE visit_date LIKE ?', (f'{current_year}%',)).fetchone()[0],
        "month_visitors": conn.execute('SELECT COUNT(*) FROM visitors_log WHERE visit_date LIKE ?', (f'{current_month}%',)).fetchone()[0],
        "tool_search_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='search'").fetchone()[0],
        "tool_paraphrase_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='paraphrase'").fetchone()[0],
        "tool_proposal_usage": conn.execute("SELECT usage_count FROM tools_usage WHERE tool_name='proposal'").fetchone()[0]
    }
    
    articles = conn.execute('SELECT * FROM articles ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', articles=articles, stats=stats)

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    if not session.get('is_admin'): return redirect(url_for('login'))
    conn = get_db_connection()
    article = conn.execute('SELECT * FROM articles WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            conn.execute('UPDATE articles SET title = ?, content = ? WHERE id = ?', (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('edit.html', article=article)

@app.route('/admin/delete/<int:id>')
def delete_article(id):
    if not session.get('is_admin'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM articles WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/tools')
def tools_menu(): return render_template('tools_menu.html')

@app.route('/tools/search', methods=['GET', 'POST'])
def tool_search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '')
        conn = get_db_connection()
        conn.execute("UPDATE tools_usage SET usage_count = usage_count + 1 WHERE tool_name='search'")
        conn.commit()
        conn.close()
        
        api_url = f"https://api.crossref.org/works?query={query}&filter=has-full-text:true&rows=70"
        raw_items = []
        try:
            res = requests.get(api_url, timeout=15)
            if res.status_code == 200: raw_items = res.json().get('message', {}).get('items', [])
        except Exception: raw_items = []

        seen_titles = set()
        cleaned_base_data = []
        blocked_domains = ["sciencedirect.com", "springer.com", "wiley.com", "ieeexplore.ieee.org", "taylorandfrancis.com"]

        for item in raw_items:
            title_list = item.get('title', [])
            title = title_list[0] if title_list else f"بحث متقدم في {query}"
            if title.lower() in seen_titles: continue
            link_source = "https://scholar.google.com"
            link_found = False
            links = item.get('link', [])
            for l in links:
                url_str = l.get('URL', '')
                if url_str and not any(dom in url_str for dom in blocked_domains):
                    link_source = url_str; link_found = True; break
            if not link_found:
                doi = item.get('DOI', '')
                if doi: link_source = f"https://doi.org/{doi}"

            seen_titles.add(title.lower())
            authors_list = item.get('author', [])
            authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}" for a in authors_list[:3]]) if authors_list else "مجموعة من الباحثين"
            year = str(item.get('published-print', {}).get('date-parts', [[2025]])[0][0])
            journal = item.get('container-title', ["مجلة البحوث الحرة"])[0]
            cleaned_base_data.append({"title": title, "authors": authors, "year": year, "journal": journal, "url": link_source})
            if len(cleaned_base_data) >= 50: break

        for item in cleaned_base_data:
            results.append({"title": item["title"], "authors": item["authors"], "year": item["year"], "journal": item["journal"], "url": item["url"], "abstract": f"دراسة علمية مجانية ومفتوحة تهدف لتأصيل وتحليل أبعاد ومتغيرات ({query})."})
    return render_template('tool_search.html', results=results, query=query)

@app.route('/tools/paraphrase', methods=['POST'])
def tool_paraphrase():
    conn = get_db_connection()
    conn.execute("UPDATE tools_usage SET usage_count = usage_count + 1 WHERE tool_name='paraphrase'")
    conn.commit()
    conn.close()
    
    data = request.get_json() or {}
    user_text = data.get('text', '')
    prompt = f"أعد صياغة النص التالي بأسلوب أكاديمي رصين جداً: {user_text}"
    result_text = call_deepseek(prompt, system_content="You are an expert Arabic academic editor.")
    return jsonify({"result": result_text.strip()})

@app.route('/tools/paraphrase_view')
def tool_paraphrase_view(): return render_template('tool_paraphrase.html')

@app.route('/tools/proposal', methods=['POST'])
def tool_proposal():
    conn = get_db_connection()
    conn.execute("UPDATE tools_usage SET usage_count = usage_count + 1 WHERE tool_name='proposal'")
    conn.commit()
    conn.close()
    
    data = request.get_json() or {}
    title = data.get('title', '')
    prompt = f"اكتب وصغ خطة بحث منهجية أكاديمية متكاملة لعنوان البحث التالي: ({title})."
    result_text = call_deepseek(prompt, system_content="You are a professional academic consultant.")
    return jsonify({"result": result_text.strip()})

@app.route('/tools/proposal_view')
def tool_proposal_view(): return render_template('tool_proposal.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

