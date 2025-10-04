from flask import Flask, render_template
from database import init_db

# 데이터베이스 초기화 (앱 시작 시 한 번만 실행)
init_db()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
