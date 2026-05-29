# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json

app = Flask(__name__)
app.secret_key = "academic_secret_key_123"

API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek(prompt, system_content):
    if not API_KEY:
        return "ERROR_NO_KEY"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "ERROR_SERVER"
    except Exception:
        return "ERROR_CONNECTION"

@app.route('/')
def index():
    if 'total_visitors' not in session:
        session['total_visitors'] = 1
    else:
        session['total_visitors'] += 1

    stats = {
        "total_visitors": session['total_visitors'],
        "tool_search_usage": session.get('tool_search_usage', 0),
        "tool_paraphrase_usage": session.get('tool_paraphrase_usage', 0),
        "tool_proposal_usage": session.get('tool_proposal_usage', 0)
    }
    
    articles = [
        {"id": 1, "title": "استراتيجيات تجاوز فحص الاستلال العلمي في الجامعات العراقية", "date": "2026-05-15", "content": "تعتبر الأمانة العلمية ورصانة البحوث حجر الزاوية في الدراسات العليا والأولية."},
        {"id": 2, "title": "أهمية اختيار المنهجية البحثية الملائمة في بحوث العلوم الإدارية", "date": "2026-05-20", "content": "يتوقف نجاح البحث العلمي على دقة المنهج المتبع في البحوث الإدارية والمالية."}
    ]
    return render_template('index.html', articles=articles, stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password123':
            return render_template('admin.html', articles=[], stats={"total_visitors": session.get('total_visitors', 1), "tool_search_usage": session.get('tool_search_usage', 0), "tool_paraphrase_usage": session.get('tool_paraphrase_usage', 0), "tool_proposal_usage": session.get('tool_proposal_usage', 0)})
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template('login.html', error=error)

@app.route('/tools')
def tools_menu():
    return render_template('tools_menu.html')

@app.route('/tools/search', methods=['GET', 'POST'])
def tool_search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '')
        session['tool_search_usage'] = session.get('tool_search_usage', 0) + 1
        
        # جلب البيانات من المراجع حرة الوصول المفتوحة
        api_url = f"https://api.crossref.org/works?query={query}&filter=has-full-text:true&rows=70"
        raw_items = []
        try:
            res = requests.get(api_url, timeout=15)
            if res.status_code == 200:
                raw_items = res.json().get('message', {}).get('items', [])
        except Exception:
            raw_items = []

        seen_titles = set()
        cleaned_base_data = []
        
        # حظر منصات الاشتراكات المعقدة والمدفوعة
        blocked_domains = ["sciencedirect.com", "springer.com", "wiley.com", "ieeexplore.ieee.org", "taylorandfrancis.com"]

        for item in raw_items:
            title_list = item.get('title', [])
            title = title_list[0] if title_list else f"بحث متقدم في {query}"
            
            if title.lower() in seen_titles:
                continue
            
            link_source = "https://scholar.google.com"
            link_found = False
            
            links = item.get('link', [])
            for l in links:
                url_str = l.get('URL', '')
                if url_str and not any(dom in url_str for dom in blocked_domains):
                    link_source = url_str
                    link_found = True
                    break
            
            if not link_found:
                doi = item.get('DOI', '')
                if doi:
                    link_source = f"https://eclass.uoa.gr/modules/document/index.php?course=DI111&download={doi}"
                    if not link_source:
                        link_source = f"https://doi.org/{doi}"

            seen_titles.add(title.lower())
            
            authors_list = item.get('author', [])
            authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}" for a in authors_list[:3]]) if authors_list else "مجموعة من الباحثين الأكاديميين"
            
            year = str(item.get('published-print', {}).get('date-parts', [[2025]])[0][0])
            journal_list = item.get('container-title', [])
            journal = journal_list[0] if journal_list else "مجلة البحوث الحرة المفتوحة"
            
            cleaned_base_data.append({
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "url": link_source
            })
            if len(cleaned_base_data) >= 50:
                break

        needed = 50 - len(cleaned_base_data)
        if needed > 0:
            prompt = f"""Generate exactly {needed} unique, completely free Open-Access academic references for ({query}) in Arabic.
CRITICAL RULE: The URLs must link only to free websites like 'https://www.asjp.cerist.dz/' or Google Scholar free direct links. Do NOT include Springer, Wiley, or ScienceDirect.
Return ONLY valid JSON array:
"title": research title in Arabic
"authors": names
"year": 2020-2026
"journal": Free Open-access journal name
"url": Direct free URL link
"abstract": Academic abstract in Arabic
"""
            system_search = "You are a precise academic data compiler. Return ONLY valid JSON as requested, with absolutely no markdown wrapper, no backticks, and no extra text."
            ai_res = call_deepseek(prompt, system_content=system_search)
            try:
                ai_cleaned = ai_res.strip().replace("```json", "").replace("```", "").strip()
                ai_data = json.loads(ai_cleaned)
                for entry in ai_data:
                    if entry.get("title", "").lower() not in seen_titles and len(cleaned_base_data) < 50:
                        seen_titles.add(entry.get("title", "").lower())
                        cleaned_base_data.append(entry)
            except Exception:
                pass

        for item in cleaned_base_data:
            abstract = item.get("abstract", "")
            if not abstract:
                abstract = f"دراسة علمية مجانية ومفتوحة تهدف لتأصيل وتحليل أبعاد ومتغيرات ({query}) وتطبيقاتها الميدانية لتقديم نموذج عملي متكامل يخدم الباحثين والمؤسسات."
            
            results.append({
                "title": item["title"],
                "authors": item["authors"],
                "year": item["year"],
                "journal": item["journal"],
                "url": item["url"],
                "abstract": abstract
            })

    return render_template('tool_search.html', results=results, query=query)

@app.route('/tools/paraphrase', methods=['POST'])
def tool_paraphrase():
    session['tool_paraphrase_usage'] = session.get('tool_paraphrase_usage', 0) + 1
    data = request.get_json() or {}
    user_text = data.get('text', '')
    
    prompt = f"أعد صياغة النص التالي بأسلوب أكاديمي رصين جداً ومفهوم لتجنب كشف الاستلال العلمي، مع الحفاظ التام على المعنى الأصلي للنص ودون وضع نجوم أو علامات غريبة أو صيغ برمجية: {user_text}"
    system_paraphrase = "You are an expert Arabic academic editor. Return ONLY the plain rewritten text. No markdown, no JSON, no quotes, no brackets, no wrapper."
    
    result_text = call_deepseek(prompt, system_content=system_paraphrase)
    
    # [تنظيف ذاتي بالسيرفر] للتخلص من الأقواس وعلامات الاقتباس إن وجدت بالخطأ قبل إرسالها للواجهة
    result_text = result_text.strip().replace('```json', '').replace('```', '')
    if result_text.startswith('{') and result_text.endswith('}'):
        try:
            json_data = json.loads(result_text)
            result_text = json_data.get('rewritten_text', list(json_data.values())[0])
        except Exception:
            pass
            
    return jsonify({"result": result_text})

@app.route('/tools/paraphrase_view')
def tool_paraphrase_view():
    return render_template('tool_paraphrase.html')

@app.route('/tools/proposal', methods=['POST'])
def tool_proposal():
    session['tool_proposal_usage'] = session.get('tool_proposal_usage', 0) + 1
    data = request.get_json() or {}
    title = data.get('title', '')
    
    prompt = f"اكتب وصغ خطة بحث منهجية أكاديمية متكاملة ومفصلة جداً لعنوان البحث التالي: ({title}). رتب الأقسام بوضوح ونظافة وبدون أي نجوم مفردة أو مزدوجة وبدون أقواس برمجية."
    system_proposal = "You are a professional academic consultant. Return the research proposal in clean, well-structured plain Arabic text. Do not wrap in JSON or brackets."
    
    result_text = call_deepseek(prompt, system_content=system_proposal)
    
    # [تنظيف ذاتي بالسيرفر]
    result_text = result_text.strip().replace('```json', '').replace('```', '')
    return jsonify({"result": result_text})

@app.route('/tools/proposal_view')
def tool_proposal_view():
    return render_template('tool_proposal.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
