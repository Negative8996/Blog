import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Config BDD
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SocketIO
socketio = SocketIO(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    text = db.Column(db.Text)

# Routes
@app.route('/')
def home():
    if 'user' in session:
        return render_template('chat.html', username=session['user'])
    return redirect('/login')

@app.route('/login', methods=['GET'])
@app.route('/register', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user'] = user.username
        return redirect('/')
    return 'Identifiants invalides', 401

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    if User.query.filter_by(username=data['username']).first():
        return 'Utilisateur existe déjà', 400
    new_user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(new_user)
    db.session.commit()
    session['user'] = new_user.username
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# SocketIO : envoi/recevoir messages
@socketio.on('send_message')
def handle_message(data):
    if 'user' not in session:
        return
    msg = Message(username=session['user'], text=data['text'])
    db.session.add(msg)
    db.session.commit()
    emit('receive_message', {'user': msg.username, 'text': msg.text}, broadcast=True)

# SocketIO : envoie tous les anciens messages
@socketio.on('load_messages')
def load_messages():
    messages = Message.query.order_by(Message.id.asc()).all()
    for msg in messages:
        emit('receive_message', {'user': msg.username, 'text': msg.text})

# Fonction d'initialisation base de données
def init_db():
    with app.app_context():
        db.create_all()

# Run
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
