@app.route('/add_journal', methods=['GET', 'POST'])
def add_journal():
    """新增日志页面"""
    if 'user_id' not in session:
        flash('請先登入')
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = _get_request_data()
        resp, status = _create_journal_from_data(data)
        
        if status == 201:
            # API 请求：返回 JSON 并告知前端要导向 dashboard
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': '日誌新增成功',
                    'redirect': url_for('dashboard')
                }), 201
            
            # 表单提交：直接导向 dashboard
            flash('日誌新增成功！')
            return redirect(url_for('dashboard'))
        else:
            # 失败情况
            if request.is_json:
                return jsonify(resp), status
            flash(resp.get('message', '新增失敗'))
            return redirect(url_for('add_journal'))

    # GET 请求：显示新增日志页面
    try:
        return render_template('add_journal.html')
    except Exception as e:
        logger.error(f"add_journal.html 渲染失敗: {e}")
        return "<h2>Add Journal</h2><p>Template error</p>", 200


@app.route('/dashboard')
def dashboard():
    """主控台 - 需要登入才能访问"""
    if 'user_id' not in session:
        flash('請先登入才能查看日誌')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('用戶不存在，請重新登入')
        return redirect(url_for('login'))

    # 获取用户的所有日志
    journals = Journal.query.filter_by(user_id=user.id)\
                             .order_by(Journal.created_at.desc())\
                             .all()
    
    # 统计国家数量
    countries = list({j.country for j in journals})
    
    return render_template('dashboard.html',
                           user=user,
                           journals=journals,
                           countries=countries,
                           journal_count=len(journals),
                           country_count=len(countries))


@app.route('/')
def index():
    """首页 - 显示欢迎介面"""
    # 不自动导向，让用户可以看到欢迎介面
    # 已登入用户可以选择进入 dashboard 或登出
    try:
        return render_template('welcome.html')
    except Exception as e:
        logger.error(f"welcome.html 渲染失敗: {e}")
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
