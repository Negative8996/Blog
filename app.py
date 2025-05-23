from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'hacker_secret'

# Render PostgreSQL URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    text = db.Column(db.String(500), nullable=False)

# Crée les tables si elles n'existent pas
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    if 'user' in session:
        return render_template('chat.html', username=session['user'])
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
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/messages')
def get_messages():
    messages = Message.query.order_by(Message.id.asc()).all()
    return jsonify([{'user': m.user, 'text': m.text} for m in messages])

@socketio.on('send_message')
def handle_send_message(data):
    if 'user' not in session:
        return
    msg = Message(user=session['user'], text=data['text'])
    db.session.add(msg)
    db.session.commit()
    emit('new_message', {'user': msg.user, 'text': msg.text}, broadcast=True)

# Lancer l'application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
