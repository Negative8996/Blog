import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'hacker_secret'

# Configuration base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Home (chat si connecté, sinon redirection login)
@app.route('/')
def home():
    if 'user' in session:
        return render_template('chat.html', username=session['user'])
    return redirect('/login')

# Affiche login.html (formulaires login/register)
@app.route('/login', methods=['GET'])
@app.route('/register', methods=['GET'])
def show_login():
    return render_template('login.html')

# Traitement connexion
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user'] = user.username
        return redirect('/')
    return 'Identifiants invalides', 401

# Traitement inscription
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

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# Initialisation BDD si nécessaire
@app.before_first_request
def create_tables():
    db.create_all()

# Lancement de l'app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
