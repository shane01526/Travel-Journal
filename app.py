# app.py (modified)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import secrets
import logging
import traceback

# basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///travel_journal.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_google = db.Column(db.Boolean, default=False)
    journals = db.relationship('Journal', backref='author', lazy=True, cascade='all, delete-orphan')

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, default=0.0)
    lng = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# initialize db
with app.app_context():
    db.create_all()

def _get_request_data():
    """
    Helper: return a dict of data from JSON or form (form prioritized if present).
    """
    if request.is_json:
        try:
            return request.get_json() or {}
        except Exception:
            return {}
    # fallback to form (works for browser form POST)
    return request.form.to_dict()

@app.route('/')
def index():
    # If user logged in go to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    # try render welcome template; if missing, return a simple fallback so we don't 500
    try:
        return render_template('welcome.html')
    except Exception as e:
        logging.error("welcome.html render failed: %s", e)
        # provide a simple fallback HTML to help debug missing template on render platform
        html = """
        <!doctype html>
        <html>
          <head><title>Welcome - Travel Journal</title></head>
          <body>
            <h1>Welcome to Travel Journal</h1>
            <p>Template <code>welcome.html</code> not found or failed to render. Please check your templates folder.</p>
            <p><a href="/register">Register</a> | <a href="/login">Login</a></p>
          </body>
        </html>
        """
        return make_response(html, 200)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = _get_request_data()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not email or not password:
            # JSON client expects JSON response; form expects redirect/flash
            if request.is_json:
                return jsonify({'success': False, 'message': '請提供 email 與 password'}), 400
            flash('請提供 email 與 password')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            # for json client
            if request.is_json:
                return jsonify({'success': True})
            flash('登入成功')
            return redirect(url_for('dashboard'))
        # invalid credentials
        if request.is_json:
            return jsonify({'success': False, 'message': '帳號或密碼錯誤'}), 401
        flash('帳號或密碼錯誤')
        return redirect(url_for('login'))

    # GET
    try:
        return render_template('login.html')
    except Exception as e:
        logging.error("login.html render failed: %s", e)
        return """
        <h2>Login</h2>
        <form method="POST" action="/login">
          <label>Email: <input type="email" name="email"></label><br/>
          <label>Password: <input type="password" name="password"></label><br/>
          <input type="submit" value="Login">
        </form>
        """, 200

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = _get_request_data()
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        # validation
        if not name or not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'name, email, password 三者皆為必填'}), 400
            flash('name, email, password 三者皆為必填')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'message': '此帳號已存在'}), 409
            flash('此帳號已存在')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error("DB error on register: %s\n%s", e, traceback.format_exc())
            if request.is_json:
                return jsonify({'success': False, 'message': '資料庫錯誤，註冊失敗'}), 500
            flash('資料庫錯誤，註冊失敗')
            return redirect(url_for('register'))

        # persist session
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name

        if request.is_json:
            return jsonify({'success': True})
        flash('註冊成功')
        return redirect(url_for('dashboard'))

    # GET
    try:
        return render_template('register.html')
    except Exception as e:
        logging.error("register.html render failed: %s", e)
        # minimal fallback form
        return """
        <h2>Register</h2>
        <form method="POST" action="/register">
          <label>Name: <input type="text" name="name"></label><br/>
          <label>Email: <input type="email" name="email"></label><br/>
          <label>Password: <input type="password" name="password"></label><br/>
          <input type="submit" value="Register">
        </form>
        """, 200

@app.route('/google-login', methods=['POST'])
def google_login():
    # create a temporary google-like user (keeps previous logic)
    user_name = f'訪客使用者_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    email = f'google_{datetime.now().timestamp()}@gmail.com'
    password = generate_password_hash(secrets.token_hex(16))

    new_user = User(name=user_name, email=email, password=password, is_google=True)
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error("DB error google-login: %s", e)
        return jsonify({'success': False, 'message': '註冊訪客失敗'}), 500

    session['user_id'] = new_user.id
    session['user_name'] = new_user.name
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    journals = Journal.query.filter_by(user_id=user.id).order_by(Journal.created_at.desc()).all()
    countries = list({j.country for j in journals})
    return render_template('dashboard.html',
                           user=user,
                           journals=journals,
                           countries=countries,
                           journal_count=len(journals),
                           country_count=len(countries))

@app.route('/add_journal', methods=['GET', 'POST'])
def add_journal():
    """Convenience route for form-based journal submission (browser)."""
    if 'user_id' not in session:
        flash('請先登入')
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = _get_request_data()
        # reuse API creation logic
        # redirect to dashboard with flash on success/failure
        resp, status = _create_journal_from_data(data)
        if status == 201:
            flash('日誌新增成功')
            return redirect(url_for('dashboard'))
        else:
            flash(resp.get('message', '新增失敗'))
            return redirect(url_for('add_journal'))

    try:
        return render_template('add_journal.html')
    except Exception as e:
        logging.error("add_journal.html render failed: %s", e)
        # simple fallback form
        return """
        <h2>Add Journal</h2>
        <form method="POST" action="/add_journal">
          <label>Date (YYYY-MM-DD): <input type="text" name="date"></label><br/>
          <label>Location: <input type="text" name="location"></label><br/>
          <label>Country: <input type="text" name="country"></label><br/>
          <label>Content: <textarea name="content"></textarea></label><br/>
          <label>Lat: <input type="text" name="lat" value="0.0"></label><br/>
          <label>Lng: <input type="text" name="lng" value="0.0"></label><br/>
          <input type="submit" value="Save">
        </form>
        """, 200

def _create_journal_from_data(data):
    """
    Create journal from dict `data`. Returns (resp_dict, status_code).
    """
    if 'user_id' not in session:
        return ({'success': False, 'message': '未登入'}, 401)

    # required fields
    date = (data.get('date') or '').strip()
    location = (data.get('location') or '').strip()
    country = (data.get('country') or '').strip()
    content = (data.get('content') or '').strip()

    if not location or not country or not content:
        return ({'success': False, 'message': 'location, country, content 為必填'}, 400)

    # date fallback to today if empty
    if not date:
        date = datetime.utcnow().strftime('%Y-%m-%d')

    # parse lat/lng safely
    lat = 0.0
    lng = 0.0
    try:
        if 'lat' in data and data.get('lat') not in (None, ''):
            lat = float(data.get('lat'))
        if 'lng' in data and data.get('lng') not in (None, ''):
            lng = float(data.get('lng'))
    except ValueError:
        return ({'success': False, 'message': 'lat/lng 需為數值'}, 400)

    try:
        new_journal = Journal(
            date=date,
            location=location,
            country=country,
            content=content,
            lat=lat,
            lng=lng,
            user_id=session['user_id']
        )
        db.session.add(new_journal)
        db.session.commit()
        return ({'success': True, 'id': new_journal.id}, 201)
    except Exception as e:
        db.session.rollback()
        logging.error("DB error create journal: %s\n%s", e, traceback.format_exc())
        return ({'success': False, 'message': '資料庫錯誤，新增日誌失敗'}, 500)

@app.route('/api/journals', methods=['GET', 'POST'])
def journals_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    if request.method == 'POST':
        data = _get_request_data()
        resp, status = _create_journal_from_data(data)
        return jsonify(resp), status

    journals = Journal.query.filter_by(user_id=session['user_id']).order_by(Journal.created_at.desc()).all()
    return jsonify([{
        'id': j.id,
        'date': j.date,
        'location': j.location,
        'country': j.country,
        'content': j.content,
        'lat': j.lat,
        'lng': j.lng
    } for j in journals])

@app.route('/api/journals/<int:journal_id>', methods=['DELETE'])
def delete_journal(journal_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    journal = Journal.query.get_or_404(journal_id)
    if journal.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '無權限'}), 403

    try:
        db.session.delete(journal)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error("DB error delete journal: %s", e)
        return jsonify({'success': False, 'message': '刪除失敗'}), 500

@app.route('/api/journals/country/<country>')
def journals_by_country(country):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    journals = Journal.query.filter_by(user_id=session['user_id'], country=country).all()
    return jsonify([{
        'id': j.id,
        'date': j.date,
        'location': j.location,
        'country': j.country,
        'content': j.content
    } for j in journals])

@app.errorhandler(404)
def not_found(e):
    try:
        return render_template('404.html'), 404
    except:
        return "404 Not Found", 404

@app.errorhandler(500)
def server_error(e):
    # log the traceback for server logs but don't show it to users
    logging.error("Internal server error: %s\n%s", e, traceback.format_exc())
    try:
        return render_template('500.html'), 500
    except:
        return "500 Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
