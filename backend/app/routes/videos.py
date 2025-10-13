from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.video import Video
from app.models.scaffolding import Scaffolding, ScaffoldingResponse
from app.models.event_log import EventLog
import json

videos_bp = Blueprint('videos', __name__)

@videos_bp.route('/', methods=['GET'])
@jwt_required()
def get_videos():
    videos = Video.query.filter_by(is_active=True).order_by(Video.order_index).all()
    return jsonify([video.to_dict() for video in videos]), 200


@videos_bp.route('/<int:video_id>', methods=['GET'])
@jwt_required()
def get_video(video_id):
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({'error': '비디오를 찾을 수 없습니다'}), 404
    
    # Log video view
    log_event(user_id, video_id, 'video_view', {})
    
    video_data = video.to_dict()
    
    # Include scaffoldings if applicable
    if video.scaffolding_mode in ['prompt', 'both']:
        scaffoldings = Scaffolding.query.filter_by(
            video_id=video_id, 
            is_active=True
        ).order_by(Scaffolding.order_index).all()
        
        video_data['scaffoldings'] = []
        for scaffolding in scaffoldings:
            scaffolding_data = scaffolding.to_dict()
            
            # Check if user has responded
            response = ScaffoldingResponse.query.filter_by(
                scaffolding_id=scaffolding.id,
                user_id=user_id
            ).first()
            
            if response:
                scaffolding_data['user_response'] = response.to_dict()
            
            video_data['scaffoldings'].append(scaffolding_data)
    
    return jsonify(video_data), 200


@videos_bp.route('/<int:video_id>/scaffoldings/<int:scaffolding_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_scaffolding(video_id, scaffolding_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    response_text = data.get('response_text')
    
    if not response_text:
        return jsonify({'error': '응답 내용을 입력해주세요'}), 400
    
    scaffolding = Scaffolding.query.get(scaffolding_id)
    
    if not scaffolding or scaffolding.video_id != video_id:
        return jsonify({'error': '스캐폴딩을 찾을 수 없습니다'}), 404
    
    # Check if response already exists
    existing_response = ScaffoldingResponse.query.filter_by(
        scaffolding_id=scaffolding_id,
        user_id=user_id
    ).first()
    
    if existing_response:
        existing_response.response_text = response_text
    else:
        new_response = ScaffoldingResponse(
            scaffolding_id=scaffolding_id,
            user_id=user_id,
            response_text=response_text
        )
        db.session.add(new_response)
    
    db.session.commit()
    
    # Log event
    log_event(user_id, video_id, 'scaffolding_response', {
        'scaffolding_id': scaffolding_id,
        'response_length': len(response_text)
    })
    
    return jsonify({'message': '응답이 저장되었습니다'}), 200


@videos_bp.route('/<int:video_id>/event', methods=['POST'])
@jwt_required()
def log_video_event(video_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    event_type = data.get('event_type')
    event_data = data.get('event_data', {})
    
    if not event_type:
        return jsonify({'error': '이벤트 타입을 지정해주세요'}), 400
    
    log_event(user_id, video_id, event_type, event_data)
    
    return jsonify({'message': '이벤트가 기록되었습니다'}), 200


def log_event(user_id, video_id, event_type, event_data):
    event_log = EventLog(
        user_id=user_id,
        video_id=video_id,
        event_type=event_type,
        event_data=json.dumps(event_data),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    db.session.add(event_log)
    db.session.commit()

