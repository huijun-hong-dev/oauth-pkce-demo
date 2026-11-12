from flask import Flask, redirect, request, session, jsonify
import requests, secrets, hashlib, base64

app = Flask(__name__)
app.secret_key = "my_super_secret_key_1234567890_abcdefg" # 用于加密 Session

# 配置项（这里是 Fake 服务器的地址）
CLIENT_ID = "my_client_id_123"
CLIENT_SECRET = "my_client_secret_456"
REDIRECT_URI = "http://localhost:5005/callback"
AUTHORIZE_URL = "http://localhost:5001/authorize" # 以后换成 Amazon 地址
TOKEN_URL = "http://localhost:5001/token"         # 以后换成 Amazon 地址

@app.route('/login')
def login():
    """第一步：发起授权，生成并保存 PKCE"""
    # 1. 生成 state
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    # 2. 生成 PKCE 对
    code_verifier = secrets.token_urlsafe(64)
    session['code_verifier'] = code_verifier # 存在后端 Session 里！
    print(f"\n🔑 [Web App] 生成 PKCE 对: {code_verifier}")

    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
    print(f"\n🔑 based on {code_verifier}: {code_challenge}")
    
    # 3. 拼接 URL 并跳转
    auth_url = f"{AUTHORIZE_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={state}&code_challenge={code_challenge}&code_challenge_method=S256"
    print(f"\n🚀 [Web App] 用户点击登录，准备跳转到:\n{auth_url}")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """第二步：处理回调，换 Token"""
    print("\n🔄 [Web App] 收到第三方回调...")
    
    # 1. 校验 state (防 CSRF)
    if request.args.get('state') != session.get('oauth_state'):
        return "State 校验失败，可能是 CSRF 攻击", 400
    
    code = request.args.get('code')
    code_verifier = session.pop('code_verifier', None) # 取出后即销毁
    
    # 2. 发起 POST 请求换 Token
    print(f"🔄 [Web App] 拿着 Code 去换 Token...")
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code_verifier': code_verifier
    }
    
    resp = requests.post(TOKEN_URL, data=token_data)
    if resp.status_code != 200:
        return f"换 Token 失败: {resp.text}", 500
        
    tokens = resp.json()
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens.get('refresh_token')
    
    print(f"🎉 [Web App] 成功拿到 Token: {tokens['access_token']}")
    
    return f"<h1>登录成功！</h1><p>Token: {tokens['access_token']}</p><a href='/'>返回首页</a>"

@app.route('/')
def index():
    if 'access_token' not in session:
        return "<a href='/login'>点击这里去第三方授权登录</a>"
    return f"<h1>你已登录</h1><p>Access Token: {session['access_token']}</p><a href='/logout'>退出</a>"

@app.route('/logout')
def logout():
    session.clear()
    return "已退出，<a href='/'>点此重新登录</a>"

if __name__ == '__main__':
    app.run(port=5005, debug=True)