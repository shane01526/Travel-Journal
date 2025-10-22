from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 資料庫配置 - 修正版
def get_database_url():
    """取得並驗證資料庫 URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.error("DATABASE_URL 環境變數未設定")
        return None
    
    # 移除密碼後顯示 (用於日誌)
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    logger.info(f"使用資料庫: ***@{safe_url}")
    
    # 強制使用 IPv4 - 添加 connect_args
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
    }
else:
    logger.warning("未設定資料庫,使用 SQLite")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 資料模型
class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }

# 初始化資料庫
def init_db():
    try:
        with app.app_context():
            # 測試連線
            db.engine.connect()
            logger.info("資料庫連線成功")
            
            # 建立資料表
            db.create_all()
            logger.info("資料表建立/檢查完成")
            return True
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        return False

# 路由
@app.route('/')
def index():
    """首頁"""
    try:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()
        return render_template('index.html', todos=todos)
    except Exception as e:
        logger.error(f"取得待辦事項失敗: {e}")
        return render_template('index.html', todos=[], error=str(e))

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """取得所有待辦事項"""
    try:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()
        return jsonify([todo.to_dict() for todo in todos])
    except Exception as e:
        logger.error(f"API 取得待辦事項失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """新增待辦事項"""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': '標題不能為空'}), 400
        
        todo = Todo(title=data['title'])
        db.session.add(todo)
        db.session.commit()
        
        logger.info(f"新增待辦事項: {todo.title}")
        return jsonify(todo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"新增待辦事項失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """更新待辦事項"""
    try:
        todo = Todo.query.get_or_404(todo_id)
        data = request.get_json()
        
        if 'title' in data:
            todo.title = data['title']
        if 'completed' in data:
            todo.completed = data['completed']
        
        db.session.commit()
        logger.info(f"更新待辦事項: {todo.id}")
        return jsonify(todo.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新待辦事項失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """刪除待辦事項"""
    try:
        todo = Todo.query.get_or_404(todo_id)
        db.session.delete(todo)
        db.session.commit()
        
        logger.info(f"刪除待辦事項: {todo_id}")
        return jsonify({'message': '刪除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"刪除待辦事項失敗: {e}")
        return jsonify({'error': str(e)}), 500

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

# 初始化資料庫
if __name__ != '__main__':
    # 在 gunicorn 啟動時初始化
    init_db()

if __name__ == '__main__':
    # 本地開發模式
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
