import sqlite3
import os
from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from flask_frozen import Freezer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
freezer = Freezer(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATABASE'] = os.path.join(app.instance_path, 'flaskr.sqlite')
app.config['BASE_URL'] = '/Instagram'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    print('Initialized the database.')

@app.context_processor
def inject_base_url():
    return dict(url_for=lambda endpoint, **values: app.config['BASE_URL'] + url_for(endpoint, **values))

@app.route('/')
def home():
    db = get_db()
    posts = db.execute(
        'SELECT post.image, user.username FROM post JOIN user ON post.user_id = user.id'
    ).fetchall()
    return render_template('home.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        db = get_db()
        try:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, hashed_password)
            )
            db.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
    return render_template('register.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            db = get_db()
            db.execute(
                'INSERT INTO post (user_id, image) VALUES (?, ?)',
                (session['user_id'], filename)
            )
            db.commit()
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()  # Initialize the database
    freezer.freeze()
    app.run(debug=True)
