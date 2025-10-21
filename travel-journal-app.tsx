import React, { useState, useEffect } from 'react';
import { MapPin, Plus, X, LogOut, User, Calendar, Globe } from 'lucide-react';

const TravelJournalApp = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [showMapDetail, setShowMapDetail] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(null);
  
  // 表單狀態
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ email: '', password: '', name: '' });
  const [newEntry, setNewEntry] = useState({ date: '', location: '', country: '', content: '', lat: 0, lng: 0 });
  
  // 模擬資料庫
  const [users, setUsers] = useState(() => {
    const saved = localStorage.getItem('travelUsers');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [journals, setJournals] = useState(() => {
    const saved = localStorage.getItem('travelJournals');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('travelUsers', JSON.stringify(users));
  }, [users]);

  useEffect(() => {
    localStorage.setItem('travelJournals', JSON.stringify(journals));
  }, [journals]);

  // 登入處理
  const handleLogin = () => {
    const user = users.find(u => u.email === loginForm.email && u.password === loginForm.password);
    if (user) {
      setCurrentUser(user);
      setShowLogin(false);
      setLoginForm({ email: '', password: '' });
    } else {
      alert('帳號或密碼錯誤');
    }
  };

  // 註冊處理
  const handleRegister = () => {
    if (!registerForm.name || !registerForm.email || !registerForm.password) {
      alert('請填寫所有欄位');
      return;
    }
    if (users.find(u => u.email === registerForm.email)) {
      alert('此帳號已存在');
      return;
    }
    const newUser = { ...registerForm, id: Date.now() };
    setUsers([...users, newUser]);
    setCurrentUser(newUser);
    setShowLogin(false);
    setRegisterForm({ email: '', password: '', name: '' });
  };

  // Google 登入模擬
  const handleGoogleLogin = () => {
    const googleUser = {
      id: Date.now(),
      email: 'google_' + Date.now() + '@gmail.com',
      name: '訪客使用者',
      isGoogle: true
    };
    setUsers([...users, googleUser]);
    setCurrentUser(googleUser);
    setShowLogin(false);
  };

  // 新增日誌
  const handleAddEntry = () => {
    if (!newEntry.date || !newEntry.location || !newEntry.country || !newEntry.content) {
      alert('請填寫所有欄位');
      return;
    }
    const entry = {
      ...newEntry,
      id: Date.now(),
      userId: currentUser.id
    };
    setJournals([...journals, entry]);
    setShowNewEntry(false);
    setNewEntry({ date: '', location: '', country: '', content: '', lat: 0, lng: 0 });
  };

  // 取得使用者的日誌
  const getUserJournals = () => {
    return journals.filter(j => j.userId === currentUser?.id);
  };

  // 取得已訪問的國家
  const getVisitedCountries = () => {
    const userJournals = getUserJournals();
    const countries = [...new Set(userJournals.map(j => j.country))];
    return countries;
  };

  // 登出
  const handleLogout = () => {
    setCurrentUser(null);
    setShowWelcome(true);
    setShowLogin(false);
  };

  // 歡迎頁面
  if (showWelcome) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-stone-100 to-slate-200 relative overflow-hidden">
        {/* 背景裝飾 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 bg-rose-300 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-300 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/3 w-80 h-80 bg-amber-300 rounded-full blur-3xl"></div>
        </div>

        {/* 旅行元素裝飾 */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 opacity-20">
            <Globe className="w-32 h-32 text-slate-400 animate-pulse" style={{animationDuration: '4s'}} />
          </div>
          <div className="absolute bottom-1/3 right-1/4 opacity-20">
            <MapPin className="w-24 h-24 text-rose-400 animate-pulse" style={{animationDuration: '3s'}} />
          </div>
        </div>

        {/* 主要內容 */}
        <div className="relative min-h-screen flex flex-col items-center justify-center px-4">
          <div className="text-center mb-16">
            {/* Logo 區域 */}
            <div className="mb-8 flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-rose-300 to-slate-400 rounded-full blur-2xl opacity-30"></div>
                <div className="relative bg-white/40 backdrop-blur-md rounded-full p-8 shadow-2xl">
                  <Globe className="w-20 h-20 text-slate-600" />
                </div>
              </div>
            </div>

            {/* 標題 */}
            <h1 className="text-6xl md:text-7xl font-extralight text-slate-700 mb-4 tracking-wide">
              旅行日誌
            </h1>
            <div className="h-1 w-32 bg-gradient-to-r from-transparent via-slate-400 to-transparent mx-auto mb-6"></div>
            <p className="text-xl md:text-2xl text-slate-600 font-light mb-3">
              記錄每一段旅程
            </p>
            <p className="text-base text-slate-500 max-w-md mx-auto leading-relaxed">
              用文字與地圖，珍藏那些讓你心動的瞬間
            </p>
          </div>

          {/* 特色說明 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mb-16">
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 text-center hover:bg-white/80 transition-all">
              <div className="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-6 h-6 text-rose-500" />
              </div>
              <h3 className="text-slate-700 font-medium mb-2">地圖標記</h3>
              <p className="text-sm text-slate-500">在世界地圖上標記你的足跡</p>
            </div>
            
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 text-center hover:bg-white/80 transition-all">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-6 h-6 text-blue-500" />
              </div>
              <h3 className="text-slate-700 font-medium mb-2">旅行日誌</h3>
              <p className="text-sm text-slate-500">記錄每個地點的故事與回憶</p>
            </div>
            
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 text-center hover:bg-white/80 transition-all">
              <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="w-6 h-6 text-amber-500" />
              </div>
              <h3 className="text-slate-700 font-medium mb-2">探索世界</h3>
              <p className="text-sm text-slate-500">追蹤你走過的國家與城市</p>
            </div>
          </div>

          {/* 按鈕區域 */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => {
                setShowWelcome(false);
                setShowLogin(true);
                setIsRegister(false);
              }}
              className="px-10 py-4 bg-slate-500 hover:bg-slate-600 text-white rounded-2xl transition-all shadow-lg hover:shadow-xl text-lg font-light"
            >
              開始登入
            </button>
            <button
              onClick={() => {
                setShowWelcome(false);
                setShowLogin(true);
                setIsRegister(true);
              }}
              className="px-10 py-4 bg-white/80 hover:bg-white text-slate-700 rounded-2xl transition-all shadow-lg hover:shadow-xl text-lg font-light border-2 border-slate-200"
            >
              建立帳號
            </button>
          </div>

          {/* 底部裝飾文字 */}
          <div className="absolute bottom-8 text-center">
            <p className="text-slate-400 text-sm font-light">
              讓每一次旅行都值得被記住
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 登入/註冊畫面
  if (showLogin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-stone-100 via-slate-100 to-stone-200 flex items-center justify-center p-4">
        {/* 返回按鈕 */}
        <button
          onClick={() => {
            setShowWelcome(true);
            setShowLogin(false);
          }}
          className="absolute top-6 left-6 flex items-center space-x-2 text-slate-600 hover:text-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
          <span className="text-sm">返回</span>
        </button>

        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <Globe className="w-16 h-16 mx-auto mb-4 text-slate-500" />
            <h1 className="text-3xl font-light text-slate-700 mb-2">旅行日誌</h1>
            <p className="text-slate-500 text-sm">記錄你的美好時光</p>
          </div>

          {!isRegister ? (
            <div className="space-y-4">
              <div>
                <label className="block text-slate-600 text-sm mb-2">帳號</label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-slate-600 text-sm mb-2">密碼</label>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                />
              </div>
              <button onClick={handleLogin} className="w-full bg-slate-500 hover:bg-slate-600 text-white py-3 rounded-xl transition-colors">
                登入
              </button>
              <button onClick={handleGoogleLogin} className="w-full bg-white border-2 border-slate-300 hover:bg-slate-50 text-slate-700 py-3 rounded-xl transition-colors">
                使用 Google 登入
              </button>
              <p className="text-center text-slate-500 text-sm">
                還沒有帳號？ 
                <button onClick={() => setIsRegister(true)} className="text-slate-700 ml-1 underline">
                  註冊
                </button>
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-slate-600 text-sm mb-2">名字</label>
                <input
                  type="text"
                  value={registerForm.name}
                  onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-slate-600 text-sm mb-2">電子郵件</label>
                <input
                  type="email"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                />
              </div>
              <div>
                <label className="block text-slate-600 text-sm mb-2">密碼</label>
                <input
                  type="password"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
                />
              </div>
              <button onClick={handleRegister} className="w-full bg-slate-500 hover:bg-slate-600 text-white py-3 rounded-xl transition-colors">
                註冊
              </button>
              <p className="text-center text-slate-500 text-sm">
                已有帳號？ 
                <button onClick={() => setIsRegister(false)} className="text-slate-700 ml-1 underline">
                  登入
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 地圖詳細頁面
  if (showMapDetail) {
    const countryJournals = getUserJournals().filter(j => j.country === selectedCountry);
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-stone-100 via-slate-100 to-stone-200 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-light text-slate-700">{selectedCountry} 的旅行記錄</h2>
              <button onClick={() => setShowMapDetail(false)} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                <X className="w-6 h-6 text-slate-600" />
              </button>
            </div>

            <div className="bg-slate-200/50 rounded-2xl p-8 mb-6 h-96 flex items-center justify-center">
              <div className="text-center">
                <MapPin className="w-16 h-16 mx-auto mb-4 text-slate-400" />
                <p className="text-slate-500">互動式地圖區域</p>
                <p className="text-sm text-slate-400 mt-2">可放大縮小與滑動查看地標</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {countryJournals.map(journal => (
                <div key={journal.id} className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center text-slate-600 text-sm">
                      <Calendar className="w-4 h-4 mr-2" />
                      {journal.date}
                    </div>
                    <MapPin className="w-5 h-5 text-rose-400" />
                  </div>
                  <h3 className="text-lg font-medium text-slate-700 mb-2">{journal.location}</h3>
                  <p className="text-slate-600 text-sm leading-relaxed">{journal.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 新增日誌表單
  if (showNewEntry) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-stone-100 via-slate-100 to-stone-200 p-6 flex items-center justify-center">
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8 w-full max-w-2xl">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-light text-slate-700">新增旅行日誌</h2>
            <button onClick={() => setShowNewEntry(false)} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
              <X className="w-6 h-6 text-slate-600" />
            </button>
          </div>

          <div className="space-y-5">
            <div>
              <label className="block text-slate-600 text-sm mb-2">日期</label>
              <input
                type="date"
                value={newEntry.date}
                onChange={(e) => setNewEntry({...newEntry, date: e.target.value})}
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
              />
            </div>
            
            <div>
              <label className="block text-slate-600 text-sm mb-2">國家</label>
              <input
                type="text"
                value={newEntry.country}
                onChange={(e) => setNewEntry({...newEntry, country: e.target.value})}
                placeholder="例：日本、法國、泰國"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
              />
            </div>

            <div>
              <label className="block text-slate-600 text-sm mb-2">地點</label>
              <input
                type="text"
                value={newEntry.location}
                onChange={(e) => setNewEntry({...newEntry, location: e.target.value})}
                placeholder="例：東京晴空塔、艾菲爾鐵塔"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400"
              />
            </div>

            <div>
              <label className="block text-slate-600 text-sm mb-2">旅行日誌</label>
              <textarea
                value={newEntry.content}
                onChange={(e) => setNewEntry({...newEntry, content: e.target.value})}
                placeholder="記錄下這段美好的回憶..."
                rows="6"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-slate-400 resize-none"
              />
            </div>

            <button onClick={handleAddEntry} className="w-full bg-slate-500 hover:bg-slate-600 text-white py-3 rounded-xl transition-colors">
              儲存日誌
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 主畫面
  const visitedCountries = getVisitedCountries();
  const userJournals = getUserJournals();

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-100 via-slate-100 to-stone-200 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 頂部導航 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-6 mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-slate-300 rounded-full flex items-center justify-center">
                <User className="w-6 h-6 text-slate-600" />
              </div>
              <div>
                <h2 className="text-xl font-light text-slate-700">嗨，{currentUser?.name}</h2>
                <p className="text-sm text-slate-500">{visitedCountries.length} 個國家 · {userJournals.length} 則日誌</p>
              </div>
            </div>
            <button onClick={handleLogout} className="flex items-center space-x-2 px-4 py-2 hover:bg-slate-100 rounded-xl transition-colors">
              <LogOut className="w-5 h-5 text-slate-600" />
              <span className="text-slate-600">登出</span>
            </button>
          </div>
        </div>

        {/* 世界地圖 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8 mb-6">
          <h3 className="text-xl font-light text-slate-700 mb-6">我的足跡地圖</h3>
          <div className="bg-slate-200/50 rounded-2xl p-12 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <Globe className="w-20 h-20 mx-auto mb-4 text-slate-400" />
              <p className="text-slate-500 mb-6">世界地圖互動區域</p>
              {visitedCountries.length > 0 && (
                <div className="flex flex-wrap gap-3 justify-center">
                  {visitedCountries.map(country => (
                    <button
                      key={country}
                      onClick={() => {
                        setSelectedCountry(country);
                        setShowMapDetail(true);
                      }}
                      className="px-6 py-3 bg-rose-400/80 hover:bg-rose-500 text-white rounded-full transition-colors shadow-sm"
                    >
                      <MapPin className="w-4 h-4 inline mr-2" />
                      {country}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 最近的日誌 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl p-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-light text-slate-700">最近的旅行</h3>
            <button
              onClick={() => setShowNewEntry(true)}
              className="flex items-center space-x-2 px-5 py-2.5 bg-slate-500 hover:bg-slate-600 text-white rounded-xl transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>新增日誌</span>
            </button>
          </div>

          {userJournals.length === 0 ? (
            <div className="text-center py-12">
              <MapPin className="w-16 h-16 mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">還沒有旅行記錄</p>
              <p className="text-sm text-slate-400 mt-2">點擊「新增日誌」開始記錄你的旅程</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {userJournals.slice(-6).reverse().map(journal => (
                <div key={journal.id} className="bg-slate-50 rounded-2xl p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center text-slate-600 text-sm">
                      <Calendar className="w-4 h-4 mr-2" />
                      {journal.date}
                    </div>
                    <span className="text-xs bg-rose-100 text-rose-600 px-3 py-1 rounded-full">
                      {journal.country}
                    </span>
                  </div>
                  <h4 className="text-lg font-medium text-slate-700 mb-2">{journal.location}</h4>
                  <p className="text-slate-600 text-sm leading-relaxed line-clamp-3">{journal.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TravelJournalApp;