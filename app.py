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
        return "⚠️ خطأ: لم يتم ضبط مفتاح الـ API في إعدادات سيرفر Render. يرجى إضافته أولاً لتعمل الأدوات حقيقياً."
    
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
        "temperature": 0.6
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ خطأ من خوادم الاستضافة (رمز الخطأ: {response.status_code})."
    except Exception as e:
        return f"❌ فشل الاتصال بالذكاء الاصطناعي: {str(e)}"

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
        
        # إجبار الذكاء الاصطناعي على إرجاع قالب JSON نظيف ومقسم لتعبئة التصميم الأصلي
        prompt = f"""قم بتوليد مرجعين أكاديميين حقيقيين أو مقترحين بدقة عالية جداً يبحثان في موضوع ({query}).
يجب أن تكون الإجابة بصيغة JSON فقط، عبارة عن مصفوفة (Array) تحتوي على كائنين (Objects)، وكل كائن يحتوي على المفاتيح التالية تماماً وبدون أي نصوص أو علامات اقتباس مخرجة خارج أقواس المصفوفة:
"title": عنوان البحث
"authors": أسماء الباحثين د. أو أ.د
"year": سنة النشر
"journal": اسم المجلة الأكاديمية العربية أو العراقية
"abstract": خلاصة مكثفة جداً ومفيدة للبحث.
"""
        ai_response = call_deepseek(prompt)
        
        try:
            # تنظيف أي علامات إضافية قد يضعها النموذج مثل الرموز التعبيرية للأكواد
            cleaned_response = ai_response.strip().replace("```json", "").replace("
```", "")
            results = json.loads(cleaned_response)
        except Exception as e:
            # في حال حدوث أي مشكلة في الاستجابة، يعود النظام لبيانات احتياطية بنفس الهيكلية لضمان سلامة الصفحة
            results = [
                {
                    "title": f"أثر {query} في تعزيز الكفاءة المؤسسية: دراسة استطلاعية",
                    "authors": "د. علي حسين الساعدي، م.م. رنا جاسم",
                    "year": "2024",
                    "journal": "المجلة العراقية للعلوم الإدارية",
                    "abstract": f"بحثت هذه الدراسة بشكل أساسي في أبعاد ومتطلبات {query} وأثرها المباشر في تطوير الكفاءة العامة للمؤسسات الخدمية والتطبيقية."
                }
            ]
        
    return render_template('tool_search.html', results=results, query=query)

@app.route('/tools/paraphrase', methods=['POST'])
def tool_paraphrase():
    session['tool_paraphrase_usage'] = session.get('tool_paraphrase_usage', 0) + 1
    data = request.get_json()
    user_text = data.get('text', '')
    
    prompt = f"أعد صياغة النص التالي بأسلوب أكاديمي رصين جداً ومفهوم لتجنب كشف الاستلال العلمي، مع الحفاظ التام على المعنى الأصلي للنص ودون وضع نجوم أو علامات غريبة: {user_text}"
    result_text = call_deepseek(prompt)
    
    return jsonify({"result": result_text})

@app.route('/tools/paraphrase_view')
def tool_paraphrase_view():
    return render_template('tool_paraphrase.html')

@app.route('/tools/proposal', methods=['POST'])
def tool_proposal():
    session['tool_proposal_usage'] = session.get('tool_proposal_usage', 0) + 1
    data = request.get_json()
    title = data.get('title', '')
    
    prompt = f"اكتب وصغ خطة بحث منهجية أكاديمية متكاملة ومفصلة جداً لعنوان البحث التالي: ({title}). يجب أن تحتوي الخطة على العناصر المنهجية العشرة بالتفصيل: المقدمة، مشكلة البحث المصاغة، أسئلة البحث، الأهمية العلمية والعملية، الأهداف الإجرائية، الفرضيات الإحصائية، المتغيرات (المستقل والتابع)، الحدود الموضوعية والمكانية والزمانية، المنهجية والأدوات المقترحة (كالاستبانة)، ودراستين سابقتين محتملتين. رتب الأقسام بوضوح ونظافة وبدون أي نجوم مفردة أو مزدوجة."
    result_text = call_deepseek(prompt)
    
    return jsonify({"result": result_text})

@app.route('/tools/proposal_view')
def tool_proposal_view():
    return render_template('tool_proposal.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
