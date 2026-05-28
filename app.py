import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = "academy_secret_key_2026"  # مفتاح تشفير الجلسات

# إعدادات افتراضية للأدمن
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# قاعدة بيانات مؤقتة في الذاكرة (تتحول لقاعدة بيانات حقيقية لاحقاً)
articles = [
    {
        "id": 1,
        "title": "استراتيجيات البحث العلمي في الجامعات العراقية",
        "content": "يعتبر البحث العلمي الركيزة الأساسية لتقدم المجتمعات وتطورها الأكاديمي...",
        "date": "2026-05-28"
    }
]

# إحصائيات لوحة التحكم
stats = {
    "total_visitors": 0,
    "tool_search_usage": 0,
    "tool_paraphrase_usage": 0,
    "tool_proposal_usage": 0
}

# قائمة لتتبع الزوار الفريدين خلال الجلسة
visited_sessions = set()

@app.before_request
def track_visitors():
    # حساب الزوار الفريدين بناءً على حيز الجلسة
    if 'user_tracked' not in session:
        session['user_tracked'] = True
        stats['total_visitors'] += 1

# --- مسارات الواجهات الرئيسية ---

@app.route('/')
def index():
    return render_template('index.html', articles=articles)

@app.route('/tools')
def tools_menu():
    return render_template('tools_menu.html')

# --- مسارات لوحة التحكم والأدمن ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template('login.html', error=error)

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html', stats=stats, articles=articles)

@app.route('/admin/add-article', methods=['POST'])
def add_article():
    if not session.get('is_admin'):
        return jsonify({"status": "error", "message": "غير مصرح"}), 403
    
    title = request.form.get('title')
    content = request.form.get('content')
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    if title and content:
        new_id = len(articles) + 1
        articles.insert(0, {"id": new_id, "title": title, "content": content, "date": today})
        return redirect(url_for('admin_dashboard'))
    return "خطأ في البيانات المرسلة", 400

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

# --- مسارات الأدوات البحثية الذكية ---

# 1. أداة الباحث العراقي
@app.route('/tools/search', methods=['GET', 'POST'])
def tool_search():
    results = None
    query = ""
    if request.method == 'POST':
        stats['tool_search_usage'] += 1
        query = request.form.get('query')
        
        # هنا يتم محاكاة استدعاء DeepSeek v4 pro ومحركات البحث المفتوحة وتوليد 20 نتيجة
        results = []
        for i in range(1, 21):
            results.append({
                "title": f"دراسة معمقة حول {query} وآثارها التطبيقية - الجزء {i}",
                "authors": "د. عبد الله فاضل، أ. محمد صفا",
                "year": "2025" if i % 2 == 0 else "2026",
                "journal": "المجلة العراقية للدراسات الأكاديمية البحتة",
                "abstract": f"تبحث هذه الدراسة في معطيات ومتغيرات '{query}' وتأثيرها على البيئة العلمية والعملية مع تقديم توصيات عملية.",
                "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            })
            
    return render_template('tool_search.html', results=results, query=query)

# 2. أداة إعادة الصياغة البشرية والأكاديمية
@app.route('/tools/paraphrase', methods=['POST'])
def tool_paraphrase():
    stats['tool_paraphrase_usage'] += 1
    text_to_paraphrase = request.json.get('text', '')
    
    if not text_to_paraphrase:
        return jsonify({"error": "النص فارغ"}), 400
        
    # هنا يتم الربط الفعلي مع الـ API الخاص بـ DeepSeek وإرسال برومبت الصياغة البشرية الأكاديمية المحكمة
    # محاكاة الاستجابة الذكية:
    paraphrased_text = f"إعادة صياغة أكاديمية رصينة ومحكمة خالية من الاستلال الذكي:\n\nمن المنظور الأكاديمي، يتضح أن {text_to_paraphrase} يمثل ركيزة جوهرية تستدعي التقصي والتحليل المنهجي المعمق، تلافياً لأي تداخل مفاهيمي وبما يضمن الرصانة العلمية المستهدفة في البيئة البحثية."
    
    return jsonify({"result": paraphrased_text})

@app.route('/tools/paraphrase/view')
def tool_paraphrase_view():
    return render_template('tool_paraphrase.html')

# 3. أداة كتابة خطة البحث
@app.route('/tools/proposal', methods=['POST'])
def tool_proposal():
    stats['tool_proposal_usage'] += 1
    title = request.json.get('title', '')
    
    if not title:
        return jsonify({"error": "العنوان فارغ"}), 400

    # برومبت البناء المنهجي لـ DeepSeek لتوليد الأجزاء العشرة بدقة
    proposal_output = f"""### خطة المنهجية البحثية المقترحة لعنوان: ({title})

#### 1. مقدمة البحث:
تعد دراسة ({title}) من الموضوعات الحيوية الهامة في سياق التطوير المعرفي المعاصر، حيث تتبلور أهميتها في مواكبة المتغيرات الحديثة وسد الفجوة المعرفية في المكتبة الأكاديمية.

#### 2. مشكلة البحث:
تكمن مشكلة البحث في وجود قصور واضح وتساؤلات جوهرية تحيط بآليات تطبيق وحوكمة ({title})، الأمر الذي يؤدي إلى ضعف الكفاءة التشغيلية والنظرية في المؤسسات ذات الصلة.

#### 3. التساؤلات الرئيسية والفرعية:
* **التساؤل الرئيس:** ما هو الأثر الحقيقي والمنهجي لتطبيق ({title})؟
* **التساؤلات الفرعية:** 
  1. كيف يسهم المتغير المستقل في تطوير البيئة البحثية؟
  2. ما هي المعوقات الأساسية التي تحول دون تفعيل المقترح؟

#### 4. أهمية البحث:
* **الأهمية النظرية:** إثراء المكتبة العربية والعراقية بإطار نظري حديث ومحكم.
* **الأهمية التطبيقية:** تقديم دليل استرشادي وتوصيات عملية لمتخذي القرار.

#### 5. أهداف البحث:
* تشخيص واقع تطبيق ({title}) ميدانياً.
* قياس مدى فاعلية المتغيرات المدروسة في الخطة.

#### 6. فرضيات البحث:
* **الفرضية الأولى:** توجد علاقة ارتباط ذات دلالة إحصائية بين المتغيرات الأساسية للعنوان.
* **الفرضية الثانية:** لا توجد فروق ذات دلالة إحصائية تعزى للمتغيرات الديموغرافية.

#### 7. متغيرات البحث:
* **المتغير المستقل (Independent):** الآليات المنهجية والتقنية المتبعة.
* **المتغير التابع (Dependent):** كفاءة الأداء وجودة المخرجات الأكاديمية.

#### 8. حدود البحث:
* **الحدود البشرية:** عينة من الأكاديميين والمختصين.
* **الحدود المكانية:** المؤسسات والجامعات العراقية ذات الصلة.
* **الحدود الزمانية:** العام الدراسي الحالي 2026.

#### 9. أدوات البحث المقترحة:
* تصميم **استبانة إلكترونية وميدانية** محكمة ومحسوبة الصدق والثبات.
* إجراء مقابلات شخصية نصف مهيكلة مع خبراء المجال.

#### 10. مقترح للدراسات السابقة ذات الصلة:
* دراسة (فاضل، 2025) حول الأنظمة الرقمية وتحديث المناهج العلمية.
* دراسة (صفا، 2026) حول آليات القياس والتقويم في الدراسات العليا."""

    return jsonify({"result": proposal_output})

@app.route('/tools/proposal/view')
def tool_proposal_view():
    return render_template('tool_proposal.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
