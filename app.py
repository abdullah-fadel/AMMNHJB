# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import re
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = "academic_secret_key_123"

API_KEY = os.getenv("DEEPSEEK_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def get_db_connection():
    # الاتصال بـ Supabase
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS visitors_log (
            id SERIAL PRIMARY KEY,
            visit_date TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tools_usage (
            tool_name TEXT PRIMARY KEY,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# تشغيل التهيئة
init_db()

# ... (بقية دوال clean_academic_text و call_deepseek كما هي دون تغيير) ...

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    # جلب المقالات (استخدام LIMIT لتسريع العرض)
    cur.execute('SELECT * FROM articles ORDER BY id DESC')
    articles = cur.fetchall()
    
    # تحديث إحصائيات بسيطة
    cur.execute("SELECT usage_count FROM tools_usage WHERE tool_name='search'")
    stats = {"tool_search_usage": cur.fetchone()[0]}
    
    cur.close()
    conn.close()
    return render_template('index.html', articles=articles, stats=stats)

# ... (قم بتطبيق نفس منطق cur = conn.cursor() على بقية الدوال admin و tools) ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
