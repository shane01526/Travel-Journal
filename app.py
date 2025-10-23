from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import secrets
import logging
import traceback
import base64
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳檔案大小為 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 資料庫配置函數
def get_database_url():
    """取得並驗證資料庫 URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.warning("DATABASE_URL 未設定，嘗試使用 Supabase 密碼")
        password = os.environ.get('SUPABASE_DB_PASSWORD')
        if password:
            database_url = f"postgresql://postgres:{password}@db.rtfdfsvqigdiadnffcxs.supabase.co:5432/postgres"
            logger.info("使用 Supabase 資料庫")
        else:
            logger.warning("資料庫連線資訊不完整，使用 SQLite")
            return 'sqlite:///travel_journal.db'
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if '@' in database_url:
        safe_url = '***@' + database_url.split('@')[-1]
    else:
        safe_url = database_url
    logger.info(f"使用資料庫: {safe_url}")
    
    return database_url

# 設定資料庫
database_url = get_database_url()
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 5,
    'max_overflow': 10,
    'connect_args': {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'
    } if 'postgresql' in database_url else {}
}

db = SQLAlchemy(app)

# 資料模型
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
    photo = db.Column(db.Text, nullable=True)  # 新增：儲存 base64 編碼的照片
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 初始化資料庫
def init_db():
    """初始化資料庫"""
    try:
        with app.app_context():
            db.engine.connect()
            logger.info("✅ 資料庫連線成功")
            db.create_all()
            logger.info("✅ 資料表建立/檢查完成")
            return True
    except Exception as e:
        logger.error(f"❌ 資料庫初始化失敗: {e}\n{traceback.format_exc()}")
        return False

# 輔助函數
def _get_request_data():
    """取得請求資料 (JSON 或表單)"""
    if request.is_json:
        try:
            return request.get_json() or {}
        except Exception:
            return {}
    return request.form.to_dict()

# 路由保持原樣，只修改需要的部分
@app.route('/')
def index():
    """首頁 - 顯示歡迎介面"""
    try:
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user:
                session.clear()
        
        return render_template('welcome.html', user=user)
    except Exception as e:
        logger.error(f"welcome.html 渲染失敗: {e}\n{traceback.format_exc()}")
        return make_response("""
        <!doctype html>
        <html>
          <head><title>Welcome - Travel Journal</title></head>
          <body>
            <h1>Welcome to Travel Journal</h1>
            <p><a href="/register">Register</a> | <a href="/login">Login</a></p>
          </body>
        </html>
        """, 200)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = _get_request_data()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': '請提供 email 與 password'}), 400
            flash('請提供 email 與 password')
            return redirect(url_for('login'))

        try:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                logger.info(f"用戶登入成功: {email}")
                
                if request.is_json:
                    return jsonify({'success': True})
                flash('登入成功')
                return redirect(url_for('dashboard'))
            
            if request.is_json:
                return jsonify({'success': False, 'message': '帳號或密碼錯誤'}), 401
            flash('帳號或密碼錯誤')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"登入錯誤: {e}\n{traceback.format_exc()}")
            if request.is_json:
                return jsonify({'success': False, 'message': '登入失敗，請稍後再試'}), 500
            flash('登入失敗，請稍後再試')
            return redirect(url_for('login'))

    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"login.html 渲染失敗: {e}")
        return "<h2>Login</h2><p>Template error</p>", 200

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = _get_request_data()
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not name or not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'name, email, password 三者皆為必填'}), 400
            flash('name, email, password 三者皆為必填')
            return redirect(url_for('register'))

        try:
            if User.query.filter_by(email=email).first():
                if request.is_json:
                    return jsonify({'success': False, 'message': '此帳號已存在'}), 409
                flash('此帳號已存在')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password)
            
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"新用戶註冊: {email}")
            
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name

            if request.is_json:
                return jsonify({'success': True})
            flash('註冊成功')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"註冊失敗: {e}\n{traceback.format_exc()}")
            if request.is_json:
                return jsonify({'success': False, 'message': '資料庫錯誤，註冊失敗'}), 500
            flash('資料庫錯誤，註冊失敗')
            return redirect(url_for('register'))

    try:
        return render_template('register.html')
    except Exception as e:
        logger.error(f"register.html 渲染失敗: {e}")
        return "<h2>Register</h2><p>Template error</p>", 200

@app.route('/google-login', methods=['POST'])
def google_login():
    try:
        user_name = f'訪客使用者_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        email = f'google_{datetime.now().timestamp()}@gmail.com'
        password = generate_password_hash(secrets.token_hex(16))

        new_user = User(name=user_name, email=email, password=password, is_google=True)
        
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"Google 登入成功: {email}")
        
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Google 登入失敗: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': '註冊訪客失敗'}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功登出')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """主控台 - 需要登入才能訪問"""
    if 'user_id' not in session:
        flash('請先登入才能查看日誌')
        return redirect(url_for('login'))

    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash('用戶不存在，請重新登入')
            return redirect(url_for('login'))

        journals = Journal.query.filter_by(user_id=user.id).order_by(Journal.date.desc(), Journal.created_at.desc()).all()
        
        journals_data = []
        for j in journals:
            journals_data.append({
                'id': j.id,
                'date': j.date,
                'location': j.location,
                'country': j.country,
                'content': j.content,
                'lat': float(j.lat) if j.lat else 0.0,
                'lng': float(j.lng) if j.lng else 0.0,
                'photo': j.photo  # 新增照片欄位
            })
        
        countries = list({j.country for j in journals})
        
        logger.info(f"用戶 {user.name} 查看 dashboard，共有 {len(journals)} 篇日誌")
        
        return render_template('dashboard.html',
                               user=user,
                               journals=journals_data,
                               countries=countries,
                               journal_count=len(journals),
                               country_count=len(countries))
    except Exception as e:
        logger.error(f"Dashboard 錯誤: {e}\n{traceback.format_exc()}")
        flash('載入日誌失敗，請稍後再試')
        return redirect(url_for('index'))

@app.route('/add_journal', methods=['GET', 'POST'])
def add_journal():
    if 'user_id' not in session:
        flash('請先登入')
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = _get_request_data()
        resp, status = _create_journal_from_data(data)
        if status == 201:
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            flash('日誌新增成功！')
            return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify(resp), status
            flash(resp.get('message', '新增失敗'))
            return redirect(url_for('add_journal'))

    try:
        return render_template('add_journal.html')
    except Exception as e:
        logger.error(f"add_journal.html 渲染失敗: {e}")
        return "<h2>Add Journal</h2><p>Template error</p>", 200

@app.route('/edit_journal/<int:journal_id>', methods=['GET'])
def edit_journal(journal_id):
    """編輯日誌頁面"""
    if 'user_id' not in session:
        flash('請先登入')
        return redirect(url_for('login'))

    try:
        journal = Journal.query.get_or_404(journal_id)
        if journal.user_id != session['user_id']:
            flash('無權限編輯此日誌')
            return redirect(url_for('dashboard'))

        return render_template('edit_journal.html', journal=journal)
    except Exception as e:
        logger.error(f"edit_journal.html 渲染失敗: {e}\n{traceback.format_exc()}")
        flash('頁面載入失敗')
        return redirect(url_for('dashboard'))

def _create_journal_from_data(data):
    """從資料建立日誌"""
    if 'user_id' not in session:
        return ({'success': False, 'message': '未登入'}, 401)

    try:
        date = (data.get('date') or '').strip()
        location = (data.get('location') or '').strip()
        country = (data.get('country') or '').strip()
        content = (data.get('content') or '').strip()
        photo = data.get('photo')  # 新增：取得照片 base64 資料

        logger.info(f"嘗試建立日誌: date={date}, location={location}, country={country}")

        if not location or not country or not content:
            return ({'success': False, 'message': 'location, country, content 為必填'}, 400)

        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%d')

        lat = 0.0
        lng = 0.0
        try:
            if 'lat' in data and data.get('lat') not in (None, '', 'null', 'undefined'):
                lat = float(data.get('lat'))
            if 'lng' in data and data.get('lng') not in (None, '', 'null', 'undefined'):
                lng = float(data.get('lng'))
        except (ValueError, TypeError) as e:
            logger.error(f"座標轉換錯誤: {e}")
            lat = 0.0
            lng = 0.0

        logger.info(f"座標值: lat={lat}, lng={lng}")

        new_journal = Journal(
            date=date,
            location=location,
            country=country,
            content=content,
            lat=lat,
            lng=lng,
            photo=photo,  # 新增：儲存照片
            user_id=session['user_id']
        )
        
        db.session.add(new_journal)
        db.session.commit()
        
        logger.info(f"✅ 日誌建立成功: ID={new_journal.id}, User={session['user_id']}, Location={location}")
        
        return ({'success': True, 'id': new_journal.id, 'journal': {
            'id': new_journal.id,
            'date': new_journal.date,
            'location': new_journal.location,
            'country': new_journal.country,
            'content': new_journal.content,
            'lat': new_journal.lat,
            'lng': new_journal.lng,
            'photo': new_journal.photo
        }}, 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 建立日誌失敗: {e}\n{traceback.format_exc()}")
        return ({'success': False, 'message': f'資料庫錯誤: {str(e)}'}, 500)

@app.route('/api/journals', methods=['GET', 'POST'])
def journals_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    if request.method == 'POST':
        data = _get_request_data()
        resp, status = _create_journal_from_data(data)
        return jsonify(resp), status

    try:
        journals = Journal.query.filter_by(user_id=session['user_id']).order_by(Journal.date.desc(), Journal.created_at.desc()).all()
        return jsonify([{
            'id': j.id,
            'date': j.date,
            'location': j.location,
            'country': j.country,
            'content': j.content,
            'lat': float(j.lat) if j.lat else 0.0,
            'lng': float(j.lng) if j.lng else 0.0,
            'photo': j.photo
        } for j in journals])
    except Exception as e:
        logger.error(f"取得日誌列表失敗: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': '取得日誌失敗'}), 500

@app.route('/api/journals/<int:journal_id>', methods=['GET', 'PUT', 'DELETE'])
def journal_detail(journal_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    try:
        journal = Journal.query.get_or_404(journal_id)
        if journal.user_id != session['user_id']:
            return jsonify({'success': False, 'message': '無權限'}), 403

        if request.method == 'DELETE':
            db.session.delete(journal)
            db.session.commit()
            logger.info(f"刪除日誌成功: {journal_id}")
            return jsonify({'success': True})
        
        elif request.method == 'PUT':
            data = _get_request_data()
            journal.date = data.get('date', journal.date)
            journal.location = data.get('location', journal.location)
            journal.country = data.get('country', journal.country)
            journal.content = data.get('content', journal.content)
            
            if 'photo' in data:
                journal.photo = data.get('photo')
            
            if 'lat' in data:
                try:
                    journal.lat = float(data.get('lat', 0))
                except (ValueError, TypeError):
                    journal.lat = 0.0
            if 'lng' in data:
                try:
                    journal.lng = float(data.get('lng', 0))
                except (ValueError, TypeError):
                    journal.lng = 0.0
            
            journal.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"更新日誌成功: {journal_id}")
            
            return jsonify({
                'success': True,
                'journal': {
                    'id': journal.id,
                    'date': journal.date,
                    'location': journal.location,
                    'country': journal.country,
                    'content': journal.content,
                    'lat': float(journal.lat) if journal.lat else 0.0,
                    'lng': float(journal.lng) if journal.lng else 0.0,
                    'photo': journal.photo
                }
            })
        
        return jsonify({
            'id': journal.id,
            'date': journal.date,
            'location': journal.location,
            'country': journal.country,
            'content': journal.content,
            'lat': float(journal.lat) if journal.lat else 0.0,
            'lng': float(journal.lng) if journal.lng else 0.0,
            'photo': journal.photo
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"日誌操作失敗: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': '操作失敗'}), 500

@app.route('/api/journals/country/<country>')
def journals_by_country(country):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401

    try:
        journals = Journal.query.filter_by(user_id=session['user_id'], country=country).all()
        return jsonify([{
            'id': j.id,
            'date': j.date,
            'location': j.location,
            'country': j.country,
            'content': j.content,
            'lat': float(j.lat) if j.lat else 0.0,
            'lng': float(j.lng) if j.lng else 0.0,
            'photo': j.photo
        } for j in journals])
    except Exception as e:
        logger.error(f"按國家查詢日誌失敗: {e}")
        return jsonify({'success': False, 'message': '查詢失敗'}), 500

@app.route('/health')
def health_check():
    """健康檢查端點"""
    try:
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
    try:
        return render_template('404.html'), 404
    except:
        return "404 Not Found", 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {e}\n{traceback.format_exc()}")
    try:
        return render_template('500.html'), 500
    except:
        return "500 Internal Server Error", 500

if __name__ != '__main__':
    init_db()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
