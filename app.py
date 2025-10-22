from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import secrets
import logging
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# 資料庫配置
def get_database_url():
    """取得並驗證資料庫 URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.warning("DATABASE_URL 未設定，嘗試使用 Supabase 密碼")
        # 嘗試使用 Supabase 密碼
        password = os.environ.get('SUPABASE_DB_PASSWORD')
        if password:
            database_url = f"postgresql://postgres:{password}@db.rtfdfsvqigdiadnffcxs.supabase.co:5432/postgres"
            logger.info("使用 Supabase 資料庫")
        else:
            logger.error("資料庫連線資訊不完整")
            return None
    
    # 移除密碼後顯示 (用於日誌)
    if '@' in database_url:
        safe_url = '***@' + database_url.split('@')[-1]
    else:
        safe_url = database_url
    logger.info(f"使用資料庫: {safe_url}")
    
    # 確保使用 postgresql:// 前綴
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url

# 設定資料庫
database_url = get_database_url()
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        },
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10
    }
else:
    logger.warning("未設定資料庫，使用 SQLite")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_journal.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 資料庫模型
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_google = db.Column(db.Boolean, default=False)
    journals = db.relationship('Journal', backref='author', lazy=True, cascade='all, delete-orphan')

class Journal(db.Model):
    __tablename__ = 'journals'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, default=0.0)
    lng = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 初始化資料庫
def init_db():
    try:
        with app.app_context():
            # 測試連線
            db.engine.connect()
            logger.info("✅ 資料庫連線成功")
            
            # 建立資料表
            db.create_all()
            logger.info("✅ 資料表建立/檢查完成")
            return True
    except Exception as e:
        logger.error(f"❌ 資料庫初始化失敗: {e}")
        return False

# 路由
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': '帳號或密碼錯誤'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '此帳號已存在'})
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        return jsonify({'success': True})
    
    return render_template('register.html')

@app.route('/google-login', methods=['POST'])
def google_login():
    user_name = f'訪客使用者_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    email = f'google_{datetime.now().timestamp()}@gmail.com'
    password = generate_password_hash(secrets.token_hex(16))
    
    new_user = User(name=user_name, email=email, password=password, is_google=True)
    db.session.add(new_user)
    db.session.commit()
    
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
    
    countries = list(set([j.country for j in journals]))
    
    return render_template('dashboard.html', 
                         user=user, 
                         journals=journals, 
                         countries=countries,
                         journal_count=len(journals),
                         country_count=len(countries))

@app.route('/add_journal')
def add_journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('add_journal.html')

@app.route('/api/journals', methods=['GET', 'POST'])
def journals_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            new_journal = Journal(
                date=data['date'],
                location=data['location'],
                country=data['country'],
                content=data['content'],
                lat=data.get('lat', 0.0),
                lng=data.get('lng', 0.0),
                user_id=session['user_id']
            )
            db.session.add(new_journal)
            db.session.commit()
            logger.info(f"新增日誌成功: {new_journal.id}")
            return jsonify({'success': True, 'id': new_journal.id})
        except Exception as e:
            db.session.rollback()
            logger.error(f"新增日誌失敗: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
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
    
    try:
        journal = Journal.query.get_or_404(journal_id)
        if journal.user_id != session['user_id']:
            return jsonify({'success': False, 'message': '無權限'}), 403
        
        db.session.delete(journal)
        db.session.commit()
        logger.info(f"刪除日誌成功: {journal_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"刪除日誌失敗: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

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

@app.route('/health')
def health_check():
    """健康檢查"""
    try:
        # 測試資料庫連線
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
        logger.error(f"健康檢查失敗: {e}")
    
    return jsonify({
        'status': 'ok' if db_status == 'healthy' else 'degraded',
        'database': db_status
    })

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# 初始化資料庫
if __name__ != '__main__':
    # 在 gunicorn 啟動時初始化
    init_db()

if __name__ == '__main__':
    # 本地開發模式
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
