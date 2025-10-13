from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models.user import User
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    student_id = data.get('student_id')
    password = data.get('password')
    name = data.get('name')
    
    if not all([student_id, password, name]):
        return jsonify({'error': '모든 필드를 입력해주세요'}), 400
    
    if User.query.filter_by(student_id=student_id).first():
        return jsonify({'error': '이미 존재하는 학번입니다'}), 409
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    user = User(
        student_id=student_id,
        password_hash=password_hash,
        name=name,
        role='user'
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '회원가입이 완료되었습니다',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    student_id = data.get('student_id')
    password = data.get('password')
    
    if not all([student_id, password]):
        return jsonify({'error': '학번과 비밀번호를 입력해주세요'}), 400
    
    user = User.query.filter_by(student_id=student_id).first()
    
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': '학번 또는 비밀번호가 올바르지 않습니다'}), 401
    
    if not user.is_active:
        return jsonify({'error': '비활성화된 계정입니다'}), 403
    
    # Reset daily token count if needed
    if user.last_token_reset.date() < datetime.utcnow().date():
        user.daily_token_usage = 0
        user.last_token_reset = datetime.utcnow()
        db.session.commit()
    
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/password-reset-request', methods=['POST'])
def password_reset_request():
    data = request.get_json()
    student_id = data.get('student_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
    
    # In production, this should send a notification to admin
    return jsonify({
        'message': '비밀번호 재설정 요청이 관리자에게 전달되었습니다'
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not all([old_password, new_password]):
        return jsonify({'error': '모든 필드를 입력해주세요'}), 400
    
    user = User.query.get(user_id)
    
    if not user or not bcrypt.check_password_hash(user.password_hash, old_password):
        return jsonify({'error': '현재 비밀번호가 올바르지 않습니다'}), 401
    
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    return jsonify({'message': '비밀번호가 변경되었습니다'}), 200

