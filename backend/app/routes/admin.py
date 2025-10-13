from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models.user import User
from app.models.video import Video
from app.models.scaffolding import Scaffolding
from app.models.chat_prompt_template import ChatPromptTemplate
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role not in ['admin', 'super']:
            return jsonify({'error': '관리자 권한이 필요합니다'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def super_admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'super':
            return jsonify({'error': '최고 관리자 권한이 필요합니다'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


# User Management
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@super_admin_required
def update_user_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['user', 'admin', 'super']:
        return jsonify({'error': '올바르지 않은 권한입니다'}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
    
    user.role = new_role
    db.session.commit()
    
    return jsonify(user.to_dict()), 200


@admin_bp.route('/users/<int:user_id>/activate', methods=['PUT'])
@admin_required
def toggle_user_activation(user_id):
    data = request.get_json()
    is_active = data.get('is_active')
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
    
    user.is_active = is_active
    db.session.commit()
    
    return jsonify(user.to_dict()), 200


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({'error': '새 비밀번호를 입력해주세요'}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
    
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    return jsonify({'message': '비밀번호가 재설정되었습니다'}), 200


# Video Management
@admin_bp.route('/videos', methods=['POST'])
@admin_required
def create_video():
    data = request.get_json()
    
    video = Video(
        title=data.get('title'),
        youtube_url=data.get('youtube_url'),
        youtube_id=data.get('youtube_id'),
        description=data.get('description'),
        duration=data.get('duration'),
        thumbnail_url=data.get('thumbnail_url'),
        scaffolding_mode=data.get('scaffolding_mode', 'both'),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify(video.to_dict()), 201


@admin_bp.route('/videos/<int:video_id>', methods=['PUT'])
@admin_required
def update_video(video_id):
    data = request.get_json()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({'error': '비디오를 찾을 수 없습니다'}), 404
    
    if 'title' in data:
        video.title = data['title']
    if 'description' in data:
        video.description = data['description']
    if 'scaffolding_mode' in data:
        video.scaffolding_mode = data['scaffolding_mode']
    if 'is_active' in data:
        video.is_active = data['is_active']
    if 'order_index' in data:
        video.order_index = data['order_index']
    
    db.session.commit()
    
    return jsonify(video.to_dict()), 200


@admin_bp.route('/videos/<int:video_id>', methods=['DELETE'])
@admin_required
def delete_video(video_id):
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({'error': '비디오를 찾을 수 없습니다'}), 404
    
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'message': '비디오가 삭제되었습니다'}), 200


# Scaffolding Management
@admin_bp.route('/videos/<int:video_id>/scaffoldings', methods=['POST'])
@admin_required
def create_scaffolding(video_id):
    data = request.get_json()
    
    scaffolding = Scaffolding(
        video_id=video_id,
        title=data.get('title'),
        prompt_text=data.get('prompt_text'),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(scaffolding)
    db.session.commit()
    
    return jsonify(scaffolding.to_dict()), 201


@admin_bp.route('/scaffoldings/<int:scaffolding_id>', methods=['PUT'])
@admin_required
def update_scaffolding(scaffolding_id):
    data = request.get_json()
    scaffolding = Scaffolding.query.get(scaffolding_id)
    
    if not scaffolding:
        return jsonify({'error': '스캐폴딩을 찾을 수 없습니다'}), 404
    
    if 'title' in data:
        scaffolding.title = data['title']
    if 'prompt_text' in data:
        scaffolding.prompt_text = data['prompt_text']
    if 'order_index' in data:
        scaffolding.order_index = data['order_index']
    if 'is_active' in data:
        scaffolding.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(scaffolding.to_dict()), 200


@admin_bp.route('/scaffoldings/<int:scaffolding_id>', methods=['DELETE'])
@admin_required
def delete_scaffolding(scaffolding_id):
    scaffolding = Scaffolding.query.get(scaffolding_id)
    
    if not scaffolding:
        return jsonify({'error': '스캐폴딩을 찾을 수 없습니다'}), 404
    
    db.session.delete(scaffolding)
    db.session.commit()
    
    return jsonify({'message': '스캐폴딩이 삭제되었습니다'}), 200


# Prompt Template Management
@admin_bp.route('/prompts', methods=['GET'])
@admin_required
def get_prompts():
    prompts = ChatPromptTemplate.query.all()
    return jsonify([prompt.to_dict() for prompt in prompts]), 200


@admin_bp.route('/prompts', methods=['POST'])
@admin_required
def create_prompt():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # If setting as default, unset other defaults
    if data.get('is_default'):
        ChatPromptTemplate.query.filter_by(is_default=True).update({'is_default': False})
    
    prompt = ChatPromptTemplate(
        name=data.get('name'),
        description=data.get('description'),
        system_prompt=data.get('system_prompt'),
        constraints=data.get('constraints'),
        video_id=data.get('video_id'),
        user_role=data.get('user_role'),
        is_default=data.get('is_default', False),
        created_by=user_id
    )
    
    db.session.add(prompt)
    db.session.commit()
    
    return jsonify(prompt.to_dict()), 201


@admin_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
@admin_required
def update_prompt(prompt_id):
    data = request.get_json()
    prompt = ChatPromptTemplate.query.get(prompt_id)
    
    if not prompt:
        return jsonify({'error': '프롬프트를 찾을 수 없습니다'}), 404
    
    # If setting as default, unset other defaults
    if data.get('is_default') and not prompt.is_default:
        ChatPromptTemplate.query.filter_by(is_default=True).update({'is_default': False})
    
    if 'name' in data:
        prompt.name = data['name']
    if 'description' in data:
        prompt.description = data['description']
    if 'system_prompt' in data:
        prompt.system_prompt = data['system_prompt']
    if 'constraints' in data:
        prompt.constraints = data['constraints']
    if 'video_id' in data:
        prompt.video_id = data['video_id']
    if 'user_role' in data:
        prompt.user_role = data['user_role']
    if 'is_active' in data:
        prompt.is_active = data['is_active']
    if 'is_default' in data:
        prompt.is_default = data['is_default']
    
    prompt.version += 1
    
    db.session.commit()
    
    return jsonify(prompt.to_dict()), 200


@admin_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@admin_required
def delete_prompt(prompt_id):
    prompt = ChatPromptTemplate.query.get(prompt_id)
    
    if not prompt:
        return jsonify({'error': '프롬프트를 찾을 수 없습니다'}), 404
    
    if prompt.is_default:
        return jsonify({'error': '기본 프롬프트는 삭제할 수 없습니다'}), 400
    
    db.session.delete(prompt)
    db.session.commit()
    
    return jsonify({'message': '프롬프트가 삭제되었습니다'}), 200

