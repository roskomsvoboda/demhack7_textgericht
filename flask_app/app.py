import sqlite3
import openai
from get_chatgpt_criteria import *
from flask import Flask, render_template, request, session, url_for, redirect, abort

app = Flask(__name__)
app.url_map.strict_slashes = False
app.secret_key = os.urandom(12)
openai.api_key = os.getenv("OPENAI_API_KEY")
WEBPAGE_PASSWORD = 'demhack7'
DATABASE_PATH = './sample_database.db'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form['password']
        if password == WEBPAGE_PASSWORD:
            print('Password correct.')
            session[f'logged_in'] = True
            return redirect(url_for('corpus_page'))
        else:
            print('Password incorrect.')
            error = 'Invalid credentials.'
    return render_template('login.html', error=error)

@app.errorhandler(404)
def not_found(e):
  return render_template("404.html")

def get_texts(source=None, manipulation_method=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT t.*, GROUP_CONCAT(m.manipulation_method_name) as manipulation_methods
        FROM texts t
        LEFT JOIN text_2_manipulation_methods tm ON t.id = tm.text_id
        LEFT JOIN manipulation_methods m ON tm.manipulation_method_id = m.id
    '''

    conditions = []

    if source:
        conditions.append(f"t.source = '{source}'")

    if manipulation_method:
        conditions.append(f"m.manipulation_method_name LIKE '{manipulation_method}'")

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' GROUP BY t.id'

    cursor.execute(query)
    texts = cursor.fetchall()

    conn.close()

    return texts

@app.route('/corpus')
def corpus_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    texts = get_texts()
    return render_template('index.html', texts=texts)

@app.route('/filter', methods=['GET', 'POST'])
def filter_texts():
    if request.method == 'POST':
        source = request.form.get('source')
        manipulation_method = request.form.get('manipulation_method')
        texts = get_texts(source=source, manipulation_method=manipulation_method)
    else:
        texts = get_texts()

    return render_template('index.html', texts=texts, source=source, manipulation_method=manipulation_method)


def analyze_text(text):
    return process_text(text)

@app.route('/analyse_text', methods=['GET', 'POST'])
def analyse_text():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    analysis_result = None

    if request.method == 'POST':
        user_text = request.form['user_text']
        analysis_result = analyze_text(user_text)

    return render_template('analyse_text.html', analysis_result=analysis_result)

def get_text_details(text_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query to retrieve text details by ID
    cursor.execute('''
        SELECT * FROM texts
        WHERE id = ?
    ''', (text_id,))

    text_details = cursor.fetchone()

    cursor.execute('''
        SELECT * FROM text_2_manipulation_methods 
        WHERE text_id = ?
    ''', (text_details[0],))

    # Fetch all the records
    records = cursor.fetchall()
    manip_ids = [r[1] for r in records]
    manip_fragments = [r[2] for r in records]
    manip_labels = []
    for manip_id in manip_ids:
        cursor.execute('''
            SELECT * FROM manipulation_methods 
            WHERE id = ?
        ''', (manip_id,))

        # Fetch all the records
        records = cursor.fetchall()
        manip_labels.extend([r[1] for r in records])
    text_details = dict(text_details)
    text_details['manipulation_methods'] = manip_labels
    text_details['manipulation_fragments'] = manip_fragments
    print(text_details)
    conn.close()

    return text_details

@app.route('/texts/<int:text_id>')
def text_details(text_id):
    text_details = get_text_details(text_id)

    if text_details:
        return render_template('text_details.html', text_details=text_details)
    else:
        abort(404)
        
if __name__ == '__main__':
    app.run(debug=True)
