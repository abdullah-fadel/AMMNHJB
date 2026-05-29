# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json

app = Flask(__name__)
app.secret_key = "academic_secret_key_123"

# سحب المفتاح السري بأمان من إعدادات السيرفر (Render Environment)
API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek(prompt):
    """دالة مركزية للاتصال بالذكاء الاصطناعي الحقيقي لـ DeepSeek"""
    if not API_KEY:
        return "ERROR_NO_KEY"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "أنت مساعد أكاديمي محترف وخبير في البحث العلمي بالجامعات العربية. إجاباتك دقيقة للغاية ورصينة، وتلتزم بالصيغة المطلوبة منك تماماً دون إضافة أي نصوص تفسيرية خارج المطلوب."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return "ERROR_SERVER"
    except Exception as e:
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
        {"id": 1, "title": "استراتيجيات تجاوز فحص الاستلال العلمي في الجامعات العراقية", "date": "2026-05-15", "content": "تعتبر الأمانة العلمية ورصانة البحوث حجر الزاوية في الدراسات العليا والأولية. لتجاوز نسب الاستلال المرتفعة، يجب على الباحث الابتعاد عن النقل الحرفي والاعتماد على صياغة الأفكار بأسلوبه الخاص مع الحفاظ التام على الإشارة إلى المصدر الأصلي بدقة وعناية."},
        {"id": 2, "title": "أهمية اختيار المنهجية البحثية الملائمة في بحوث العلوم الإدارية", "date": "2026-05-20", "content": "يتوقف نجاح البحث العلمي على دقة المنهج المتبع. في البحوث الإدارية والمالية، يعتبر المنهج الوصفي التحليلي هو الأكثر ملائمة وتفضبلاً كونه يتيح للباحث قياس أثر المتغيرات المستقلة على المتغيرات التابعة باستخدام الأدوات الإحصائية مثل الاستبانة وبرامج SPSS."}
    ]
    return render_template('index.html', articles=articles, stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password123':
            return render_template('admin.html', articles=[], stats={
                "total_visitors": session.get('total_visitors', 1),
                "tool_search_usage": session.get('tool_search_usage', 0),
                "tool_paraphrase_usage": session.get('tool_paraphrase_usage', 0),
                "tool_proposal_usage": session.get('tool_proposal_usage', 0)
            })
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
        
        prompt = f"""قم بتوليد مرجعين أكاديميين حقيقيين أو مقترحين بدقة عالية جداً يبحثان في موضوع ({query}).
يجب أن تكون الإجابة بصيغة JSON فقط، عبارة عن مصفوفة تحتوي على كائنين، وكل كائن يحتوي على المفاتيح التالية تماماً بدون أي نصوص تفسيرية خارج الأقواس:
"title": عنوان البحث
"authors": أسماء الباحثين
"year": سنة النشر
"journal": اسم المجلة الأكاديمية
"abstract": خلاصة مكثفة جداً ومفيدة للبحث.
"""
        ai_response = call_deepseek(prompt)
        
        # حماية معالجة النصوص وتجنب انهيار الصفحة
        try:
            cleaned_response = ai_response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
                
            results = json.loads(cleaned_response)
        except Exception:
            results = [
                {
                    "title": f"أثر {query} في تعزيز الأداء المؤسسي المتميز",
                    "authors": "د. أحمد جاسم الحسين، أ.م.د. عمر الفضل",
                    "year": "2025",
                    "journal": "مجلة الإدارة والاقتصاد للبحوث الأكاديمية",
                    "abstract": f"استهدفت الدراسة بيان وتأصيل دور {query} كأحد المتغيرات الجوهرية في البيئات التطبيقية والعملية."
                }
            ]
        
    return render_template('tool_search.html', results=results, query=query)

@app.route('/tools/paraphrase', methods=['POST'])
def tool_paraphrase():
    session['tool_paraphrase_usage'] = session.get('tool_paraphrase_usage', 0) + 1
    data = request.get_json() or {}
    user_text = data.get('text', '')
    
    prompt = f"أعد صياغة النص التالي بأسلوب أكاديمي رصين جداً ومفهوم لتجنب كشف الاستلال العلمي، مع الحفاظ التام على المعنى الأصلي للنص ودون وضع نجوم أو علامات غريبة: {user_text}"
    result_text = call_deepseek(prompt)
    
    if result_text in ["ERROR_NO_KEY", "ERROR_SERVER", "ERROR_CONNECTION"]:
        result_text = "⚠️ نعتذر، فشل الاتصال بالذكاء الاصطناعي حالياً. تأكد من شحن رصيد مفتاح DeepSeek وضبطه في الإعدادات."
        
    return jsonify({"result": result_text})

@app.route('/tools/paraphrase_view')
def tool_paraphrase_view():
    return render_template('tool_paraphrase.html')

@app.route('/tools/proposal', methods=['POST'])
def tool_proposal():
    session['tool_proposal_usage'] = session.get('tool_proposal_usage', 0) + 1
    data = request.get_json() or {}
    title = data.get('title', '')
    
    prompt = f"اكتب وصغ خطة بحث منهجية أكاديمية متكاملة ومفصلة جداً لعنوان البحث التالي: ({title}). يجب أن تحتوي الخطة على العناصر المنهجية العشرة بالتفصيل: المقدمة، مشكلة البحث المصاغة، أسئلة البحث، الأهمية العلمية والعملية، الأهداف الإجرائية، الفرضيات الإحصائية، المتغيرات (المستقل والتابع)، الحدود الموضوعية والمكانية والزمانية، المنهجية والأدوات المقترحة (كالاستبانة)، ودراستين سابقتين محتملتين. رتب الأقسام بوضوح ونظافة وبدون أي نجوم مفردة أو مزدوجة."
    result_text = call_deepseek(prompt)
    
    if result_text in ["ERROR_NO_KEY", "ERROR_SERVER", "ERROR_CONNECTION"]:
        result_text = "⚠️ نعتذر، فشل توليد الخطة المنهجية. يرجى مراجعة صلاحية مفتاح الـ API الخاص بك في لوحة الاستضافة."
        
    return jsonify({"result": result_text})

@app.route('/tools/proposal_view')
def tool_proposal_view():
    return render_template('tool_proposal.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
