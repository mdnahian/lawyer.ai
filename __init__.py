from flask import Flask, request, url_for
from lawyerai import exe_api
import sqlite3
import os

app = Flask(__name__)



@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)




@app.route('/', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        text = request.form['text']
        print text
        response = str(exe_api(text))
        print response
        conn = sqlite3.connect('C:\Users\mdnah\Desktop\lawyerai\lawyerai.db')
        c = conn.cursor()
        c.execute('INSERT INTO sessions VALUES (?)', (response,))
        conn.commit()
    return 'running...'




@app.route('/get')
def get():
    conn = sqlite3.connect('C:\Users\mdnah\Desktop\lawyerai\lawyerai.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sessions')
    sessions = c.fetchall()
    response = '['
    for session in sessions:
        response += session[0] + ','
    response = response[:-1]
    response += ']'
    return response




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)