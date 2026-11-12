from flask import Flask, request, redirect, jsonify
import hashlib, base64, secrets

app = Flask(__name__)
fake_codes = {}
fake_tokens = {}

@app.route('/authorize')
def authorize():
    redirect_uri = request.args.get('redirect_uri')
    state = request.args.get('state')
    code_challenge = request.args.get('code_challenge')
    
    print(f"\n👉 [Fake Auth] 收到授权请求，Challenge: {code_challenge}")
    code = secrets.token_urlsafe(16)
    fake_codes[code] = {'challenge': code_challenge, 'redirect_uri': redirect_uri}
    
    print(f"✅ [Fake Auth] 生成授权码: {code}，重定向回客户端...")
    return redirect(f"{redirect_uri}?code={code}&state={state}")

@app.route('/token', methods=['POST'])
def token():
    grant_type = request.form.get('grant_type')
    if grant_type == 'authorization_code':
        code = request.form.get('code')
        code_verifier = request.form.get('code_verifier')
        
        code_data = fake_codes.get(code)
        if not code_data:
            return jsonify({"error": "invalid_grant"}), 400
            
        sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        calculated_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
        
        if calculated_challenge != code_data['challenge']:
            print("❌ [Fake Auth] PKCE 校验失败！")
            return jsonify({"error": "invalid_grant", "error_description": "PKCE 不匹配"}), 400
        
        print("✅ [Fake Auth] PKCE 校验成功，发放 Token！")
        del fake_codes[code]
        
        return jsonify({
            "access_token": f"fake_access_{secrets.token_hex(8)}",
            "refresh_token": f"fake_refresh_{secrets.token_hex(8)}",
            "token_type": "Bearer",
            "expires_in": 3600
        })

if __name__ == '__main__':
    app.run(port=5001, debug=True)