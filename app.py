
from flask import Flask, render_template, request, redirect, session, jsonify
import json, os

app = Flask(__name__)
app.secret_key = 'hacker_secret'

USERS_FILE = 'users.json'
MESSAGES_FILE = 'messages.json'

def load_data(file):
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)
    with open(file, 'r') as f:
        return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

@app.route('/')
def home():
    if 'user' in session:
        return render_template('chat.html', username=session['user'])
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    users = load_data(USERS_FILE)
    data = request.form
    for user in users:
        if user['username'] == data['username'] and user['password'] == data['password']:
            session['user'] = user['username']
            return redirect('/')
    return 'Identifiants invalides', 401

@app.route('/register', methods=['POST'])
def register():
    users = load_data(USERS_FILE)
    data = request.form
    if any(u['username'] == data['username'] for u in users):
        return 'Utilisateur existe déjà', 400
    users.append({'username': data['username'], 'password': data['password']})
    save_data(USERS_FILE, users)
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/messages')
def get_messages():
    messages = load_data(MESSAGES_FILE)
    return jsonify(messages)

@app.route('/messages', methods=['POST'])
def post_message():
    if 'user' not in session:
        return 'Non autorisé', 403
    messages = load_data(MESSAGES_FILE)
    messages.append({'user': session['user'], 'text': request.form['text']})
    save_data(MESSAGES_FILE, messages)
    return '', 204

if __name__ == '__main__':
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
