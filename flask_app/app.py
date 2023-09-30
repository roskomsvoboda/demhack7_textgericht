from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def get_texts(source=None, manipulation_method=None):
    conn = sqlite3.connect('../notebooks/text_database.db')
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
        conditions.append(f"m.manipulation_method_name = '{manipulation_method}'")

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' GROUP BY t.id'

    cursor.execute(query)
    texts = cursor.fetchall()

    conn.close()

    return texts

@app.route('/')
def index():
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

if __name__ == '__main__':
    app.run(debug=True)
