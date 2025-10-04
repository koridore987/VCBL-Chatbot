from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from database import init_db

# 데이터베이스 초기화 (앱 시작 시 한 번만 실행)
init_db()

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_123!@#'  # 세션을 위한 시크릿키 설정

# 루트 경로: 로그인 페이지 렌더링
@app.route('/', methods=['GET'])
def login_page():
    return render_template('login.html')

# 로그인 처리: POST만 허용
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    if not username:
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    try:
        # username이 이미 있는지 확인
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            user_id = row[0]
        else:
            # 없으면 새로 추가
            cursor.execute("INSERT INTO user (username) VALUES (?)", (username,))
            conn.commit()
            user_id = cursor.lastrowid
        # 세션에 user_id 저장
        session['user_id'] = user_id
    finally:
        conn.close()
    return redirect(url_for('chat'))

# /chat 경로: 로그인된 사용자만 접근 가능
@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

# 메시지 전송 API
@app.route('/send_message', methods=['POST'])
def send_message():
    import openai
    from config import OPENAI_API_KEY

    openai.api_key = OPENAI_API_KEY

    # 세션에서 user_id 가져오기
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401

    user_id = session['user_id']

    # JSON 데이터에서 메시지 추출
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': '메시지가 필요합니다'}), 400

    message = data['message']

    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()

    try:
        # 사용자 메시지를 데이터베이스에 저장
        cursor.execute(
            "INSERT INTO message (user_id, sender, content) VALUES (?, ?, ?)",
            (user_id, 'user', message)
        )

        # OpenAI API 호출로 챗봇 답변 생성
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            bot_reply = response.choices[0].message.content.strip()
        except Exception as e:
            return jsonify({'error': f'OpenAI API 오류: {str(e)}'}), 500

        # 봇 답변을 데이터베이스에 저장
        cursor.execute(
            "INSERT INTO message (user_id, sender, content) VALUES (?, ?, ?)",
            (user_id, 'bot', bot_reply)
        )

        conn.commit()

        # 봇 답변을 JSON으로 반환
        return jsonify({'reply': bot_reply})

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': '데이터베이스 오류가 발생했습니다'}), 500

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
